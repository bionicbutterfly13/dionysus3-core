import os
import json
from typing import Any, Dict

from smolagents import ToolCallingAgent, LiteLLMModel
from api.agents.perception_agent import PerceptionAgent
from api.agents.reasoning_agent import ReasoningAgent
from api.agents.metacognition_agent import MetacognitionAgent
from api.agents.tools.cognitive_tools import context_explorer, cognitive_check
from api.services.bootstrap_recall_service import BootstrapRecallService
from api.services.metaplasticity_service import get_metaplasticity_controller
from api.models.bootstrap import BootstrapConfig
from api.agents.self_modeling_callback import create_self_modeling_callback

class ConsciousnessManager:
    """
    Orchestrates specialized cognitive agents (Perception, Reasoning, Metacognition)
    using smolagents hierarchical managed_agents architecture.
    """

    def __init__(self, model_id: str = "dionysus-agents"):
        """
        Initialize the Consciousness Manager and its managed sub-agents.
        """
        from api.services.llm_service import get_router_model
        self.model = get_router_model(model_id=model_id)
        
        # Instantiate cognitive services
        self.bootstrap_svc = BootstrapRecallService()
        self.metaplasticity_svc = get_metaplasticity_controller()
        
        # Instantiate sub-agent wrappers
        self.perception_agent_wrapper = PerceptionAgent()
        self.reasoning_agent_wrapper = ReasoningAgent()
        self.metacognition_agent_wrapper = MetacognitionAgent()
        
        self.orchestrator = None
        self._entered = False

    def __enter__(self):
        from api.agents.audit import get_audit_callback
        from api.utils.callbacks import CallbackRegistry
        from smolagents.memory import ActionStep
        
        # 1. Initialize Audit Registry (T2.1)
        audit = get_audit_callback()
        
        # Helper to setup standardized registries for agents
        def setup_agent_registry(agent_name):
            registry = CallbackRegistry()
            
            # Add audit callbacks
            audit_dict = audit.get_registry(agent_name)
            for step_type, callback in audit_dict.items():
                registry.register(step_type, callback)
                
            # Add opt-in self-modeling callback (conditional on feature flag)
            self_modeling_cb = create_self_modeling_callback(agent_id=agent_name)
            if self_modeling_cb:
                # self-modeling currently only supports ActionStep
                registry.register(ActionStep, self_modeling_cb)
                print(f"DEBUG: Self-modeling callback enabled for {agent_name}")
                
            return registry.wrap_as_dict() # smolagents 1.23 still uses dict internally mostly

        # Enter sub-agents and apply callbacks
        self.perception_agent_wrapper.__enter__()
        self.perception_agent_wrapper.agent.step_callbacks = setup_agent_registry("perception")

        self.reasoning_agent_wrapper.__enter__()
        self.reasoning_agent_wrapper.agent.step_callbacks = setup_agent_registry("reasoning")

        self.metacognition_agent_wrapper.__enter__()
        self.metacognition_agent_wrapper.agent.step_callbacks = setup_agent_registry("metacognition")
        
        # Add Explorer and Cognitive tools to Reasoning specifically
        self.reasoning_agent_wrapper.agent.tools[context_explorer.name] = context_explorer
        self.reasoning_agent_wrapper.agent.tools[cognitive_check.name] = cognitive_check
        
        # T0.2: The orchestrator agent manages specialized agents.
        # (Docker sandboxing disabled for local Darwin environment stability)
        self.orchestrator = CodeAgent(
            tools=[],
            model=self.model,
            managed_agents=[
                self.perception_agent_wrapper.agent, 
                self.reasoning_agent_wrapper.agent, 
                self.metacognition_agent_wrapper.agent
            ],
            name="consciousness_manager",
            description="High-level cognitive orchestrator. Use 'perception' to gather data, 'reasoning' to analyze, and 'metacognition' to decide on strategy.",
            use_structured_outputs_internally=True,
            executor_type="local",
            additional_authorized_imports=["importlib.resources", "json", "datetime"],
            step_callbacks=setup_agent_registry("consciousness_manager"), # T2.1
            max_steps=10, 
            planning_interval=3 
        )
        self._entered = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.perception_agent_wrapper.__exit__(exc_type, exc_val, exc_tb)
        self.reasoning_agent_wrapper.__exit__(exc_type, exc_val, exc_tb)
        self.metacognition_agent_wrapper.__exit__(exc_type, exc_val, exc_tb)
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
        
        print("=== CONSCIOUSNESS OODA CYCLE START (MANAGED AGENTS) ===")
        
        # T012: Bootstrap Recall Integration
        project_id = initial_context.get("project_id", "default")
        task_query = initial_context.get("task", "")
        
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
            print(f"DEBUG: Bootstrap Recall injected {bootstrap_result.source_count} sources (summarized={bootstrap_result.summarized})")

        prompt = f"""
        Execute a full OODA (Observe-Orient-Decide-Act) cycle based on the current context.
        
        Initial Context:
        {json.dumps(initial_context, indent=2)}
        
        Your Goal:
        1. Delegate to 'perception' to gather current state and relevant memories. 
           NOTE: Check 'bootstrap_past_context' in initial_context for automatic grounding.
        2. Delegate to 'reasoning' to analyze the perception results and initial context.
        3. Delegate to 'metacognition' to review goals and decide on strategic updates.
        4. Synthesize everything into a final actionable plan.
        
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
        
        # Log adjustment for observability
        print(f"DEBUG: Metaplasticity adjusted learning_rate={adjusted_lr:.4f}, max_steps={new_max_steps} (surprise={surprise_level:.2f})")
        
        # Note: In smolagents, we update the agent properties directly
        for agent in [self.perception_agent_wrapper.agent, self.reasoning_agent_wrapper.agent, self.metacognition_agent_wrapper.agent]:
            agent.max_steps = new_max_steps
        
        print("\n=== CONSCIOUSNESS OODA CYCLE COMPLETE ===")

        return {
            "final_plan": structured_result.get("reasoning", str(raw_result)),
            "actions": structured_result.get("actions", []),
            "confidence": structured_result.get("confidence", 0.5),
            "orchestrator_log": self.orchestrator.memory.steps
        }

    def close(self):
        """Cascade close to all managed sub-agents."""
        for agent_wrapper in [self.perception_agent_wrapper, self.reasoning_agent_wrapper, self.metacognition_agent_wrapper]:
            if hasattr(agent_wrapper, 'close'):
                agent_wrapper.close()
