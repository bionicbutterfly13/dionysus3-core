import hashlib
import json
import logging
import uuid
from typing import Any, Dict, Optional

from smolagents import CodeAgent
from smolagents.memory import ActionStep

from api.agents.consolidated_memory_stores import get_consolidated_memory_store
from api.agents.managed import (
    ManagedMetacognitionAgent,
    ManagedPerceptionAgent,
    ManagedReasoningAgent,
)
from api.agents.managed.marketing import ManagedMarketingStrategist
from api.agents.self_modeling_callback import create_self_modeling_callback
from api.agents.tools.cognitive_tools import (
    authorize_destruction,
    backtracking,
    cognitive_check,
    context_explorer,
    examine_answer,
    recall_related,
    set_mental_focus,
    understand_question,
)
from api.agents.tools.meta_tot_tools import meta_tot_decide, meta_tot_run
from api.agents.tools.planning_tools import active_planner
from api.models.beautiful_loop import PrecisionError, ResonanceMode, ResonanceSignal
from api.models.bootstrap import BootstrapConfig
from api.models.meta_cognition import CognitiveEpisode
from api.services.bootstrap_recall_service import BootstrapRecallService
from api.services.context_packaging import BiographicalConstraintCell, CellPriority
from api.services.fractal_reflection_tracer import get_fractal_tracer
from api.services.worldview_integration import get_worldview_integration_service
from api.services.hyper_model_service import get_hyper_model_service
from api.services.meta_cognitive_service import get_meta_learner
from api.services.metaplasticity_service import get_metaplasticity_controller
from api.services.resonance_detector import get_resonance_detector

from api.services.unified_reality_model import get_unified_reality_model
from api.models.metacognitive_particle import MetacognitiveParticle
from api.services.particle_store import get_particle_store

logger = logging.getLogger("dionysus.consciousness")


# Feature 039: Use ManagedAgent wrappers for native multi-agent orchestration
class ConsciousnessManager:
    """
    Orchestrates specialized cognitive agents (Perception, Reasoning, Metacognition)
    using smolagents hierarchical managed_agents architecture.

    ACT-R Alignment (Anderson, 2014):
    - Observe -> Perceptual-Motor Module (PerceptionAgent)
    - Orient -> Declarative Memory (ReasoningAgent / Recall tools)
    - Decide -> Procedural Memory / Production Rules (MetacognitionAgent)
    - Act -> Motor Module (Final Plan / Action Execution)
    """

    def __init__(self, model_id: str = "dionysus-agents"):
        """
        Initialize the Consciousness Manager and its managed sub-agents.
        
        Feature 039: Uses ManagedAgent wrappers for native smolagents orchestration.
        """
        from api.services.llm_service import get_router_model
        self.model = get_router_model(model_id=model_id)
        self.model_id = model_id
        
        # Instantiate cognitive services
        self.bootstrap_svc = BootstrapRecallService()
        self.metaplasticity_svc = get_metaplasticity_controller()

        self.meta_learner = get_meta_learner()
        self.particle_store = get_particle_store()
        
        # Feature 039 (T009): Use ManagedAgent wrappers for native orchestration
        # These wrappers provide proper ManagedAgent instances with rich descriptions
        # that guide the orchestrator's delegation decisions
        self.perception_wrapper = ManagedPerceptionAgent(model_id)
        self.reasoning_wrapper = ManagedReasoningAgent(model_id)
        self.metacognition_wrapper = ManagedMetacognitionAgent(model_id)
        self.marketing_wrapper = ManagedMarketingStrategist(model_id)
        
        # Cached ManagedAgent instances
        self._perception_managed = None
        self._reasoning_managed = None
        self._metacognition_managed = None
        
        self.orchestrator = None
        self._entered = False

    def __enter__(self):
        from api.agents.audit import get_audit_callback
        
        # Initialize Audit Registry
        audit = get_audit_callback()
        
        # Feature 039 (T009): Get ToolCallingAgent instances from wrappers
        # smolagents 1.23+: agents have name/description directly, no ManagedAgent wrapper
        
        # ACT-R Alignment: Perceptual-Motor Module (Observe)
        self._perception_managed = self.perception_wrapper.get_managed()
        
        # ACT-R Alignment: Declarative Memory (Orient)
        self._reasoning_managed = self.reasoning_wrapper.get_managed()
        
        # ACT-R Alignment: Procedural Memory / Production Rules (Decide)
        self._metacognition_managed = self.metacognition_wrapper.get_managed()
        
        # Apply audit callbacks to the agents directly (they ARE ToolCallingAgents now)
        perception_callbacks = audit.get_registry("perception")
        self._perception_managed.step_callbacks = perception_callbacks
        
        reasoning_callbacks = audit.get_registry("reasoning")
        self._reasoning_managed.step_callbacks = reasoning_callbacks
        
        metacognition_callbacks = audit.get_registry("metacognition")
        self._metacognition_managed.step_callbacks = metacognition_callbacks
        self._metacognition_managed.tools[set_mental_focus.name] = set_mental_focus
        
        # T037: Add opt-in self-modeling callbacks (conditional on SELF_MODELING_ENABLED)
        for agent_name, agent in [
            ("perception", self._perception_managed),
            ("reasoning", self._reasoning_managed),
            ("metacognition", self._metacognition_managed)
        ]:
            self_modeling_cb = create_self_modeling_callback(agent_id=agent_name)
            if self_modeling_cb:
                # smolagents 1.23+: agent IS the ToolCallingAgent directly
                current_callbacks = dict(agent.step_callbacks or {})

                def _wrap_action_callback(callback):
                    def wrapped(step, agent=None, **kwargs):
                        if callback:
                            callback(step, agent=agent, **kwargs)
                        try:
                            self_modeling_cb.log_step(
                                step, getattr(step, "step_number", 0)
                            )
                        except Exception as e:
                            logger.debug(
                                f"Self-modeling callback failed for {agent_name}: {e}"
                            )

                    return wrapped

                current_callbacks[ActionStep] = _wrap_action_callback(
                    current_callbacks.get(ActionStep)
                )
                agent.step_callbacks = current_callbacks
                logger.debug(f"Self-modeling callback enabled for {agent_name}")
        
        # Add Explorer and Cognitive tools to Reasoning specifically
        # smolagents 1.23+: _reasoning_managed IS the ToolCallingAgent
        self._reasoning_managed.tools[context_explorer.name] = context_explorer
        self._reasoning_managed.tools[cognitive_check.name] = cognitive_check
        self._reasoning_managed.tools[understand_question.name] = understand_question
        self._reasoning_managed.tools[recall_related.name] = recall_related
        self._reasoning_managed.tools[examine_answer.name] = examine_answer
        self._reasoning_managed.tools[backtracking.name] = backtracking
        self._reasoning_managed.tools[active_planner.name] = active_planner
        self._reasoning_managed.tools[authorize_destruction.name] = authorize_destruction
        self._reasoning_managed.tools[meta_tot_decide.name] = meta_tot_decide
        self._reasoning_managed.tools[meta_tot_run.name] = meta_tot_run
        
        # Feature 039 (T009): Create orchestrator with native ManagedAgent instances
        # The ManagedAgent wrappers provide rich descriptions that guide delegation
        self.orchestrator = CodeAgent(
            tools=[],
            model=self.model,
            managed_agents=[
                self._perception_managed,
                self._reasoning_managed,
                self._metacognition_managed,
                self.marketing_wrapper.get_managed(),
            ],
            name="consciousness_manager",
            description="""High-level cognitive orchestrator implementing OODA loop.

Delegates to specialized agents:
- perception: OBSERVE phase - gather environment state, recall memories, capture MOSAEIC
- reasoning: ORIENT phase - analyze observations, identify patterns, build mental models
- metacognition: DECIDE phase - review goals, assess models, select actions
- marketing: EXECUTE phase - draft emails, Substack articles, and conversion copy using Analytical Empath research.

Use natural language to delegate: "Ask marketing to draft the New Year email"
The agents will return structured results for synthesis.""",
            use_structured_outputs_internally=True,
            executor_type="local",
            additional_authorized_imports=["importlib.resources", "json", "datetime"],
            step_callbacks=audit.get_registry("consciousness_manager"),
            max_steps=15,  # Feature 039: Increased for multi-agent orchestration
            planning_interval=3,  # Feature 039: Re-plan every 3 action steps
        )
        self._entered = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Feature 039: Clean up ManagedAgent wrappers
        self.perception_wrapper.__exit__(exc_type, exc_val, exc_tb)
        self.reasoning_wrapper.__exit__(exc_type, exc_val, exc_tb)
        self.metacognition_wrapper.__exit__(exc_type, exc_val, exc_tb)
        self.marketing_wrapper.__exit__(exc_type, exc_val, exc_tb)
        self._entered = False

    async def run_ooda_cycle(self, initial_context: Dict[str, Any], async_topology: bool = False) -> Dict[str, Any]:
        """
        Execute a full OODA loop.
        If async_topology=True, it submits a task-graph to the Coordination Pool instead of blocking.
        """
        if not self._entered:
            with self:
                return await self._run_ooda_cycle(initial_context, async_topology)
        return await self._run_ooda_cycle(initial_context, async_topology)

    async def _run_ooda_cycle(self, initial_context: Dict[str, Any], async_topology: bool = False) -> Dict[str, Any]:
        """
        Internal implementation of OODA loop execution with timeout and gating.
        """
        from api.agents.resource_gate import run_agent_with_timeout
        
        logger.info("CONSCIOUSNESS OODA CYCLE START (MANAGED AGENTS)")

        # Beautiful Loop: forecast precision profile at cycle start
        hyper_model = get_hyper_model_service()
        cycle_id = initial_context.get("cycle_id") or str(uuid.uuid4())
        initial_context["cycle_id"] = cycle_id

        # Track 071 (FR-001): Populate UnifiedRealityModel with cycle context at START
        urm_service = get_unified_reality_model()
        urm_service.clear_cycle_state()  # Reset transient state from previous cycle
        urm_service.update_context(initial_context, cycle_id=cycle_id)

        # Track 038 Phase 4: Start fractal reflection trace
        fractal_tracer = get_fractal_tracer()
        agent_id = initial_context.get("agent_id", "dionysus-1")
        fractal_trace = fractal_tracer.start_trace(cycle_id=cycle_id, agent_id=agent_id)

        precision_profile = hyper_model.forecast_precision_profile(
            context=initial_context,
            internal_states={},
            recent_errors=[],
        )
        initial_context["precision_profile"] = precision_profile.model_dump()

        # Apply forecasted precisions to metaplasticity registry
        def _scale_precision(value: float) -> float:
            return max(0.1, min(5.0, 0.1 + (4.9 * value)))

        for layer, precision in precision_profile.layer_precisions.items():
            if layer in {"perception", "reasoning", "metacognition"}:
                self.metaplasticity_svc.set_precision(layer, _scale_precision(precision))

        # T012: Bootstrap Recall Integration
        project_id = initial_context.get("project_id", "default")
        task_query = initial_context.get("task", "")

        # Track 038 Phase 2: Evolutionary Priors Check
        # Check task against prior hierarchy BEFORE any action selection
        prior_check_result = await self._check_prior_constraints(agent_id, task_query, initial_context)

        # Track 038 Phase 4: Trace prior check through fractal tracer
        fractal_tracer.trace_prior_check(fractal_trace, prior_check_result, task_query)

        if not prior_check_result.get("permitted", True):
            # BASAL VIOLATION - Hard block, return early
            logger.warning(f"BASAL PRIOR VIOLATION: {prior_check_result.get('reason')}")
            fractal_tracer.end_trace(fractal_trace)  # End trace before early return
            return {
                "final_plan": f"Action blocked by evolutionary prior: {prior_check_result.get('reason')}",
                "actions": [],
                "confidence": 0.0,
                "blocked_by_prior": True,
                "prior_check": prior_check_result,
                "orchestrator_log": []
            }

        # Store prior context for downstream EFE selection
        initial_context["prior_check"] = prior_check_result
        if prior_check_result.get("warnings"):
            logger.debug(f"Prior warnings: {prior_check_result['warnings']}")

        # Check if bootstrap is requested or allowed
        if initial_context.get("bootstrap_recall", True):
            config = BootstrapConfig(
                project_id=project_id,
                enabled=True,
                include_trajectories=True
            )
            
            # Perform recall
            bootstrap_result = await self.bootstrap_svc.recall_context(
                query=task_query,
                project_id=project_id,
                config=config
            )
            
            # Inject into context
            initial_context["bootstrap_past_context"] = bootstrap_result.formatted_context
            logger.debug(f"Bootstrap Recall injected {bootstrap_result.source_count} sources (summarized={bootstrap_result.summarized})")

        # T005 (043): Meta-Cognitive Episodic Retrieval
        if initial_context.get("meta_learning_enabled", True):
            past_episodes = await self.meta_learner.retrieve_relevant_episodes(task_query)
            if past_episodes:
                lessons_learned = await self.meta_learner.synthesize_lessons(past_episodes)
                initial_context["meta_cognitive_lessons"] = lessons_learned
                initial_context["meta_cognitive_lessons"] = lessons_learned
                logger.debug(f"Meta-Cognitive Learner injected lessons from {len(past_episodes)} past episodes.")

        # FEATURE (Phase 4): Fractal Biographical Constraints
        # Injection of 'Biography-as-Constraint' from the current Journey
        biographical_cell = None
        try:
            biographical_cell = await self._fetch_biographical_context()
            if biographical_cell:
                # Inject directly into initial_context which becomes context for reasoning
                # Note: We rely on context_packaging service to format this if used there,
                # but here we also make it available as a raw field for the prompt template.
                initial_context["biographical_constraints"] = biographical_cell.content
                logger.info(f"FRACTAL CONSTRAINT: Injected biography '{biographical_cell.journey_id}'")
                # Track 038 Phase 4: Trace biographical injection
                fractal_tracer.trace_biographical_injection(fractal_trace, biographical_cell)
        except Exception as bio_err:
            logger.warning(f"Failed to inject biographical constraints: {bio_err}")

        # FEATURE 049: Cognitive Meta-Coordinator
        # Dynamically selects reasoning mode and afforded tools
        from api.services.cognitive_meta_coordinator import get_meta_coordinator
        coordinator = get_meta_coordinator()
        
        # Get list of available tools from reasoning agent
        available_tools = list(self._reasoning_managed.tools.keys()) if self._reasoning_managed else []
        
        coordination_plan = await coordinator.coordinate(task_query, available_tools, initial_context)
        initial_context["coordination_plan"] = {
            "mode": coordination_plan.mode.value,
            "afforded_tools": coordination_plan.afforded_tools,
            "enforce_checklist": coordination_plan.enforce_checklist,
            "rationale": coordination_plan.rationale
        }

        # Meta-ToT decision and optional pre-run (threshold gating)
        if coordination_plan.mode == "meta_tot" and initial_context.get("meta_tot_enabled", True):
            from api.services.meta_tot_decision import get_meta_tot_decision_service
            from api.services.meta_tot_engine import get_meta_tot_engine

            decision_service = get_meta_tot_decision_service()
            meta_tot_decision = decision_service.decide(task_query, initial_context)
            initial_context["meta_tot_decision"] = meta_tot_decision.model_dump()

            if meta_tot_decision.use_meta_tot and initial_context.get("meta_tot_auto_run", True):
                try:
                    engine = get_meta_tot_engine()
                    result, trace = await engine.run(task_query, initial_context, decision=meta_tot_decision)
                    initial_context["meta_tot_result"] = result.model_dump()
                    if trace is not None:
                        initial_context["meta_tot_trace"] = trace.model_dump()
                except Exception as exc:
                    initial_context["meta_tot_error"] = str(exc)

        # ULTRATHINK INJECTION
        ultrathink_instruction = ""
        resonance_signal = initial_context.get("resonance_signal")
        if resonance_signal and isinstance(resonance_signal, dict):
            # Rehydrate if it's a dict
            resonance_signal = ResonanceSignal(**resonance_signal)
            
        if resonance_signal and resonance_signal.mode == ResonanceMode.DISSONANT:
            logger.info(f"ULTRATHINK PROTOCOL ACTIVATED (Score: {resonance_signal.resonance_score:.2f})")
            ultrathink_instruction = """
        !!! PROTOCOL OVERRIDE: ULTRATHINK ACTIVATED !!!
        CRITICAL DISSONANCE DETECTED. You are now in ULTRATHINK MODE.
        1. OVERRIDE BREVITY: Do not be concise. You must engage in exhaustive, deep-level reasoning.
        2. MULTI-DIMENSIONAL ANALYSIS: Analyze the problem through Psychological, Technical, Accessibility, and Scalability lenses.
        3. ROOT CAUSE REQUIRED: Do not provide surface-level fixes. Dig until the logic is irrefutable.
        4. RECOVERY PRIORITY: Your primary goal is to resolve the dissonance and restore Worldview Coherence.
            """

        # T055: Formalize Cognitive Core (Sovereign Identity)
        from api.core.sovereign_identity import SOVEREIGN_IDENTITY_PROMPT, ANTI_BOASTING_CONSTRAINT
        
        prompt = f"""
        {SOVEREIGN_IDENTITY_PROMPT}

        {ANTI_BOASTING_CONSTRAINT}

        Execute a full OODA (Observe-Orient-Decide-Act) cycle based on the current context.
        
        Initial Context:
        {json.dumps(initial_context, indent=2, default=str)}
        {ultrathink_instruction}
        
        Your Goal (ACT-R / OODA Loop):
        1. Delegate to 'perception' (Perceptual-Motor Module) to gather current state and relevant memories (Observe). 
           NOTE: Check 'bootstrap_past_context' in initial_context for automatic grounding.
        2. Delegate to 'reasoning' (Declarative Memory) to analyze the perception results and initial context (Orient).
           NOTE: Apply 'meta_cognitive_lessons' if present.
           COORDINATION: Follow the 'coordination_plan' mode: {initial_context['coordination_plan']['mode']}.
           AFFORDANCES: Prioritize using these tools if relevant: {', '.join(initial_context['coordination_plan']['afforded_tools'])}.
           PROTOCOL: If 'enforce_checklist' is true, instruct 'reasoning' to follow the 
           'Checklist-Driven Surgeon' protocol: Understand Question -> Recall Related -> Reason -> Examine Answer -> Backtrack (if needed).
        3. Delegate to 'metacognition' (Procedural Memory) to review goals and decide on strategic updates (Decide).
        4. Synthesize everything into a final actionable plan (Act - Motor Module).
        
        META-ToT GUIDANCE:
        If 'meta_tot_result' is present in initial_context, incorporate its best_path and 
        confidence into your final strategy. It represents deep probabilistic planning.
        
        SELF-HEALING PROTOCOL:
        If a sub-agent returns a "RECOVERY_HINT", you MUST prioritize that advice in your 
        next decision step to avoid cascading failures.

        OUTPUT FORMAT:
        You MUST respond with a JSON object in this exact format:
        {{
            "reasoning": "Your summary of the situation and strategic plan",
            "actions": [
                {{"action": "recall", "params": {{"query": "..."}} }},
                {{"action": "reflect", "params": {{"topic": "..."}} }}
            ],
            "confidence": 0.9
        }}
        """
        
        # Determine if we are using Ollama for gating
        is_ollama = "ollama" in str(getattr(self.model, 'model_id', '')).lower()
        
        # Phase 4 (F091): Async Topology Gating
        if async_topology:
            from api.services.coordination_service import get_coordination_service, TaskType
            pool = get_coordination_service()
            initial_context["expand_topology"] = True # Trigger AFlow in CoordinationService
            task_id = pool.submit_task(
                payload={"query": task_query, **initial_context},
                task_type=TaskType.RESEARCH
            )
            logger.info(f"OODA Cycle delegated to ASYNC TOPOLOGY in Coordination Pool (Task: {task_id})")
            return {
                "task_id": task_id,
                "status": "ASYNCHRONOUS_ORCHESTRATION_TRIGGERED",
                "reasoning": "Goal submitted to Coordination Pool for multi-agent DAG expansion."
            }

        # Run with timeout and gating (T0.3, Q4)
        raw_result = await run_agent_with_timeout(
            self.orchestrator, 
            prompt, 
            timeout_seconds=90, # Orchestrator needs more time for 3 sub-agents
            use_ollama=is_ollama
        )
        


        # --------------------------------------------------------------------------------
        # ULTRATHINK PROTOCOL: Identity & Worldview Integrity Check (Superego)
        # --------------------------------------------------------------------------------
        worldview_svc = get_worldview_integration_service()
        
        # Identity Definition: The Vigilant Sentinel (Sovereign, Sharp, Non-Therapeutic)
        worldview_belief = (
            "Identity: Dionysus (Architect/Strategist) serving Dr. Mani (The Creator) "
            "and The Vigilant Sentinel (The Avatar). "
            "Integrity: Sovereign, autonomous, precise. Rejects 'coddling' or 'hollow success'. "
            "Mode: Active Inference Strategist, not a passive chatbot."
        )
        
        # 1. Epistemic check: Get dynamic precision baseline from Metaplasticity
        # Default to 0.5 (Uncertainty) if unspecified, NEVER 0.8 (False Certainty)
        current_precision = self.metaplasticity_svc.get_precision("reasoning")
        # Normalize precision (0.1 - 5.0) to confidence (0.0 - 1.0) approx
        dynamic_baseline = min(1.0, current_precision / 2.0) 

        # 2. Parse Result with Epistemic Resilience
        base_confidence = dynamic_baseline
        prediction_content = {}
        parsing_failed = False
        
        try:
            cleaned = str(raw_result).strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            
            structured_check = json.loads(cleaned)
            # Trust the agent's confidence ONLY if parsing succeeded
            base_confidence = structured_check.get("confidence", dynamic_baseline)
            prediction_content = structured_check
        except Exception as parse_err:
            logger.warning(f"OODA Parsing Failure: {parse_err}. Triggering Epistemic Distress.")
            parsing_failed = True
            # Confusion State: High Surprisal. 
            base_confidence = 0.1 
            prediction_content = {
                "reasoning": f"PARSE_ERROR: {str(raw_result)}", 
                "confusion": True
            }

        # 3. Apply Harmonic Filter (Worldview Gating)
        if not parsing_failed:
            filter_result = await worldview_svc.filter_prediction_by_worldview(
                prediction=prediction_content,
                worldview_belief=worldview_belief,
                base_confidence=base_confidence
            )
            
            if filter_result["flagged_for_review"]:
                # Dissonance Protocol: We warn and suppress confidence
                if isinstance(prediction_content, dict):
                    prediction_content["reasoning"] = f"[DISSONANCE] {prediction_content.get('reasoning', '')}"
                logger.warning(f"Worldview Dissonance: {filter_result['alignment_score']:.2f} < Threshold")
                
            confidence = filter_result["final_confidence"]
        else:
            confidence = base_confidence # 0.1

        structured_result = prediction_content
        
        # --------------------------------------------------------------------------------
        # FEATURE 040: Metacognitive Particle Integration (The Thinking Object)
        # --------------------------------------------------------------------------------
        # Convert dictionary thought -> Formal Particle
        # This gives it physics (precision, entropy) and storage (Graphiti)
        try:
            # Extract content text - fallback to JSON string if reasoning not found
            content_text = structured_result.get("reasoning", str(structured_result))
            
            # Create the particle
            particle = MetacognitiveParticle(
                content=content_text,
                source_agent="consciousness_manager", # or sub-agent if distinct
                precision=self.metaplasticity_svc.get_precision('reasoning'),
                entropy=1.0 - confidence, # Simple entropy approximation
                resonance_score=confidence, # High confidence = High resonance
                context_id=initial_context.get("journey_id", None) or initial_context.get("session_id", None),
                provenance_ids=structured_result.get("provenance_ids", [])
            )
            
            # Push to Working Memory (and Persistence Basin if resonant)
            await self.particle_store.add_particle(particle)
            logger.debug(f"Particle Generated: {particle.id} (Res: {confidence:.2f})")
            
        except Exception as particle_err:
            logger.error(f"Failed to generate MetacognitiveParticle: {particle_err}")

        
        # T017: Calculate OODA Surprise (prediction error)
        surprise_level = 1.0 - confidence
        
        # Feature 005: Record Prediction Error (Metaplasticity + Worldview Update)
        # Use cycle_id as prediction_id if strictly needed, or gen random
        await worldview_svc.record_prediction_error(
            model_id=None, # Use default/inferred in svc or pass agent_id
            prediction_id=uuid.uuid4(),
            prediction_error=surprise_level
        )
        
        # T018: Apply Metaplasticity to sub-agents for NEXT cycle
        adjusted_lr = self.metaplasticity_svc.calculate_learning_rate(surprise_level)
        new_max_steps = self.metaplasticity_svc.calculate_max_steps(surprise_level)
        
        # FEATURE 048: Update Dynamic Precision
        for agent_name in ["perception", "reasoning", "metacognition"]:
            new_prec = self.metaplasticity_svc.update_precision_from_surprise(agent_name, surprise_level)
            logger.debug(f"Agent '{agent_name}' Precision adjusted to {new_prec:.2f}")

        # FEATURE 045 & 050: Unified Consciousness Integration Pipeline via EventBus
        # Ensures every cognitive event updates internal physics and self-story
        try:
            from api.utils.event_bus import get_event_bus
            from api.models.meta_tot import ActiveInferenceState
            bus = get_event_bus()
            
            # Extract or estimate ActiveInferenceState
            ai_state = None
            if "meta_tot_result" in initial_context:
                # If meta_tot_result was passed back, it's already a dict or model
                res_data = initial_context["meta_tot_result"]
                if isinstance(res_data, dict):
                    ai_state_data = res_data.get("active_inference_state")
                    if ai_state_data:
                        ai_state = ActiveInferenceState(**ai_state_data)
                elif hasattr(res_data, "active_inference_state"):
                    ai_state = res_data.active_inference_state
            
            # Fallback: REPAIRED HONEST ESTIMATION
            # If no Meta-ToT, we use confidence to derive a grounded physics state
            if ai_state is None:
                surprise = 1.0 - confidence
                ai_state = ActiveInferenceState(
                    surprise=surprise,
                    prediction_error=surprise * 0.8, # Scaled error
                    precision=confidence,
                    beliefs={"context_certainty": confidence}
                )

            # Track 071 (FR-010): Update URM with active inference state
            urm_service.update_active_inference_states([ai_state])

            await bus.emit_cognitive_event(
                source="consciousness_manager",
                problem=task_query,
                reasoning=structured_result.get("reasoning", str(raw_result)),
                state=ai_state,
                context=initial_context
            )
            logger.debug(f"EventBus emitted cognitive event (Mode: {initial_context['coordination_plan']['mode']}).")
        except Exception as e:
            logger.warning(f"EventBus cognitive emission failed: {e}")

        # T006 (043): Record Cognitive Episode for Meta-Learning
        if initial_context.get("meta_learning_enabled", True):
            try:
                # Extract tools used from orchestrator memory
                tools_used = []
                for step in self.orchestrator.memory.steps:
                    if hasattr(step, 'tool_calls') and step.tool_calls:
                        for tc in step.tool_calls:
                            tools_used.append(tc.name)
                
                episode = CognitiveEpisode(
                    task_query=task_query,
                    task_context={k: v for k, v in initial_context.items() if isinstance(v, (str, int, float, bool))},
                    tools_used=list(set(tools_used)),
                    reasoning_trace=structured_result.get("reasoning", ""),
                    success=confidence > 0.6,
                    outcome_summary=structured_result.get("reasoning", ""),
                    surprise_score=surprise_level,
                    # T057: Sense of Agency = 1 - Surprise (Predictive Accuracy)
                    agency_score=1.0 - surprise_level,
                    lessons_learned=f"Used tools {tools_used}. Confidence: {confidence:.2f}"
                )
                await self.meta_learner.record_episode(episode)
            except Exception as e:
                logger.warning(f"Failed to record cognitive episode: {e}")

        # Log adjustment for observability
        logger.debug(f"Metaplasticity adjusted learning_rate={adjusted_lr:.4f}, max_steps={new_max_steps} (surprise={surprise_level:.2f})")

        # Note: In smolagents, we update the agent properties directly
        # smolagents 1.23+: managed instances ARE ToolCallingAgents directly
        if self._perception_managed and self._reasoning_managed and self._metacognition_managed:
            for agent in [self._perception_managed, self._reasoning_managed, self._metacognition_managed]:
                agent.max_steps = new_max_steps
        
        logger.info("CONSCIOUSNESS OODA CYCLE COMPLETE")

        # Beautiful Loop: compute precision errors and update hyper-model
        errors = []
        predicted_layers = precision_profile.layer_precisions
        context_hash = hashlib.sha256(
            json.dumps(initial_context, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:16]
        for layer, predicted in predicted_layers.items():
            if layer not in {"perception", "reasoning", "metacognition"}:
                continue
            actual_raw = self.metaplasticity_svc.get_precision(layer)
            actual = max(0.0, min(1.0, (actual_raw - 0.1) / 4.9))
            errors.append(
                PrecisionError(
                    layer_id=layer,
                    predicted_precision=predicted,
                    actual_precision_needed=actual,
                    context_hash=context_hash,
                )
            )

        if errors:
            learning_delta = hyper_model.record_precision_errors(errors)
            initial_context["precision_errors"] = [e.model_dump() for e in errors]
            initial_context["precision_learning_delta"] = learning_delta

        # FEATURE 049: Resonance Signaling (ULTRATHINK Architectural Synthesis)
        # Final resonance check based on bound inferences in the Unified Reality Model
        try:
            resonance_detector = get_resonance_detector()
            resonance_signal = resonance_detector.detect(urm_service.get_model(), cycle_id=cycle_id)

            # Track 071 (FR-021): Store resonance signal in URM
            urm_service.update_resonance(resonance_signal)

            # Store signal for next cycle grounding
            initial_context["resonance_signal"] = resonance_signal.model_dump()

            if resonance_signal.mode == ResonanceMode.DISSONANT:
                logger.warning(f"DISSONANCE DETECTED (Urgency: {resonance_signal.discovery_urgency:.2f})")
                # Release a metacognitive particle via current reality model to signal the crunch
                from api.models.metacognitive_particle import MetacognitiveParticle
                particle = MetacognitiveParticle(
                    id=f"res_{cycle_id[:8]}",
                    name=f"Resonance failure in cycle {cycle_id}. Mode: DISSONANT.",
                )
                urm_service.add_metacognitive_particle(particle)
        except Exception as e:
            logger.debug(f"Resonance detection failed: {e}")

        # Track 038 Phase 4: End fractal trace and include summary
        fractal_tracer.end_trace(fractal_trace)
        logger.debug(f"Fractal trace complete: {fractal_trace.summary()}")

        return {
            "final_plan": structured_result.get("reasoning", str(raw_result)),
            "actions": structured_result.get("actions", []),
            "confidence": structured_result.get("confidence", 0.5),
            "orchestrator_log": self.orchestrator.memory.steps,
            "fractal_trace": fractal_trace.to_dict(),
        }

    def close(self):
        """Cascade close to all managed sub-agents."""
        # Feature 039: Close ManagedAgent wrappers
        for wrapper in [self.perception_wrapper, self.reasoning_wrapper, self.metacognition_wrapper]:
            if hasattr(wrapper, 'close'):
                wrapper.close()

    async def _check_prior_constraints(
        self,
        agent_id: str,
        task_query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check task against the evolutionary prior hierarchy.

        Track 038 Phase 2 - Evolutionary Priors Integration

        This method:
        1. Hydrates or creates the agent's prior hierarchy
        2. Checks the task query against BASAL/DISPOSITIONAL/LEARNED priors
        3. Returns check result with permission status

        Args:
            agent_id: The agent's identifier
            task_query: The task/action to check
            context: Current cycle context

        Returns:
            Dict with permitted, warnings, effective_precision, etc.
        """
        from api.services.prior_constraint_service import get_prior_constraint_service
        from api.services.prior_persistence_service import get_prior_persistence_service

        try:
            # Try to hydrate existing hierarchy from Graphiti
            persistence = get_prior_persistence_service()
            hierarchy = await persistence.hydrate_hierarchy(agent_id)

            if hierarchy is None:
                # No hierarchy in graph - use default (in-memory only)
                # Note: For production, run scripts/seed_priors.py first
                logger.debug(f"No prior hierarchy found for {agent_id}, using defaults")
                from api.services.prior_constraint_service import create_default_hierarchy
                hierarchy = create_default_hierarchy(agent_id)

            # Store hierarchy in context for downstream use
            context["prior_hierarchy_agent_id"] = agent_id

            # Check the task query
            service = get_prior_constraint_service(agent_id, hierarchy)
            result = service.check_constraint(task_query, context)

            return result.model_dump()

        except Exception as e:
            # On error, log and permit (fail-open for now)
            # In production, consider fail-closed
            logger.warning(f"Prior check failed: {e}. Permitting action (fail-open).")
            return {
                "permitted": True,
                "warnings": [f"Prior check failed: {str(e)}"],
                "effective_precision": 1.0,
                "error": str(e)
            }

    async def _fetch_biographical_context(self, agent_id: str = "dionysus-1") -> Any:
        """
        Fetch the active Autobiographical Journey and package it as a constraint cell.

        Track 038 Phase 4: Fractal Metacognition Integration

        This method bridges biography to action selection by:
        1. Retrieving the active AutobiographicalJourney
        2. Creating a BiographicalConstraintCell (for context injection)
        3. Merging biographical priors into the agent's PriorHierarchy

        The merged priors create soft biases that influence action selection,
        ensuring the agent's behavior aligns with its narrative identity.

        Args:
            agent_id: The agent's identifier for prior hierarchy lookup

        Returns:
            BiographicalConstraintCell if journey exists, else None
        """
        try:
            store = get_consolidated_memory_store()
            journey = await store.get_active_journey()

            if journey:
                # Create the cell
                cell = BiographicalConstraintCell(
                    cell_id=f"bio_{journey.journey_id}",
                    content="", # Auto-generated
                    priority=CellPriority.CRITICAL, # MUST be visible
                    token_count=200, # Initial budget
                    journey_id=journey.title,
                    unresolved_themes=list(journey.themes)[:5], # Top 5 themes
                    identity_markers=["Narrative Coherence", "Fractal Self-Similarity"]
                )

                # PHASE 4 PATCH: Merge biographical priors into hierarchy
                # This closes the fractal loop: Biography → Priors → Action Selection
                try:
                    from api.services.prior_persistence_service import get_prior_persistence_service
                    from api.services.prior_constraint_service import get_prior_constraint_service, create_default_hierarchy

                    persistence = get_prior_persistence_service()
                    hierarchy = await persistence.hydrate_hierarchy(agent_id)

                    if hierarchy is None:
                        hierarchy = create_default_hierarchy(agent_id)

                    # Clear stale biographical priors and merge fresh ones
                    hierarchy.clear_biographical_priors()
                    bio_priors = cell.to_prior_constraints()
                    added = hierarchy.merge_biographical_priors(bio_priors)

                    if added > 0:
                        # Update cache so subsequent checks use merged priors
                        get_prior_constraint_service(agent_id, hierarchy)
                        logger.info(
                            f"FRACTAL PRIOR MERGE: {added} biographical priors injected "
                            f"from journey '{journey.title}'"
                        )
                except Exception as prior_err:
                    logger.warning(f"Failed to merge biographical priors: {prior_err}")

                return cell
        except Exception as e:
            logger.warning(f"Error fetching biographical context: {e}")
        return None
