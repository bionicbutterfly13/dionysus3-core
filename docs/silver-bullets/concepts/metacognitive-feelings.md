# Metacognitive Feelings

**Category**: Core Concept  
**Type**: Phenomenological Signal  
**Implementation**: Free Energy Transitions + Basin Dynamics

---

## Definition

**Metacognitive feelings** are phenomenological signals that bridge unconscious cognitive processing to conscious awareness and control. They are the **felt experience** of cognitive state changes.

Not thoughts ABOUT feelings, but feelings ABOUT thinking itself.

## Key Characteristics

- **Non-Propositional**: Felt directly, not verbalized first
- **Transitional**: Arise during cognitive state changes
- **Informative**: Carry information about cognitive processes
- **Regulatory**: Guide control decisions
- **Universal**: Present across species (not language-dependent)
- **Rapid**: Arise in milliseconds
- **Phenomenological**: Subjective, qualitative experience

## Types of Metacognitive Feelings

### 1. Aha! Moment (Epistemic Gain)
**What it signals**: Sudden large reduction in free energy

**Trigger**:
- ΔF < -2.0 (large sudden drop)
- Multiple competing thoughtseeds → one clear winner
- Complex problem → simple elegant solution

**Phenomenology**:
- "It clicks into place!"
- Sense of illumination
- Feeling of rightness/certainty
- Relief and satisfaction

**Function**:
- Reinforces successful insight
- Signals to continue current path
- Consolidates new understanding

**Example**: "Wait... thoughtseeds ARE metacognitive feelings! Everything makes sense now!"

### 2. Confusion (High Uncertainty)
**What it signals**: Free energy stays high, no clear winner

**Trigger**:
- F > 3.0 (persists above threshold)
- Multiple thoughtseeds with similar energy
- Prediction errors remain unresolved

**Phenomenology**:
- "I don't get this"
- Cognitive fog
- Sense of being lost
- Frustration or discomfort

**Function**:
- Signals need for strategy change
- Prompts information seeking
- Slows processing for careful analysis

**Example**: "I've read this three times and still don't understand how this works"

### 3. Tip-of-Tongue (Retrieval Imminent)
**What it signals**: High confidence but blocked access

**Trigger**:
- Confidence level high
- Memory retrieval partially activated
- Final access blocked

**Phenomenology**:
- "It's right there, I can almost remember it"
- Feeling of nearness
- Frustration mixed with anticipation

**Function**:
- Maintains search effort
- Prevents premature abandonment
- Guides continued retrieval attempts

**Example**: "I know his name starts with 'D'... it's... ugh, it's on the tip of my tongue!"

### 4. Effort (Active Control)
**What it signals**: High cognitive load, resource depletion

**Trigger**:
- Large free energy gradient
- Sustained control intervention
- Resource allocation strain

**Phenomenology**:
- Mental strain
- "This is hard"
- Desire to rest or switch tasks

**Function**:
- Monitors resource expenditure
- Prevents cognitive burnout
- Signals when to take breaks

**Example**: Concentrating intensely on difficult math problem for extended period

### 5. Flow (Optimal State)
**What it signals**: Stable low free energy basin

**Trigger**:
- F < 1.5 (stable minimum)
- Deep attractor basin
- Smooth action-outcome coupling

**Phenomenology**:
- Effortless execution
- "Everything just works"
- Loss of self-consciousness
- Time distortion

**Function**:
- Signals optimal performance
- Maintains current strategy
- Reduces monitoring overhead

**Example**: Expert coder writing familiar patterns, thoughts flowing naturally to screen

### 6. Surprise (Prediction Error)
**What it signals**: Unexpected mismatch between prediction and reality

**Trigger**:
- High surprise score (KL divergence)
- Basin destabilization
- Sudden prediction error

**Phenomenology**:
- "Wait, what?"
- Jarring discontinuity
- Alert orienting response

**Function**:
- Triggers basin reorganization
- Prompts model updating
- Increases attention allocation

**Example**: Code that should work throws unexpected error

### 7. Uncertainty (Oscillating Energy)
**What it signals**: Multiple basins with similar depth

**Trigger**:
- Free energy oscillates
- No clear winner emerges
- Context ambiguity

**Phenomenology**:
- Torn between options
- "I'm not sure which is right"
- Vacillation

**Function**:
- Prompts information seeking
- Delays commitment
- Maintains option value

**Example**: Choosing between two equally valid architectural approaches

## Computational Mechanism

### Free Energy Changes → Feelings

```python
# Metacognitive feeling generator
def generate_feeling(
    current_energy: float,
    previous_energy: float,
    basin_stability: float
) -> MetacognitiveFeeling:
    
    delta_F = previous_energy - current_energy
    
    # Large sudden drop → Aha!
    if delta_F < -2.0:
        return MetacognitiveFeeling(
            type="aha",
            intensity=abs(delta_F) / 2.0,
            valence=1.0,  # Positive
            arousal=0.8   # High
        )
    
    # Energy stays high → Confusion
    elif current_energy > 3.0:
        return MetacognitiveFeeling(
            type="confusion",
            intensity=current_energy / 3.0,
            valence=-0.3,  # Slightly negative
            arousal=0.6
        )
    
    # Stable low → Flow
    elif current_energy < 1.5 and basin_stability > 0.85:
        return MetacognitiveFeeling(
            type="flow",
            intensity=0.7,
            valence=0.8,  # Positive
            arousal=0.4   # Calm
        )
    
    # Oscillating → Uncertainty
    elif abs(delta_F) < 0.2 and current_energy > 2.0:
        return MetacognitiveFeeling(
            type="uncertainty",
            intensity=0.5,
            valence=0.0,  # Neutral
            arousal=0.5
        )
```

### Feelings Catalog

| Feeling | ΔF Pattern | F Range | Basin Stability | Valence | Function |
|---------|-----------|---------|----------------|---------|----------|
| **Aha!** | -2.5 | Any → <1.5 | Any → High | +1.0 | Reinforce insight |
| **Confusion** | ±0.1 | >3.0 | Low | -0.3 | Seek clarity |
| **Flow** | -0.1 | <1.5 | >0.85 | +0.8 | Maintain |
| **Effort** | -1.0 gradual | 2.0-3.0 | Medium | -0.2 | Monitor resources |
| **Surprise** | +1.5 | Any ↑ | Drops | 0.0 | Update model |
| **Uncertainty** | ±0.2 | >2.0 | Low | 0.0 | Gather info |

## Dionysus Implementation

```python
# In HeartbeatAgent OODA loop
class MetacognitionAgent:
    
    async def decide(self, observations: Dict) -> Action:
        # Calculate current free energy
        current_F = self.calculate_free_energy(observations)
        
        # Compare to previous state
        delta_F = self.previous_F - current_F
        basin_stability = self.assess_basin_stability()
        
        # Generate metacognitive feeling
        feeling = self.feeling_generator.generate(
            current_F, self.previous_F, basin_stability
        )
        
        # Log feeling for analysis
        logger.info(f"Metacognitive feeling: {feeling.type} "
                   f"(intensity={feeling.intensity:.2f})")
        
        # Use feeling to guide action selection
        if feeling.type == "aha":
            # Continue current strategy
            action = self.reinforce_current_path()
        elif feeling.type == "confusion":
            # Change strategy, seek information
            action = self.trigger_replanning()
        elif feeling.type == "flow":
            # Maintain current approach
            action = self.continue_smoothly()
        elif feeling.type == "effort":
            # Check resource budget, consider break
            action = self.evaluate_resource_depletion()
        
        # Update state for next cycle
        self.previous_F = current_F
        
        return action
```

## The Bridge Function

Metacognitive feelings serve as the **bridge** between:

```
UNCONSCIOUS PROCESSING
    ↓
    (Thoughtseed competition happens below awareness)
    ↓
METACOGNITIVE FEELING
    ↓
    (Subjective phenomenological signal)
    ↓
CONSCIOUS AWARENESS
    ↓
    (You notice the feeling)
    ↓
REGULATORY CONTROL
    ↓
    (You adjust behavior based on feeling)
```

**Without metacognitive feelings**:
- Unconscious processes would remain invisible
- No subjective guidance for control
- Harder to regulate cognition voluntarily

**With metacognitive feelings**:
- Unconscious → conscious communication
- Affective guidance for decisions
- Subjective experience of thinking

## Clinical Significance

### Therapy Integration
**Declarative knowledge** (WARM tier):
- "I know anxiety feels like tightness in chest"
- Semantic understanding of feeling

**Procedural competence** (HOT tier):
- *Actually noticing* the feeling arise
- *Automatically regulating* in response

Effective therapy builds procedural capacity to:
1. **Notice** metacognitive feelings quickly
2. **Interpret** them accurately
3. **Respond** adaptively

### Psychedelic Amplification
Psychedelics **amplify** metacognitive feelings:
- **↑ Monitoring precision** → Stronger feelings
- **↓ Control precision** → Less suppression
- **Result**: Profound Aha! moments, emotional breakthroughs

Mechanism:
```python
# Psychedelic-like state
precision_weights["prediction_errors"] *= 1.5  # Amplify
precision_weights["prior_beliefs"] *= 0.5      # Relax

# Result: Feelings become more intense and salient
feeling_intensity *= 2.0
```

### Meditation Training
Meditation enhances metacognitive feeling awareness:
- **Monitoring**: Notice feelings as they arise
- **Non-Reactivity**: Observe without judgment
- **Differentiation**: Distinguish feeling types
- **Response**: Choose how to engage

## Related Concepts

- **[Thoughtseed](./thoughtseed.md)** - What competes to generate feelings
- **[Thoughtseed Competition](./thoughtseed-competition.md)** - Competition mechanism
- **[Free Energy](./free-energy.md)** - Quantitative signal
- **[Attractor Basin](./attractor-basin.md)** - Stability determines feeling
- **[Aha Moment](./aha-moment.md)** - Specific feeling type
- **[Procedural Metacognition](./procedural-metacognition.md)** - System that uses feelings

## Bidirectional Links

### This concept is referenced in:
- [01-metacognition-two-layer-model.md](../01-metacognition-two-layer-model.md)
- [05-thoughtseed-competition-explained.md](../05-thoughtseed-competition-explained.md)
- [02-agency-and-altered-states.md](../02-agency-and-altered-states.md)

### This concept references:
- [Thoughtseed](./thoughtseed.md)
- [Free Energy](./free-energy.md)
- [Attractor Basin](./attractor-basin.md)

---

**Author**: Dr. Mani Saint-Victor  
**Last Updated**: 2026-01-01  
**Integration Event**: Metacognition Framework → Dionysus Architecture
