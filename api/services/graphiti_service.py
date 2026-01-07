"""
Graphiti Service - Real-time knowledge graph for entity tracking.

Uses Graphiti for temporal entity extraction and hybrid search.
"""

from __future__ import annotations

import os
import json
import logging
from datetime import datetime
from typing import Optional, Any
from uuid import uuid4

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
# Note: search_config_recipes not available in graphiti-core 0.24.3
from api.models.memevolve import TrajectoryData
from api.services.llm_service import chat_completion, GPT5_NANO

logger = logging.getLogger(__name__)

try:
    from neo4j.graph import Node, Relationship, Path
    from neo4j.time import DateTime, Date, Time, Duration
except Exception:  # pragma: no cover - optional import guard
    Node = Relationship = Path = DateTime = Date = Time = Duration = ()


def _normalize_neo4j_value(value: Any) -> Any:
    if isinstance(value, Node) or isinstance(value, Relationship):
        return {k: _normalize_neo4j_value(v) for k, v in dict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (DateTime, Date, Time)):
        return value.to_native().isoformat()
    if isinstance(value, Duration):
        return {
            "months": value.months,
            "days": value.days,
            "seconds": value.seconds,
            "nanoseconds": value.nanoseconds,
        }
    if isinstance(value, list):
        return [_normalize_neo4j_value(item) for item in value]
    if isinstance(value, dict):
        return {k: _normalize_neo4j_value(v) for k, v in value.items()}
    return value


class GraphitiConfig:
    """Configuration for Graphiti service."""

    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        group_id: str = "dionysus",
        index_build_timeout_seconds: Optional[float] = None,
        cypher_timeout_seconds: Optional[float] = None,
        health_check_timeout_seconds: Optional[float] = None,
        skip_index_build: Optional[bool] = None,
    ):
        # 1. Start with provided or env URI
        raw_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")

        # 2. Auto-detection for local vs docker vs VPS
        import platform

        # Default to localhost if host.docker.internal is present but we are on Darwin (local Mac)
        if "host.docker.internal" in raw_uri and platform.system() == "Darwin":
            logger.info("Local environment detected. Switching host.docker.internal -> localhost")
            raw_uri = raw_uri.replace("host.docker.internal", "localhost")

        # If using docker-internal host outside Docker, fall back to external host/URI
        if "neo4j" in raw_uri and not os.path.exists("/.dockerenv"):
            external_uri = os.getenv("NEO4J_EXTERNAL_URI")
            external_host = os.getenv("NEO4J_EXTERNAL_HOST", "72.61.78.89")
            raw_uri = external_uri or raw_uri.replace("neo4j", external_host)
            
        self.neo4j_uri = raw_uri
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.group_id = group_id
        self.index_build_timeout_seconds = (
            index_build_timeout_seconds
            if index_build_timeout_seconds is not None
            else float(os.getenv("GRAPHITI_INDEX_BUILD_TIMEOUT", "20"))
        )
        self.cypher_timeout_seconds = (
            cypher_timeout_seconds
            if cypher_timeout_seconds is not None
            else float(os.getenv("GRAPHITI_CYPHER_TIMEOUT", "20"))
        )
        self.health_check_timeout_seconds = (
            health_check_timeout_seconds
            if health_check_timeout_seconds is not None
            else float(os.getenv("GRAPHITI_HEALTH_TIMEOUT", "5"))
        )
        self.skip_index_build = (
            skip_index_build
            if skip_index_build is not None
            else os.getenv("GRAPHITI_SKIP_INDEX_BUILD", "false").lower() == "true"
        )

        if not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD environment variable required")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable required")


import asyncio
import threading

# Dedicated thread and loop for Graphiti operations to ensure thread-safety
_graphiti_loop: Optional[asyncio.AbstractEventLoop] = None
_graphiti_thread: Optional[threading.Thread] = None

def _start_graphiti_loop():
    global _graphiti_loop
    _graphiti_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_graphiti_loop)
    _graphiti_loop.run_forever()

def get_graphiti_loop() -> asyncio.AbstractEventLoop:
    global _graphiti_thread, _graphiti_loop
    if _graphiti_thread is None:
        _graphiti_thread = threading.Thread(target=_start_graphiti_loop, daemon=True)
        _graphiti_thread.start()
        # Wait for loop to be initialized
        import time
        while _graphiti_loop is None:
            time.sleep(0.1)
    return _graphiti_loop

# Global Graphiti instance
_global_graphiti: Optional[Graphiti] = None
_global_graphiti_lock = threading.Lock() # Use threading lock for initialization

class GraphitiService:
    """
    Service wrapper for Graphiti knowledge graph operations.

    Provides:
    - Episode ingestion with entity extraction
    - Hybrid search (semantic + keyword + graph)
    - Temporal tracking of facts

    Note: Now uses a global client instance to maintain stable event loop connection.
    """

    def __init__(self, config: Optional[GraphitiConfig] = None):
        self.config = config or GraphitiConfig()
        self._initialized = False
        self._index_build_task: Optional[asyncio.Task] = None

    @classmethod
    async def get_instance(cls, config: Optional[GraphitiConfig] = None) -> "GraphitiService":
        """Create or return existing instance with global graphiti client."""
        instance = cls(config)
        await instance.initialize()
        return instance

    async def initialize(self) -> None:
        """Initialize Graphiti connection and indexes."""
        global _global_graphiti
        
        if self._initialized:
            return

        with _global_graphiti_lock:
            if _global_graphiti is None:
                logger.info(f"Initializing Global Graphiti with Neo4j at {self.config.neo4j_uri}")
                _global_graphiti = Graphiti(
                    uri=self.config.neo4j_uri,
                    user=self.config.neo4j_user,
                    password=self.config.neo4j_password,
                )
                # Build indexes (safe, won't delete existing) in background
                if self.config.skip_index_build:
                    logger.info("Skipping Graphiti index build (GRAPHITI_SKIP_INDEX_BUILD=true).")
                elif self._index_build_task is None:
                    self._index_build_task = asyncio.create_task(
                        _global_graphiti.build_indices_and_constraints(delete_existing=False)
                    )
                    self._index_build_task.add_done_callback(self._handle_index_build_result)

                if self._index_build_task is not None:
                    try:
                        await asyncio.wait_for(
                            asyncio.shield(self._index_build_task),
                            timeout=self.config.index_build_timeout_seconds,
                        )
                    except asyncio.TimeoutError:
                        logger.warning(
                            "Graphiti index build timed out; continuing in background."
                        )

        self._initialized = True
        logger.info("Graphiti Service initialized successfully")

    @staticmethod
    def _handle_index_build_result(task: asyncio.Task) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.warning(f"Graphiti index build failed: {exc}")

    async def close(self) -> None:
        """Note: Global instance is not closed per-request."""
        pass

    def _get_graphiti(self) -> Graphiti:
        if _global_graphiti is None:
            raise RuntimeError("GraphitiService not initialized")
        return _global_graphiti

    async def ingest_message(
        self,
        content: str,
        source_description: str = "conversation",
        group_id: Optional[str] = None,
        valid_at: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Ingest a message/episode and extract entities.
        """
        graphiti = self._get_graphiti()
        group = group_id or self.config.group_id
        timestamp = valid_at or datetime.now()

        logger.info(f"Ingesting message into group '{group}': {content[:100]}...")

        result = await graphiti.add_episode(
            name=f"episode_{uuid4().hex[:8]}",
            episode_body=content,
            source=EpisodeType.message,
            source_description=source_description,
            group_id=group,
            reference_time=timestamp,
        )

        logger.info(
            f"Extracted {len(result.nodes)} entities, "
            f"{len(result.edges)} relationships"
        )

        return {
            "episode_uuid": str(result.episode.uuid) if result.episode else None,
            "nodes": [
                {
                    "uuid": str(n.uuid),
                    "name": n.name,
                    "labels": getattr(n, "labels", []),
                    "summary": getattr(n, "summary", None),
                }
                for n in result.nodes
            ],
            "edges": [
                {
                    "uuid": str(e.uuid),
                    "name": e.name,
                    "fact": e.fact,
                    "source": str(e.source_node_uuid),
                    "target": str(e.target_node_uuid),
                }
                for e in result.edges
            ],
        }

    @staticmethod
    def _format_trajectory_text(trajectory: TrajectoryData, max_chars: int = 8000) -> str:
        metadata = trajectory.metadata
        metadata_lines = []
        if metadata:
            if metadata.agent_id:
                metadata_lines.append(f"Agent: {metadata.agent_id}")
            if metadata.session_id:
                metadata_lines.append(f"Session: {metadata.session_id}")
            if metadata.project_id:
                metadata_lines.append(f"Project: {metadata.project_id}")

        lines: list[str] = []
        if metadata_lines:
            lines.append("Metadata: " + " | ".join(metadata_lines))

        for idx, step in enumerate(trajectory.steps, start=1):
            if step.observation:
                lines.append(f"Step {idx} Observation: {step.observation}")
            if step.thought:
                lines.append(f"Step {idx} Thought: {step.thought}")
            if step.action:
                lines.append(f"Step {idx} Action: {step.action}")

        text = "\n".join(lines).strip()
        if len(text) > max_chars:
            text = text[:max_chars].rstrip() + "\n[truncated]"
        return text

    async def _summarize_trajectory(self, trajectory_text: str) -> str:
        if not trajectory_text:
            return "Empty trajectory."

        system_prompt = (
            "You are a concise technical summarizer. Summarize the agent trajectory "
            "in 1-3 sentences, focusing on key observations, decisions, and outcomes."
        )
        try:
            return await chat_completion(
                messages=[{"role": "user", "content": trajectory_text}],
                system_prompt=system_prompt,
                model=GPT5_NANO,
                max_tokens=1024,
            )
        except Exception as exc:
            logger.warning(f"Trajectory summarization failed: {exc}")
            fallback = trajectory_text[:280].rstrip()
            return f"{fallback}..." if len(trajectory_text) > 280 else fallback

    @staticmethod
    def _parse_json_response(text: str) -> dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # Remove opening/closing backticks and potential "json" tag
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()
                
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end >= start:
            cleaned = cleaned[start:end + 1]
        
        if not cleaned:
            return {}
            
        try:
            return json.loads(cleaned)
        except Exception as e:
            logger.error(f"Failed to parse JSON response from LLM: {e}. Cleaned text: {cleaned}")
            return {}

    @staticmethod
    def _normalize_entity_objects(payload: dict[str, Any]) -> list[dict[str, Any]]:
        entities: list[dict[str, Any]] = []

        for item in payload.get("entities", []):
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if not name:
                continue
            entities.append(
                {
                    "name": str(name),
                    "type": str(item.get("type", "concept")),
                    "description": item.get("description"),
                }
            )

        return entities

    @staticmethod
    def _normalize_relationship_objects(payload: dict[str, Any]) -> list[dict[str, Any]]:
        relationships: list[dict[str, Any]] = []

        for item in payload.get("relationships", []):
            if not isinstance(item, dict):
                continue
            source = item.get("source")
            target = item.get("target")
            relation = item.get("relation")
            if not source or not target or not relation:
                continue
            relationships.append(
                {
                    "source": str(source),
                    "target": str(target),
                    "relation": str(relation),
                    "evidence": item.get("evidence"),
                }
            )

        return relationships

    @staticmethod
    def _normalize_extraction(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        entities = GraphitiService._normalize_entity_objects(payload)
        relationships = GraphitiService._normalize_relationship_objects(payload)
        return entities, relationships

    @staticmethod
    def _normalize_relationships_with_confidence(
        raw_relationships: list[dict[str, Any]],
        confidence_threshold: float,
    ) -> tuple[list[dict[str, Any]], int, int]:
        approved: list[dict[str, Any]] = []
        pending: list[dict[str, Any]] = []

        for rel in raw_relationships:
            confidence = float(rel.get("confidence", 0.5))
            normalized = {
                "source": rel.get("source", ""),
                "target": rel.get("target", ""),
                "relation_type": rel.get("type", rel.get("relation", "RELATES_TO")),
                "confidence": confidence,
                "evidence": rel.get("evidence", ""),
                "status": "approved" if confidence >= confidence_threshold else "pending_review",
            }

            if confidence >= confidence_threshold:
                approved.append(normalized)
            else:
                pending.append(normalized)

        return approved + pending, len(approved), len(pending)

    async def extract_and_structure_from_trajectory(
        self,
        trajectory: TrajectoryData,
    ) -> dict[str, Any]:
        """
        Extract summary, entities, and relationships from a trajectory using LLM calls.

        Returns:
            Dict with keys: summary, entities, relationships
        """
        trajectory_text = self._format_trajectory_text(trajectory)
        summary = trajectory.summary or await self._summarize_trajectory(trajectory_text)

        system_prompt = (
            "You are an information extraction system. Extract named entities "
            "(people, organizations, tools, concepts) and relationships from the trajectory. "
            "Respond with JSON only using this schema:\n"
            "{\n"
            "  \"entities\": [{\"name\": \"...\", \"type\": \"person|organization|tool|concept|other\", "
            "\"description\": \"short\"}],\n"
            "  \"relationships\": [{\"source\": \"...\", \"target\": \"...\", \"relation\": \"...\", "
            "\"evidence\": \"...\"}]\n"
            "}"
        )
        extraction_text = f"Summary:\n{summary}\n\nTrajectory:\n{trajectory_text}"

        entities: list[dict[str, Any]] = []
        relationships: list[dict[str, Any]] = []

        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": extraction_text}],
                system_prompt=system_prompt,
                model=GPT5_NANO,
                max_tokens=4096,
            )
            parsed = self._parse_json_response(response)
            entities, relationships = self._normalize_extraction(parsed)
        except Exception as exc:
            logger.warning(f"Trajectory extraction failed: {exc}")

        return {
            "summary": summary,
            "entities": entities,
            "relationships": relationships,
        }

    async def extract_with_context(
        self,
        content: str,
        basin_context: Optional[str] = None,
        strategy_context: Optional[str] = None,
        confidence_threshold: float = 0.6,
        model: str = None,
    ) -> dict[str, Any]:
        """
        Extract entities and relationships with optional basin/strategy context.
        
        Consolidates extraction logic used by KGLearningService and provides
        confidence-scored relationships for threshold gating.
        
        Args:
            content: Text to extract from
            basin_context: Attractor basin context for guiding extraction
            strategy_context: Cognition strategy context (prioritized relation types)
            confidence_threshold: Minimum confidence for auto-approval (default 0.6)
            model: LLM model to use (defaults to GPT5_NANO)
            
        Returns:
            Dict with entities, relationships (with confidence), approved/pending counts
        """
        use_model = model or GPT5_NANO
        
        # Build context-aware prompt
        context_section = ""
        if basin_context:
            context_section += f"\nCONTEXT FROM ATTRACTOR BASINS:\n{basin_context}\n"
        if strategy_context:
            context_section += f"\n{strategy_context}\n"
        
        prompt = f"""You are an expert knowledge extraction agent.
{context_section}
Analyze the following document and extract key CONCEPTS and semantic RELATIONSHIPS.

DOCUMENT:
{content[:4000]}

Respond ONLY with a JSON object:
{{
    "entities": ["concept1", "concept2"],
    "relationships": [
        {{"source": "A", "target": "B", "type": "EXTENDS", "confidence": 0.9, "evidence": "..."}}
    ]
}}

IMPORTANT:
- Each relationship must have a confidence score between 0.0 and 1.0
- Use specific relationship types like EXTENDS, VALIDATES, CONTRADICTS, REPLACES, CAUSES, ENABLES
- Provide brief evidence for each relationship
"""
        
        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="Extract structured knowledge with confidence-scored relationships.",
                model=use_model,
                max_tokens=2048
            )
            
            parsed = self._parse_json_response(response)
            entities = parsed.get("entities", [])
            raw_relationships = parsed.get("relationships", [])
            relationships, approved_count, pending_count = self._normalize_relationships_with_confidence(
                raw_relationships,
                confidence_threshold,
            )
            
            return {
                "entities": entities,
                "relationships": relationships,
                "approved_count": approved_count,
                "pending_count": pending_count,
                "confidence_threshold": confidence_threshold,
                "model_used": str(use_model),
            }
            
        except Exception as e:
            logger.error(f"Context-aware extraction failed: {e}")
            return {
                "entities": [],
                "relationships": [],
                "approved_count": 0,
                "pending_count": 0,
                "error": str(e),
            }

    async def ingest_extracted_relationships(
        self,
        relationships: list[dict[str, Any]],
        source_id: str,
        group_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Ingest pre-extracted relationships without re-extraction.
        
        This bypasses Graphiti's internal extraction when relationships
        are already extracted by extract_with_context.
        
        Args:
            relationships: List of relationship dicts with source/target/type/evidence
            source_id: Source identifier for provenance
            group_id: Optional group ID for the ingestion
            
        Returns:
            Dict with ingestion results
        """
        graphiti = self._get_graphiti()
        group = group_id or self.config.group_id
        ingested = 0
        errors = []
        
        for rel in relationships:
            if rel.get("status") != "approved":
                continue
                
            try:
                fact = (
                    f"{rel['source']} {rel['relation_type']} {rel['target']}. "
                    f"Evidence: {rel.get('evidence', 'N/A')}"
                )
                
                await graphiti.add_episode(
                    name=f"fact_{uuid4().hex[:8]}",
                    episode_body=fact,
                    source=EpisodeType.message,
                    source_description=source_id,
                    group_id=group,
                    reference_time=datetime.now(),
                )
                ingested += 1
                
            except Exception as e:
                errors.append({"relationship": rel, "error": str(e)})
                logger.warning(f"Failed to ingest relationship: {e}")
        
        return {
            "ingested": ingested,
            "skipped": len(relationships) - ingested - len(errors),
            "errors": errors,
        }

    async def ingest_contextual_triplet(
        self,
        head_id: str,
        relation: str,
        tail_id: str,
        context: dict[str, Any],
        group_id: Optional[str] = None,
        source_id: Optional[str] = None,
    ) -> bool:
        """
        Ingest a reified Triplet node with rich Relation Context (RC).
        Follows the (h, r, t, rc) quadruple structure used by CGR3/ToG-3.
        
        Args:
            head_id: ID/Label of the subject
            relation: Predicate type
            tail_id: ID/Label of the object
            context: Dictionary of RC properties (confidence, temporal, geographic, etc.)
            group_id: Optional group filter
            source_id: Optional source provenance ID
            
        Returns:
            True if ingestion was successful
        """
        tid = f"{head_id}_{relation}_{tail_id}"
        
        # Flatten context for Neo4j properties
        props = {
            "id": tid,
            "relation": relation,
            "confidence": context.get("confidence", 1.0),
            "geographic": context.get("geographic"),
            "provenance": json.dumps(context.get("provenance", [])),
            "source_id": source_id,
            "group_id": group_id or self.config.group_id
        }
        
        # Add temporal and custom details if present
        if temporal := context.get("temporal"):
            for k, v in temporal.items():
                props[f"temporal_{k}"] = v
        
        if details := context.get("details"):
            for k, v in details.items():
                props[f"prop_{k}"] = v

        cypher = """
        MERGE (h:Entity {id: $head_id})
        SET h.name = coalesce(h.name, $head_id)
        MERGE (t:Entity {id: $tail_id})
        SET t.name = coalesce(t.name, $tail_id)
        MERGE (tr:Triplet {id: $tid})
        SET tr += $props
        MERGE (h)-[:HAS_SUBJECT_OF]->(tr)
        MERGE (tr)-[:HAS_OBJECT_OF]->(t)
        """
        try:
            await self.execute_query(cypher, {
                "head_id": head_id,
                "tail_id": tail_id,
                "tid": tid,
                "props": props
            })
            return True
        except Exception as e:
            logger.error(f"Failed to ingest contextual triplet: {e}")
            return False

    async def search(
        self,
        query: str,
        group_ids: Optional[list[str]] = None,
        limit: int = 10,
        use_cross_encoder: bool = False,
    ) -> dict[str, Any]:
        """
        Hybrid search across entities and relationships.
        """
        graphiti = self._get_graphiti()
        groups = group_ids or [self.config.group_id]

        logger.info(f"Searching for: {query}")

        results = await graphiti.search(
            query=query,
            group_ids=groups,
            num_results=limit,
        )
        
        # graphiti-core 0.24.3 returns a list of edges directly
        edges = results if isinstance(results, list) else getattr(results, 'edges', [])
        
        return {
            "edges": [
                {
                    "uuid": str(e.uuid),
                    "name": getattr(e, "name", None),
                    "fact": getattr(e, "fact", None),
                    "valid_at": e.valid_at.isoformat() if getattr(e, "valid_at", None) else None,
                    "invalid_at": e.invalid_at.isoformat() if getattr(e, "invalid_at", None) else None,
                }
                for e in edges
            ],
            "count": len(edges),
        }

    async def execute_cypher(
        self,
        statement: str,
        params: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Sole authorized gateway for direct Cypher execution.
        Proxies through Graphiti's internal driver with a Destruction Gate.
        """
        import re
        params = params or {}
        
        # 1. Destruction Gate: Scan for destructive keywords
        destructive_pattern = re.compile(r"\b(DELETE|DETACH|DROP|REMOVE)\b", re.IGNORECASE)
        is_destructive = destructive_pattern.search(statement)
        
        if is_destructive:
            # Check for two-step authorization flags
            authorized = params.get("fingerprint_authorized", False)
            confirmed = params.get("user_confirmed", False)
            
            if not (authorized and confirmed):
                logger.warning(f"BLOCKING destructive Cypher: {statement}")
                return [{
                    "error": "DESTRUCTION_GATE_TRIGGERED",
                    "requires": ["fingerprint", "confirmation"],
                    "statement": statement,
                    "reason": "Destructive operations require biometric (fingerprint) and manual confirmation."
                }]

        # 2. Proxy to internal driver
        graphiti = self._get_graphiti()
        try:
            result = await asyncio.wait_for(
                graphiti.driver.execute_query(statement, params=params),
                timeout=self.config.cypher_timeout_seconds,
            )
            
            records = getattr(result, "records", None)
            if records is None:
                raw = result if isinstance(result, list) else []
                return [_normalize_neo4j_value(row) for row in raw]
            return [_normalize_neo4j_value(record.data()) for record in records]
            
        except asyncio.TimeoutError:
            logger.warning("Graphiti Cypher execution timed out.")
            raise
        except Exception as e:
            logger.error(f"Cypher execution via Graphiti failed: {e}")
            raise

    async def get_entity(self, name: str, group_id: Optional[str] = None) -> Optional[dict[str, Any]]:
        """Get entity by name."""
        results = await self.search(name, group_ids=[group_id or self.config.group_id], limit=1)
        nodes = results.get("nodes", [])
        return nodes[0] if nodes else None

    async def health_check(self) -> dict[str, Any]:
        """Check Graphiti and Neo4j health."""
        try:
            graphiti = self._get_graphiti()

            # Simple search to verify connectivity
            await asyncio.wait_for(
                asyncio.shield(
                    graphiti.search(
                        query="test",
                        group_ids=[self.config.group_id],
                        num_results=1,
                    )
                ),
                timeout=self.config.health_check_timeout_seconds,
            )

            return {
                "healthy": True,
                "neo4j_uri": self.config.neo4j_uri,
                "group_id": self.config.group_id,
            }
        except asyncio.TimeoutError:
            return {"healthy": False, "error": "timeout"}
        except Exception as e:
            return {"healthy": False, "error": str(e) or type(e).__name__}


# Convenience function
async def get_graphiti_service(config: Optional[GraphitiConfig] = None) -> GraphitiService:
    """Get the GraphitiService singleton."""
    return await GraphitiService.get_instance(config)


async def get_graphiti_dependency() -> GraphitiService:
    """Dependency for FastAPI that doesn't require arguments."""
    return await get_graphiti_service()
