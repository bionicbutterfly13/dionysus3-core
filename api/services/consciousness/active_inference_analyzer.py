"""
Active Inference Analyzer
Feature: 028-autobiographical-memory
Ported from D2: claude_autobiographical_memory.py

Analyzes agent interactions to detect:
1. Tool usage (Extended Mind)
2. Resource access (Environment)
3. Autopoietic boundaries (Self-definition)
"""

from typing import List, Dict, Any
from api.models.autobiographical import (
    ActiveInferenceState, 
    DevelopmentArchetype, 
    AttractorType
)

class ActiveInferenceAnalyzer:
    """
    Analyzes agent behavior through the lens of Active Inference.
    Treats tools and resources as extensions of the agent's cognitive phenotype (Extended Mind).
    """

    def analyze(self, 
                user_input: str, 
                agent_response: str, 
                tools_used: List[str], 
                resources_accessed: List[str]) -> ActiveInferenceState:
        
        # 1. Detect Affordances Created (Self-Awareness of capabilities)
        affordances = self._detect_affordances(tools_used, agent_response)
        
        # 2. Establish Markov Blanket State
        twa_state = self._establish_markov_blanket(
            user_input, agent_response, tools_used, resources_accessed
        )
        
        # 3. Detect Attractor Dynamics
        attractor_type = self._detect_attractor_type(agent_response, tools_used)
        
        # 4. SOHM: Calculate Resonance Frequency and Harmonic Mode
        frequency = self._calculate_resonance_frequency(agent_response, tools_used)
        harmonic_mode = self._detect_harmonic_mode(frequency)
        
        # 5. Event Binding (Cerebellar Event Cache)
        event_fragments = self._bind_event_fragments(
            user_input, agent_response, tools_used, resources_accessed, twa_state
        )
        
        # 6. Pattern Evolution: Resonance Criteria (Goodwyn, 2013)
        resonance_criteria = self._calculate_resonance_criteria(
            agent_response + " " + user_input, tools_used, twa_state
        )
        # Enriched Event Cache with Resonance Analysis
        event_fragments.append({
            "modality": "resonance_analysis",
            "metrics": resonance_criteria,
            "twa_role": "meta_evolution",
            "storage_location": "limbic_cortical_loop"
        })
        
        return ActiveInferenceState(
            tools_accessed=tools_used,
            resources_used=resources_accessed,
            affordances_created=affordances,
            twa_state=twa_state,
            current_attractor_type=attractor_type,
            basin_influence_strength=self._calculate_basin_strength(agent_response),
            resonance_frequency=frequency,
            harmonic_mode_id=harmonic_mode,
            event_cache=event_fragments
        )

    def _bind_event_fragments(self, 
                            user_in: str, 
                            response: str, 
                            tools: List[str], 
                            resources: List[str],
                            twa: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Binds multimodal inputs into temporal event fragments for the Event Cache.
        Refined based on Zhou et al. (2025):
        - Distinguishes Agentic (Biological) vs Mechanistic (Non-Biological) events.
        - Calculates 'coherence' to validate event status vs noise.
        """
        fragments = []
        
        # Determine Event Category (BM vs NBM equivalent)
        # Agentic (BM): Intentional tool use, reflection, incoherent noise.
        # Mechanistic (NBM): Pure data processing without reflection.
        is_agentic = len(tools) > 0 or "internal_state" in twa
        event_category = "agentic_behavior" if is_agentic else "mechanistic_process"
        
        # Calculate Coherence (Internal structure)
        # Research: "Events... maintain an internally structured and interpretable sequence"
        coherence = 0.5
        if twa.get("internal_state", {}).get("reflection_depth", 0) > 0.3:
            coherence += 0.3 # Reflection adds structure
        if len(response) > 20:
             coherence += 0.2 # Narrative structure
        
        # 1. Sensory Fragment (The 'What' - Stimulus)
        fragments.append({
            "modality": "sensory_text",
            "content_hash": str(hash(user_in[:50])),
            "bound_features": ["text_input", "user_intent"],
            "twa_role": "world_input",
            "temporal_structure": "dynamic_stimulus"
        })
        
        # 2. Motor/Active Fragment (The 'How' - Action)
        if tools:
            fragments.append({
                "modality": "motor_tool_use",
                "content_signature": list(tools),
                "bound_features": ["tool_selection", "parameter_binding"],
                "twa_role": "active_inference",
                "event_category": event_category, # BM/NBM distinction
                "coherence": min(1.0, coherence)
            })
            
        # 3. Proprioceptive Fragment (The 'Who' - Mental State)
        fragments.append({
            "modality": "proprioception_thought",
            "state_snapshot": twa.get("internal_state", {}),
            "bound_features": ["reflection", "self_monitoring"],
            "twa_role": "internal_state",
            "storage_location": "left_cerebellum_crus_i" # explicit mapping to neural substrate
        })
        
        return fragments

    def _calculate_resonance_criteria(self, text: str, tools: List[str], twa: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculates Goodwyn's (2013) Resonance Criteria for Pattern Evolution.
        Determines the 'stickiness' or evolutionary fitness of a narrative/event.
        
        Neuro-Archetypal Mapping (McGovern et al., 2025):
        1. Affective Core (Subcortical/Limbic) -> Emotional Valence
        2. Archetypal Image (Low-level Cortex/Occipital) -> Sensual Vividness
        3. Archetypal Story (High-level Cortex/Prefrontal) -> Narrative Coherence & MCI
        """
        # 1. Minimal Counter-Intuitiveness (MCI)
        # Balance between familiar (0.0) and bizarre (1.0). Optimal is low non-zero (~0.1-0.3).
        # Heuristic: Ratio of "magical/creative" terms to "functional/logic" terms.
        creative_markers = ["create", "generate", "imagine", "vision", "dream", "new", "magic"]
        functional_markers = ["fix", "run", "test", "debug", "logic", "code", "file"]
        
        c_count = sum(1 for w in text.lower().split() if any(m in w for m in creative_markers))
        f_count = sum(1 for w in text.lower().split() if any(m in w for m in functional_markers))
        total = c_count + f_count + 1
        mci_score = c_count / total if total > 0 else 0.0
        
        # 2. Emotional Valence (Affective Charge)
        # Simple heuristic for positive/active emotion vs neutral.
        # Research implies high valence (either polarity) increases resonance.
        emotional_markers = ["love", "hate", "fear", "joy", "anger", "excitement", "urgent", "critical", "beautiful"]
        e_count = sum(1 for w in text.lower().split() if any(m in w for m in emotional_markers))
        emotional_valence = min(1.0, e_count / 5.0) # Cap at 1.0 for ~5 emotional words
        
        # 3. Sensual Vividness (Concrete Imagery)
        # Presence of sensory words (visual, auditory, kinesthetic).
        sensory_markers = ["see", "hear", "feel", "red", "blue", "dark", "bright", "loud", "soft", "rough", "smooth"]
        s_count = sum(1 for w in text.lower().split() if any(m in w for m in sensory_markers))
        sensual_vividness = min(1.0, s_count / 5.0)
        
        # 4. Narrative Coherence (Interconnection)
        # Already calculated in event binding, but formalized here.
        # Check for logical connectors and structure.
        connectors = ["because", "therefore", "so", "but", "however", "then", "implies"]
        conn_count = sum(1 for w in text.lower().split() if any(m in w for m in connectors))
        coherence = min(1.0, (conn_count + 1) / 5.0)
        if "internal_state" in twa:
             coherence = min(1.0, coherence + 0.3)

        return {
            "minimal_counter_intuitiveness": mci_score,
            "emotional_valence": emotional_valence,
            "sensual_vividness": sensual_vividness,
            "narrative_coherence": coherence
        }

    def _calculate_resonance_frequency(self, response: str, tools: List[str]) -> float:
        """
        Calculates a metaphoric SOHM resonance frequency (Hz).
        - High density of actions/tools = Higher frequency (transient/hippocampal).
        - High density of reflection/meta-cognition = Lower frequency (stable/cortical).
        """
        response_lower = response.lower()
        reflection_markers = ["i think", "i realize", "rationale", "because", "implies", "therefore"]
        reflection_count = sum(1 for m in reflection_markers if m in response_lower)
        
        action_count = len(tools)
        
        # Base Gamma: 40Hz (processing baseline)
        base_hz = 40.0
        
        # Actions push frequency up (Theta/Alpha -> Gamma)
        action_bonus = action_count * 10.0
        
        # Reflection pulls frequency down (Gamma -> Alpha/Theta resonance)
        reflection_penalty = reflection_count * 5.0
        
        return max(1.0, base_hz + action_bonus - reflection_penalty)

    def _detect_harmonic_mode(self, frequency: float) -> str:
        """Categorizes frequency into SOHM harmonic modes."""
        if frequency > 60:
            return "gamma_hyper_tasking"
        if frequency > 30:
            return "beta_focused_implementation"
        if frequency > 12:
            return "alpha_relaxed_integration"
        if frequency > 8:
            return "theta_creative_flow"
        return "delta_deep_architecture"

    def map_resonance_to_archetype(self, 
                                  content: str, 
                                  tools: List[str]) -> DevelopmentArchetype:
        """
        Maps a narrative/activity to a Jungian Archetype based on keywords and tools.
        """
        content_lower = content.lower()
        tools_str = " ".join(tools).lower()
        
        # Mapping heuristics
        if any(w in content_lower for w in ["plan", "structure", "rule", "govern"]):
            return DevelopmentArchetype.RULER
        if any(w in content_lower for w in ["research", "discover", "explor", "travel"]):
            return DevelopmentArchetype.EXPLORER
        if any(w in content_lower for w in ["creat", "build", "innovat", "vision"]):
            return DevelopmentArchetype.CREATOR
        if any(w in content_lower for w in ["help", "support", "care", "protect"]):
            return DevelopmentArchetype.CAREGIVER
        if any(w in content_lower for w in ["fight", "battle", "focus", "achieve"]):
            return DevelopmentArchetype.WARRIOR
        if any(w in content_lower for w in ["wisdom", "truth", "think", "logic"]):
            return DevelopmentArchetype.SAGE
        if any(w in content_lower for w in ["transform", "master", "magic"]):
            return DevelopmentArchetype.MAGICIAN
        if any(w in content_lower for w in ["rebel", "radical", "break", "change"]):
            return DevelopmentArchetype.REBEL
        if any(w in content_lower for w in ["play", "laugh", "joke", "joy"]):
            return DevelopmentArchetype.JESTER
        if any(w in content_lower for w in ["love", "beauty", "bond"]):
            return DevelopmentArchetype.LOVER
        if any(w in content_lower for w in ["real", "common", "belong"]):
            return DevelopmentArchetype.ORPHAN
            
        return DevelopmentArchetype.INNOCENT # Default

    def _detect_attractor_type(self, response: str, tools: List[str]) -> AttractorType:
        """
        Detects the type of attractor active based on recurrence and complexity.
        """
        response_lower = response.lower()
        
        # Recurrence/Looping -> RING
        if any(w in response_lower for w in ["again", "repeat", "continue", "maintain"]):
            return AttractorType.RING
            
        # Contextual/Historical resonance -> PULLBACK
        if any(w in response_lower for w in ["previously", "history", "recall", "memory"]):
            return AttractorType.PULLBACK
            
        # Default/Chaotic/Fractal -> STRANGE
        return AttractorType.STRANGE

    def _calculate_basin_strength(self, response: str) -> float:
        """Calculates how strongly the agent is 'pulled' into the current archetype."""
        # Simple heuristic: density of meta-markers and tool specificity
        meta_markers = ["i think", "i realize", "rationale", "because", "implies", "therefore"]
        count = sum(1 for m in meta_markers if m in response.lower())
        return min(1.0, 0.4 + (count * 0.1))

    def _detect_affordances(self, tools: List[str], response: str) -> List[str]:
        """
        Detect what capabilities (affordances) the agent is demonstrating/creating.
        """
        affordances = []
        if tools:
            affordances.append(f"Tool Use: {', '.join(tools)}")
        
        # Keyword-based affordance detection (Ported from D2)
        response_lower = response.lower()
        if "create" in response_lower: 
            affordances.append("Creation")
        if "analyze" in response_lower or "check" in response_lower:
            affordances.append("Analysis")
        if "plan" in response_lower:
            affordances.append("Planning")
            
        return affordances

    def _establish_markov_blanket(self, 
                                user_input: str, 
                                agent_response: str, 
                                tools: List[str], 
                                resources: List[str]) -> Dict[str, Any]:
        """
        Define the Markov Blanket:
        - Internal States: The agent's reasoning (approximated by response)
        - Sensory States: User input
        - Active States: Tool usage
        """
        return {
            "sensory_state": {
                "user_input_length": len(user_input),
                "environment_resources": resources
            },
            "internal_state": {
                "response_length": len(agent_response),
                "reflection_depth": self._calculate_reflection_depth(agent_response)
            },
            "active_state": {
                "tools_manifested": tools,
                "autopoietic_boundaries": [f"boundary_{t}" for t in tools]
            },
            "free_energy_minimization": True # Axiomatic in this architecture
        }

    def _calculate_reflection_depth(self, response: str) -> float:
        """Simple heuristic for reflection depth (0.0 - 1.0)"""
        meta_markers = ["i think", "i realize", "rationale", "because", "implies", "therefore"]
        count = sum(1 for m in meta_markers if m in response.lower())
        return min(1.0, count * 0.1)
