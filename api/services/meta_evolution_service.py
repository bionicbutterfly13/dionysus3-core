"""
Meta-Evolution Service (Feature 049)

Analyzes past performance episodes and system snapshots to autonomously
propose and apply strategic improvements to the system's cognitive architecture.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from api.models.evolution import SystemMoment, EvolutionUpdate
from api.services.webhook_neo4j_driver import get_neo4j_driver
from api.services.llm_service import chat_completion
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
        Main evolution cycle:
        1. Identify low-performance/high-surprise episodes.
        2. Propose structural or strategic updates.
        3. Apply the update to the Knowledge Graph.
        """
        logger.info("Starting Meta-Evolutionary Cycle...")
        
        # 1. Fetch high-surprise episodes from last 24h
        driver = get_neo4j_driver()
        query = """
        MATCH (e:CognitiveEpisode)
        WHERE (e.surprise_score > 0.5 OR e:MACERTrajectory)
          AND e.timestamp > $cutoff
        RETURN e
        ORDER BY e.surprise_score DESC
        LIMIT 10
        """
        cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        
        episodes_data = await driver.execute_query(query, {"cutoff": cutoff})
        if not episodes_data:
            logger.info("No evolution-worthy episodes found. Evolution cycle idle.")
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
        else:
            # If no strategy shift proposed, trigger a DISCOVERY task to find gaps
            from api.services.coordination_service import get_coordination_service, TaskType
            pool = get_coordination_service()
            task_id = pool.submit_task(
                payload={
                    "query": "Analyze high-surprise episodes and find missing contextual links in the graph.",
                    "episodes": [e.get("id") for e in episodes_data]
                },
                task_type=TaskType.DISCOVERY
            )
            logger.info(f"Submitted DISCOVERY task {task_id} to resolve surprise gaps.")
            
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
        memory_rows = await driver.execute_query(
            "MATCH (m:Memory) RETURN count(m) as count"
        )
        total_memories = memory_rows[0]["count"] if memory_rows else 0

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

        # Cognitive episode metrics (last 24h)
        cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
        episode_rows = await driver.execute_query(
            """
            MATCH (e:CognitiveEpisode)
            WHERE datetime(e.timestamp) > datetime($cutoff)
            RETURN
                avg(coalesce(e.surprise_score, 0.0)) as avg_surprise,
                avg(CASE WHEN e.success THEN 1.0 ELSE 0.0 END) as avg_success,
                count(e) as episode_count
            """,
            {"cutoff": cutoff},
        )
        episode_row = episode_rows[0] if episode_rows else {}
        avg_surprise = float(episode_row.get("avg_surprise") or 0.0)
        # Use success rate as a proxy for confidence until explicit confidence is tracked.
        avg_confidence = float(episode_row.get("avg_success") or 0.0)

        # Current focus: most recently touched active goal, fallback to queued.
        focus_rows = await driver.execute_query(
            """
            MATCH (g:Goal)
            WHERE g.priority IN ['active', 'queued']
            RETURN g.title as title, g.priority as priority, g.last_touched as last_touched
            ORDER BY CASE g.priority WHEN 'active' THEN 0 ELSE 1 END, g.last_touched DESC
            LIMIT 1
            """
        )
        current_focus = focus_rows[0]["title"] if focus_rows else None

        # Recent errors from latest heartbeat logs.
        recent_errors = []
        log_rows = await driver.execute_query(
            """
            MATCH (l:HeartbeatLog)
            RETURN l.actions_taken as actions
            ORDER BY l.ended_at DESC
            LIMIT 5
            """
        )
        for row in log_rows:
            raw_actions = row.get("actions")
            if not raw_actions:
                continue
            if isinstance(raw_actions, str):
                try:
                    actions = json.loads(raw_actions)
                except json.JSONDecodeError:
                    continue
            elif isinstance(raw_actions, list):
                actions = raw_actions
            else:
                continue

            for action in actions:
                if not isinstance(action, dict):
                    continue
                error = action.get("error")
                if error and error not in recent_errors:
                    recent_errors.append(error)

        moment = SystemMoment(
            total_memories_count=total_memories,
            energy_level=energy_level,
            active_basins_count=active_basins_count,
            avg_surprise_score=avg_surprise,
            avg_confidence_score=avg_confidence,
            current_focus=current_focus,
            recent_errors=recent_errors,
        )

        # Persist moment
        persist_query = """
        CREATE (m:SystemMoment {id: $id})
        SET m.timestamp = $timestamp,
            m.energy_level = $energy,
            m.total_memories_count = $mem_count,
            m.active_basins_count = $basins,
            m.avg_surprise_score = $avg_surprise,
            m.avg_confidence_score = $avg_confidence,
            m.current_focus = $current_focus,
            m.recent_errors = $recent_errors
        """
        await driver.execute_query(persist_query, {
            "id": moment.id,
            "timestamp": moment.timestamp.isoformat(),
            "energy": moment.energy_level,
            "mem_count": moment.total_memories_count,
            "basins": moment.active_basins_count,
            "avg_surprise": moment.avg_surprise_score,
            "avg_confidence": moment.avg_confidence_score,
            "current_focus": moment.current_focus,
            "recent_errors": moment.recent_errors,
        })

        logger.info(
            f"Captured system moment: energy={energy_level:.2f}, "
            f"active_basins={active_basins_count}, memories={total_memories}, "
            f"avg_surprise={avg_surprise:.2f}, avg_confidence={avg_confidence:.2f}"
        )

        return moment

# Singleton
_evolution_instance = None

def get_meta_evolution_service() -> MetaEvolutionService:
    global _evolution_instance
    if _evolution_instance is None:
        _evolution_instance = MetaEvolutionService()
    return _evolution_instance
