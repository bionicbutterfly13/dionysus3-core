"""
Meta-Cognitive Learning Service (Feature 043)

Implements Episodic Meta-Learning by recording and retrieving 'Cognitive Episodes'.
Ported from Dionysus 2.0 MetaCognitiveEpisodicLearner logic.
"""

import json
import logging
from typing import List
from datetime import datetime

from api.models.meta_cognition import CognitiveEpisode
from api.services.remote_sync import get_neo4j_driver
from api.services.llm_service import chat_completion

logger = logging.getLogger(__name__)

class MetaCognitiveLearner:
    """
    Manages the lifecycle of Cognitive Episodes:
    1. Retrieval: Finding past similar tasks to guide current strategy.
    2. Recording: Saving current task outcomes and lessons.
    3. Optimization: Synthesizing lessons into actionable strategy hints.
    """

    async def retrieve_relevant_episodes(
        self, 
        task_query: str, 
        limit: int = 3
    ) -> List[CognitiveEpisode]:
        """
        Retrieve similar past episodes using vector search on task description.
        
        Note: Requires a vector index on :CognitiveEpisode(embedding).
        If index doesn't exist, this might fail or return empty until setup.
        """
        driver = get_neo4j_driver()
        
        # 1. Generate embedding for the query (using a simple mock or actual embedding service if available)
        # For D3, we often rely on Neo4j's GenAI plugin or an external embedder.
        # Since we don't have a dedicated embedding service in imports, we'll try a text search fallback 
        # or assume an index exists. 
        # FALLBACK: Use full-text search if vector index not ready.
        
        query = """
        CALL db.index.fulltext.queryNodes("cognitive_task_index", $task_query) YIELD node, score
        RETURN node, score
        LIMIT $limit
        """
        
        # If fulltext index doesn't exist, fallback to simple CONTAINS
        fallback_query = """
        MATCH (n:CognitiveEpisode)
        WHERE toLower(n.task_query) CONTAINS toLower($task_query)
        RETURN n as node, 1.0 as score
        ORDER BY n.timestamp DESC
        LIMIT $limit
        """

        episodes = []
        async with driver.session() as session:
            try:
                # Try fulltext first
                result = await session.run(query, {"task_query": task_query, "limit": limit})
                records = await result.data()
            except Exception:
                # Fallback
                result = await session.run(fallback_query, {"task_query": task_query, "limit": limit})
                records = await result.data()

            for record in records:
                node = record["node"]
                episodes.append(CognitiveEpisode(
                    id=node["id"],
                    timestamp=datetime.fromisoformat(node["timestamp"]),
                    task_query=node["task_query"],
                    task_context=json.loads(node.get("task_context", "{}")),
                    tools_used=json.loads(node.get("tools_used", "[]")),
                    reasoning_trace=node.get("reasoning_trace", ""),
                    success=node.get("success", False),
                    outcome_summary=node.get("outcome_summary", ""),
                    surprise_score=float(node.get("surprise_score", 0.0)),
                    lessons_learned=node.get("lessons_learned", "")
                ))
        
        return episodes

    async def record_episode(self, episode: CognitiveEpisode):
        """
        Persist a completed episode to Neo4j.
        """
        driver = get_neo4j_driver()
        
        query = """
        MERGE (c:CognitiveEpisode {id: $id})
        SET c.timestamp = $timestamp,
            c.task_query = $task_query,
            c.task_context = $task_context,
            c.tools_used = $tools_used,
            c.reasoning_trace = $reasoning_trace,
            c.success = $success,
            c.outcome_summary = $outcome_summary,
            c.surprise_score = $surprise_score,
            c.lessons_learned = $lessons_learned
        """
        
        params = {
            "id": episode.id,
            "timestamp": episode.timestamp.isoformat(),
            "task_query": episode.task_query,
            "task_context": json.dumps(episode.task_context),
            "tools_used": json.dumps(episode.tools_used),
            "reasoning_trace": episode.reasoning_trace,
            "success": episode.success,
            "outcome_summary": episode.outcome_summary,
            "surprise_score": episode.surprise_score,
            "lessons_learned": episode.lessons_learned
        }
        
        async with driver.session() as session:
            await session.run(query, params)
            logger.info(f"Recorded Cognitive Episode {episode.id} (Surprise: {episode.surprise_score:.2f})")

    async def synthesize_lessons(self, episodes: List[CognitiveEpisode]) -> str:
        """
        Synthesize a meta-cognitive strategy string from past episodes.
        """
        if not episodes:
            return ""
            
        context_str = "\n".join([
            f"- Task: {e.task_query}\n  Strategy: {e.tools_used}\n  Outcome: {'Success' if e.success else 'Failure'}\n  Lesson: {e.lessons_learned}"
            for e in episodes
        ])
        
        prompt = f"""Analyze these past cognitive episodes for similar tasks.
        Synthesize a brief strategic advice block (3 bullet points max) for the current session.
        Focus on which tools worked and which failed.
        
        Past Episodes:
        {context_str}
        """
        
        return await chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a meta-cognitive optimizer.",
            max_tokens=256
        )

# Singleton
_learner_instance = None

def get_meta_learner() -> MetaCognitiveLearner:
    global _learner_instance
    if _learner_instance is None:
        _learner_instance = MetaCognitiveLearner()
    return _learner_instance
