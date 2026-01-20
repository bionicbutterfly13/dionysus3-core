"""
Agentic Knowledge Graph Learning Loop Service
Feature: 022-agentic-kg-learning

Implements self-improving extraction loop using attractor basins and
cognition-base strategy boosting.
"""

import json
import logging
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from api.models.kg_learning import ExtractionResult, RelationshipProposal
from api.models.sync import MemoryType
from api.services.memevolve_adapter import get_memevolve_adapter, MemEvolveAdapter
from api.services.llm_service import chat_completion, GPT5_NANO
from api.services.memory_basin_router import get_memory_basin_router, BASIN_MAPPING
from api.models.network_state import get_network_state_config

logger = logging.getLogger(__name__)


class KGLearningService:
    def __init__(self, adapter: Optional[MemEvolveAdapter] = None):
        self._adapter = adapter or get_memevolve_adapter()

    async def extract_and_learn(self, content: str, source_id: str) -> ExtractionResult:
        """Extract relationships with basin-guidance and strategy-boosting."""
        # 1. Get context from basins and cognition base
        basin_context = await self._get_relevant_basins(content)
        strategy_context = await self._get_active_strategies()

        # 2. Extract via MemEvolve adapter (Graphiti gateway) to avoid double extraction
        CONFIDENCE_THRESHOLD = 0.6
        extraction = await self._adapter.extract_with_context(
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
        
        # 4. Ingest approved relationships via MemEvolve adapter
        approved_rels = [r for r in extraction.get("relationships", []) if r["status"] == "approved"]
        if approved_rels:
            await self._adapter.ingest_relationships(
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

    async def extract_and_learn_typed(
        self,
        content: str,
        source_id: str,
        memory_type: Optional[MemoryType] = None,
    ) -> ExtractionResult:
        """
        Extract relationships with memory-type-aware basin routing.
        
        This method extends extract_and_learn by first classifying the content
        into a memory type (EPISODIC, SEMANTIC, PROCEDURAL, STRATEGIC) and
        routing through the appropriate attractor basin.
        
        Args:
            content: Text content to extract from
            source_id: Source identifier for provenance
            memory_type: Optional pre-classified type; auto-classifies if None
            
        Returns:
            ExtractionResult with extracted entities and relationships
        """
        router = get_memory_basin_router()
        
        # 1. Classify memory type if not provided
        if memory_type is None:
            memory_type = await router.classify_memory_type(content)
        
        logger.info(f"Processing {memory_type.value} memory for source {source_id}")
        
        # 2. Get memory-type-specific basin context
        basin_config = BASIN_MAPPING[memory_type]
        basin_name = basin_config["basin_name"]
        basin_context = await router._activate_basin(basin_name, content)
        
        # 3. Get strategy context (existing behavior)
        strategy_context = await self._get_active_strategies()
        # Augment with memory type info
        strategy_context += f"\nMemory Type: {memory_type.value.upper()}"
        strategy_context += f"\nExtraction Focus: {basin_config['extraction_focus']}"
        
        # 4. Extract via MemEvolve adapter
        CONFIDENCE_THRESHOLD = 0.6
        extraction = await self._adapter.extract_with_context(
            content=content,
            basin_context=basin_context,
            strategy_context=strategy_context,
            confidence_threshold=CONFIDENCE_THRESHOLD,
        )
        
        # 5. Build ExtractionResult from GraphitiService response
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
            
            # Persist the proposal for tracking/review
            await self._persist_proposal(rel)
        
        result = ExtractionResult(
            run_id=run_id,
            entities=extraction.get("entities", []),
            relationships=relationships,
        )
        
        # 6. Ingest approved relationships via MemEvolve adapter
        approved_rels = [r for r in extraction.get("relationships", []) if r["status"] == "approved"]
        if approved_rels:
            await self._adapter.ingest_relationships(
                relationships=approved_rels,
                source_id=f"typed_extraction:{memory_type.value}:{source_id}:{run_id}",
            )
        
        # Log pending reviews
        pending_count = extraction.get("pending_count", 0)
        if pending_count > 0:
            logger.info(f"{pending_count} low-confidence extractions queued for review")

        # 7. Update basins and learn - strengthen the memory-type-specific basin
        await self._strengthen_basins(result.entities)
        await router._record_basin_memory(basin_name, memory_type, extraction)
        
        # T010: Automatic Feedback Loop
        evaluation = await self.evaluate_extraction(result, content)
        
        if evaluation.get("precision_score", 0.0) > 0.8:
            await self._record_learning(result.relationships)
            logger.info(f"Automatic Strategy Boost applied for typed run {run_id}")

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
        rows = await self._adapter.execute_cypher(cypher)
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
        rows = await self._adapter.execute_cypher(cypher)
        if not rows:
            return "Preferred Relation Types: THEORETICALLY_EXTENDS, EMPIRICALLY_VALIDATES, CONTRADICTS, REPLACES"
        
        types = [r['name'] for r in rows]
        return f"Prioritized Relation Types: {', '.join(types)}"

    async def _llm_extract(self, content: str, basin_ctx: str, strategy_ctx: str) -> ExtractionResult:
        warnings.warn(
            "_llm_extract is deprecated and unused. Use GraphitiService.extract_with_context instead.",
            DeprecationWarning,
            stacklevel=2
        )
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
        await self._adapter.execute_cypher(cypher, params)

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
        await self._adapter.execute_cypher(cypher, params)

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
                await self._adapter.execute_cypher(cypher, {"name": rel.relation_type})

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

    async def ingest_unified(
        self,
        content: str,
        source_id: str,
        memory_type: Optional[MemoryType] = None,
        strategy_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Unified Ingestion Pipeline (The 'Express Highway').
        
        Orchestrates:
        1. Nemori (Context & Basin Alignment) - inferred via Router
        2. AutoSchema (5-Level Concept Extraction) - Transformer step
        3. MemEvolve (Persistence Gateway) - Consumer step
        
        Args:
            content: The raw content to ingest
            source_id: Provenance identifier
            memory_type: Optional memory type override
            strategy_context: Optional active inference / strategy context
            
        Returns:
            Dict containing ingestion stats and run_id
        """
        from api.services.concept_extraction.service import get_concept_extraction_service
        
        start_time = datetime.utcnow()
        router = get_memory_basin_router()
        
        # 1. Nemori / Basin Alignment
        if memory_type is None:
            memory_type = await router.classify_memory_type(content)
            
        basin_config = BASIN_MAPPING.get(memory_type, BASIN_MAPPING[MemoryType.EPISODIC])
        basin_context = await router._activate_basin(basin_config["basin_name"], content)
        
        # 2. AutoSchema (Transformation)
        extractor_service = await get_concept_extraction_service()
        
        extraction_context = {
            "domain_focus": basin_config["extraction_focus"],
            "basin_context": basin_context,
            "strategy_context": strategy_context or await self._get_active_strategies(),
            "min_confidence": 0.6
        }
        
        five_level_result = await extractor_service.extract_all(
            content=content,
            context=extraction_context,
            document_id=source_id
        )
        
        # Map 5-Level Result to flat lists for Graphiti/MemEvolve
        flat_entities = []
        for c in five_level_result.all_concepts:
            flat_entities.append(c.name)
            
        flat_relationships = []
        # Add explicit relationships
        for rel in five_level_result.cross_level_relationships:
            flat_relationships.append({
                "source": rel.source_concept_id,
                "target": rel.target_concept_id,
                "type": rel.relationship_type.upper(),
                "confidence": rel.strength,
                "evidence": f"Cross-level: {rel.source_level.name} -> {rel.target_level.name}"
            })
            
        # Add hierarchy relationships
        for parent, children in five_level_result.concept_hierarchy.items():
            for child in children:
                flat_relationships.append({
                    "source": child,
                    "target": parent,
                    "type": "IS_PART_OF",
                    "confidence": 0.9,
                    "evidence": "Hierarchical Structure"
                })

        # 3. MemEvolve (Persistence)
        # Construct ingestion request
        from api.models.memevolve import MemoryIngestRequest, TrajectoryData, TrajectoryStep, TrajectoryMetadata
        
        trajectory = TrajectoryData(
            query=source_id,
            steps=[TrajectoryStep(observation=content)],
            metadata=TrajectoryMetadata(
                timestamp=start_time,
                tags=[c.name for c in five_level_result.all_concepts[:5]], # Top concepts as tags
                memory_type=memory_type.value,
                project_id="unified_pipeline",
                session_id=str(uuid4())
            )
        )
        
        ingest_request = MemoryIngestRequest(
            trajectory=trajectory,
            conversation_id=source_id,
            memory_type=memory_type.value,
            entities=flat_entities,
            edges=flat_relationships
        )

        ingestion_result = await self._adapter.ingest_trajectory(ingest_request)
        
        # 4. Feedback Loop (Structure Learning / Hebbian)
        if five_level_result.overall_consciousness_level > 0.7:
             # If high quality, reinforce the basin
             await self._strengthen_basins(flat_entities[:5])

        return {
            "run_id": five_level_result.document_id,
            "ingestion_stats": ingestion_result,
            "consciousness_level": five_level_result.overall_consciousness_level,
            "concept_count": len(five_level_result.all_concepts)
        }


_kg_learning_service: Optional[KGLearningService] = None


def get_kg_learning_service() -> KGLearningService:
    global _kg_learning_service
    if _kg_learning_service is None:
        _kg_learning_service = KGLearningService()
    return _kg_learning_service
