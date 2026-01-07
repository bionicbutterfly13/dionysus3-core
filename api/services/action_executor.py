"""
Action Executor for Heartbeat System
Feature: 004-heartbeat-system
Tasks: T012, T013, T014

Implements all action handlers for the heartbeat cognitive loop.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from api.models.action import (
    ActionRequest,
    ActionResult,
    ActionStatus,
    EnvironmentSnapshot,
)
from api.services.energy_service import ActionType, EnergyService

logger = logging.getLogger("dionysus.action_executor")


# =============================================================================
# Base Action Handler
# =============================================================================


class ActionHandler(ABC):
    """Base class for action handlers."""

    action_type: ActionType

    def __init__(self, energy_service: EnergyService, driver=None):
        """
        Initialize action handler.

        Args:
            energy_service: EnergyService for cost tracking
            driver: Neo4j driver for database operations
        """
        self.energy_service = energy_service
        self._driver = driver

    def _get_driver(self):
        """Get Neo4j driver."""
        if self._driver:
            return self._driver
        from api.services.remote_sync import get_neo4j_driver

        return get_neo4j_driver()

    @abstractmethod
    async def execute(self, request: ActionRequest) -> ActionResult:
        """
        Execute the action.

        Args:
            request: Action request with parameters

        Returns:
            ActionResult with outcome
        """
        pass


# =============================================================================
# T012: Free Actions (cost 0)
# =============================================================================


class ObserveHandler(ActionHandler):
    """
    Observe: Gather environmental context.

    Cost: 0 (free, always runs)
    Output: EnvironmentSnapshot with current state
    """

    action_type = ActionType.OBSERVE

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Gather environmental snapshot."""
        started_at = datetime.utcnow()

        try:
            driver = self._get_driver()
            async with driver.session() as session:
                # Get heartbeat state
                state_result = await session.run(
                    """
                    MATCH (s:HeartbeatState {singleton_id: 'main'})
                    RETURN s
                    """
                )
                state_record = await state_result.single()

                # Count recent memories (last 24 hours)
                memory_result = await session.run(
                    """
                    MATCH (m:Memory)
                    WHERE m.created_at > datetime() - duration('PT24H')
                    RETURN count(m) as recent_count
                    """
                )
                memory_record = await memory_result.single()

                # Count goals by status
                goals_result = await session.run(
                    """
                    MATCH (g:Goal)
                    RETURN g.priority as priority, count(g) as count
                    """
                )
                goals_data = await goals_result.data()

                # Count blocked goals
                blocked_result = await session.run(
                    """
                    MATCH (g:Goal)
                    WHERE g.blocked_by IS NOT NULL
                    RETURN count(g) as blocked_count
                    """
                )
                blocked_record = await blocked_result.single()

                # Check last user interaction
                user_result = await session.run(
                    """
                    MATCH (m:Memory)
                    WHERE m.source = 'user'
                    RETURN max(m.created_at) as last_user
                    """
                )
                user_record = await user_result.single()

            # Build snapshot
            s = state_record["s"] if state_record else {}
            goals_by_priority = {r["priority"]: r["count"] for r in goals_data}
            blocked_count = blocked_record["blocked_count"] if blocked_record else 0

            last_user = user_record["last_user"] if user_record else None
            time_since_user = None
            if last_user:
                delta = datetime.utcnow() - last_user.to_native()
                time_since_user = delta.total_seconds() / 3600  # hours

            snapshot = EnvironmentSnapshot(
                timestamp=datetime.utcnow(),
                user_present=time_since_user is not None and time_since_user < 0.5,
                time_since_user_hours=time_since_user,
                pending_events=[],  # TODO: implement event queue
                recent_memories_count=memory_record["recent_count"] if memory_record else 0,
                active_goals_count=goals_by_priority.get("active", 0),
                queued_goals_count=goals_by_priority.get("queued", 0),
                blocked_goals_count=blocked_count,
                current_energy=s.get("current_energy", 10.0),
                heartbeat_number=s.get("heartbeat_count", 0),
            )

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=0.0,
                data={"snapshot": snapshot.to_dict()},
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Observe action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


class ReviewGoalsHandler(ActionHandler):
    """
    ReviewGoals: Review current goal state.

    Cost: 0 (free, always runs)
    Output: GoalAssessment with active/queued/blocked/stale analysis
    """

    action_type = ActionType.REVIEW_GOALS

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Review goals and produce assessment."""
        started_at = datetime.utcnow()

        try:
            from api.services.goal_service import get_goal_service

            goal_service = get_goal_service()
            assessment = await goal_service.review_goals()

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=0.0,
                data={
                    "active_count": len(assessment.active_goals),
                    "queued_count": len(assessment.queued_goals),
                    "blocked_count": len(assessment.blocked_goals),
                    "stale_count": len(assessment.stale_goals),
                    "promotion_candidates": len(assessment.promotion_candidates),
                    "needs_brainstorm": assessment.needs_brainstorm,
                    "issues": assessment.issues,
                },
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"ReviewGoals action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


class RememberHandler(ActionHandler):
    """
    Remember: Store current context/thought as memory.

    Cost: 0 (free)
    Params: content (str), memory_type (str)
    Output: Created memory ID
    """

    action_type = ActionType.REMEMBER

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Store a memory."""
        started_at = datetime.utcnow()

        try:
            content = request.params.get("content", "")
            memory_type = request.params.get("memory_type", "thought")

            if not content:
                return ActionResult(
                    action_type=self.action_type,
                    status=ActionStatus.FAILED,
                    energy_cost=0.0,
                    error="No content provided",
                    started_at=started_at,
                    ended_at=datetime.utcnow(),
                )

            # Create memory using MCP or Neo4j driver
            driver = self._get_driver()
            async with driver.session() as session:
                result = await session.run(
                    """
                    CREATE (m:Memory {
                        id: randomUUID(),
                        content: $content,
                        memory_type: $memory_type,
                        source: 'heartbeat',
                        created_at: datetime(),
                        updated_at: datetime()
                    })
                    RETURN m.id as id
                    """,
                    content=content,
                    memory_type=memory_type,
                )
                record = await result.single()

            memory_id = record["id"] if record else None

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=0.0,
                data={"memory_id": memory_id, "content_length": len(content)},
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Remember action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


class RestHandler(ActionHandler):
    """
    Rest: Do nothing, conserve energy for next heartbeat.

    Cost: 0 (free)
    Output: Success
    """

    action_type = ActionType.REST

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Rest action - intentionally do nothing."""
        started_at = datetime.utcnow()

        logger.info("Resting this heartbeat - conserving energy")

        return ActionResult(
            action_type=self.action_type,
            status=ActionStatus.COMPLETED,
            energy_cost=0.0,
            data={"rested": True},
            started_at=started_at,
            ended_at=datetime.utcnow(),
        )


# =============================================================================
# T013: Memory/Reasoning Actions
# =============================================================================


class RecallHandler(ActionHandler):
    """
    Recall: Query memories by semantic similarity.

    Cost: 1
    Params: query (str), limit (int)
    Output: List of matching memories
    """

    action_type = ActionType.RECALL

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Search memories by query."""
        started_at = datetime.utcnow()
        cost = self.energy_service.get_action_cost(self.action_type)

        try:
            query = request.params.get("query", "")
            limit = request.params.get("limit", 5)

            if not query:
                return ActionResult(
                    action_type=self.action_type,
                    status=ActionStatus.FAILED,
                    energy_cost=0.0,
                    error="No query provided",
                    started_at=started_at,
                    ended_at=datetime.utcnow(),
                )

            # Use semantic search (would integrate with existing recall service)
            driver = self._get_driver()
            async with driver.session() as session:
                # Fallback to text-based search if vector search not available
                result = await session.run(
                    """
                    MATCH (m:Memory)
                    WHERE toLower(m.content) CONTAINS toLower($query)
                    RETURN m.id as id, m.content as content, m.memory_type as type,
                           m.created_at as created_at
                    ORDER BY m.created_at DESC
                    LIMIT $limit
                    """,
                    query=query,
                    limit=limit,
                )
                records = await result.data()

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=cost,
                data={
                    "query": query,
                    "memories_found": len(records),
                    "memories": records,
                },
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Recall action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


class ConnectHandler(ActionHandler):
    """
    Connect: Create relationship between memories.

    Cost: 1
    Params: source_id (str), target_id (str), relationship (str)
    Output: Created relationship
    """

    action_type = ActionType.CONNECT

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Connect two memories."""
        started_at = datetime.utcnow()
        cost = self.energy_service.get_action_cost(self.action_type)

        try:
            source_id = request.params.get("source_id")
            target_id = request.params.get("target_id")
            relationship = request.params.get("relationship", "RELATED_TO")

            if not source_id or not target_id:
                return ActionResult(
                    action_type=self.action_type,
                    status=ActionStatus.FAILED,
                    energy_cost=0.0,
                    error="Both source_id and target_id required",
                    started_at=started_at,
                    ended_at=datetime.utcnow(),
                )

            driver = self._get_driver()
            async with driver.session() as session:
                result = await session.run(
                    f"""
                    MATCH (s:Memory {{id: $source_id}})
                    MATCH (t:Memory {{id: $target_id}})
                    MERGE (s)-[r:{relationship}]->(t)
                    ON CREATE SET r.created_at = datetime()
                    RETURN s.id as source, t.id as target, type(r) as rel_type
                    """,
                    source_id=source_id,
                    target_id=target_id,
                )
                record = await result.single()

            if not record:
                return ActionResult(
                    action_type=self.action_type,
                    status=ActionStatus.FAILED,
                    energy_cost=cost,
                    error="Could not create connection - memories not found",
                    started_at=started_at,
                    ended_at=datetime.utcnow(),
                )

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=cost,
                data={
                    "source": record["source"],
                    "target": record["target"],
                    "relationship": record["rel_type"],
                },
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Connect action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


class MaintainHandler(ActionHandler):
    """
    Maintain: Reinforce/update memory importance.

    Cost: 2
    Params: memory_id (str), boost (float)
    Output: Updated memory
    """

    action_type = ActionType.MAINTAIN

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Maintain a memory by boosting its importance."""
        started_at = datetime.utcnow()
        cost = self.energy_service.get_action_cost(self.action_type)

        try:
            memory_id = request.params.get("memory_id")
            boost = request.params.get("boost", 0.1)

            if not memory_id:
                return ActionResult(
                    action_type=self.action_type,
                    status=ActionStatus.FAILED,
                    energy_cost=0.0,
                    error="memory_id required",
                    started_at=started_at,
                    ended_at=datetime.utcnow(),
                )

            driver = self._get_driver()
            async with driver.session() as session:
                result = await session.run(
                    """
                    MATCH (m:Memory {id: $memory_id})
                    SET m.importance = COALESCE(m.importance, 0.5) + $boost,
                        m.last_accessed = datetime(),
                        m.access_count = COALESCE(m.access_count, 0) + 1
                    RETURN m.id as id, m.importance as importance
                    """,
                    memory_id=memory_id,
                    boost=boost,
                )
                record = await result.single()

            if not record:
                return ActionResult(
                    action_type=self.action_type,
                    status=ActionStatus.FAILED,
                    energy_cost=cost,
                    error="Memory not found",
                    started_at=started_at,
                    ended_at=datetime.utcnow(),
                )

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=cost,
                data={
                    "memory_id": record["id"],
                    "new_importance": record["importance"],
                },
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Maintain action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


class ReflectHandler(ActionHandler):
    """
    Reflect: Generate insight from memories.

    Cost: 2
    Params: topic (str), memories (list)
    Output: Reflection text (LLM-generated)
    """

    action_type = ActionType.REFLECT

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Generate reflection on a topic."""
        started_at = datetime.utcnow()
        cost = self.energy_service.get_action_cost(self.action_type)

        try:
            topic = request.params.get("topic", "recent experiences")
            memories = request.params.get("memories", [])

            # 1. Generate actual reflection via LLM
            from api.services.llm_service import chat_completion, GPT5_NANO
            
            system_prompt = """You are Dionysus's reflective faculty. 
            Analyze the provided memories and topic to find root causes, hidden implications, 
            and systemic connections. Connect them to broader patterns and potential future actions.
            """
            
            user_content = f"Topic to reflect on: {topic}\n\nRelated memories:\n"
            user_content += "\n".join(f"- {m}" for m in memories[:10])
            
            reflection = await chat_completion(
                messages=[{"role": "user", "content": user_content}],
                system_prompt=system_prompt,
                model=GPT5_NANO,
                max_tokens=1000
            )

            # 2. Store reflection as memory
            driver = self._get_driver()
            async with driver.session() as session:
                result = await session.run(
                    """
                    CREATE (m:Memory {
                        id: randomUUID(),
                        content: $content,
                        memory_type: 'reflection',
                        source: 'heartbeat',
                        topic: $topic,
                        created_at: datetime()
                    })
                    RETURN m.id as id
                    """,
                    content=reflection,
                    topic=topic,
                )
                record = await result.single()

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=cost,
                data={
                    "topic": topic,
                    "reflection": reflection,
                    "memory_id": record["id"] if record else None,
                },
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Reflect action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


class InquireShallowHandler(ActionHandler):
    """
    InquireShallow: Quick factual lookup.

    Cost: 3
    Params: question (str)
    Output: Answer (LLM or search result)
    """

    action_type = ActionType.INQUIRE_SHALLOW

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Quick inquiry on a topic."""
        started_at = datetime.utcnow()
        cost = self.energy_service.get_action_cost(self.action_type)

        try:
            question = request.params.get("question", "")

            if not question:
                return ActionResult(
                    action_type=self.action_type,
                    status=ActionStatus.FAILED,
                    energy_cost=0.0,
                    error="No question provided",
                    started_at=started_at,
                    ended_at=datetime.utcnow(),
                )

            # 1. Quick search via vector store
            from api.services.vector_search import get_vector_search_service
            from api.services.llm_service import chat_completion
            
            search_service = get_vector_search_service()
            results = await search_service.semantic_search(question, top_k=3)
            
            context = "\n".join([r.content for r in results.results])
            
            # 2. Quick answer via Haiku
            system_prompt = "You are a quick factual lookup service. Answer the question based ONLY on the provided context."
            user_content = f"Question: {question}\n\nContext:\n{context}"
            
            answer = await chat_completion(
                messages=[{"role": "user", "content": user_content}],
                system_prompt=system_prompt,
                model=GPT5_NANO,
                max_tokens=200
            )

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=cost,
                data={
                    "question": question,
                    "answer": answer,
                    "depth": "shallow",
                },
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"InquireShallow action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


class InquireDeepHandler(ActionHandler):
    """
    InquireDeep: Deep research with multiple sources.

    Cost: 6
    Params: question (str), sources (list)
    Output: Detailed answer with sources
    """

    action_type = ActionType.INQUIRE_DEEP

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Deep inquiry with research."""
        started_at = datetime.utcnow()
        cost = self.energy_service.get_action_cost(self.action_type)

        try:
            question = request.params.get("question", "")

            if not question:
                return ActionResult(
                    action_type=self.action_type,
                    status=ActionStatus.FAILED,
                    energy_cost=0.0,
                    error="No question provided",
                    started_at=started_at,
                    ended_at=datetime.utcnow(),
                )

            # 1. Deep search via vector store + Graphiti
            from api.services.vector_search import get_vector_search_service
            from api.services.graphiti_service import get_graphiti_service
            from api.services.llm_service import chat_completion, GPT5_NANO
            
            search_service = get_vector_search_service()
            graphiti = await get_graphiti_service()
            
            # Parallel search
            import asyncio
            vector_task = search_service.semantic_search(question, top_k=10)
            graph_task = graphiti.search(question, limit=10)
            
            vector_results, graph_results = await asyncio.gather(vector_task, graph_task)
            
            # Combine context
            context_blocks = []
            for r in vector_results.results: context_blocks.append(f"[Memory]: {r.content}")
            for e in graph_results.get("edges", []): context_blocks.append(f"[Graph Fact]: {e.get('fact')}")
            
            context = "\n".join(context_blocks)
            
            # 2. Comprehensive analysis via Sonnet
            system_prompt = """You are a deep research faculty. Analyze all provided context to answer the complex question. 
            Identify contradictions, weight evidence by relevance, and provide a nuanced, detailed synthesis.
            """
            user_content = f"Complex Question: {question}\n\nContext Pool:\n{context}"
            
            answer = await chat_completion(
                messages=[{"role": "user", "content": user_content}],
                system_prompt=system_prompt,
                model=GPT5_NANO,
                max_tokens=1500
            )

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=cost,
                data={
                    "question": question,
                    "answer": answer,
                    "depth": "deep",
                    "sources_count": len(context_blocks),
                },
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"InquireDeep action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


class SynthesizeHandler(ActionHandler):
    """
    Synthesize: Generate new understanding from multiple inputs.

    Cost: 4
    Params: inputs (list of memory IDs or texts), goal (str)
    Output: Synthesized insight
    """

    action_type = ActionType.SYNTHESIZE

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Synthesize insights from multiple inputs."""
        started_at = datetime.utcnow()
        cost = self.energy_service.get_action_cost(self.action_type)

        try:
            inputs = request.params.get("inputs", [])
            goal = request.params.get("goal", "find patterns")

            if not inputs:
                return ActionResult(
                    action_type=self.action_type,
                    status=ActionStatus.FAILED,
                    energy_cost=0.0,
                    error="No inputs provided",
                    started_at=started_at,
                    ended_at=datetime.utcnow(),
                )

            # 1. Generate synthesis via LLM
            from api.services.llm_service import chat_completion, GPT5_NANO
            
            system_prompt = f"""You are Dionysus's synthesis faculty.
            Your task is to take disparate data points and weave them into a high-level, 
            actionable, and coherent narrative or plan. Goal: {goal}
            """
            
            user_content = "Inputs for synthesis:\n"
            user_content += "\n".join(f"- {i}" for i in inputs[:15])
            
            synthesis = await chat_completion(
                messages=[{"role": "user", "content": user_content}],
                system_prompt=system_prompt,
                model=GPT5_NANO,
                max_tokens=1000
            )

            # 2. Store as memory
            driver = self._get_driver()
            async with driver.session() as session:
                result = await session.run(
                    """
                    CREATE (m:Memory {
                        id: randomUUID(),
                        content: $content,
                        memory_type: 'synthesis',
                        source: 'heartbeat',
                        input_count: $input_count,
                        created_at: datetime()
                    })
                    RETURN m.id as id
                    """,
                    content=synthesis,
                    input_count=len(inputs),
                )
                record = await result.single()

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=cost,
                data={
                    "input_count": len(inputs),
                    "goal": goal,
                    "synthesis": synthesis,
                    "memory_id": record["id"] if record else None,
                },
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Synthesize action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


# =============================================================================
# T014: Goal/Communication Actions
# =============================================================================


class ReprioritizeHandler(ActionHandler):
    """
    Reprioritize: Change goal priorities.

    Cost: 1
    Params: changes (list of {goal_id, new_priority})
    Output: Updated goals
    """

    action_type = ActionType.REPRIORITIZE

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Reprioritize goals."""
        started_at = datetime.utcnow()
        cost = self.energy_service.get_action_cost(self.action_type)

        try:
            changes = request.params.get("changes", [])

            if not changes:
                return ActionResult(
                    action_type=self.action_type,
                    status=ActionStatus.FAILED,
                    energy_cost=0.0,
                    error="No changes provided",
                    started_at=started_at,
                    ended_at=datetime.utcnow(),
                )

            from api.services.goal_service import get_goal_service

            goal_service = get_goal_service()

            results = []
            for change in changes:
                goal_id = change.get("goal_id")
                new_priority = change.get("new_priority")
                if goal_id and new_priority:
                    try:
                        goal_uuid = UUID(goal_id) if isinstance(goal_id, str) else goal_id
                        if new_priority == "active":
                            await goal_service.promote_goal(goal_uuid)
                        elif new_priority in ("queued", "backburner"):
                            await goal_service.demote_goal(goal_uuid, new_priority)
                        results.append({"goal_id": str(goal_id), "new_priority": new_priority, "success": True})
                    except Exception as e:
                        results.append({"goal_id": str(goal_id), "error": str(e), "success": False})

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=cost,
                data={
                    "changes_requested": len(changes),
                    "changes_applied": sum(1 for r in results if r.get("success")),
                    "results": results,
                },
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Reprioritize action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


class BrainstormGoalsHandler(ActionHandler):
    """
    BrainstormGoals: Generate new goal ideas.

    Cost: 3
    Params: context (str), count (int)
    Output: List of suggested goals
    """

    action_type = ActionType.BRAINSTORM_GOALS

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Brainstorm new goals."""
        started_at = datetime.utcnow()
        cost = self.energy_service.get_action_cost(self.action_type)

        try:
            context = request.params.get("context", "current state")
            count = request.params.get("count", 3)

            # 1. Generate goal ideas via LLM
            from api.services.llm_service import chat_completion
            import json
            
            system_prompt = f"""You are Dionysus's creative goal-setting faculty.
            Generate {count} new goal ideas for the cognitive system based on the provided context.
            Respond ONLY with a JSON list of objects: [{{"title": "...", "description": "...", "priority": "queued", "source": "curiosity"}}]
            """
            
            response = await chat_completion(
                messages=[{"role": "user", "content": f"Context for brainstorming: {context}"}],
                system_prompt=system_prompt,
                model=GPT5_NANO,
                max_tokens=500
            )
            
            try:
                # Clean JSON response
                cleaned = response.strip()
                if cleaned.startswith("```"): cleaned = cleaned.strip("`").replace("json", "").strip()
                suggestions = json.loads(cleaned)
            except:
                suggestions = [{"title": f"Explore {context}", "source": "curiosity"}]

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=cost,
                data={
                    "context": context,
                    "suggestions": suggestions,
                },
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"BrainstormGoals action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


class ReachOutUserHandler(ActionHandler):
    """
    ReachOutUser: Send message to user.

    Cost: 5
    Params: message (str), urgency (str)
    Output: Delivery status
    """

    action_type = ActionType.REACH_OUT_USER

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Send a message to the user."""
        started_at = datetime.utcnow()
        cost = self.energy_service.get_action_cost(self.action_type)

        try:
            message = request.params.get("message", "")
            urgency = request.params.get("urgency", "normal")

            if not message:
                return ActionResult(
                    action_type=self.action_type,
                    status=ActionStatus.FAILED,
                    energy_cost=0.0,
                    error="No message provided",
                    started_at=started_at,
                    ended_at=datetime.utcnow(),
                )

            # Check cooldown (don't spam user)
            driver = self._get_driver()
            async with driver.session() as session:
                cooldown_result = await session.run(
                    """
                    MATCH (c:HeartbeatConfig {key: 'user_reach_out_cooldown_hours'})
                    RETURN c.value as cooldown
                    """
                )
                cooldown_record = await cooldown_result.single()
                cooldown_hours = cooldown_record["cooldown"] if cooldown_record else 4.0

                # Check last reach out
                last_result = await session.run(
                    """
                    MATCH (m:Memory)
                    WHERE m.memory_type = 'user_outreach'
                    RETURN max(m.created_at) as last_outreach
                    """
                )
                last_record = await last_result.single()

                if last_record and last_record["last_outreach"]:
                    last_outreach = last_record["last_outreach"].to_native()
                    since_last = (datetime.utcnow() - last_outreach).total_seconds() / 3600
                    if since_last < cooldown_hours:
                        return ActionResult(
                            action_type=self.action_type,
                            status=ActionStatus.SKIPPED,
                            energy_cost=0.0,  # No cost if skipped
                            error=f"Cooldown: {cooldown_hours - since_last:.1f}h remaining",
                            data={"cooldown_remaining_hours": cooldown_hours - since_last},
                            started_at=started_at,
                            ended_at=datetime.utcnow(),
                        )

                # Store outreach as memory
                await session.run(
                    """
                    CREATE (m:Memory {
                        id: randomUUID(),
                        content: $message,
                        memory_type: 'user_outreach',
                        source: 'heartbeat',
                        urgency: $urgency,
                        created_at: datetime()
                    })
                    """,
                    message=message,
                    urgency=urgency,
                )

            # TODO: Actually send via notification system
            logger.info(f"User outreach ({urgency}): {message[:100]}...")

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=cost,
                data={
                    "message_sent": True,
                    "urgency": urgency,
                    "message_length": len(message),
                },
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"ReachOutUser action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


class ReachOutPublicHandler(ActionHandler):
    """
    ReachOutPublic: Post to public channel (X/Twitter, etc).

    Cost: 7
    Params: content (str), platform (str)
    Output: Post status
    """

    action_type = ActionType.REACH_OUT_PUBLIC

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Post to a public channel."""
        started_at = datetime.utcnow()
        cost = self.energy_service.get_action_cost(self.action_type)

        try:
            content = request.params.get("content", "")
            platform = request.params.get("platform", "twitter")

            if not content:
                return ActionResult(
                    action_type=self.action_type,
                    status=ActionStatus.FAILED,
                    energy_cost=0.0,
                    error="No content provided",
                    started_at=started_at,
                    ended_at=datetime.utcnow(),
                )

            # TODO: Integrate with social media APIs
            # For now, just log and store
            driver = self._get_driver()
            async with driver.session() as session:
                await session.run(
                    """
                    CREATE (m:Memory {
                        id: randomUUID(),
                        content: $content,
                        memory_type: 'public_outreach',
                        source: 'heartbeat',
                        platform: $platform,
                        created_at: datetime()
                    })
                    """,
                    content=content,
                    platform=platform,
                )

            logger.info(f"Public outreach ({platform}): {content[:100]}...")

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=cost,
                data={
                    "posted": True,  # Would be False if API fails
                    "platform": platform,
                    "content_length": len(content),
                },
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"ReachOutPublic action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


# =============================================================================
# T050: Mental Model Actions
# =============================================================================


class ReviseModelHandler(ActionHandler):
    """
    ReviseModel: Revise a mental model's structure.

    Cost: 3
    Params: model_id (UUID), trigger_description (str), add_basins (list), remove_basins (list)
    Output: Revision result with new accuracy
    """

    action_type = ActionType.REVISE_MODEL

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Revise a mental model."""
        started_at = datetime.utcnow()
        cost = self.energy_service.get_action_cost(self.action_type)

        try:
            model_id = request.params.get("model_id")
            trigger_description = request.params.get("trigger_description", "Automatic revision")
            add_basins = request.params.get("add_basins", [])
            remove_basins = request.params.get("remove_basins", [])

            if not model_id:
                return ActionResult(
                    action_type=self.action_type,
                    status=ActionStatus.FAILED,
                    energy_cost=0.0,
                    error="model_id is required",
                    started_at=started_at,
                    ended_at=datetime.utcnow(),
                )

            from api.models.mental_model import ReviseModelRequest
            from api.services.model_service import get_model_service

            model_service = get_model_service()

            model_uuid = UUID(model_id) if isinstance(model_id, str) else model_id
            revision_request = ReviseModelRequest(
                trigger_description=trigger_description,
                add_basins=[UUID(b) if isinstance(b, str) else b for b in add_basins],
                remove_basins=[UUID(b) if isinstance(b, str) else b for b in remove_basins],
            )

            revision = await model_service.apply_revision(model_uuid, revision_request)
            updated_model = await model_service.get_model(model_uuid)

            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                energy_cost=cost,
                data={
                    "model_id": str(model_uuid),
                    "revision_id": str(revision.id),
                    "revision_number": revision.revision_number,
                    "new_accuracy": updated_model.prediction_accuracy if updated_model else None,
                },
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )

        except ValueError as e:
            logger.warning(f"ReviseModel validation error: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"ReviseModel action failed: {e}")
            return ActionResult(
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=str(e),
                started_at=started_at,
                ended_at=datetime.utcnow(),
            )


# =============================================================================
# T007: MOSAEIC Memory Management Actions
# =============================================================================


class ReviseBeliefHandler(ActionHandler):
    """
    ReviseBelief: Update or replace a semantic belief.

    DEPRECATED: Feature 011 - Belief revision moved to Neo4j via n8n webhooks.
    Beliefs are now stored as Belief nodes in Neo4j graph with Pattern relationships.
    This handler is a no-op stub for backwards compatibility.

    Cost: 0 (no-op)
    Params: belief_id (UUID), prediction_correct (bool) - ignored
    Output: Deprecation notice
    """

    action_type = ActionType.REVISE_BELIEF

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Return deprecation notice - belief revision now handled by Neo4j."""
        started_at = datetime.utcnow()

        return ActionResult(
            action_type=self.action_type,
            status=ActionStatus.COMPLETED,
            energy_cost=0.0,  # No-op, no cost
            data={
                "deprecated": True,
                "message": "Belief revision moved to Neo4j. Use mosaeic/v1/pattern/detect webhook.",
                "belief_id": request.params.get("belief_id"),
            },
            started_at=started_at,
            ended_at=datetime.utcnow(),
        )


class PruneEpisodicHandler(ActionHandler):
    """
    PruneEpisodic: Apply episodic decay to old memories.

    DEPRECATED: Feature 011 - Episodic decay moved to Neo4j via n8n workflows.
    MoSAEIC captures are now stored in Neo4j graph with Graphiti temporal versioning.
    This handler is a no-op stub for backwards compatibility.

    Cost: 0 (no-op)
    Params: threshold_days (int, optional) - ignored
    Output: Deprecation notice
    """

    action_type = ActionType.PRUNE_EPISODIC

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Return deprecation notice - episodic decay now handled by Neo4j/Graphiti."""
        started_at = datetime.utcnow()

        return ActionResult(
            action_type=self.action_type,
            status=ActionStatus.COMPLETED,
            energy_cost=0.0,  # No-op, no cost
            data={
                "deprecated": True,
                "message": "Episodic decay moved to Neo4j. MoSAEIC captures use Graphiti temporal versioning.",
                "candidates_found": 0,
                "fully_decayed": 0,
                "dimensions_decayed": 0,
                "duration_ms": 0,
                "errors": 0,
            },
            started_at=started_at,
            ended_at=datetime.utcnow(),
        )


class ArchiveSemanticHandler(ActionHandler):
    """
    ArchiveSemantic: Archive low-confidence semantic beliefs.

    DEPRECATED: Feature 011 - Semantic archival moved to Neo4j via Graphiti.
    Beliefs are now stored in Neo4j graph with temporal versioning (valid_from/valid_to).
    This handler is a no-op stub for backwards compatibility.

    Cost: 0 (no-op)
    Params: confidence_threshold, stale_days - ignored
    Output: Deprecation notice
    """

    action_type = ActionType.ARCHIVE_SEMANTIC

    async def execute(self, request: ActionRequest) -> ActionResult:
        """Return deprecation notice - semantic archival now handled by Graphiti."""
        started_at = datetime.utcnow()

        return ActionResult(
            action_type=self.action_type,
            status=ActionStatus.COMPLETED,
            energy_cost=0.0,  # No-op, no cost
            data={
                "deprecated": True,
                "message": "Semantic archival moved to Neo4j. Graphiti handles temporal versioning.",
                "candidates_found": 0,
                "archived": 0,
                "duration_ms": 0,
                "errors": 0,
            },
            started_at=started_at,
            ended_at=datetime.utcnow(),
        )


# =============================================================================
# Action Executor Registry
# =============================================================================


class ActionExecutor:
    """
    Central action executor that routes requests to appropriate handlers.
    """

    def __init__(self, energy_service: EnergyService | None = None, driver=None):
        """
        Initialize the action executor.

        Args:
            energy_service: EnergyService instance (creates one if not provided)
            driver: Neo4j driver
        """
        if energy_service is None:
            from api.services.energy_service import get_energy_service

            energy_service = get_energy_service()

        self._energy_service = energy_service
        self._driver = driver

        # Register all handlers
        self._handlers: dict[ActionType, ActionHandler] = {
            # Free actions (T012)
            ActionType.OBSERVE: ObserveHandler(energy_service, driver),
            ActionType.REVIEW_GOALS: ReviewGoalsHandler(energy_service, driver),
            ActionType.REMEMBER: RememberHandler(energy_service, driver),
            ActionType.REST: RestHandler(energy_service, driver),
            # Memory/Reasoning actions (T013)
            ActionType.RECALL: RecallHandler(energy_service, driver),
            ActionType.CONNECT: ConnectHandler(energy_service, driver),
            ActionType.MAINTAIN: MaintainHandler(energy_service, driver),
            ActionType.REFLECT: ReflectHandler(energy_service, driver),
            ActionType.INQUIRE_SHALLOW: InquireShallowHandler(energy_service, driver),
            ActionType.INQUIRE_DEEP: InquireDeepHandler(energy_service, driver),
            ActionType.SYNTHESIZE: SynthesizeHandler(energy_service, driver),
            # Goal/Communication actions (T014)
            ActionType.REPRIORITIZE: ReprioritizeHandler(energy_service, driver),
            ActionType.BRAINSTORM_GOALS: BrainstormGoalsHandler(energy_service, driver),
            ActionType.REACH_OUT_USER: ReachOutUserHandler(energy_service, driver),
            ActionType.REACH_OUT_PUBLIC: ReachOutPublicHandler(energy_service, driver),
            # Mental Model actions (T050)
            ActionType.REVISE_MODEL: ReviseModelHandler(energy_service, driver),
            # MOSAEIC Memory Management actions (T007)
            ActionType.REVISE_BELIEF: ReviseBeliefHandler(energy_service, driver),
            ActionType.PRUNE_EPISODIC: PruneEpisodicHandler(energy_service, driver),
            ActionType.ARCHIVE_SEMANTIC: ArchiveSemanticHandler(energy_service, driver),
        }

    async def execute(self, request: ActionRequest) -> ActionResult:
        """
        Execute an action request.

        Args:
            request: The action to execute

        Returns:
            ActionResult with outcome
        """
        handler = self._handlers.get(request.action_type)

        if not handler:
            logger.error(f"No handler for action type: {request.action_type}")
            return ActionResult(
                action_type=request.action_type,
                status=ActionStatus.FAILED,
                energy_cost=0.0,
                error=f"No handler for action type: {request.action_type}",
                started_at=datetime.utcnow(),
                ended_at=datetime.utcnow(),
            )

        # Check if we can afford this action
        cost = self._energy_service.get_action_cost(request.action_type)
        if cost > 0:
            can_afford = await self._energy_service.can_afford_action(request.action_type)
            if not can_afford:
                logger.warning(f"Cannot afford action {request.action_type.value} (cost: {cost})")
                return ActionResult(
                    action_type=request.action_type,
                    status=ActionStatus.SKIPPED,
                    energy_cost=0.0,
                    error="Insufficient energy",
                    started_at=datetime.utcnow(),
                    ended_at=datetime.utcnow(),
                )

        # Execute the action
        result = await handler.execute(request)

        # Spend energy if successful
        if result.status == ActionStatus.COMPLETED and result.energy_cost > 0:
            await self._energy_service.spend_energy(result.energy_cost)

        return result

    async def execute_plan(self, requests: list[ActionRequest]) -> list[ActionResult]:
        """
        Execute a list of action requests in order.

        Stops when energy is exhausted.

        Args:
            requests: List of actions to execute

        Returns:
            List of results
        """
        results = []

        for request in requests:
            result = await self.execute(request)
            results.append(result)

            # Stop if we ran out of energy
            if result.status == ActionStatus.SKIPPED and result.error == "Insufficient energy":
                logger.info("Energy exhausted, stopping action plan execution")
                break

        return results


# =============================================================================
# Service Factory
# =============================================================================

_action_executor_instance: ActionExecutor | None = None


def get_action_executor() -> ActionExecutor:
    """Get or create the ActionExecutor singleton."""
    global _action_executor_instance
    if _action_executor_instance is None:
        _action_executor_instance = ActionExecutor()
    return _action_executor_instance
