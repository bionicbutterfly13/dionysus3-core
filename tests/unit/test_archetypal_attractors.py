import asyncio
import pytest
from api.services.consciousness.active_inference_analyzer import ActiveInferenceAnalyzer
from api.models.autobiographical import DevelopmentArchetype, AttractorType

@pytest.mark.asyncio
async def test_archetype_mapping():
    analyzer = ActiveInferenceAnalyzer()
    
    # Test Ruler
    assert analyzer.map_resonance_to_archetype("Setting new governance rules for the system.", []) == DevelopmentArchetype.RULER
    
    # Test Explorer
    assert analyzer.map_resonance_to_archetype("Exploring uncharted regions of the knowledge graph.", []) == DevelopmentArchetype.EXPLORER
    
    # Test Creator
    assert analyzer.map_resonance_to_archetype("Innovating a new cognitive bridge between services.", []) == DevelopmentArchetype.CREATOR
    
    # Test default (Innocent)
    assert analyzer.map_resonance_to_archetype("A simple processing task.", []) == DevelopmentArchetype.INNOCENT

@pytest.mark.asyncio
async def test_attractor_detection():
    analyzer = ActiveInferenceAnalyzer()
    
    # Test Ring
    assert analyzer._detect_attractor_type("Maintaining the repeat cycle.", []) == AttractorType.RING
    
    # Test Pullback
    assert analyzer._detect_attractor_type("Recalling previous state.", []) == AttractorType.PULLBACK
    
    # Test Strange
    assert analyzer._detect_attractor_type("Emergent behavior detected.", []) == AttractorType.STRANGE

@pytest.mark.asyncio
async def test_basin_strength():
    analyzer = ActiveInferenceAnalyzer()
    
    # High depth
    strength_high = analyzer._calculate_basin_strength("I realize this implies a new rationale because of the change.")
    # Low depth
    strength_low = analyzer._calculate_basin_strength("Done.")
    
    assert strength_high > strength_low
    assert strength_high <= 1.0
    assert strength_low >= 0.4

@pytest.mark.asyncio
async def test_sohm_metrics():
    analyzer = ActiveInferenceAnalyzer()
    
    # High frequency (many tools, little reflection)
    freq_high = analyzer._calculate_resonance_frequency("Working hard.", ["tool1", "tool2", "tool3"])
    mode_high = analyzer._detect_harmonic_mode(freq_high)
    
    # Low frequency (many reflections, no tools)
    freq_low = analyzer._calculate_resonance_frequency(
        "I think this implies a deeper rationale because of the architecture.", []
    )
    mode_low = analyzer._detect_harmonic_mode(freq_low)
    
    assert freq_high > freq_low
    assert mode_high == "gamma_hyper_tasking"
    assert mode_low == "alpha_relaxed_integration"

@pytest.mark.asyncio
async def test_full_analysis():
    analyzer = ActiveInferenceAnalyzer()
    
    state = analyzer.analyze(
        user_input="Implement a new feature.",
        agent_response="I will create a visionary new component. I think this implies a robust design.",
        tools_used=["tool_a"],
        resources_accessed=["res_b"]
    )
    
    assert state.current_attractor_type == AttractorType.STRANGE
    assert state.basin_influence_strength > 0.4
    assert state.basin_influence_strength > 0.4
    assert state.resonance_frequency > 0
    assert state.harmonic_mode_id is not None
    assert "tool_a" in state.tools_accessed
    assert "res_b" in state.resources_used
    
    # Verify Event Cache Binding (Cerebellar Binding)
    assert len(state.event_cache) >= 2 # Sensory + Active + Internal
    assert state.event_cache[0]["modality"] == "sensory_text"
    
    # Check BM/NBM Distinction
    tool_fragment = state.event_cache[1]
    assert tool_fragment["modality"] == "motor_tool_use"
    assert tool_fragment["event_category"] == "agentic_behavior" # Biological equivalent
    assert tool_fragment["coherence"] > 0.5
    
    # Check Neural Substrate Mapping
    proprio_fragment = state.event_cache[2]
    assert proprio_fragment["modality"] == "proprioception_thought"
    assert proprio_fragment["storage_location"] == "left_cerebellum_crus_i"

@pytest.mark.asyncio
async def test_pattern_evolution_criteria():
    analyzer = ActiveInferenceAnalyzer()
    
    # Input with creative/chaotic markers (Van Eenwyk's "Chaos") + Emotional/Vivid content (Goodwyn)
    state = analyzer.analyze(
        user_input="Imagine a beautiful, shimmering crystal dragon that defies logic and creates magic.",
        agent_response="I feel the chaotic energy of this vision. It implies a new structural evolution.",
        tools_used=["tool_x"],
        resources_accessed=[]
    )
    
    # 1. Verify Resonance Analysis Fragment exists
    resonance_frag = next(f for f in state.event_cache if f["modality"] == "resonance_analysis")
    metrics = resonance_frag["metrics"]
    
    # 2. Verify Goodwyn's Criteria
    assert metrics["minimal_counter_intuitiveness"] > 0.0 # "defies logic", "magic"
    assert metrics["emotional_valence"] > 0.0 # "beautiful", "chaotic"
    assert metrics["sensual_vividness"] > 0.0 # "shimmering", "crystal"
    assert metrics["narrative_coherence"] > 0.0 # "implies"
    
    # 3. Verify Van Eenwyk's "Chaos as Adaptability"
    # High MCI + High Coherence should map to STRANGE attractor (Healthy Chaos)
    assert state.current_attractor_type == AttractorType.STRANGE
    assert state.basin_influence_strength > 0.5 # Strong influence of the strange attractor
