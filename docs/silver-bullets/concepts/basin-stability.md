# Basin Stability

**Category**: Core Concept
**Type**: Property
**Implementation**: `api/services/memory_basin_router.py:203-217`, `api/models/cognitive.py:35`, `api/models/mental_model.py:170`

---

## Definition

**Basin stability** is the resistance of an attractor basin to displacement—how much energy is required to push consciousness out of its current stable state. It determines how persistent a mental state remains under perturbation.

Think of it as **the depth and steepness of a valley**—a deep, steep-walled valley (high stability) keeps the ball from escaping, while a shallow, gentle depression (low stability) allows easy exit.

## Key Characteristics

- **Depth-Dependent**: Deeper basins (lower free energy minima) have higher stability
- **Dynamic**: Stability increases with repeated activation (Hebbian strengthening)
- **Measurable**: Quantified as resistance to perturbation (0.0-1.0 scale)
- **Multi-Scale**: Operates from milliseconds (fleeting thoughts) to years (core beliefs)
- **Energy Barrier**: Higher stability = higher activation energy required for basin transition
- **Self-Reinforcing**: Each activation strengthens the basin, increasing future stability

## How It Works

### The Ball-and-Valley Analogy

```
Low Stability (Shallow Basin):
     /\      Small push
    /  \       ↓
   / 🔵 \  → 🔵  → Basin exit (easy)
  /______\
  [Shallow]

Medium Stability:
    /\       Medium push
   /  \         ↓
  /    \    🔵 → ↑ (resisted)
 /  🔵  \___/
 [Moderate depth]

High Stability (Deep Basin):
   /\         Large push
  /  \           ↓
 /    \      🔵 → ↑↑ (strongly resisted)
/      \________/
        🔵
   [Deep, steep walls]
```

### Step-by-Step Process

1. **Basin Formation**
   - Thoughtseed wins competition → creates attractor basin
   - Initial stability set to default (0.5)
   - Basin depth determined by free energy minimum

2. **Activation Strengthening**
   - Each time basin activated → stability += 0.02
   - Hebbian learning: "Neurons that fire together wire together"
   - Ceiling at 1.0 (maximum stability)

3. **Perturbation Arrival**
   - New information challenges current basin
   - Creates prediction error (increases free energy locally)
   - Tests basin's resistance to displacement

4. **Stability Check**
   - Compare perturbation energy vs basin stability
   - High stability: Basin absorbs perturbation, returns to equilibrium
   - Low stability: Basin destabilizes, transition triggered

5. **Transition or Persistence**
   - If stability > perturbation: Basin persists (thought continues)
   - If stability < perturbation: Basin transition (new thought emerges)

6. **Decay Over Time**
   - Unused basins: Stability gradually decreases
   - Long-term disuse: Basin becomes easier to displace
   - Eventually: Basin fades from energy landscape

## Implementation

### Basin Creation and Strengthening

**Code**: `api/services/memory_basin_router.py:197-219`

```python
# Initial creation
ON CREATE SET
    b.stability = 0.5,
    b.strength = $strength,
    b.activation_count = 1

# Hebbian strengthening on each activation
ON MATCH SET
    b.stability = CASE
        WHEN b.stability < 1.0 THEN b.stability + 0.02
        ELSE b.stability
    END,
    b.strength = CASE
        WHEN b.strength < 2.0 THEN b.strength + 0.05
        ELSE b.strength
    END,
    b.activation_count = b.activation_count + 1
```

**Mechanism**:
- `stability`: 0.0-1.0, how resistant to displacement
- `strength`: Basin depth (inversely related to free energy)
- `activation_count`: Historical activation frequency

### Stability in Cognitive Models

**Code**: `api/models/cognitive.py:32-35`

```python
class MemoryCluster(BaseModel):
    cluster_id: str
    name: str
    boundary_energy: float = Field(default=0.5, ge=0.0, le=1.0)  # Energy barrier
    cohesion_ratio: float = Field(default=1.0, ge=0.0)
    stability: float = Field(default=0.5, ge=0.0, le=1.0)  # Resistance to exit
```

**Properties**:
- `boundary_energy`: Height of energy barrier surrounding basin
- `stability`: Depth/steepness of basin interior
- `cohesion_ratio`: Internal cohesion of basin structure

### Runtime Monitoring

**Code**: `api/services/metacognition_runtime_integration.py:37-58`

```python
class MetacognitionRuntimeMonitor:
    """
    Monitoring runtime that checks surprise, confidence, basin_stability
    at intervals specified by monitoring patterns.
    """

    async def assess(self, agent_id: str, metrics: Dict[str, float]):
        """
        Args:
            metrics: {
                "surprise": 0.0-1.0,
                "confidence": 0.0-1.0,
                "basin_stability": 0.0-1.0,  # Current basin resistance
                "free_energy": float
            }
        """
        # Low stability triggers basin transition monitoring
        if metrics["basin_stability"] < 0.3:
            # High risk of unintended basin exit
            # Consider control intervention
```

**Monitoring Pattern**: `scripts/store_metacognition_memory.py:264`

```python
"checks": [
    "surprise_score = calculate_prediction_error()",
    "confidence = reasoning_agent.get_confidence()",
    "basin_stability = attractor_depth > threshold"  # Depth-based check
]
```

### Tests

- **Integration**: `tests/integration/test_metacognition_semantic_storage.py:368` - "Attractor Basin stability → Persistent belief configuration"
- **Contract**: `tests/contract/test_neo4j_schema.py:21-24` - Schema validation for stability property
- **Runtime**: `tests/unit/test_metacognition_runtime_integration.py:39` - Metrics including `basin_stability`

## Related Concepts

**Prerequisites** (understand these first):
- [[attractor-basin]] - What has stability
- [[free-energy]] - Determines basin depth
- [[thoughtseed]] - Creates initial basin

**Builds Upon** (this uses):
- [[prediction-error]] - Destabilizes basins
- [[activation-energy]] - Required to overcome stability
- [[energy-barrier]] - Boundary surrounding basin

**Used By** (depends on this):
- [[basin-transition]] - Stability determines transition difficulty
- [[metacognitive-feelings]] - Low stability → confusion, high → confidence
- [[procedural-integration]] - Skill stabilization via practice

**Related** (similar or complementary):
- [[hebbian-learning]] - Mechanism for stability increase
- [[memory-persistence]] - Stability determines retention duration
- [[cognitive-resilience]] - High stability resists interference

## Examples

### Example 1: Hypervigilance Basin (Clinical)

**Context**: [LEGACY_AVATAR_HOLDER] in chronic threat-detection mode

```
Basin Properties:
- Name: "threat-detection-basin"
- Stability: 0.92 (very high)
- Strength: 2.8 (deep valley)
- Activation Count: 15,847 (years of practice)

Why High Stability:
1. Repeated activation over years → Hebbian strengthening
2. Prediction accuracy (threats DO exist sometimes) → reinforced
3. Survival value → evolutionarily weighted
4. Self-fulfilling: Defensive stance → others react defensively → confirms threat

Escape Difficulty:
- Small perturbations absorbed (evidence of safety ignored)
- Requires large activation energy (therapeutic intervention + new evidence)
- Or basin reorganization (psychedelic-assisted therapy)
```

**Therapeutic Challenge**: High stability = resistance to change
- Can't just tell patient "stop being hypervigilant"
- Must either:
  1. Destabilize current basin (reduce stability via prediction errors)
  2. Create competing basin with lower free energy (healthier attractor)
  3. Temporarily reduce precision on priors (psychedelic mechanism)

### Example 2: Flow State Basin (Positive)

**Context**: Deep work, coding in the zone

```python
# Initial entry
basin = create_basin(
    name="coding-flow-state",
    stability=0.3,  # Low initial stability (easy to interrupt)
    strength=1.2
)

# After 20 minutes uninterrupted
# Each 3-minute cycle strengthens basin
for cycle in range(7):
    basin.stability += 0.02  # Now 0.44
    basin.activation_count += 1

# Now:
basin.stability = 0.44  # Moderate stability
# Small interruptions absorbed (Slack notification → ignored)
# Medium interruptions disruptive (colleague question → breaks flow)
# Large interruptions exit basin (fire alarm → complete context switch)
```

**Characteristics**:
- Gradual stability build-up (0.3 → 0.44 over 20 min)
- Moderate stability resists small perturbations
- Still vulnerable to medium/large disruptions
- Requires protection during build-up phase

### Example 3: Code Understanding (Learning)

**Initial Basin**: "This codebase is confusing" (stability=0.2, shallow)

```
Minute 1: Reading authentication.py
- Prediction errors frequent (don't understand patterns)
- Free energy high (F=3.2)
- Basin very unstable (stability=0.2)
- Easily displaced by distractions

Minute 10: Patterns emerging
- Some predictions correct (recognizing patterns)
- Free energy decreasing (F=2.1)
- Basin stabilizing (stability=0.35)
- Small distractions absorbed

Minute 30: Deep understanding
- Predictions accurate (see the architecture)
- Free energy low (F=1.1)
- Basin stable (stability=0.65)
- Resistant to interruptions
```

**Transition**: "Confusing" basin → "Understanding" basin
- Driven by: Accumulated correct predictions
- Stability trajectory: 0.2 → 0.35 → 0.65
- Result: New basin MORE stable than old (easier to maintain understanding than confusion)

### Example 4: Skill Acquisition (Procedural)

**Code**: From procedural basin strengthening pattern

```
Skill: Using vim text editor
Basin: "vim-fluency-basin"

Day 1: stability=0.1 (very fragile)
- Every command requires conscious effort
- Tiny perturbation exits basin (forgot command → switch to GUI editor)

Week 1: stability=0.3 (building)
- Common commands automatic
- Still fragile (complex operation → confusion → Google search)

Month 3: stability=0.7 (stable)
- Muscle memory established
- Resilient to interruptions (conversation while editing)

Year 1: stability=0.95 (deeply entrenched)
- Using other editors feels unnatural
- High activation energy to switch tools
```

**Implication**: High stability can be maladaptive
- Vim expert has difficulty using standard editors
- Basin too stable = inflexibility
- Optimal: Moderate stability (fluent but adaptable)

## Basin Stability Spectrum

### Ultra-Low Stability (0.0-0.2)
- **Duration**: Milliseconds to seconds
- **Type**: Fleeting thoughts, distractions
- **Resistance**: None (any perturbation displaces)
- **Example**: Random thought while walking
- **Clinical**: ADHD attention, mania, racing thoughts

### Low Stability (0.2-0.4)
- **Duration**: Seconds to minutes
- **Type**: Exploratory thinking, learning new concepts
- **Resistance**: Minimal (small interruptions displace)
- **Example**: Browsing documentation, early learning
- **Clinical**: Normal exploration, mild anxiety

### Moderate Stability (0.4-0.7)
- **Duration**: Minutes to hours
- **Type**: Active work, conversation, reading
- **Resistance**: Moderate (absorbs small perturbations)
- **Example**: Focused work, engaging discussion
- **Clinical**: Healthy cognitive function

### High Stability (0.7-0.9)
- **Duration**: Hours to days
- **Type**: Deep convictions, flow states, obsessions
- **Resistance**: High (requires significant effort to exit)
- **Example**: Solving complex problem, creative flow
- **Clinical**: Adaptive (flow) or maladaptive (rumination)

### Ultra-High Stability (0.9-1.0)
- **Duration**: Days to years
- **Type**: Core beliefs, identity, trauma patterns
- **Resistance**: Extreme (major life events required to shift)
- **Example**: Religious beliefs, trauma responses
- **Clinical**: Personality structure, PTSD, deep-rooted patterns

## Factors Affecting Stability

### Increases Stability
1. **Repeated Activation**: Hebbian strengthening (+0.02 per activation)
2. **Prediction Accuracy**: Correct predictions deepen basin
3. **Emotional Salience**: Affect-tagged memories more stable
4. **Coherence**: Internally consistent basins resist disruption
5. **Rehearsal**: Active practice strengthens procedural basins
6. **Social Reinforcement**: Shared beliefs gain stability

### Decreases Stability
1. **Disuse**: Inactive basins decay (stability -= 0.01 per week)
2. **Prediction Errors**: Accumulated errors destabilize basin
3. **Competing Basins**: Stronger alternative available
4. **Reduced Precision**: Lower confidence in priors (psychedelic effect)
5. **Sleep Deprivation**: Global stability reduction
6. **Cognitive Load**: Executive depletion reduces maintenance

## Common Misconceptions

**Misconception 1**: "High stability is always good"
**Reality**: High stability resists both bad AND good changes. A maladaptive belief with high stability (trauma response, hypervigilance) is harder to change therapeutically. Optimal stability depends on context—you want high stability for skills, moderate for beliefs, low for exploration.

**Misconception 2**: "Stability is static—basins are either stable or not"
**Reality**: Stability is dynamic and continuously updated. Each activation slightly increases stability (+0.02), while disuse decreases it. A basin's stability right now differs from its stability tomorrow.

**Misconception 3**: "You can force a basin to be stable through willpower"
**Reality**: Stability emerges from repeated successful activation (Hebbian learning), not conscious intent. You can't will a basin to be stable—you must activate it repeatedly with confirming evidence.

**Misconception 4**: "Low stability means the thought is weak or unimportant"
**Reality**: Exploratory thinking REQUIRES low stability. Early learning, creativity, and hypothesis generation all operate in low-stability basins. The goal isn't always high stability—it's appropriate stability for the task.

**Misconception 5**: "Stability and strength are the same thing"
**Reality**:
- **Stability**: Resistance to displacement (how hard to exit)
- **Strength**: Basin depth (how low the energy minimum)
- A basin can be deep (strong) but have gentle slopes (low stability)
- Or shallow (weak) but steep-walled (high stability)

## When to Use This Concept

✅ **Use basin stability when**:
- Explaining why beliefs persist despite contradictory evidence
- Designing therapeutic interventions (must destabilize maladaptive basins)
- Understanding skill acquisition (stability builds with practice)
- Predicting cognitive resilience to interruptions
- Implementing memory persistence mechanisms
- Analyzing resistance to learning new approaches

❌ **Don't use when**:
- Explaining single-shot decisions (no basin formation)
- Rapid task-switching (shallow basins throughout)
- One-time events without repetition
- Explaining basin transitions themselves (use [[basin-transition]])
- Initial thoughtseed competition (pre-basin formation)

## Stability vs Related Properties

| Property | What It Measures | Range | Changes Via |
|----------|-----------------|-------|-------------|
| **Stability** | Resistance to exit | 0.0-1.0 | Activation frequency |
| **Strength** | Basin depth | 0.0-3.0 | Free energy minimum |
| **Boundary Energy** | Exit energy barrier | 0.0-1.0 | Basin geometry |
| **Activation Count** | Usage history | 0-∞ | Historical record |
| **Free Energy** | Current energy | 0.0-5.0 | Prediction accuracy |

## Clinical Applications

### PTSD Treatment
**Problem**: Trauma basin has ultra-high stability (0.95+)
- Persistent despite contradictory safety evidence
- High activation energy required to exit
- Prediction errors absorbed (safety cues dismissed)

**Intervention Strategy**:
1. **Gradual Destabilization**: Introduce small prediction errors
2. **Alternative Basin**: Build competing "safety" basin simultaneously
3. **Reduced Precision**: Temporarily lower prior confidence (EMDR, psychedelics)
4. **Hebbian Weakening**: Reduce activation frequency of trauma basin
5. **Threshold Crossing**: Accumulate enough errors to trigger transition

### Flow State Cultivation
**Goal**: Build moderate-high stability (0.6-0.8) for deep work

**Protocol**:
```
1. Initial Entry (0-5 min):
   - Eliminate interruptions (stability builds slowly)
   - Low stability = vulnerable to displacement

2. Build-Up (5-20 min):
   - Each 3-min cycle: stability += 0.02
   - Target: 0.5 stability (absorbs small perturbations)

3. Deep Flow (20+ min):
   - Stability 0.6-0.8 (resistant to moderate interruptions)
   - Can maintain through brief disruptions

4. Exit Strategy:
   - Planned exit easier than forced displacement
   - Gradual wind-down preserves basin for re-entry
```

### Meditation Practice
**Goal**: Develop meta-awareness of basin stability

**Training**:
1. **Notice Current Stability**: How persistent is this thought?
2. **Observe Build-Up**: Feel stability increasing with attention
3. **Practice Transitions**: Voluntary basin exits (attentional control)
4. **Cultivate Flexibility**: Avoid ultra-high stability (non-attachment)

**Result**: Ability to modulate stability voluntarily
- High when needed (concentration meditation)
- Low when needed (open awareness meditation)

## Physics Foundation

### Dynamical Systems Theory

**Stability = Second Derivative of Energy**

```
Free Energy Landscape:

     dF/dx = 0 (at basin minimum)

     Stability = |d²F/dx²|

High d²F/dx²  → Steep walls → High stability
Low d²F/dx²   → Gentle slopes → Low stability
```

### Lyapunov Stability

A basin is Lyapunov stable if:
- Small perturbations → system returns to equilibrium
- Stability = size of perturbation that can be absorbed

### Bistability

Two basins with different stabilities:
```
Basin A: stability=0.3 (shallow)
Basin B: stability=0.8 (deep)

System naturally settles in B
Requires high energy to reach A
A → B transition: Easy (downhill)
B → A transition: Hard (uphill)
```

## Further Reading

- **Research**:
  - Kelso (1995): "Dynamic Patterns" - Attractor dynamics
  - Friston (2010): "Free-Energy Principle" - Basin depth and prediction
  - Thelen & Smith (1994): "A Dynamic Systems Approach" - Development as basin transitions

- **Documentation**:
  - [[01-metacognition-two-layer-model]] - Theoretical foundation
  - [[attractor-basin]] - What stability applies to
  - [[basin-transition]] - How stability affects transitions
  - [[05-thoughtseed-competition-explained]] - Basin formation mechanics
  - [[02-agency-and-altered-states]] - Stability modulation via psychedelics

- **Implementation**:
  - `api/services/memory_basin_router.py` - Basin strengthening logic
  - `api/services/metacognition_runtime_integration.py` - Stability monitoring
  - `.specify/features/038-thoughtseeds-framework/spec.md` - Design spec

- **Clinical**:
  - van der Kolk (2014): "The Body Keeps the Score" - Trauma basin stability
  - Csikszentmihalyi (1990): "Flow" - Optimal stability for deep work

---

**Author**: Dr. Mani Saint-Victor, MD
**Last Updated**: 2026-01-02
**Status**: Production
**Created By**: Agent-6 (Documentation Specialist)
