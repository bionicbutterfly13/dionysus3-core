import hashlib
import json
import logging
import uuid
from typing import Any, Dict

from smolagents import CodeAgent

logger = logging.getLogger("dionysus.consciousness")

# Feature 039: Use ManagedAgent wrappers for native multi-agent orchestration
from api.agents.managed import (
    ManagedPerceptionAgent,
    ManagedReasoningAgent,
    ManagedMetacognitionAgent,
)
from api.agents.managed.marketing import ManagedMarketingStrategist
from api.agents.tools.cognitive_tools import (
    context_explorer,
    cognitive_check,
    understand_question,
    recall_related,
    examine_answer,
    backtracking,
    authorize_destruction,
    set_mental_focus
)
from api.agents.tools.planning_tools import active_planner
from api.agents.tools.meta_tot_tools import meta_tot_decide, meta_tot_run
from api.services.bootstrap_recall_service import BootstrapRecallService
from api.services.metaplasticity_service import get_metaplasticity_controller
from api.services.meta_cognitive_service import get_meta_learner
from api.models.meta_cognition import CognitiveEpisode
from api.models.bootstrap import BootstrapConfig
from api.agents.self_modeling_callback import create_self_modeling_callback
from api.models.beautiful_loop import PrecisionError, ResonanceMode, ResonanceSignal
from api.services.hyper_model_service import get_hyper_model_service
from api.services.resonance_detector import get_resonance_detector
from api.services.unified_reality_model import get_unified_reality_model

class ConsciousnessManager:
    """
    Orchestrates specialized cognitive agents (Perception, Reasoning, Metacognition)
    using smolagents hierarchical managed_agents architecture.
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
        self._perception_managed = self.perception_wrapper.get_managed()
        self._reasoning_managed = self.reasoning_wrapper.get_managed()
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
                current_callbacks = agent.step_callbacks or {}
                # Note: step_callbacks is a dict in smolagents, we extend via audit registry
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
        self._entered = False

    async def run_ooda_cycle(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a full OODA loop via the managed agent hierarchy.
        """
        if not self._entered:
            with self:
                return await self._run_ooda_cycle(initial_context)
        return await self._run_ooda_cycle(initial_context)

    async def _run_ooda_cycle(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal implementation of OODA loop execution with timeout and gating.
        """
        from api.agents.resource_gate import run_agent_with_timeout
        
        logger.info("CONSCIOUSNESS OODA CYCLE START (MANAGED AGENTS)")

        # Beautiful Loop: forecast precision profile at cycle start
        hyper_model = get_hyper_model_service()
        cycle_id = initial_context.get("cycle_id") or str(uuid.uuid4())
        initial_context["cycle_id"] = cycle_id
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
        agent_id = initial_context.get("agent_id", "dionysus-1")
        prior_check_result = await self._check_prior_constraints(agent_id, task_query, initial_context)

        if not prior_check_result.get("permitted", True):
            # BASAL VIOLATION - Hard block, return early
            logger.warning(f"BASAL PRIOR VIOLATION: {prior_check_result.get('reason')}")
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
                logger.debug(f"Meta-Cognitive Learner injected lessons from {len(past_episodes)} past episodes.")

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
        
        Your Goal:
        1. Delegate to 'perception' to gather current state and relevant memories. 
           NOTE: Check 'bootstrap_past_context' in initial_context for automatic grounding.
        2. Delegate to 'reasoning' to analyze the perception results and initial context.
           NOTE: Apply 'meta_cognitive_lessons' if present.
           COORDINATION: Follow the 'coordination_plan' mode: {initial_context['coordination_plan']['mode']}.
           AFFORDANCES: Prioritize using these tools if relevant: {', '.join(initial_context['coordination_plan']['afforded_tools'])}.
           PROTOCOL: If 'enforce_checklist' is true, instruct 'reasoning' to follow the 
           'Checklist-Driven Surgeon' protocol: Understand Question -> Recall Related -> Reason -> Examine Answer -> Backtrack (if needed).
        3. Delegate to 'metacognition' to review goals and decide on strategic updates.
        4. Synthesize everything into a final actionable plan.
        
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
        
        # Run with timeout and gating (T0.3, Q4)
        raw_result = await run_agent_with_timeout(
            self.orchestrator, 
            prompt, 
            timeout_seconds=90, # Orchestrator needs more time for 3 sub-agents
            use_ollama=is_ollama
        )
        
        # T017: Calculate OODA Surprise (prediction error)
        confidence = 0.8 # Default
        try:
            cleaned = str(raw_result).strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            
            structured_result = json.loads(cleaned)
            confidence = structured_result.get("confidence", 0.8)
        except Exception:
            structured_result = {"reasoning": str(raw_result)}

        surprise_level = 1.0 - confidence
        
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
            urm_service = get_unified_reality_model()
            resonance_detector = get_resonance_detector()
            resonance_signal = resonance_detector.detect(urm_service.get_model(), cycle_id=cycle_id)
            
            # Store signal for next cycle grounding
            initial_context["resonance_signal"] = resonance_signal.model_dump()
            
            if resonance_signal.mode == ResonanceMode.DISSONANT:
                logger.warning(f"DISSONANCE DETECTED (Urgency: {resonance_signal.discovery_urgency:.2f})")
                # Release a metacognitive particle via current reality model to signal the crunch
                from api.models.meta_cognition import MetacognitiveParticle
                particle = MetacognitiveParticle(
                    particle_id=f"res_{cycle_id[:8]}",
                    content=f"Resonance failure in cycle {cycle_id}. Mode: DISSONANT.",
                    urgency=resonance_signal.discovery_urgency,
                    metadata={"surprisal": resonance_signal.surprisal}
                )
                urm_service.add_metacognitive_particle(particle)
        except Exception as e:
            logger.debug(f"Resonance detection failed: {e}")

        return {
            "final_plan": structured_result.get("reasoning", str(raw_result)),
            "actions": structured_result.get("actions", []),
            "confidence": structured_result.get("confidence", 0.5),
            "orchestrator_log": self.orchestrator.memory.steps
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
