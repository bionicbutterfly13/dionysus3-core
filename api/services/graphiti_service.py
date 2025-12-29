"""
Graphiti Service - Real-time knowledge graph for entity tracking.

Direct Neo4j access (exception to n8n-only rule for this trusted component).
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


class GraphitiConfig:
    """Configuration for Graphiti service."""

    def __init__(
        self,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        group_id: str = "dionysus",
    ):
        # Force VPS IP if not explicitly provided
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://72.61.78.89:7687")
        
        if "neo4j" in self.neo4j_uri and not os.path.exists("/.dockerenv"):
            self.neo4j_uri = self.neo4j_uri.replace("neo4j", "72.61.78.89")

        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.group_id = group_id

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
                # Build indexes (safe, won't delete existing)
                await _global_graphiti.build_indices_and_constraints(delete_existing=False)

        self._initialized = True
        logger.info("Graphiti Service initialized successfully")

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
            
        return json.loads(cleaned)

    @staticmethod
    def _normalize_extraction(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        entities: list[dict[str, Any]] = []
        relationships: list[dict[str, Any]] = []

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

        return entities, relationships

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
            await graphiti.search(
                query="test",
                group_ids=[self.config.group_id],
                num_results=1,
            )

            return {
                "healthy": True,
                "neo4j_uri": self.config.neo4j_uri,
                "group_id": self.config.group_id,
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}


# Convenience function
async def get_graphiti_service(config: Optional[GraphitiConfig] = None) -> GraphitiService:
    """Get the GraphitiService singleton."""
    return await GraphitiService.get_instance(config)


async def get_graphiti_dependency() -> GraphitiService:
    """Dependency for FastAPI that doesn't require arguments."""
    return await get_graphiti_service()
