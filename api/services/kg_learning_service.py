"""
Agentic Knowledge Graph Learning Loop Service
Feature: 022-agentic-kg-learning

Implements self-improving extraction loop using attractor basins and
cognition-base strategy boosting.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from api.models.kg_learning import ExtractionResult, RelationshipProposal, AttractorBasin, CognitionStrategy
from api.services.graphiti_service import get_graphiti_service
from api.services.llm_service import chat_completion, GPT5_NANO
from api.services.webhook_neo4j_driver import get_neo4j_driver
from api.models.network_state import get_network_state_config

logger = logging.getLogger(__name__)


class KGLearningService:
    def __init__(self, driver=None):
        self._driver = driver or get_neo4j_driver()

    async def extract_and_learn(self, content: str, source_id: str) -> ExtractionResult:
        """Extract relationships with basin-guidance and strategy-boosting."""
        # 1. Get context from basins and cognition base
        basin_context = await self._get_relevant_basins(content)
        strategy_context = await self._get_active_strategies()

        # 2. Extract via consolidated GraphitiService extractor (eliminates double extraction)
        CONFIDENCE_THRESHOLD = 0.6
        graphiti = await get_graphiti_service()
        
        extraction = await graphiti.extract_with_context(
            content=content,
            basin_context=basin_context,
            strategy_context=strategy_context,
            confidence_threshold=CONFIDENCE_THRESHOLD,
        )
        
        # 3. Build ExtractionResult from GraphitiService response
        run_id = str(uuid4())
        relationships = []
        
        for rel_dict in extraction.get("relationships", []):
            rel = RelationshipProposal(
                source=rel_dict["source"],
                target=rel_dict["target"],
                relation_type=rel_dict["relation_type"],
                confidence=rel_dict["confidence"],
                evidence=rel_dict.get("evidence", ""),
                status=rel_dict["status"],
                run_id=run_id,
                model_id=extraction.get("model_used", str(GPT5_NANO)),
            )
            relationships.append(rel)
            
            # Persist the proposal for tracking/review (T007)
            await self._persist_proposal(rel)
        
        result = ExtractionResult(
            run_id=run_id,
            entities=extraction.get("entities", []),
            relationships=relationships,
        )
        
        # 4. Ingest approved relationships via GraphitiService (no double extraction)
        approved_rels = [r for r in extraction.get("relationships", []) if r["status"] == "approved"]
        if approved_rels:
            await graphiti.ingest_extracted_relationships(
                relationships=approved_rels,
                source_id=f"agentic_extraction:{source_id}:{run_id}",
            )
        
        # Log pending reviews
        pending_count = extraction.get("pending_count", 0)
        if pending_count > 0:
            logger.info(f"{pending_count} low-confidence extractions queued for review")

        # 5. Update basins and learn
        await self._strengthen_basins(result.entities)
        
        # T010: Automatic Feedback Loop
        evaluation = await self.evaluate_extraction(result, content)
        
        if evaluation.get("precision_score", 0.0) > 0.8:
            await self._record_learning(result.relationships)
            logger.info(f"Automatic Strategy Boost applied for run {run_id}")

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
            model=GPT5_NANO,
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
                MERGE (s:CognitionStrategy {category: 'relationship_types', name: $name})
                SET s.success_count = coalesce(s.success_count, 0) + 1,
                    s.priority_boost = coalesce(s.priority_boost, 0.0) + 0.05,
                    s.last_used = datetime()
                """
                await self._driver.execute_query(cypher, {"name": rel.relation_type})

        # T048: Hebbian co-activation learning (conditional on feature flag)
        config = get_network_state_config()
        if config.hebbian_learning_enabled:
            await self._apply_hebbian_coactivation(relationships)

    async def _apply_hebbian_coactivation(self, relationships: List[RelationshipProposal]):
        """
        Apply Hebbian learning to relationship connections (T048).

        When entities co-activate through successful extraction, strengthen
        their connection weights using the Hebbian learning formula.
        """
        from api.services.hebbian_service import get_hebbian_service

        hebbian_svc = get_hebbian_service()

        for rel in relationships:
            if rel.confidence < 0.6:
                continue

            # Record co-activation between source and target entities
            # Activation values scaled by confidence
            try:
                await hebbian_svc.record_coactivation(
                    source_id=rel.source,
                    target_id=rel.target,
                    v1=rel.confidence,
                    v2=rel.confidence
                )
                logger.debug(f"Hebbian co-activation recorded: {rel.source} -> {rel.target}")
            except Exception as e:
                # Don't fail extraction on Hebbian errors - just log
                logger.warning(f"Hebbian co-activation failed for {rel.source}->{rel.target}: {e}")

    async def evaluate_extraction(self, extraction: ExtractionResult, ground_truth: str) -> Dict[str, Any]:
        """
        Evaluate an extraction result against ground truth.
        T009: Calculates precision proxy and provides learning signals.
        """
        prompt = f"""
        You are a Knowledge Graph Evaluator. Compare the EXTRACTED relationships 
        against the GROUND TRUTH document and existing knowledge.
        
        GROUND TRUTH:
        {ground_truth[:3000]}
        
        EXTRACTED:
        {extraction.model_dump_json()}
        
        Evaluate each relationship for:
        1. Accuracy (Is it actually in the text?)
        2. Relevance (Is it strategically important?)
        3. Contradiction (Does it conflict with high-stability basins?)
        
        Respond ONLY with a JSON object:
        {{
            "precision_score": 0.0-1.0,
            "recall_proxy": 0.0-1.0,
            "hallucinations": ["list", "of", "errors"],
            "learning_signal": "Description of why this was good or bad",
            "recommended_boosts": ["relation_type_to_boost"]
        }}
        """
        
        response = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a rigorous mathematical evaluator of Knowledge Graphs.",
            model=GPT5_NANO,
            max_tokens=1024
        )
        
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("`").replace("json", "").strip()
            eval_data = json.loads(cleaned)
            
            # Record the evaluation in Neo4j (T014)
            await self._record_evaluation_metric(extraction.run_id, eval_data)
            
            return eval_data
        except Exception as e:
            logger.error(f"evaluation_failed: {e}")
            return {"error": "Evaluation parsing failed", "precision_score": 0.0}

    async def _record_evaluation_metric(self, run_id: str, eval_data: Dict[str, Any]):
        """Persist learning metrics to Neo4j (T014)."""
        cypher = """
        MATCH (r:RelationshipProposal {run_id: $run_id})
        MERGE (m:LearningMetric {run_id: $run_id})
        SET m.precision = $precision,
            m.recall = $recall,
            m.timestamp = datetime(),
            m.hallucinations = $hallucinations,
            m.signal = $signal
        WITH m, r
        CREATE (r)-[:EVALUATED_AS]->(m)
        """
        params = {
            "run_id": run_id,
            "precision": eval_data.get("precision_score", 0.0),
            "recall": eval_data.get("recall_proxy", 0.0),
            "hallucinations": eval_data.get("hallucinations", []),
            "signal": eval_data.get("learning_signal", "")
        }
        await self._driver.execute_query(cypher, params)


_kg_learning_service: Optional[KGLearningService] = None


def get_kg_learning_service() -> KGLearningService:
    global _kg_learning_service
    if _kg_learning_service is None:
        _kg_learning_service = KGLearningService()
    return _kg_learning_service