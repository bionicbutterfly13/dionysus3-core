"""
Belief Tracking Service

Manages belief transformation lifecycle through IAS journey.
Integrates with Graphiti for Neo4j persistence.

Feature: IAS Belief Tracking
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from api.models.belief_journey import (
    BeliefJourney,
    LimitingBelief,
    EmpoweringBelief,
    BeliefExperiment,
    ReplayLoop,
    MOSAEICCapture,
    VisionElement,
    SupportCircle,
    SupportCircleMember,
    BeliefStatus,
    EmpoweringBeliefStatus,
    ExperimentOutcome,
    ReplayLoopStatus,
    IASPhase,
    IASLesson,
    BeliefIngestionPayload,
    ExperimentIngestionPayload,
    ReplayLoopIngestionPayload,
)
from api.services.graphiti_service import get_graphiti_service

logger = logging.getLogger(__name__)


class BeliefTrackingService:
    """
    Service for tracking belief transformation through IAS journey.
    
    Responsibilities:
    - Create and manage belief journeys
    - Track limiting belief identification and dissolution
    - Track empowering belief building and embodiment
    - Record experiments and their outcomes
    - Manage replay loop identification and resolution
    - Persist all events to Neo4j via Graphiti
    """
    
    def __init__(self, driver=None):
        from api.services.remote_sync import get_neo4j_driver
        self._driver = driver or get_neo4j_driver()
        self._journeys: Dict[UUID, BeliefJourney] = {}
        # Track ingestion failures for observability
        self._failed_ingestions: List[Dict[str, Any]] = []
        self._successful_ingestions: int = 0
        self._total_ingestion_attempts: int = 0
    
    # =========================================================================
    # Journey Management
    # =========================================================================
    
    async def create_journey(
        self,
        participant_id: Optional[str] = None,
    ) -> BeliefJourney:
        """Create a new belief transformation journey."""
        journey = BeliefJourney(
            id=uuid4(),
            participant_id=participant_id,
            graphiti_group_id=f"ias_journey_{uuid4().hex[:8]}",
        )
        self._journeys[journey.id] = journey
        await self._persist_journey(journey)
        
        # Ingest journey start event
        await self._ingest_journey_event(
            journey_id=journey.id,
            event_type="journey_started",
            content=f"IAS belief transformation journey started for participant {participant_id or 'anonymous'}",
        )
        
        logger.info(f"Created belief journey {journey.id}")
        return journey

    async def _persist_journey(self, journey: BeliefJourney) -> None:
        """Persist basic journey state to Neo4j."""
        cypher = """
        MERGE (j:IASJourney {id: $id})
        SET j.participant_id = $participant_id,
            j.graphiti_group_id = $group_id,
            j.current_phase = $phase,
            j.current_lesson = $lesson,
            j.lessons_completed = $lessons,
            j.created_at = datetime($created_at),
            j.last_activity_at = datetime($updated_at)
        """
        await self._driver.execute_query(cypher, {
            "id": str(journey.id),
            "participant_id": journey.participant_id,
            "group_id": journey.graphiti_group_id,
            "phase": journey.current_phase.value,
            "lesson": journey.current_lesson.value,
            "lessons": [l.value for l in journey.lessons_completed],
            "created_at": journey.created_at.isoformat(),
            "updated_at": journey.last_activity_at.isoformat()
        })
    
    async def get_journey(self, journey_id: UUID) -> Optional[BeliefJourney]:
        """Get a journey by ID, from memory or Neo4j."""
        if journey_id in self._journeys:
            return self._journeys[journey_id]
            
        # Try loading from Neo4j
        cypher = "MATCH (j:IASJourney {id: $id}) RETURN j"
        result = await self._driver.execute_query(cypher, {"id": str(journey_id)})
        
        if not result:
            return None
            
        # For MVP, we'll re-populate memory cache
        # Real implementation would rehydrate the full object
        # For now, we trust the cache for active sessions
        return None 

    
    async def advance_lesson(
        self,
        journey_id: UUID,
        lesson: IASLesson,
    ) -> BeliefJourney:
        """Mark a lesson as completed and advance progress."""
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        if lesson not in journey.lessons_completed:
            journey.lessons_completed.append(lesson)
        
        journey.current_lesson = lesson
        journey.last_activity_at = datetime.utcnow()
        
        # Update phase based on lesson
        if lesson in [IASLesson.BREAKTHROUGH_MAPPING, IASLesson.MOSAEIC_METHOD, IASLesson.REPLAY_LOOP_BREAKER]:
            journey.current_phase = IASPhase.REVELATION
        elif lesson in [IASLesson.CONVICTION_GAUNTLET, IASLesson.PERSPECTIVE_MATRIX, IASLesson.VISION_ACCELERATOR]:
            journey.current_phase = IASPhase.REPATTERNING
        else:
            journey.current_phase = IASPhase.STABILIZATION
        
        await self._ingest_journey_event(
            journey_id=journey_id,
            event_type="lesson_completed",
            content=f"Completed {lesson.value} in phase {journey.current_phase.value}",
        )
        
        return journey
    
    # =========================================================================
    # Limiting Belief Tracking
    # =========================================================================
    
    async def identify_limiting_belief(
        self,
        journey_id: UUID,
        content: str,
        pattern_name: Optional[str] = None,
        origin_memory: Optional[str] = None,
        self_talk: Optional[List[str]] = None,
        mental_blocks: Optional[List[str]] = None,
        self_sabotage_behaviors: Optional[List[str]] = None,
        protects_from: Optional[str] = None,
    ) -> LimitingBelief:
        """
        Identify a new limiting belief (Lesson 1: Breakthrough Mapping).
        """
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        belief = LimitingBelief(
            id=uuid4(),
            journey_id=journey_id,
            content=content,
            pattern_name=pattern_name,
            origin_memory=origin_memory,
            origin_lesson=IASLesson.BREAKTHROUGH_MAPPING,
            self_talk=self_talk or [],
            mental_blocks=mental_blocks or [],
            self_sabotage_behaviors=self_sabotage_behaviors or [],
            protects_from=protects_from,
            status=BeliefStatus.IDENTIFIED,
        )
        
        journey.limiting_beliefs.append(belief)
        journey.last_activity_at = datetime.utcnow()
        
        # Ingest to Graphiti
        payload = BeliefIngestionPayload(
            event_type="belief_identified",
            journey_id=journey_id,
            belief_id=belief.id,
            content=content,
            context={
                "pattern_name": pattern_name,
                "origin": origin_memory,
                "protects_from": protects_from,
                "self_talk": self_talk,
                "mental_blocks": mental_blocks,
                "behaviors": self_sabotage_behaviors,
            },
        )
        await self._ingest_belief_event(payload)
        
        logger.info(f"Identified limiting belief: {content[:50]}...")
        return belief
    
    async def map_belief_to_behaviors(
        self,
        journey_id: UUID,
        belief_id: UUID,
        self_talk: List[str],
        mental_blocks: List[str],
        self_sabotage_behaviors: List[str],
        protects_from: str,
    ) -> LimitingBelief:
        """
        Map a belief to its behavioral manifestations (Lesson 1, Action 3).
        """
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        belief = next((b for b in journey.limiting_beliefs if b.id == belief_id), None)
        if not belief:
            raise ValueError(f"Belief {belief_id} not found")
        
        belief.self_talk = self_talk
        belief.mental_blocks = mental_blocks
        belief.self_sabotage_behaviors = self_sabotage_behaviors
        belief.protects_from = protects_from
        belief.status = BeliefStatus.MAPPED
        
        journey.last_activity_at = datetime.utcnow()
        
        # Ingest mapping event
        payload = BeliefIngestionPayload(
            event_type="belief_mapped",
            journey_id=journey_id,
            belief_id=belief_id,
            content=belief.content,
            context={
                "self_talk": self_talk,
                "mental_blocks": mental_blocks,
                "behaviors": self_sabotage_behaviors,
                "protects_from": protects_from,
            },
        )
        await self._ingest_belief_event(payload)
        
        return belief
    
    async def add_evidence_for_belief(
        self,
        journey_id: UUID,
        belief_id: UUID,
        evidence: str,
        evidence_type: str = "for",  # "for" or "against"
    ) -> LimitingBelief:
        """Add evidence for or against a limiting belief."""
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        belief = next((b for b in journey.limiting_beliefs if b.id == belief_id), None)
        if not belief:
            raise ValueError(f"Belief {belief_id} not found")
        
        if evidence_type == "for":
            belief.evidence_for.append(evidence)
        else:
            belief.evidence_against.append(evidence)
            # Adjust strength based on counter-evidence
            belief.strength = max(0.0, belief.strength - 0.1)
            if belief.strength < 0.3:
                belief.status = BeliefStatus.DISSOLVING
        
        journey.last_activity_at = datetime.utcnow()
        return belief
    
    async def dissolve_belief(
        self,
        journey_id: UUID,
        belief_id: UUID,
        replaced_by_id: Optional[UUID] = None,
    ) -> LimitingBelief:
        """Mark a limiting belief as dissolved."""
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        belief = next((b for b in journey.limiting_beliefs if b.id == belief_id), None)
        if not belief:
            raise ValueError(f"Belief {belief_id} not found")
        
        belief.status = BeliefStatus.DISSOLVED
        belief.strength = 0.0
        belief.dissolved_at = datetime.utcnow()
        belief.replaced_by = replaced_by_id
        
        journey.beliefs_dissolved += 1
        journey.last_activity_at = datetime.utcnow()
        
        # Ingest dissolution event
        payload = BeliefIngestionPayload(
            event_type="belief_dissolved",
            journey_id=journey_id,
            belief_id=belief_id,
            content=belief.content,
            context={
                "replaced_by": str(replaced_by_id) if replaced_by_id else None,
                "final_strength": belief.strength,
                "evidence_against_count": len(belief.evidence_against),
            },
        )
        await self._ingest_belief_event(payload)
        
        logger.info(f"Dissolved belief: {belief.content[:50]}...")
        return belief
    
    # =========================================================================
    # Empowering Belief Tracking
    # =========================================================================
    
    async def propose_empowering_belief(
        self,
        journey_id: UUID,
        content: str,
        bridge_version: Optional[str] = None,
        replaces_belief_id: Optional[UUID] = None,
    ) -> EmpoweringBelief:
        """
        Propose a new empowering belief (Lesson 4: Conviction Gauntlet).
        """
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        belief = EmpoweringBelief(
            id=uuid4(),
            journey_id=journey_id,
            content=content,
            bridge_version=bridge_version,
            replaces_belief_id=replaces_belief_id,
            status=EmpoweringBeliefStatus.PROPOSED,
        )
        
        journey.empowering_beliefs.append(belief)
        journey.last_activity_at = datetime.utcnow()
        
        # Ingest to Graphiti
        payload = BeliefIngestionPayload(
            event_type="empowering_belief_proposed",
            journey_id=journey_id,
            belief_id=belief.id,
            content=content,
            context={
                "bridge_version": bridge_version,
                "replaces": str(replaces_belief_id) if replaces_belief_id else None,
            },
        )
        await self._ingest_belief_event(payload)
        
        logger.info(f"Proposed empowering belief: {content[:50]}...")
        return belief
    
    async def strengthen_empowering_belief(
        self,
        journey_id: UUID,
        belief_id: UUID,
        evidence: str,
        embodiment_increase: float = 0.1,
    ) -> EmpoweringBelief:
        """Add evidence and increase embodiment of an empowering belief."""
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        belief = next((b for b in journey.empowering_beliefs if b.id == belief_id), None)
        if not belief:
            raise ValueError(f"Belief {belief_id} not found")
        
        belief.evidence_collected.append(evidence)
        belief.embodiment_level = min(1.0, belief.embodiment_level + embodiment_increase)
        
        if belief.embodiment_level >= 0.3 and belief.status == EmpoweringBeliefStatus.PROPOSED:
            belief.status = EmpoweringBeliefStatus.TESTING
            belief.first_tested_at = datetime.utcnow()
        elif belief.embodiment_level >= 0.6:
            belief.status = EmpoweringBeliefStatus.STRENGTHENING
        elif belief.embodiment_level >= 0.85:
            belief.status = EmpoweringBeliefStatus.EMBODIED
            belief.embodied_at = datetime.utcnow()
            journey.beliefs_embodied += 1
        
        journey.last_activity_at = datetime.utcnow()
        return belief
    
    async def anchor_belief_to_habit(
        self,
        journey_id: UUID,
        belief_id: UUID,
        habit_stack: str,
        checklist_items: List[str],
    ) -> EmpoweringBelief:
        """
        Anchor empowering belief to daily habit (Lesson 7: Habit Harmonizer).
        """
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        belief = next((b for b in journey.empowering_beliefs if b.id == belief_id), None)
        if not belief:
            raise ValueError(f"Belief {belief_id} not found")
        
        belief.habit_stack = habit_stack
        belief.daily_checklist_items = checklist_items
        
        journey.last_activity_at = datetime.utcnow()
        
        # Ingest anchoring event
        payload = BeliefIngestionPayload(
            event_type="belief_anchored",
            journey_id=journey_id,
            belief_id=belief_id,
            content=belief.content,
            context={
                "habit_stack": habit_stack,
                "checklist_items": checklist_items,
            },
        )
        await self._ingest_belief_event(payload)
        
        return belief
    
    # =========================================================================
    # Experiment Tracking
    # =========================================================================
    
    async def design_experiment(
        self,
        journey_id: UUID,
        limiting_belief_id: Optional[UUID] = None,
        empowering_belief_id: Optional[UUID] = None,
        hypothesis: str = "",
        action_to_take: str = "",
        context: str = "low",  # low, mid, high stakes
    ) -> BeliefExperiment:
        """
        Design a belief experiment (Lesson 4: Conviction Gauntlet).
        """
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        # Get belief strength before
        limiting_strength = None
        empowering_strength = None
        
        if limiting_belief_id:
            belief = next((b for b in journey.limiting_beliefs if b.id == limiting_belief_id), None)
            if belief:
                limiting_strength = belief.strength
        
        if empowering_belief_id:
            belief = next((b for b in journey.empowering_beliefs if b.id == empowering_belief_id), None)
            if belief:
                empowering_strength = belief.embodiment_level
        
        experiment = BeliefExperiment(
            id=uuid4(),
            journey_id=journey_id,
            limiting_belief_id=limiting_belief_id,
            empowering_belief_id=empowering_belief_id,
            hypothesis=hypothesis,
            action_taken=action_to_take,
            context=context,
            limiting_belief_strength_before=limiting_strength,
            empowering_belief_strength_before=empowering_strength,
        )
        
        journey.experiments.append(experiment)
        journey.last_activity_at = datetime.utcnow()
        
        return experiment
    
    async def record_experiment_result(
        self,
        journey_id: UUID,
        experiment_id: UUID,
        outcome: ExperimentOutcome,
        actual_result: str,
        emotional_response: Optional[str] = None,
        belief_shift_observed: Optional[str] = None,
    ) -> BeliefExperiment:
        """Record the results of a belief experiment."""
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        experiment = next((e for e in journey.experiments if e.id == experiment_id), None)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment.outcome = outcome
        experiment.actual_result = actual_result
        experiment.emotional_response = emotional_response
        experiment.belief_shift_observed = belief_shift_observed
        experiment.executed_at = datetime.utcnow()
        
        # Update belief strengths based on outcome
        if outcome == ExperimentOutcome.DISCONFIRMING:
            if experiment.limiting_belief_id:
                await self.add_evidence_for_belief(
                    journey_id, experiment.limiting_belief_id, actual_result, "against"
                )
                belief = next((b for b in journey.limiting_beliefs if b.id == experiment.limiting_belief_id), None)
                if belief:
                    experiment.limiting_belief_strength_after = belief.strength
            
            if experiment.empowering_belief_id:
                await self.strengthen_empowering_belief(
                    journey_id, experiment.empowering_belief_id, actual_result, 0.15
                )
                belief = next((b for b in journey.empowering_beliefs if b.id == experiment.empowering_belief_id), None)
                if belief:
                    experiment.empowering_belief_strength_after = belief.embodiment_level
        
        journey.total_experiments_run += 1
        journey.last_activity_at = datetime.utcnow()
        
        # Ingest to Graphiti
        limiting_belief = next((b for b in journey.limiting_beliefs if b.id == experiment.limiting_belief_id), None) if experiment.limiting_belief_id else None
        
        payload = ExperimentIngestionPayload(
            journey_id=journey_id,
            experiment_id=experiment_id,
            belief_tested=limiting_belief.content if limiting_belief else "Unknown",
            hypothesis=experiment.hypothesis,
            action_taken=experiment.action_taken,
            outcome=outcome.value,
            result_description=actual_result,
            belief_shift=belief_shift_observed,
        )
        await self._ingest_experiment_event(payload)
        
        return experiment
    
    # =========================================================================
    # Replay Loop Tracking
    # =========================================================================
    
    async def identify_replay_loop(
        self,
        journey_id: UUID,
        trigger_situation: str,
        story_text: str,
        emotion: str,
        fear_underneath: str,
        pattern_name: Optional[str] = None,
        fed_by_belief_id: Optional[UUID] = None,
    ) -> ReplayLoop:
        """
        Identify a new replay loop (Lesson 3: Replay Loop Breaker).
        """
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        loop = ReplayLoop(
            id=uuid4(),
            journey_id=journey_id,
            trigger_situation=trigger_situation,
            story_text=story_text,
            pattern_name=pattern_name,
            emotion=emotion,
            fear_underneath=fear_underneath,
            fed_by_belief_id=fed_by_belief_id,
            status=ReplayLoopStatus.ACTIVE,
        )
        
        # Link to belief if provided
        if fed_by_belief_id:
            belief = next((b for b in journey.limiting_beliefs if b.id == fed_by_belief_id), None)
            if belief:
                belief.triggers_replay_loops.append(loop.id)
        
        journey.replay_loops.append(loop)
        journey.last_activity_at = datetime.utcnow()
        
        # Ingest to Graphiti
        payload = ReplayLoopIngestionPayload(
            event_type="loop_identified",
            journey_id=journey_id,
            loop_id=loop.id,
            trigger=trigger_situation,
            story=story_text,
            emotion=emotion,
            fear=fear_underneath,
        )
        await self._ingest_replay_event(payload)
        
        logger.info(f"Identified replay loop: {pattern_name or trigger_situation[:30]}...")
        return loop
    
    async def interrupt_replay_loop(
        self,
        journey_id: UUID,
        loop_id: UUID,
        compassionate_reflection: str,
    ) -> ReplayLoop:
        """Apply compassionate reflection to interrupt a loop (Step 2)."""
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        loop = next((l for l in journey.replay_loops if l.id == loop_id), None)
        if not loop:
            raise ValueError(f"Replay loop {loop_id} not found")
        
        loop.compassionate_reflection = compassionate_reflection
        loop.status = ReplayLoopStatus.INTERRUPTED
        loop.last_triggered_at = datetime.utcnow()
        
        journey.last_activity_at = datetime.utcnow()
        return loop
    
    async def resolve_replay_loop(
        self,
        journey_id: UUID,
        loop_id: UUID,
        lesson_found: str,
        comfort_offered: str,
        next_step_taken: Optional[str] = None,
        time_to_resolution_minutes: Optional[float] = None,
    ) -> ReplayLoop:
        """
        Resolve a replay loop with lesson and comfort (Lesson 3, Step 3).
        """
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        loop = next((l for l in journey.replay_loops if l.id == loop_id), None)
        if not loop:
            raise ValueError(f"Replay loop {loop_id} not found")
        
        loop.lesson_found = lesson_found
        loop.comfort_offered = comfort_offered
        loop.next_step_taken = next_step_taken
        loop.time_to_resolution_minutes = time_to_resolution_minutes
        loop.status = ReplayLoopStatus.RESOLVED
        loop.resolved_at = datetime.utcnow()
        
        journey.replay_loops_resolved += 1
        journey.last_activity_at = datetime.utcnow()
        
        # Ingest resolution event
        payload = ReplayLoopIngestionPayload(
            event_type="loop_resolved",
            journey_id=journey_id,
            loop_id=loop_id,
            trigger=loop.trigger_situation,
            story=loop.story_text,
            emotion=loop.emotion,
            fear=loop.fear_underneath,
            resolution=f"Lesson: {lesson_found}. Comfort: {comfort_offered}",
        )
        await self._ingest_replay_event(payload)
        
        logger.info(f"Resolved replay loop: {loop.pattern_name or loop.trigger_situation[:30]}...")
        return loop
    
    # =========================================================================
    # MOSAEIC Tracking
    # =========================================================================
    
    async def capture_mosaeic(
        self,
        journey_id: UUID,
        high_pressure_context: str,
        sensations: Optional[List[str]] = None,
        actions: Optional[List[str]] = None,
        emotions: Optional[List[str]] = None,
        impulses: Optional[List[str]] = None,
        cognitions: Optional[List[str]] = None,
        narrative_identified: Optional[str] = None,
        connects_to_belief_id: Optional[UUID] = None,
    ) -> MOSAEICCapture:
        """
        Capture a MOSAEIC observation (Lesson 2: Mosaeic Method).
        """
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        capture = MOSAEICCapture(
            id=uuid4(),
            journey_id=journey_id,
            high_pressure_context=high_pressure_context,
            sensations=sensations or [],
            actions=actions or [],
            emotions=emotions or [],
            impulses=impulses or [],
            cognitions=cognitions or [],
            narrative_identified=narrative_identified,
            connects_to_belief_id=connects_to_belief_id,
        )
        
        journey.mosaeic_captures.append(capture)
        journey.last_activity_at = datetime.utcnow()
        
        return capture
    
    # =========================================================================
    # Vision Tracking
    # =========================================================================
    
    async def add_vision_element(
        self,
        journey_id: UUID,
        description: str,
        category: str = "general",
        values_aligned: Optional[List[str]] = None,
        first_step: Optional[str] = None,
        requires_dissolution_of: Optional[List[UUID]] = None,
    ) -> VisionElement:
        """
        Add a vision element (Lesson 6: Vision Accelerator).
        """
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        vision = VisionElement(
            id=uuid4(),
            journey_id=journey_id,
            description=description,
            category=category,
            values_aligned=values_aligned or [],
            first_step=first_step,
            requires_dissolution_of=requires_dissolution_of or [],
        )
        
        journey.vision_elements.append(vision)
        journey.last_activity_at = datetime.utcnow()
        
        return vision
    
    # =========================================================================
    # Support Circle
    # =========================================================================
    
    async def create_support_circle(
        self,
        journey_id: UUID,
    ) -> SupportCircle:
        """Create a support circle (Lesson 9: Growth Anchor)."""
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        circle = SupportCircle(
            id=uuid4(),
            journey_id=journey_id,
        )
        
        journey.support_circle = circle
        journey.last_activity_at = datetime.utcnow()
        
        return circle
    
    async def add_circle_member(
        self,
        journey_id: UUID,
        role: str,
        name: Optional[str] = None,
        check_in_frequency: str = "monthly",
        value_provided: Optional[str] = None,
    ) -> SupportCircle:
        """Add a member to the support circle."""
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        if not journey.support_circle:
            await self.create_support_circle(journey_id)
        
        member = SupportCircleMember(
            role=role,
            name=name,
            check_in_frequency=check_in_frequency,
            value_provided=value_provided,
        )
        
        journey.support_circle.members.append(member)
        journey.support_circle.total_members += 1
        journey.support_circle.active_members += 1
        journey.support_circle.last_updated = datetime.utcnow()
        journey.last_activity_at = datetime.utcnow()
        
        return journey.support_circle
    
    # =========================================================================
    # Metrics & Analytics
    # =========================================================================
    
    def get_journey_metrics(self, journey_id: UUID) -> Dict[str, Any]:
        """Get comprehensive metrics for a journey."""
        journey = self._journeys.get(journey_id)
        if not journey:
            raise ValueError(f"Journey {journey_id} not found")
        
        # Calculate belief dissolution rate
        total_limiting = len(journey.limiting_beliefs)
        dissolved = sum(1 for b in journey.limiting_beliefs if b.status == BeliefStatus.DISSOLVED)
        dissolution_rate = dissolved / total_limiting if total_limiting > 0 else 0
        
        # Calculate embodiment rate
        total_empowering = len(journey.empowering_beliefs)
        embodied = sum(1 for b in journey.empowering_beliefs if b.status == EmpoweringBeliefStatus.EMBODIED)
        embodiment_rate = embodied / total_empowering if total_empowering > 0 else 0
        
        # Average replay resolution time
        resolved_loops = [l for l in journey.replay_loops if l.time_to_resolution_minutes]
        avg_resolution_time = (
            sum(l.time_to_resolution_minutes for l in resolved_loops) / len(resolved_loops)
            if resolved_loops else None
        )
        
        # Experiment success rate
        disconfirming = sum(1 for e in journey.experiments if e.outcome == ExperimentOutcome.DISCONFIRMING)
        experiment_success_rate = disconfirming / journey.total_experiments_run if journey.total_experiments_run > 0 else 0
        
        return {
            "journey_id": str(journey_id),
            "current_phase": journey.current_phase.value,
            "current_lesson": journey.current_lesson.value,
            "lessons_completed": len(journey.lessons_completed),
            "limiting_beliefs": {
                "total": total_limiting,
                "dissolved": dissolved,
                "dissolution_rate": dissolution_rate,
            },
            "empowering_beliefs": {
                "total": total_empowering,
                "embodied": embodied,
                "embodiment_rate": embodiment_rate,
            },
            "experiments": {
                "total": journey.total_experiments_run,
                "success_rate": experiment_success_rate,
            },
            "replay_loops": {
                "total": len(journey.replay_loops),
                "resolved": journey.replay_loops_resolved,
                "avg_resolution_time_minutes": avg_resolution_time,
            },
            "support_circle": {
                "total_members": journey.support_circle.total_members if journey.support_circle else 0,
                "active_members": journey.support_circle.active_members if journey.support_circle else 0,
            },
        }
    
    # =========================================================================
    # Graphiti Integration
    # =========================================================================
    
    async def _ingest_journey_event(
        self,
        journey_id: UUID,
        event_type: str,
        content: str,
    ) -> None:
        """Ingest a journey event into Graphiti."""
        self._total_ingestion_attempts += 1
        try:
            graphiti = await get_graphiti_service()
            journey = self._journeys.get(journey_id)
            group_id = journey.graphiti_group_id if journey else f"ias_journey_{journey_id.hex[:8]}"
            
            await graphiti.ingest_message(
                content=f"IAS JOURNEY EVENT: {event_type}\n{content}",
                source_description="ias_belief_tracking",
                group_id=group_id,
            )
            self._successful_ingestions += 1
        except Exception as e:
            logger.warning(f"Failed to ingest journey event to Graphiti: {e}")
            self._failed_ingestions.append({
                "type": "journey_event",
                "journey_id": str(journey_id),
                "event_type": event_type,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _ingest_belief_event(self, payload: BeliefIngestionPayload) -> None:
        """Ingest a belief event into Graphiti."""
        self._total_ingestion_attempts += 1
        try:
            graphiti = await get_graphiti_service()
            journey = self._journeys.get(payload.journey_id)
            group_id = journey.graphiti_group_id if journey else f"ias_journey_{payload.journey_id.hex[:8]}"
            
            await graphiti.ingest_message(
                content=payload.to_episode_text(),
                source_description="ias_belief_tracking",
                group_id=group_id,
            )
            self._successful_ingestions += 1
        except Exception as e:
            logger.warning(f"Failed to ingest belief event to Graphiti: {e}")
            self._failed_ingestions.append({
                "type": "belief_event",
                "journey_id": str(payload.journey_id),
                "belief_id": str(payload.belief_id),
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _ingest_experiment_event(self, payload: ExperimentIngestionPayload) -> None:
        """Ingest an experiment event into Graphiti."""
        self._total_ingestion_attempts += 1
        try:
            graphiti = await get_graphiti_service()
            journey = self._journeys.get(payload.journey_id)
            group_id = journey.graphiti_group_id if journey else f"ias_journey_{payload.journey_id.hex[:8]}"
            
            await graphiti.ingest_message(
                content=payload.to_episode_text(),
                source_description="ias_belief_tracking",
                group_id=group_id,
            )
            self._successful_ingestions += 1
        except Exception as e:
            logger.warning(f"Failed to ingest experiment event to Graphiti: {e}")
            self._failed_ingestions.append({
                "type": "experiment_event",
                "journey_id": str(payload.journey_id),
                "experiment_id": str(payload.experiment_id),
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def _ingest_replay_event(self, payload: ReplayLoopIngestionPayload) -> None:
        """Ingest a replay loop event into Graphiti."""
        self._total_ingestion_attempts += 1
        try:
            graphiti = await get_graphiti_service()
            journey = self._journeys.get(payload.journey_id)
            group_id = journey.graphiti_group_id if journey else f"ias_journey_{payload.journey_id.hex[:8]}"
            
            await graphiti.ingest_message(
                content=payload.to_episode_text(),
                source_description="ias_belief_tracking",
                group_id=group_id,
            )
            self._successful_ingestions += 1
        except Exception as e:
            logger.warning(f"Failed to ingest replay event to Graphiti: {e}")
            self._failed_ingestions.append({
                "type": "replay_event",
                "journey_id": str(payload.journey_id),
                "loop_id": str(payload.loop_id),
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })

    def get_ingestion_health(self) -> Dict[str, Any]:
        """
        Get ingestion health status for observability.
        
        Returns stats on successful vs failed Graphiti ingestions,
        allowing operators to detect silent failures.
        """
        success_rate = (
            self._successful_ingestions / self._total_ingestion_attempts
            if self._total_ingestion_attempts > 0 else 1.0
        )
        
        return {
            "total_attempts": self._total_ingestion_attempts,
            "successful": self._successful_ingestions,
            "failed": len(self._failed_ingestions),
            "success_rate": round(success_rate, 4),
            "healthy": len(self._failed_ingestions) == 0,
            "recent_failures": self._failed_ingestions[-10:],  # Last 10 failures
        }

    def clear_failed_ingestions(self) -> int:
        """Clear the failed ingestions log. Returns count cleared."""
        count = len(self._failed_ingestions)
        self._failed_ingestions.clear()
        return count


# =============================================================================
# Singleton Instance
# =============================================================================

_belief_tracking_service: Optional[BeliefTrackingService] = None


def get_belief_tracking_service() -> BeliefTrackingService:
    """Get or create the belief tracking service singleton."""
    global _belief_tracking_service
    if _belief_tracking_service is None:
        _belief_tracking_service = BeliefTrackingService()
    return _belief_tracking_service
