"""
Agentic Knowledge Graph Learning Loop Service
Feature: 022-agentic-kg-learning

Implements self-improving extraction loop using attractor basins and
cognition-base strategy boosting.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from api.models.kg_learning import ExtractionResult, RelationshipProposal, AttractorBasin, CognitionStrategy
from api.services.graphiti_service import get_graphiti_service
from api.services.llm_service import chat_completion, SONNET
from api.services.webhook_neo4j_driver import get_neo4j_driver

logger = logging.getLogger(__name__)


class KGLearningService:
    def __init__(self, driver=None):
        self._driver = driver or get_neo4j_driver()

    async def extract_and_learn(self, content: str, source_id: str) -> ExtractionResult:
        """Extract relationships with basin-guidance and strategy-boosting."""
        # 1. Get context from basins and cognition base
        basin_context = await self._get_relevant_basins(content)
        strategy_context = await self._get_active_strategies()

        # 2. Extract via LLM
        result = await self._llm_extract(content, basin_context, strategy_context)
        
        # 3. Store in Graphiti with threshold gating (FR-004)
        CONFIDENCE_THRESHOLD = 0.6
        graphiti = await get_graphiti_service()
        
        for rel in result.relationships:
            # Set provenance
            rel.run_id = result.run_id
            rel.model_id = str(SONNET)
            
            # Persist the proposal itself for tracking/review (T007)
            await self._persist_proposal(rel)
            
            if rel.confidence >= CONFIDENCE_THRESHOLD:
                rel.status = "approved"
                # Map to Graphiti ingestion
                fact = f"{rel.source} {rel.relation_type} {rel.target}. Evidence: {rel.evidence}"
                await graphiti.ingest_message(
                    content=fact,
                    source_description=f"agentic_extraction:{source_id}:{result.run_id}",
                    valid_at=datetime.utcnow()
                )
            else:
                rel.status = "pending_review"
                logger.info(f"Low confidence ({rel.confidence}) extraction queued for review: {rel.source}->{rel.target}")

        # 4. Update basins and learn
        await self._strengthen_basins(result.entities)
        await self._record_learning(result.relationships)

        result.end_time = datetime.utcnow()
        return result

    async def _get_relevant_basins(self, content: str) -> str:
        """Query Neo4j for basins relevant to the content."""
        cypher = """
        MATCH (b:AttractorBasin)
        RETURN b.name as name, b.strength as strength, b.concepts as concepts
        ORDER BY b.strength DESC
        LIMIT 5
        """
        rows = await self._driver.execute_query(cypher)
        if not rows:
            return "No active attractor basins yet."
        
        ctx = "Relevant Attractor Basins:\n"
        for r in rows:
            ctx += f"- {r['name']} (Strength: {r['strength']:.1f}): {', '.join(r['concepts'])}\n"
        return ctx

    async def _get_active_strategies(self) -> str:
        """Get prioritized relationship types from cognition base."""
        cypher = """
        MATCH (s:CognitionStrategy {category: 'relationship_types'})
        RETURN s.name as name, s.priority_boost as boost
        ORDER BY s.priority_boost DESC
        LIMIT 10
        """
        rows = await self._driver.execute_query(cypher)
        if not rows:
            return "Preferred Relation Types: THEORETICALLY_EXTENDS, EMPIRICALLY_VALIDATES, CONTRADICTS, REPLACES"
        
        types = [r['name'] for r in rows]
        return f"Prioritized Relation Types: {', '.join(types)}"

    async def _llm_extract(self, content: str, basin_ctx: str, strategy_ctx: str) -> ExtractionResult:
        prompt = f"""
        You are an expert knowledge extraction agent.
        
        CONTEXT FROM COGNITION BASE:
        {basin_ctx}
        
        {strategy_ctx}
        
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
        """
        
        response = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="Extract structured knowledge with dynamic relationship types.",
            model=SONNET,
            max_tokens=2048
        )
        
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`").replace("json", "").strip()
            data = json.loads(cleaned)
            return ExtractionResult(**data)
        except Exception as e:
            logger.error(f"failed_to_parse_extraction: {e}")
            return ExtractionResult()

    async def _persist_proposal(self, rel: RelationshipProposal):
        """Store a relationship proposal in Neo4j for audit/review."""
        cypher = """
        CREATE (r:RelationshipProposal {{
            source: $source,
            target: $target,
            relation_type: $type,
            confidence: $confidence,
            evidence: $evidence,
            run_id: $run_id,
            model_id: $model_id,
            status: $status,
            created_at: datetime()
        }})
        """
        params = rel.model_dump(by_alias=True)
        await self._driver.execute_query(cypher, params)

    async def _strengthen_basins(self, entities: List[str]):
        """Update/Create basins based on extracted entities."""
        if not entities: return
        
        cypher = """
        MERGE (b:AttractorBasin {{name: $main}})
        SET b.strength = coalesce(b.strength, 1.0) + 0.1,
            b.concepts = apoc.coll.toSet(coalesce(b.concepts, []) + $all),
            b.last_strengthened = datetime()
        """
        params = {"main": entities[0], "all": entities}
        await self._driver.execute_query(cypher, params)

    async def _record_learning(self, relationships: List[RelationshipProposal]):
        """Update strategy priorities based on successful extractions."""
        for rel in relationships:
            if rel.confidence > 0.7:
                cypher = """
                MERGE (s:CognitionStrategy {{category: 'relationship_types', name: $name}})
                SET s.success_count = coalesce(s.success_count, 0) + 1,
                    s.priority_boost = coalesce(s.priority_boost, 0.0) + 0.05,
                    s.last_used = datetime()
                """
                await self._driver.execute_query(cypher, {"name": rel.relation_type})


_kg_learning_service: Optional[KGLearningService] = None


def get_kg_learning_service() -> KGLearningService:
    global _kg_learning_service
    if _kg_learning_service is None:
        _kg_learning_service = KGLearningService()
    return _kg_learning_service