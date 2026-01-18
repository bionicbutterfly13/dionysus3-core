"""
Memory Basin Router - Memory Type Routing through Attractor Basins
Feature: 038-thoughtseeds-framework
Priority 0: Memory Type Basin Routing

Routes memory content through specialized attractor basins based on memory type.
Bridges the gap between memory types (EPISODIC, SEMANTIC, PROCEDURAL, STRATEGIC)
and attractor basin dynamics from Dionysus-2.0.
"""

import logging
from typing import Any, Dict, Optional

from api.models.sync import MemoryType
from api.services.llm_service import chat_completion, GPT5_NANO
from api.services.memevolve_adapter import get_memevolve_adapter, MemEvolveAdapter

logger = logging.getLogger(__name__)


# Basin mapping for each memory type
BASIN_MAPPING: Dict[MemoryType, Dict[str, Any]] = {
    MemoryType.EPISODIC: {
        "basin_name": "experiential-basin",
        "description": "Time-tagged personal experiences and events",
        "concepts": ["experience", "event", "timeline", "context", "memory"],
        "default_strength": 0.7,
        "extraction_focus": "temporal context and personal significance",
    },
    MemoryType.SEMANTIC: {
        "basin_name": "conceptual-basin",
        "description": "Facts, relationships, and conceptual knowledge",
        "concepts": ["concept", "fact", "relationship", "definition", "knowledge"],
        "default_strength": 0.8,
        "extraction_focus": "entities, relationships, and factual accuracy",
    },
    MemoryType.PROCEDURAL: {
        "basin_name": "procedural-basin",
        "description": "How-to knowledge and skill-based patterns",
        "concepts": ["procedure", "skill", "step", "technique", "method"],
        "default_strength": 0.75,
        "extraction_focus": "action sequences, dependencies, and execution order",
    },
    MemoryType.STRATEGIC: {
        "basin_name": "strategic-basin",
        "description": "Planning patterns and decision frameworks",
        "concepts": ["strategy", "goal", "plan", "decision", "tradeoff"],
        "default_strength": 0.85,
        "extraction_focus": "goals, constraints, tradeoffs, and optimization criteria",
    },
}


class MemoryBasinRouter:
    """
    Routes memory content through specialized attractor basins based on memory type.
    
    Implements:
    1. LLM-based memory type classification
    2. Basin activation for the appropriate memory type
    3. Context-aware ingestion through MemEvolve (Graphiti gateway) with basin context
    """

    def __init__(self, memevolve_adapter: Optional[MemEvolveAdapter] = None):
        self._memevolve_adapter = memevolve_adapter

    async def _get_memevolve_adapter(self) -> MemEvolveAdapter:
        if self._memevolve_adapter is None:
            self._memevolve_adapter = get_memevolve_adapter()
        return self._memevolve_adapter

    async def classify_memory_type(self, content: str) -> MemoryType:
        """
        Use LLM to classify content into a memory type.
        
        Args:
            content: Text content to classify
            
        Returns:
            MemoryType enum value
        """
        prompt = f"""Classify the following content into exactly ONE memory type.

MEMORY TYPES:
- EPISODIC: Personal experiences, events, time-specific memories (e.g., "Yesterday I learned...", "During the meeting...")
- SEMANTIC: Facts, concepts, relationships, definitions (e.g., "Python is a programming language", "The capital of France is Paris")
- PROCEDURAL: How-to knowledge, skills, step-by-step processes (e.g., "To deploy, first run...", "The algorithm works by...")
- STRATEGIC: Planning, goals, decisions, tradeoffs (e.g., "We should prioritize X over Y because...", "The strategy involves...")

CONTENT:
{content[:2000]}

Respond with ONLY the memory type name in uppercase (EPISODIC, SEMANTIC, PROCEDURAL, or STRATEGIC).
"""
        
        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a memory classification system. Respond with only the memory type.",
                model=GPT5_NANO,
                max_tokens=32
            )
            
            response_clean = response.strip().upper()
            
            # Map response to MemoryType
            type_map = {
                "EPISODIC": MemoryType.EPISODIC,
                "SEMANTIC": MemoryType.SEMANTIC,
                "PROCEDURAL": MemoryType.PROCEDURAL,
                "STRATEGIC": MemoryType.STRATEGIC,
            }
            
            if response_clean in type_map:
                logger.info(f"Classified content as {response_clean}")
                return type_map[response_clean]
            
            # Default to SEMANTIC if classification unclear
            logger.warning(f"Unclear classification '{response_clean}', defaulting to SEMANTIC")
            return MemoryType.SEMANTIC
            
        except Exception as e:
            logger.error(f"Memory type classification failed: {e}")
            return MemoryType.SEMANTIC

    def get_basin_for_type(self, memory_type: MemoryType) -> Dict[str, Any]:
        """Get the basin configuration for a given memory type."""
        return BASIN_MAPPING.get(memory_type, BASIN_MAPPING[MemoryType.SEMANTIC])

    async def route_memory(
        self,
        content: str,
        memory_type: Optional[MemoryType] = None,
        source_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Route memory content to appropriate basin and ingest.
        
        Args:
            content: Memory content to route
            memory_type: Optional pre-classified memory type
            source_id: Optional source identifier for provenance
            
        Returns:
            Dict with routing and ingestion results
        """
        # Classify if not provided
        if memory_type is None:
            memory_type = await self.classify_memory_type(content)
        
        basin_config = BASIN_MAPPING[memory_type]
        basin_name = basin_config["basin_name"]
        
        logger.info(f"Routing {memory_type.value} memory to {basin_name}")
        
        # Activate the appropriate basin
        basin_context = await self._activate_basin(basin_name, content)
        
        # Ingest with basin context
        result = await self._ingest_with_basin_context(
            content=content,
            basin_name=basin_name,
            basin_context=basin_context,
            memory_type=memory_type,
            source_id=source_id,
        )
        
        return {
            "memory_type": memory_type.value,
            "basin_name": basin_name,
            "basin_context": basin_context,
            "ingestion_result": result,
        }

    async def _activate_basin(self, basin_name: str, content: str) -> str:
        """
        Activate an attractor basin and return context for extraction.
        
        Creates or strengthens the basin in Neo4j and retrieves
        relevant context for guiding extraction.
        
        Args:
            basin_name: Name of the basin to activate
            content: Content that triggered activation (for relevance)
            
        Returns:
            Basin context string for extraction guidance
        """
        # Get or create the basin with initial strength
        basin_config = None
        for mem_type, config in BASIN_MAPPING.items():
            if config["basin_name"] == basin_name:
                basin_config = config
                break
        
        if not basin_config:
            logger.warning(f"Unknown basin {basin_name}, using default context")
            return f"Attractor Basin: {basin_name}"
        
        # Ensure basin exists and strengthen it
        create_cypher = """
        MERGE (b:AttractorBasin {name: $name})
        ON CREATE SET 
            b.description = $description,
            b.concepts = $concepts,
            b.strength = $strength,
            b.stability = 0.5,
            b.activation_count = 1,
            b.created_at = datetime()
        ON MATCH SET 
            b.strength = CASE 
                WHEN b.strength < 2.0 THEN b.strength + 0.05 
                ELSE b.strength 
            END,
            b.stability = CASE 
                WHEN b.stability < 1.0 THEN b.stability + 0.02 
                ELSE b.stability 
            END,
            b.activation_count = coalesce(b.activation_count, 0) + 1,
            b.last_activated = datetime()
        RETURN b.name as name, b.strength as strength, b.stability as stability, 
               b.concepts as concepts, b.description as description
        """
        
        params = {
            "name": basin_name,
            "description": basin_config["description"],
            "concepts": basin_config["concepts"],
            "strength": basin_config["default_strength"],
        }
        
        try:
            memevolve = await self._get_memevolve_adapter()
            rows = await memevolve.execute_cypher(create_cypher, params)
            
            if rows:
                basin = rows[0]
                context = self._format_basin_context(basin, basin_config["extraction_focus"])
                logger.info(f"Activated basin {basin_name} (strength: {basin.get('strength', 0):.2f})")
                return context
            
        except Exception as e:
            logger.error(f"Basin activation failed: {e}")
        
        # Fallback context
        return self._format_basin_context(
            {
                "name": basin_name,
                "description": basin_config["description"],
                "concepts": basin_config["concepts"],
                "strength": basin_config["default_strength"],
            },
            basin_config["extraction_focus"]
        )

    def _format_basin_context(self, basin: Dict[str, Any], extraction_focus: str) -> str:
        """Format basin data into context string for extraction."""
        concepts = basin.get("concepts", [])
        if isinstance(concepts, str):
            concepts = [concepts]
        
        return f"""Active Attractor Basin: {basin.get('name', 'unknown')}
Description: {basin.get('description', 'No description')}
Strength: {basin.get('strength', 0.5):.2f}
Stability: {basin.get('stability', 0.5):.2f}
Core Concepts: {', '.join(concepts)}
Extraction Focus: {extraction_focus}

When extracting entities and relationships, prioritize:
- Concepts related to: {', '.join(concepts)}
- Focus on: {extraction_focus}
"""

    async def _ingest_with_basin_context(
        self,
        content: str,
        basin_name: str,
        basin_context: str,
        memory_type: MemoryType,
        source_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ingest content through MemEvolve with basin context.
        
        Args:
            content: Content to ingest
            basin_name: Name of the active basin
            basin_context: Context string from basin activation
            memory_type: The classified memory type
            source_id: Optional source identifier
            
        Returns:
            Ingestion result from Graphiti
        """
        memevolve = await self._get_memevolve_adapter()
        
        # Extract with basin context
        extraction = await memevolve.extract_with_context(
            content=content,
            basin_context=basin_context,
            strategy_context=f"Memory Type: {memory_type.value.upper()}",
            confidence_threshold=0.6,
        )
        
        # Record basin-memory association
        await self._record_basin_memory(basin_name, memory_type, extraction)
        
        # Ingest approved relationships
        approved_rels = [
            r for r in extraction.get("relationships", [])
            if r.get("status") == "approved"
        ]
        
        ingestion_result = {"extracted": extraction}
        
        if approved_rels:
            source = source_id or f"basin_router:{basin_name}"
            ingest_result = await memevolve.ingest_relationships(
                relationships=approved_rels,
                source_id=source,
            )
            ingestion_result["ingested"] = ingest_result
        
        return ingestion_result

    async def _record_basin_memory(
        self,
        basin_name: str,
        memory_type: MemoryType,
        extraction: Dict[str, Any],
    ) -> None:
        """
        Record the association between basin and memory for learning.
        
        Tracks which basins process which memory types and their
        extraction success for Hebbian-style learning.
        """
        cypher = """
        MATCH (b:AttractorBasin {name: $basin_name})
        MERGE (m:MemoryTypeStats {type: $memory_type})
        ON CREATE SET m.count = 0, m.avg_entities = 0.0, m.avg_relationships = 0.0
        MERGE (b)-[r:PROCESSES]->(m)
        ON CREATE SET r.count = 1, r.first_processed = datetime()
        ON MATCH SET r.count = r.count + 1, r.last_processed = datetime()
        WITH m, $entity_count as entities, $rel_count as rels
        SET m.count = m.count + 1,
            m.avg_entities = (m.avg_entities * (m.count - 1) + entities) / m.count,
            m.avg_relationships = (m.avg_relationships * (m.count - 1) + rels) / m.count
        """
        
        params = {
            "basin_name": basin_name,
            "memory_type": memory_type.value,
            "entity_count": len(extraction.get("entities", [])),
            "rel_count": len(extraction.get("relationships", [])),
        }
        
        try:
            memevolve = await self._get_memevolve_adapter()
            await memevolve.execute_cypher(cypher, params)
        except Exception as e:
            logger.warning(f"Failed to record basin-memory stats: {e}")

    async def get_basin_stats(self, basin_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for basin(s).
        
        Args:
            basin_name: Optional specific basin, or all basins if None
            
        Returns:
            Dict with basin statistics
        """
        if basin_name:
            cypher = """
            MATCH (b:AttractorBasin {name: $name})
            OPTIONAL MATCH (b)-[r:PROCESSES]->(m:MemoryTypeStats)
            RETURN b.name as name, b.strength as strength, b.stability as stability,
                   b.activation_count as activations, b.concepts as concepts,
                   collect({type: m.type, count: r.count}) as memory_types
            """
            params = {"name": basin_name}
        else:
            cypher = """
            MATCH (b:AttractorBasin)
            OPTIONAL MATCH (b)-[r:PROCESSES]->(m:MemoryTypeStats)
            RETURN b.name as name, b.strength as strength, b.stability as stability,
                   b.activation_count as activations, b.concepts as concepts,
                   collect({type: m.type, count: r.count}) as memory_types
            ORDER BY b.strength DESC
            """
            params = {}
        
        try:
            memevolve = await self._get_memevolve_adapter()
            rows = await memevolve.execute_cypher(cypher, params)
            return {"basins": rows}
        except Exception as e:
            logger.error(f"Failed to get basin stats: {e}")
            return {"basins": [], "error": str(e)}


# Module-level singleton
_memory_basin_router: Optional[MemoryBasinRouter] = None


def get_memory_basin_router() -> MemoryBasinRouter:
    """Get the MemoryBasinRouter singleton."""
    global _memory_basin_router
    if _memory_basin_router is None:
        _memory_basin_router = MemoryBasinRouter()
    return _memory_basin_router
