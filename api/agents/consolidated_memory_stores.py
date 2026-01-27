import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from api.models.autobiographical import (
    DevelopmentEvent,
    DevelopmentEpisode,
    AutobiographicalJourney,
    RiverStage,
    DevelopmentArchetype
)
from api.services.webhook_neo4j_driver import get_neo4j_driver
from api.services.graphiti_service import get_graphiti_service

logger = logging.getLogger("dionysus.memory.consolidated")

class ConsolidatedMemoryStore:
    """
    Unified storage backend for Dionysus 3.0.
    Wraps Neo4j and Graphiti to provide a single interface for the River Flow.
    """
    def __init__(self, driver=None):
        self._driver = driver or get_neo4j_driver()

    async def store_event(self, event: DevelopmentEvent) -> bool:
        """Persist a raw development event (SOURCE)."""
        cypher = """
        MERGE (e:DevelopmentEvent {id: $id})
        SET e += $props,
            e.river_stage = 'source'
        WITH e
        // Link to Attractor Basin if present
        FOREACH (_ IN CASE WHEN $basin_id IS NOT NULL THEN [1] ELSE [] END |
            MERGE (b:AttractorBasin {id: $basin_id})
            MERGE (e)-[:ALIGNS_WITH {score: $basin_score}]->(b)
        )
        // Link to Markov Blanket if present
        FOREACH (_ IN CASE WHEN $blanket_id IS NOT NULL THEN [1] ELSE [] END |
            MERGE (mb:MarkovBlanket {id: $blanket_id})
            MERGE (e)-[:WITHIN_BLANKET]->(mb)
        )
        RETURN e.id
        """
        props = event.model_dump(exclude={"event_id", "timestamp"})
        props["timestamp"] = event.timestamp.isoformat()
        
        # Serialize nested objects
        if event.active_inference_state:
            props["active_inference_state"] = event.active_inference_state.model_dump_json()
        
        try:
            await self._driver.execute_query(cypher, {
                "id": event.event_id,
                "props": props,
                "basin_id": event.linked_basin_id,
                "basin_score": event.basin_r_score,
                "blanket_id": event.markov_blanket_id
            })
            return True
        except Exception as e:
            logger.error(f"Failed to store event {event.event_id}: {e}")
            return False

    async def create_episode(self, episode: DevelopmentEpisode) -> bool:
        """Create a TRIBUTARY (Episode) and link its events/trajectories."""
        cypher = """
        MERGE (ep:DevelopmentEpisode {id: $id})
        SET ep += $props,
            ep.river_stage = 'tributary'
        
        // Link Events
        WITH ep
        UNWIND CASE WHEN $event_ids = [] THEN [null] ELSE $event_ids END as event_id
        OPTIONAL MATCH (e:DevelopmentEvent {id: event_id})
        FOREACH (_ IN CASE WHEN e IS NOT NULL THEN [1] ELSE [] END |
            MERGE (ep)-[:CONTAINS_EVENT]->(e)
            SET e.parent_episode_id = $id,
                e.river_stage = 'tributary'
        )
        
        // Link Trajectories (Protocol 060)
        WITH ep
        UNWIND CASE WHEN $traj_ids = [] THEN [null] ELSE $traj_ids END as t_id
        OPTIONAL MATCH (t:Trajectory {id: t_id})
        FOREACH (_ IN CASE WHEN t IS NOT NULL THEN [1] ELSE [] END |
            MERGE (ep)-[:SUMMARIZES]->(t)
        )
        
        RETURN ep.id
        """
        props = episode.model_dump(exclude={"episode_id", "events", "start_time", "end_time", "source_trajectory_ids"})
        props["start_time"] = episode.start_time.isoformat()
        props["end_time"] = episode.end_time.isoformat()
        
        try:
            await self._driver.execute_query(cypher, {
                "id": episode.episode_id,
                "props": props,
                "event_ids": episode.events,
                "traj_ids": episode.source_trajectory_ids
            })
            return True
        except Exception as e:
            logger.error(f"Failed to create episode {episode.episode_id}: {e}")
            return False

    async def update_journey(self, journey: AutobiographicalJourney) -> bool:
        """Update the MAIN_RIVER (Journey) and link its episodes."""
        cypher = """
        MERGE (j:AutobiographicalJourney {id: $id})
        SET j += $props,
            j.river_stage = 'main_river'
        WITH j
        UNWIND $episode_ids as ep_id
        MATCH (ep:DevelopmentEpisode {id: ep_id})
        MERGE (j)-[:HAS_EPISODE]->(ep)
        SET ep.river_stage = 'main_river' // Promote to main river stage
        RETURN j.id
        """
        props = journey.model_dump(exclude={"journey_id", "episodes", "created_at", "updated_at", "themes"})
        props["created_at"] = journey.created_at.isoformat()
        props["updated_at"] = journey.updated_at.isoformat()
        props["themes"] = list(journey.themes)
        
        try:
            await self._driver.execute_query(cypher, {
                "id": journey.journey_id,
                "props": props,
                "episode_ids": journey.episodes
            })
            return True
        except Exception as e:
            logger.error(f"Failed to update journey {journey.journey_id}: {e}")
            return False

    async def get_recent_events(self, limit: int = 20) -> List[DevelopmentEvent]:
        """Fetch recent events for boundary detection."""
        cypher = """
        MATCH (e:DevelopmentEvent)
        WHERE e.river_stage = 'source'
        RETURN e
        ORDER BY e.timestamp DESC
        LIMIT $limit
        """
        try:
            result = await self._driver.execute_query(cypher, {"limit": limit})
            events = []
            for row in result:
                data = row["e"]
                # Manual rehydration for now, could use a helper
                events.append(DevelopmentEvent.model_validate(data))
            return events
        except Exception as e:
            logger.error(f"Error fetching recent events: {e}")
            return []

    async def get_active_journey(self, 
                                 participant_id: Optional[str] = None, 
                                 device_id: Optional[str] = None) -> Optional[AutobiographicalJourney]:
        """
        Retrieve the currently active Autobiographical Journey for a specific identity.
        
        If participant_id or device_id is provided, it filters for the most recent
        journey linked to that identity.
        """
        where_clause = ""
        params = {}
        
        if participant_id:
            where_clause = "WHERE j.participant_id = $participant_id"
            params["participant_id"] = participant_id
        elif device_id:
            where_clause = "WHERE j.device_id = $device_id"
            params["device_id"] = device_id

        # LABEL BRIDGE: Match both AutobiographicalJourney and Journey
        # This ensures that technical sessions are anchored to cognitive identity correctly.
        cypher = f"""
        MATCH (j)
        WHERE (j:AutobiographicalJourney OR j:Journey)
        {where_clause.replace('WHERE ', 'AND ')}
        RETURN labels(j) as labels, j {{.*}} as data
        ORDER BY j.updated_at DESC
        LIMIT 1
        """
        try:
            result = await self._driver.execute_query(cypher, params)
            if result and result[0]:
                data = result[0]["data"]
                labels = result[0]["labels"]
                
                # Rehydrate dates
                if isinstance(data.get("created_at"), str):
                    data["created_at"] = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
                if isinstance(data.get("updated_at"), str):
                    data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))
                
                # Technical Journey Fallback Mapping
                if "Journey" in labels and "AutobiographicalJourney" not in labels:
                    return AutobiographicalJourney(
                        journey_id=data.get("id", "technical_seed"),
                        title=f"Technical Journey ({data.get('device_id', 'unknown')})",
                        description="Auto-generated from session tracking",
                        created_at=data.get("created_at", datetime.utcnow()),
                        updated_at=data.get("updated_at", datetime.utcnow()),
                        episodes=[],
                        themes=set()
                    )
                
                return AutobiographicalJourney(**data)
            return None
        except Exception as e:
            logger.error(f"Failed to fetch active journey: {e}")
            return None

    async def search_episodes(
        self,
        query: str,
        limit: int = 10,
        group_ids: Optional[List[str]] = None,
        anchor_node_ids: Optional[List[str]] = None
    ) -> List[DevelopmentEpisode]:
        """
        Hybrid search for episodes using Graphiti with graph-distance re-ranking.
        
        T041-031: Refactor episode retrieval to use Graphiti hybrid search.
        Includes graph distance re-ranking based on anchor nodes (e.g. goals).
        """
        graphiti = await get_graphiti_service()
        
        # 1. Search for relevant facts in episodes
        results = await graphiti.search(
            query=query,
            group_ids=group_ids,
            limit=limit * 2 # Get more candidates for re-ranking
        )
        
        # episode_id -> max_similarity
        candidate_scores: Dict[str, float] = {}
        
        for edge in results.get("edges", []):
            fact_id = edge.get("uuid")
            # Graphiti results usually have some similarity score
            score = edge.get("score", 0.5)
            
            if fact_id:
                ep_records = await self._driver.execute_query(
                    """
                    MATCH (f:Fact {id: $fact_id})-[:DISTILLED_FROM]->(ep:DevelopmentEpisode)
                    RETURN ep.id as ep_id
                    """,
                    {"fact_id": fact_id}
                )
                for rec in ep_records:
                    eid = rec["ep_id"]
                    candidate_scores[eid] = max(candidate_scores.get(eid, 0.0), score)
        
        # 2. Direct title/summary search (keyword fallback)
        direct_records = await self._driver.execute_query(
            """
            MATCH (ep:DevelopmentEpisode)
            WHERE toLower(ep.title) CONTAINS toLower($query) 
               OR toLower(ep.summary) CONTAINS toLower($query)
            RETURN ep.id as ep_id
            LIMIT $limit
            """,
            {"query": query, "limit": limit}
        )
        for rec in direct_records:
            eid = rec["ep_id"]
            candidate_scores[eid] = max(candidate_scores.get(eid, 0.0), 0.4) # Base score for keyword match
            
        if not candidate_scores:
            return []

        # 3. Graph Distance Re-ranking
        if anchor_node_ids:
            for eid in list(candidate_scores.keys()):
                # Find shortest path distance to ANY anchor
                dist_records = await self._driver.execute_query(
                    """
                    MATCH (ep:DevelopmentEpisode {id: $eid}), (anchor)
                    WHERE anchor.id IN $anchors
                    MATCH p = shortestPath((ep)-[*..3]-(anchor))
                    RETURN length(p) as distance
                    ORDER BY distance ASC
                    LIMIT 1
                    """,
                    {"eid": eid, "anchors": anchor_node_ids}
                )
                if dist_records:
                    distance = dist_records[0]["distance"]
                    # Boost: 1.0 for dist 0, 0.8 for dist 1, etc.
                    boost = 1.0 - (distance * 0.2)
                    candidate_scores[eid] *= (1.0 + boost)
                    logger.debug(f"Episode {eid} distance boost: {boost:.2f} (dist {distance})")

        # 4. Sort and rehydrate
        sorted_ids = sorted(candidate_scores.keys(), key=lambda k: candidate_scores[k], reverse=True)
        
        episodes = []
        for ep_id in sorted_ids[:limit]:
            episode = await self.get_episode(ep_id)
            if episode:
                episodes.append(episode)
                
        return episodes

    async def get_episode(self, episode_id: str) -> Optional[DevelopmentEpisode]:
        """Retrieve a single episode by ID."""
        cypher = "MATCH (ep:DevelopmentEpisode {id: $id}) RETURN ep"
        result = await self._driver.execute_query(cypher, {"id": episode_id})
        if result and result[0]:
            data = result[0]["ep"]
            # Rehydrate dates
            if isinstance(data.get("start_time"), str):
                data["start_time"] = datetime.fromisoformat(data["start_time"])
            if isinstance(data.get("end_time"), str):
                data["end_time"] = datetime.fromisoformat(data["end_time"])
            return DevelopmentEpisode(**data)
        return None


_instance: Optional[ConsolidatedMemoryStore] = None

def get_consolidated_memory_store() -> ConsolidatedMemoryStore:
    global _instance
    if _instance is None:
        _instance = ConsolidatedMemoryStore()
    return _instance
