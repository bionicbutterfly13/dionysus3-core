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
        relevant context for guiding extraction. Also applies decay
        to non-activated basins (Hebbian forgetting).

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
            b.importance = 0.5,
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
            b.importance = CASE
                WHEN b.importance IS NULL THEN 0.5
                WHEN b.importance < 1.0 THEN b.importance + 0.03
                ELSE b.importance
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

                # Apply decay to non-activated basins (Hebbian forgetting)
                await self._apply_decay_to_other_basins(basin_name)

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

    async def _apply_decay_to_other_basins(self, active_basin_name: str, decay_rate: float = 0.01) -> None:
        """
        Apply decay to basins that were not activated (Hebbian forgetting).

        Maintains basin competition by slightly weakening unused basins,
        preventing runaway strength accumulation.

        Args:
            active_basin_name: Name of the currently activated basin (exempt from decay)
            decay_rate: Amount to decay strength (default 0.01)
        """
        decay_cypher = """
        MATCH (b:AttractorBasin)
        WHERE b.name <> $active_name
        SET b.strength = CASE
            WHEN b.strength - $decay > 0.1 THEN b.strength - $decay
            ELSE 0.1
        END,
        b.importance = CASE
            WHEN b.importance IS NULL THEN 0.5
            WHEN b.importance - $decay > 0.1 THEN b.importance - $decay
            ELSE 0.1
        END
        RETURN count(b) as decayed_count
        """

        try:
            memevolve = await self._get_memevolve_adapter()
            result = await memevolve.execute_cypher(
                decay_cypher,
                {"active_name": active_basin_name, "decay": decay_rate}
            )
            if result:
                logger.debug(f"Applied decay to {result[0].get('decayed_count', 0)} basins")
        except Exception as e:
            logger.warning(f"Failed to apply basin decay: {e}")

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

    async def calculate_resonance(
        self,
        content: str,
        basin_config: Dict[str, Any],
    ) -> float:
        """
        Calculate semantic resonance between content and basin concepts.
        
        Resonance measures how well content aligns with a basin's conceptual
        attractors. High resonance amplifies extraction signals; low resonance
        may trigger basin transition exploration.
        
        Args:
            content: Text content to evaluate
            basin_config: Basin configuration with concepts and description
            
        Returns:
            Resonance score from 0.0 (no alignment) to 1.0 (perfect alignment)
        """
        concepts = basin_config.get("concepts", [])
        description = basin_config.get("description", "")
        
        # Build resonance evaluation prompt
        prompt = f"""Evaluate semantic resonance between content and conceptual attractor.

ATTRACTOR BASIN:
- Description: {description}
- Core Concepts: {', '.join(concepts)}

CONTENT:
{content[:1500]}

TASK: Rate how strongly this content resonates with the basin's conceptual attractor.
Consider:
1. Explicit mention of core concepts
2. Implicit alignment with the basin's purpose
3. Thematic coherence with the description

Respond with ONLY a decimal number between 0.0 and 1.0:
- 0.0-0.3: Weak/no resonance (content misaligned with basin)
- 0.3-0.6: Moderate resonance (partial alignment)
- 0.6-0.8: Strong resonance (clear alignment)
- 0.8-1.0: Maximum resonance (perfect conceptual match)
"""
        
        try:
            response = await chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a semantic resonance evaluator. Respond with only a decimal number.",
                model=GPT5_NANO,
                max_tokens=16,
            )
            
            # Parse resonance score
            score_str = response.strip()
            score = float(score_str)
            score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
            
            logger.debug(f"Resonance score for {basin_config.get('basin_name', 'unknown')}: {score:.3f}")
            return score
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse resonance score: {e}, defaulting to 0.5")
            return 0.5
        except Exception as e:
            logger.error(f"Resonance calculation failed: {e}")
            return 0.5

    async def apply_resonance_coupling(
        self,
        content: str,
        primary_basin: Dict[str, Any],
        extraction: Dict[str, Any],
        resonance_score: float,
    ) -> Dict[str, Any]:
        """
        Apply resonance coupling to modulate extraction confidence.
        
        Implements the Cellular Memory Physics principle: resonance between
        content and basin concepts amplifies or dampens extracted relationships.
        
        High resonance → Boost confidence of aligned entities/relationships
        Low resonance → Dampen confidence, flag for potential basin transition
        
        Args:
            content: Original content
            primary_basin: The activated basin configuration
            extraction: Raw extraction result with entities and relationships
            resonance_score: Calculated resonance (0.0 to 1.0)
            
        Returns:
            Modified extraction with resonance-adjusted confidences
        """
        # Resonance coupling parameters
        AMPLIFICATION_FACTOR = 1.3  # Max boost at resonance=1.0
        DAMPENING_FACTOR = 0.7      # Max reduction at resonance=0.0
        TRANSITION_THRESHOLD = 0.35  # Below this, suggest basin exploration
        
        # Calculate coupling multiplier (linear interpolation)
        # resonance=0 → DAMPENING_FACTOR, resonance=1 → AMPLIFICATION_FACTOR
        coupling_multiplier = DAMPENING_FACTOR + (
            (AMPLIFICATION_FACTOR - DAMPENING_FACTOR) * resonance_score
        )
        
        # Apply coupling to entities
        coupled_entities = []
        for entity in extraction.get("entities", []):
            coupled_entity = dict(entity)
            original_conf = entity.get("confidence", 0.7)
            coupled_entity["confidence"] = min(1.0, original_conf * coupling_multiplier)
            coupled_entity["resonance_applied"] = True
            coupled_entity["resonance_score"] = resonance_score
            coupled_entities.append(coupled_entity)
        
        # Apply coupling to relationships
        coupled_relationships = []
        for rel in extraction.get("relationships", []):
            coupled_rel = dict(rel)
            original_conf = rel.get("confidence", 0.7)
            coupled_rel["confidence"] = min(1.0, original_conf * coupling_multiplier)
            coupled_rel["resonance_applied"] = True
            coupled_rel["resonance_score"] = resonance_score
            coupled_relationships.append(coupled_rel)
        
        result = {
            "entities": coupled_entities,
            "relationships": coupled_relationships,
            "resonance": {
                "score": resonance_score,
                "coupling_multiplier": coupling_multiplier,
                "basin_name": primary_basin.get("basin_name"),
            },
        }
        
        # Flag for basin transition exploration if resonance is low
        if resonance_score < TRANSITION_THRESHOLD:
            result["transition_suggested"] = True
            result["transition_reason"] = (
                f"Low resonance ({resonance_score:.2f}) with {primary_basin.get('basin_name')} - "
                "content may better fit another attractor basin"
            )
            logger.info(
                f"Basin transition suggested: resonance={resonance_score:.2f} "
                f"below threshold {TRANSITION_THRESHOLD}"
            )
        
        return result

    async def explore_basin_transitions(
        self,
        content: str,
        current_basin: Dict[str, Any],
        current_resonance: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Explore alternative basins when resonance is low.
        
        Implements attractor basin transition dynamics: when content doesn't
        resonate with current basin, explore neighboring basins to find
        better conceptual fit.
        
        Args:
            content: Content to evaluate
            current_basin: Currently activated basin
            current_resonance: Resonance score with current basin
            
        Returns:
            Best alternative basin if found, None otherwise
        """
        current_name = current_basin.get("basin_name")
        best_alternative = None
        best_resonance = current_resonance
        
        # Evaluate all other basins
        for memory_type, basin_config in BASIN_MAPPING.items():
            if basin_config["basin_name"] == current_name:
                continue
            
            alternative_resonance = await self.calculate_resonance(content, basin_config)
            
            # Check if this basin is significantly better (improvement > 0.15)
            improvement = alternative_resonance - best_resonance
            if improvement > 0.15:
                best_alternative = {
                    "basin": basin_config,
                    "memory_type": memory_type,
                    "resonance": alternative_resonance,
                    "improvement": improvement,
                }
                best_resonance = alternative_resonance
                logger.info(
                    f"Found better basin: {basin_config['basin_name']} "
                    f"(resonance={alternative_resonance:.2f}, improvement={improvement:.2f})"
                )
        
        return best_alternative

    async def route_memory_with_resonance(
        self,
        content: str,
        memory_type: Optional[MemoryType] = None,
        source_id: Optional[str] = None,
        enable_transition_exploration: bool = True,
    ) -> Dict[str, Any]:
        """
        Route memory with full resonance coupling dynamics.
        
        Enhanced routing that:
        1. Classifies memory type and activates basin
        2. Calculates resonance with activated basin
        3. Applies resonance coupling to extraction
        4. Explores basin transitions if resonance is low
        
        Args:
            content: Memory content to route
            memory_type: Optional pre-classified type
            source_id: Optional source identifier
            enable_transition_exploration: Whether to explore alternative basins
            
        Returns:
            Routing result with resonance-coupled extraction
        """
        # Classify if not provided
        if memory_type is None:
            memory_type = await self.classify_memory_type(content)
        
        basin_config = BASIN_MAPPING[memory_type]
        basin_name = basin_config["basin_name"]
        
        logger.info(f"Routing {memory_type.value} memory to {basin_name} with resonance coupling")
        
        # Calculate resonance with primary basin
        resonance_score = await self.calculate_resonance(content, basin_config)
        
        # Check for basin transition if resonance is low
        transition_result = None
        final_basin = basin_config
        final_memory_type = memory_type
        
        if enable_transition_exploration and resonance_score < 0.35:
            transition_result = await self.explore_basin_transitions(
                content, basin_config, resonance_score
            )
            
            if transition_result:
                # Use the better-fitting basin
                final_basin = transition_result["basin"]
                final_memory_type = transition_result["memory_type"]
                resonance_score = transition_result["resonance"]
                basin_name = final_basin["basin_name"]
                logger.info(f"Basin transition: {basin_config['basin_name']} → {basin_name}")
        
        # Activate the (possibly transitioned) basin
        basin_context = await self._activate_basin(basin_name, content)
        
        # Perform extraction
        memevolve = await self._get_memevolve_adapter()
        extraction = await memevolve.extract_with_context(
            content=content,
            basin_context=basin_context,
            strategy_context=f"Memory Type: {final_memory_type.value.upper()}",
            confidence_threshold=0.5,  # Lower threshold, resonance coupling adjusts
        )
        
        # Apply resonance coupling to modulate confidences
        coupled_extraction = await self.apply_resonance_coupling(
            content=content,
            primary_basin=final_basin,
            extraction=extraction,
            resonance_score=resonance_score,
        )
        
        # Record basin-memory association
        await self._record_basin_memory(basin_name, final_memory_type, coupled_extraction)
        
        # Ingest approved relationships (above coupled confidence threshold)
        approved_rels = [
            r for r in coupled_extraction.get("relationships", [])
            if r.get("status") == "approved" or r.get("confidence", 0) >= 0.6
        ]
        
        ingestion_result = {"extracted": coupled_extraction}
        
        if approved_rels:
            source = source_id or f"basin_router:{basin_name}:resonance"
            ingest_result = await memevolve.ingest_relationships(
                relationships=approved_rels,
                source_id=source,
            )
            ingestion_result["ingested"] = ingest_result
        
        # Update basin strength based on resonance (Hebbian learning)
        await self._update_basin_from_resonance(basin_name, resonance_score)
        
        return {
            "memory_type": final_memory_type.value,
            "original_type": memory_type.value if memory_type != final_memory_type else None,
            "basin_name": basin_name,
            "basin_context": basin_context,
            "resonance": {
                "score": resonance_score,
                "coupling_applied": True,
            },
            "transition": transition_result,
            "ingestion_result": ingestion_result,
        }

    async def _update_basin_from_resonance(
        self,
        basin_name: str,
        resonance_score: float,
    ) -> None:
        """
        Update basin strength based on resonance (Hebbian-style learning).
        
        High resonance strengthens the basin-concept association.
        Low resonance slightly weakens it (forgetting).
        
        Args:
            basin_name: Name of the basin to update
            resonance_score: Resonance score from coupling
        """
        # Hebbian learning: strength delta proportional to resonance
        # resonance > 0.5 → strengthen, resonance < 0.5 → weaken
        strength_delta = (resonance_score - 0.5) * 0.1
        
        cypher = """
        MATCH (b:AttractorBasin {name: $name})
        SET b.strength = CASE
            WHEN b.strength + $delta < 0.1 THEN 0.1
            WHEN b.strength + $delta > 2.0 THEN 2.0
            ELSE b.strength + $delta
        END,
        b.resonance_history = CASE
            WHEN b.resonance_history IS NULL THEN [$score]
            WHEN size(b.resonance_history) >= 100 THEN 
                tail(b.resonance_history) + [$score]
            ELSE b.resonance_history + [$score]
        END,
        b.avg_resonance = CASE
            WHEN b.resonance_history IS NULL THEN $score
            ELSE (coalesce(b.avg_resonance, 0.5) * 0.95 + $score * 0.05)
        END
        RETURN b.strength as strength, b.avg_resonance as avg_resonance
        """
        
        params = {
            "name": basin_name,
            "delta": strength_delta,
            "score": resonance_score,
        }
        
        try:
            memevolve = await self._get_memevolve_adapter()
            result = await memevolve.execute_cypher(cypher, params)
            if result:
                logger.debug(
                    f"Updated {basin_name}: strength_delta={strength_delta:.3f}, "
                    f"new_strength={result[0].get('strength', 'N/A')}"
                )
        except Exception as e:
            logger.warning(f"Failed to update basin from resonance: {e}")

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
