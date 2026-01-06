"""
Meta-Evolution Service (Feature 049)

Analyzes past performance episodes and system snapshots to autonomously
propose and apply strategic improvements to the system's cognitive architecture.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from api.models.evolution import SystemMoment, EvolutionUpdate
from api.models.meta_cognition import CognitiveEpisode
from api.services.meta_cognitive_service import get_meta_learner
from api.services.webhook_neo4j_driver import get_neo4j_driver
from api.services.llm_service import chat_completion, GPT5_NANO
from api.services.consciousness_integration_pipeline import get_consciousness_pipeline
from api.services.memory_basin_router import get_memory_basin_router

logger = logging.getLogger("dionysus.meta_evolution")

class MetaEvolutionService:
    """
    The 'Reflective Brain' of Dionysus. 
    Reviews CognitiveEpisodes and SystemMoments to evolve the strategy.
    """

    async def run_evolution_cycle(self) -> Optional[EvolutionUpdate]:
        """
        1. Identify low-performance/high-surprise episodes.
        2. Propose structural or strategic updates.
        3. Apply the update to the Knowledge Graph.
        """
        logger.info("Starting Meta-Evolutionary Cycle...")
        
        # 1. Fetch high-surprise episodes from last 24h
        driver = get_neo4j_driver()
        query = """
        MATCH (e:CognitiveEpisode)
        WHERE e.surprise_score > 0.5
          AND e.timestamp > $cutoff
        RETURN e
        ORDER BY e.surprise_score DESC
        LIMIT 5
        """
        cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        
        episodes_data = await driver.execute_query(query, {"cutoff": cutoff})
        if not episodes_data:
            logger.info("No high-surprise episodes found. Evolution cycle idle.")
            return None
            
        # 2. Reflect and Propose
        update = await self._propose_evolution(episodes_data)
        
        # 3. Apply via Unified Integration Pipeline
        if update:
            pipeline = get_consciousness_pipeline()
            await pipeline.process_cognitive_event(
                problem="System Self-Evolution",
                reasoning_trace=f"Rationale: {update.rationale}\nStrategy: {update.new_strategy_description}",
                outcome="Applied strategy shift.",
                context={"project_id": "system_evolution", "confidence": 1.0}
            )
            logger.info(f"Evolution Update applied: {update.id}")
            
        return update

    async def _propose_evolution(self, episodes: List[Dict]) -> Optional[EvolutionUpdate]:
        """
        Use LLM to analyze failures and propose a shift.
        """
        context_str = json.dumps(episodes, indent=2)
        
        prompt = f"""
        Analyze these high-surprise cognitive episodes:
        {context_str}
        
        Identify the shared failure pattern. Propose a new 'Strategic Principle' to 
        prevent this in the future.
        
        Respond ONLY with a JSON object:
        {{
          "new_strategy_description": "...",
          "rationale": "...",
          "expected_improvement": 0.2
        }}
        """
        
        response = await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an Evolutionary Architect.",
            max_tokens=512
        )
        
        try:
            data = json.loads(response.strip())
            return EvolutionUpdate(**data)
        except Exception as e:
            logger.error(f"Failed to parse evolution proposal: {e}")
            return None

    async def capture_system_moment(self) -> SystemMoment:
        """
        Gathers current metrics and persists them as a moment.

        Feature 057: Replaced placeholder values with real basin-based computation.
        - energy_level: Sum of active basin strengths (strength > 0.3)
        - active_basins_count: Count of basins above activation threshold
        """
        driver = get_neo4j_driver()

        # Gather memory count
        query = "MATCH (n) RETURN labels(n) as l, count(*) as c"
        results = await driver.execute_query(query)
        total_nodes = sum(r["c"] for r in results)

        # Query attractor basins for real metrics (FR-001, FR-002)
        basin_router = get_memory_basin_router()
        basin_stats = await basin_router.get_basin_stats()
        basins = basin_stats.get("basins", [])

        # Filter active basins (strength > 0.3 threshold)
        ACTIVE_THRESHOLD = 0.3
        active_basins = [b for b in basins if b.get("strength", 0.0) > ACTIVE_THRESHOLD]

        # Compute real metrics
        active_basins_count = len(active_basins)
        energy_level = sum(b.get("strength", 0.0) for b in active_basins)

        # Validate energy_level in expected range [0, 10] (FR-011)
        if energy_level < 0.0 or energy_level > 10.0:
            logger.warning(
                f"Energy level {energy_level:.2f} out of expected range [0, 10]. "
                f"Active basins: {active_basins_count}, Basin strengths: {[b.get('strength') for b in active_basins]}"
            )
            # Clamp to valid range
            energy_level = max(0.0, min(10.0, energy_level))

        moment = SystemMoment(
            total_memories_count=total_nodes,
            energy_level=energy_level,
            active_basins_count=active_basins_count
        )

        # Persist moment
        persist_query = """
        CREATE (m:SystemMoment {id: $id})
        SET m.timestamp = $timestamp,
            m.energy_level = $energy,
            m.total_memories_count = $mem_count,
            m.active_basins_count = $basins
        """
        await driver.execute_query(persist_query, {
            "id": moment.id,
            "timestamp": moment.timestamp.isoformat(),
            "energy": moment.energy_level,
            "mem_count": moment.total_memories_count,
            "basins": moment.active_basins_count
        })

        logger.info(
            f"Captured system moment: energy={energy_level:.2f}, "
            f"active_basins={active_basins_count}, memories={total_nodes}"
        )

        return moment

# Singleton
_evolution_instance = None

def get_meta_evolution_service() -> MetaEvolutionService:
    global _evolution_instance
    if _evolution_instance is None:
        _evolution_instance = MetaEvolutionService()
    return _evolution_instance
