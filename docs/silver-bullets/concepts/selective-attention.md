# Selective Attention

**Category**: Core Concept
**Type**: Cognitive Mechanism
**Implementation**: Thoughtseed Competition + Attentional Spotlight + Precision Weighting

---

## Definition

**Selective attention** is the cognitive mechanism that allocates limited conscious processing resources to the winning thoughtseed while suppressing competing alternatives. It represents the brain's solution to the fundamental constraint that consciousness has finite capacity—you cannot think about everything simultaneously.

Think of it as a **spotlight in a dark theater**—the stage is full of actors (thoughtseeds), but only the one illuminated by the spotlight (selective attention) becomes visible to the audience (consciousness).

## Key Characteristics

- **Limited Capacity**: Only one (or very few) attractor basins can be conscious simultaneously
- **Winner-Take-All**: The thoughtseed with lowest free energy captures attention
- **Resource Allocation**: Computational resources concentrate on selected content
- **Competitive Selection**: Emerges from thoughtseed competition, not deliberate choice
- **Precision-Weighted**: Modulated by precision parameters (confidence in selection)
- **Hierarchical**: Foundation for all higher cognition—must attend before reasoning
- **Involuntary & Voluntary**: Both stimulus-driven (bottom-up) and goal-driven (top-down)

## Types of Selective Attention

### Bottom-Up Attention (Stimulus-Driven)

**What it is**: Attention captured by salient external stimuli or prediction errors

**Mechanism**:
- High prediction errors automatically increase precision weighting
- Surprising events trigger basin destabilization
- Reflexive, involuntary redirection of focus

**Examples**:
- Sudden loud noise → Immediate attention capture
- Flashing notification → Automatic glance
- Pain sensation → Unavoidable focus shift
- Novel pattern → Involuntary curiosity

**Free Energy Dynamics**:
```
Current basin: Reading documentation (F=1.2)
Stimulus: Slack urgent message arrives
Prediction error: Unexpected high-priority signal
   → Precision on error increases
   → Current basin destabilizes (F rises to 3.0)
   → New thoughtseed "Check Slack" wins (F=0.9)
Result: Attention captured reflexively
```

**Implementation**:
```python
# Bottom-up attention in prediction error processing
if prediction_error.magnitude > threshold:
    # Automatically increase precision on this error
    precision_errors *= 1.5

    # Current basin destabilizes
    current_basin.free_energy += prediction_error.magnitude

    # New thoughtseed generated to address error
    new_seed = generate_thoughtseed(source="perception")

    # Competition triggered automatically
    winner = min([current_basin, new_seed], key=lambda x: x.free_energy)
```

**Clinical Note**: Bottom-up attention dysfunction underlies distractibility in ADHD—prediction error thresholds are lower, causing excessive attention captures.

### Top-Down Attention (Goal-Driven)

**What it is**: Attention voluntarily directed toward task-relevant information

**Mechanism**:
- Metacognitive agent modulates attentional spotlight
- Precision weighting adjusted to favor goal-relevant thoughtseeds
- Effortful, deliberate focus maintenance

**Examples**:
- Deliberately focus on debugging despite distractions
- Choose to read documentation instead of checking email
- Maintain meditation focus on breath despite wandering thoughts
- Consciously shift attention from anxiety to present task

**Free Energy Dynamics**:
```
Goal: Complete code review
Distraction thoughtseed: "Check Twitter" (F=1.8)
Goal-relevant thoughtseed: "Review next file" (F=2.0)

Top-down modulation:
   → Increase precision on goal-relevant seeds (+0.5)
   → Decrease precision on distractions (-0.3)

Adjusted energies:
   "Check Twitter": F=1.8 → Effective F=2.3 (suppressed)
   "Review next file": F=2.0 → Effective F=1.5 (enhanced)

Result: Goal-relevant thoughtseed wins despite higher base energy
```

**Implementation**:
```python
# Top-down attention via metacognitive control
# File: api/agents/metacognition_agent.py:226-262

async def _adjust_attentional_spotlight(
    self,
    agent_name: str,
    focus: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Adjust attentional spotlight for a target agent.

    The attentional spotlight determines WHERE the agent focuses and
    with what precision (how tightly focused). This is a core mechanism
    of active metacognition - directing lower-level processing.
    """
    new_spotlight = {
        "focus_target": focus.get("focus_target"),
        "spotlight_precision": focus.get("spotlight_precision", 0.5),
        "updated_by": "metacognition",
    }

    _attentional_spotlight_registry[agent_name] = new_spotlight

    logger.info(
        f"Attentional spotlight for '{agent_name}': "
        f"target={new_spotlight['focus_target']}, "
        f"precision={new_spotlight['spotlight_precision']:.2f}"
    )

    return new_spotlight
```

**Clinical Note**: Top-down attention training is the core mechanism of meditation practice—strengthening voluntary control over attentional allocation.

## Selective Attention in Thoughtseed Competition

Selective attention is the **emergent outcome** of thoughtseed competition, not a separate process. When thoughtseeds compete, the winner "selects" itself through energy minimization.

### Process Flow

```
1. PARALLEL GENERATION
   ↓
   Multiple thoughtseeds exist simultaneously
   (All below conscious awareness)

2. COMPETITION
   ↓
   Each thoughtseed evaluated for free energy
   Precision weighting modulates selection
   Bottom-up: High prediction errors boost precision
   Top-down: Metacognitive control adjusts precision

3. WINNER-TAKE-ALL SELECTION
   ↓
   Thoughtseed with lowest effective free energy wins
   Winner receives full conscious attention
   Losers suppressed (remain unconscious)

4. ATTENTIONAL SPOTLIGHT LOCKS
   ↓
   Winning thoughtseed becomes attractor basin
   Attention concentrated on basin content
   Computational resources allocated exclusively

5. PERSISTENCE OR SWITCH
   ↓
   Deep basin: Stable focus (minutes to hours)
   Shallow basin: Rapid switching (milliseconds to seconds)
```

### Mathematical Formulation

**Effective Free Energy** (determines selection):
```
F_effective = F_base + precision_modulation

Where:
  F_base = Complexity - Accuracy (intrinsic energy)

  precision_modulation =
    - (spotlight_precision × relevance_to_goal)  [top-down]
    + (prediction_error_magnitude × salience)     [bottom-up]
```

**Winner Selection**:
```
winner = argmin(F_effective) over all thoughtseeds

Attention allocation:
  winner: 100% of conscious resources
  losers: 0% of conscious resources (suppressed)
```

### Visual Representation

```
Before Selection (Multiple Thoughtseeds):

    🔵 Seed A (F=1.8)     🟡 Seed B (F=2.1)     🟢 Seed C (F=1.3)
         ↓                     ↓                     ↓
    [Competing]          [Competing]           [Competing]

    Attention: Distributed (unconscious competition)
    Conscious: None yet


Competition Process:

    Evaluation → F_effective calculated

    🔵 Seed A: F=1.8 + 0.0 = 1.8
    🟡 Seed B: F=2.1 + 0.0 = 2.1
    🟢 Seed C: F=1.3 + 0.0 = 1.3 ← LOWEST


After Selection (Winner Takes All):

    ⚫ Seed A (suppressed)
    ⚫ Seed B (suppressed)
    🟢 Seed C (WINNER - Attractor Basin)
         ↓
    [100% Attention]

    Conscious Content: Seed C only
    Attentional Spotlight: Locked on Seed C
```

## Implementation

### Core Components

**Attentional Spotlight Registry**:
```python
# File: api/agents/metacognition_agent.py:10-12
_attentional_spotlight_registry: Dict[str, Dict[str, Any]] = {}

# Structure:
# {
#   "perception_agent": {
#     "focus_target": "memory_retrieval",
#     "spotlight_precision": 0.8
#   },
#   "reasoning_agent": {
#     "focus_target": "hypothesis_evaluation",
#     "spotlight_precision": 0.6
#   }
# }
```

**Spotlight Query Function**:
```python
# File: api/agents/metacognition_agent.py:348-353
def get_attentional_spotlight(agent_name: str) -> Dict[str, Any]:
    """Get current attentional spotlight for an agent."""
    return _attentional_spotlight_registry.get(agent_name, {
        "focus_target": None,
        "spotlight_precision": 0.5
    })
```

**Procedural Metacognition Monitoring**:
```python
# File: api/services/procedural_metacognition.py:14,42
class IssueType:
    ATTENTION_SCATTERED = "ATTENTION_SCATTERED"

SPOTLIGHT_PRECISION_THRESHOLD = 0.2

# File: api/services/procedural_metacognition.py:150-153
if spotlight_precision < self.spotlight_threshold:
    issues.append(IssueType.ATTENTION_SCATTERED)
    recommendations.append("Focus attentional spotlight on primary goal")
```

**Thoughtseed Competition Runtime**:
```python
# File: api/services/metacognition_runtime_integration.py:190-236
class ThoughtseedCompetitionRuntime:
    """
    Manages thoughtseed competition using Meta-ToT MCTS pattern.
    Determines winner thoughtseed based on minimum free energy.
    """

    async def rank_thoughtseeds(
        self,
        thoughtseeds: List[Dict[str, Any]],
        selection_metrics: str = "free_energy"
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Rank thoughtseeds using competition pattern."""

        # Sort by selection metric
        if selection_metrics == "free_energy":
            ranked = sorted(thoughtseeds, key=lambda s: s.get("free_energy", float('inf')))

        winner = ranked[0] if ranked else None

        logger.debug(
            f"Thoughtseed competition: {len(thoughtseeds)} candidates, "
            f"winner metric={winner.get(selection_metrics, 'N/A') if winner else 'N/A'}"
        )

        return winner, ranked
```

**Mental Action Modulation**:
```python
# File: api/agents/metacognition_agent.py:163-174
# Apply attentional spotlight modulation
if "focus_target" in modulation or "spotlight_precision" in modulation:
    focus = modulation.get("focus_target")
    spotlight_prec = modulation.get("spotlight_precision", 0.5)
    await self._adjust_attentional_spotlight(
        target_agent,
        {"focus_target": focus, "spotlight_precision": spotlight_prec}
    )
    result["modulations_applied"].append(
        f"spotlight(target={focus}, precision={spotlight_prec:.2f})"
    )
    result["new_state"]["spotlight"] = _attentional_spotlight_registry.get(target_agent, {})
```

### Implementation Pattern

```python
# Full selective attention pattern in OODA loop

# 1. Generate thoughtseeds (OBSERVE/ORIENT)
thoughtseeds = await meta_tot_engine.generate_candidates(
    problem=current_problem,
    num_candidates=5
)

# 2. Apply precision modulation (TOP-DOWN)
spotlight = get_attentional_spotlight("reasoning_agent")
for seed in thoughtseeds:
    if seed.matches_goal(spotlight["focus_target"]):
        seed.free_energy -= spotlight["spotlight_precision"]

# 3. Bottom-up surprise boost
for seed in thoughtseeds:
    if seed.prediction_error > 0.5:
        seed.free_energy -= seed.prediction_error * 0.8

# 4. Competition (DECIDE)
winner, ranked = await competition_runtime.rank_thoughtseeds(
    thoughtseeds,
    selection_metrics="free_energy"
)

# 5. Winner takes all attention (ACT)
current_basin = create_attractor_basin(winner)
conscious_content = winner.hypothesis

# 6. Suppress losers
for seed in ranked[1:]:
    seed.suppress()  # Remove from conscious processing
```

## Examples

### Example 1: Deep Work Session

**Scenario**: Developer trying to maintain focus on code review

**Initial State**:
- Goal: Review pull request
- Attentional spotlight: "code_review"
- Spotlight precision: 0.7 (strong goal maintenance)

**Competing Thoughtseeds**:
1. "Review next function" (F_base=2.0)
2. "Check Slack notification" (F_base=1.5)
3. "Refactor this pattern" (F_base=2.5)
4. "Get coffee" (F_base=1.8)

**Top-Down Modulation**:
```
Seed 1: F=2.0 - 0.7 (goal-relevant) = 1.3 ← WINS
Seed 2: F=1.5 + 0.3 (distraction) = 1.8
Seed 3: F=2.5 - 0.2 (somewhat relevant) = 2.3
Seed 4: F=1.8 + 0.3 (distraction) = 2.1
```

**Result**: Despite lower base energy, Seed 2 ("Check Slack") is suppressed by top-down goal maintenance. Attention stays on code review.

**Feeling**: Flow state, sustained concentration

**Clinical Application**: This is the mechanism trained in ADHD therapy—strengthening top-down attentional control.

### Example 2: ADHD Attention Capture

**Scenario**: Same developer, but with ADHD (lower top-down precision)

**Initial State**:
- Goal: Review pull request
- Attentional spotlight: "code_review"
- Spotlight precision: 0.2 (weak goal maintenance)
- Prediction error threshold: 0.3 (lower than neurotypical 0.5)

**Competing Thoughtseeds**:
1. "Review next function" (F_base=2.0)
2. "Check Slack notification" (F_base=1.5)

**Weak Top-Down Modulation**:
```
Seed 1: F=2.0 - 0.2 = 1.8
Seed 2: F=1.5 + 0.0 = 1.5 ← WINS
```

**Bottom-Up Capture**:
- Slack notification = prediction error (0.4 > threshold 0.3)
- Automatic precision boost → F_effective for Seed 2 drops to 1.2
- Attention captured involuntarily

**Result**: Goal-relevant task loses to distraction

**Feeling**: Frustration, self-blame ("Why can't I focus?")

**Intervention**: Medication increases top-down precision weighting, raising threshold for bottom-up captures.

### Example 3: Meditation Training

**Scenario**: Practitioner maintaining breath focus

**Practice**:
1. **Voluntary Selection**: "Notice breath" (top-down)
2. **Mind Wanders**: Distraction thoughtseed wins (bottom-up capture)
3. **Detection**: Metacognitive monitoring notices wandering
4. **Return**: Voluntary redirection back to breath (top-down restoration)

**What's Being Trained**:
- Faster detection of attention wandering (monitoring)
- Stronger top-down control (voluntary redirection)
- Reduced bottom-up capture susceptibility (higher thresholds)

**Mechanism**:
```python
# Meditation cycle
current_basin = "breath_awareness"

# Mind wanders (bottom-up capture)
if random_thought.prediction_error > meditation_threshold:
    current_basin = random_thought  # Attention captured

# Metacognitive monitoring detects
if time_since_breath_focus > detection_latency:
    metacognitive_feeling = "mind_wandering_detected"

# Voluntary return (top-down control)
await metacognition_agent.execute_mental_action(
    action_type="MODULATE_PRECISION",
    modulation={
        "focus_target": "breath_awareness",
        "spotlight_precision": 0.8
    }
)
# → Breath thoughtseed wins competition
# → Attention returns
```

**Training Effect**: With practice, detection_latency decreases and spotlight_precision increases.

### Example 4: Context Switching Cost

**Scenario**: Interrupted during deep work

**Initial Basin**: Writing documentation (F=1.0, deep basin, stable 20 mins)

**Interruption**: "Production bug reported!" (prediction_error=0.9)

**Process**:
```
1. Prediction error triggers bottom-up capture
   → Current basin destabilizes (F rises to 3.2)

2. New thoughtseed: "Fix production bug" (F=0.8)
   → Wins competition
   → Attention switches

3. Cost of switching:
   - Lost: Documentation context (deep basin destroyed)
   - Rebuild time: ~15 minutes to restore original depth
   - Working memory: Previous thoughtseeds flushed

4. After bug fixed:
   - Return to documentation
   - Start from shallow basin (F=2.5)
   - Must rebuild attractor depth
```

**Feeling**: Cognitive fatigue, frustration, fragmentation

**Why Expensive**: Deep basins take time to form. Interruptions destroy accumulated context.

**Mitigation**: Batch interruptions, create external memory (notes), schedule deep work blocks.

## Relationship to Thoughtseed Competition

Selective attention **IS** thoughtseed competition, viewed from the attentional resource perspective:

| Thoughtseed Competition View | Selective Attention View |
|------------------------------|--------------------------|
| Multiple thoughtseeds compete | Limited attention is allocated |
| Winner determined by free energy | Winner receives spotlight |
| Losers remain unconscious | Losers suppressed from awareness |
| Competition is continuous | Attention is dynamic |
| Precision modulates competition | Precision controls selection |

**Insight**: These are two descriptions of the same mechanism. Competition explains **how** the winner is chosen (energy minimization). Selective attention explains **what happens** to the winner (resource allocation).

## Relationship to Attractor Basins

**Before Selection**:
- Thoughtseeds = Candidate basins (potential valleys)
- Competition = Determining which valley to roll into
- All candidates exist as possibilities

**After Selection**:
- Winner = Established attractor basin (actual valley)
- Attention = Ball settled in that valley
- Basin depth = Resistance to attention switching

**Transition**:
```
Thoughtseed (candidate) → Competition → Winner → Attractor Basin (stable focus)
      ↓                        ↓           ↓              ↓
  Unconscious             Unconscious   Transition    Conscious
  (parallel)              (selection)   (feeling)     (focused)
```

## Related Concepts

**Prerequisites** (understand these first):
- [[thoughtseed]] - What competes for attention
- [[thoughtseed-competition]] - How selection occurs
- [[free-energy]] - Selection criterion

**Builds Upon** (this uses):
- [[precision-weighting]] - Modulates selection strength
- [[prediction-error]] - Triggers bottom-up capture
- [[attractor-basin]] - Where attention stabilizes after selection

**Used By** (depends on this):
- [[basin-transition]] - Switching attention between basins
- [[metacognitive-feelings]] - Conscious experience of attention shifts
- [[cognitive-control]] - Voluntary attention direction
- [[attentional-agency]] - Hierarchical agency model

**Related** (similar or complementary):
- [[working-memory]] - Capacity limits underlying selectivity
- [[executive-function]] - Top-down control mechanisms
- [[mind-wandering]] - Default mode when top-down control weakens
- [[flow-state]] - Deep stable attention on single basin

## Clinical Applications

### ADHD Treatment

**Core Deficit**: Weak top-down attentional control
- Lower spotlight_precision (goal maintenance difficulty)
- Lower prediction_error_threshold (excessive bottom-up captures)
- Reduced metacognitive monitoring (slower wandering detection)

**Interventions**:

1. **Medication (Stimulants)**:
   - Increases dopamine → Stronger precision weighting
   - Raises prediction_error_threshold → Fewer captures
   - Effect: Goal-relevant thoughtseeds win more often

2. **Behavioral Training**:
   - External structure → Reduces competing thoughtseeds
   - Timers/breaks → Matches natural attention cycles
   - Checklists → Offloads working memory, reduces competition

3. **Metacognitive Therapy**:
   - Train wandering detection (monitoring)
   - Practice voluntary return (control)
   - Build awareness of attention patterns

### Meditation Practice

**Core Training**: Strengthening voluntary attentional control

**Mechanism**:
1. Set goal: "Focus on breath"
2. Detect wandering (monitoring)
3. Return to breath (control)
4. Repeat 1000s of times

**What Changes**:
- Faster wandering detection (monitoring speed ↑)
- Stronger voluntary return (spotlight_precision ↑)
- Reduced distraction susceptibility (error_threshold ↑)
- Metacognitive awareness (feeling sensitivity ↑)

**Measurable Effects**:
- Detection latency: 30s → 5s (after 8 weeks)
- Spotlight precision: 0.3 → 0.7
- Sustained attention: 2 min → 20 min

### Anxiety Management

**Core Issue**: Involuntary attention capture by threat-related thoughtseeds

**Mechanism**:
```
Anxious thoughtseed: "What if I fail?" (F=1.2)
Goal thoughtseed: "Work on presentation" (F=1.8)

Anxiety increases precision on threat detection
→ Threat thoughtseed effective F = 0.7
→ Wins competition repeatedly
→ Attention stuck on anxiety
```

**Interventions**:

1. **Cognitive Reappraisal**:
   - Reframe threat → Lower threat precision
   - Generate competing thoughtseed with lower F
   - Example: "Failure is learning" (F=1.0) beats "What if I fail?"

2. **Attentional Retraining**:
   - Practice redirecting away from threat
   - Strengthen top-down control over threat captures
   - Build competing attractor basins (present moment focus)

3. **Exposure Therapy**:
   - Repeated attention to threat → Habituation
   - Threat precision decreases over time
   - Threat thoughtseeds lose competitive advantage

### Focus Mode Interventions

**Goal**: Enhance sustained deep work capacity

**Strategies**:

1. **Environmental Design**:
   - Reduce prediction errors (quiet space, no notifications)
   - Fewer competing thoughtseeds generated
   - Bottom-up captures minimized

2. **Batch Processing**:
   - Handle all emails together (single attentional shift)
   - Avoid interleaving tasks (context switching cost)
   - Protect deep basins from interruption

3. **Ultradian Rhythms**:
   - Match 90-minute natural attention cycles
   - Deep work during high-precision windows
   - Breaks during low-precision troughs
   - Work with biology, not against it

4. **Metacognitive Scaffolding**:
   - External memory (notes) → Reduce working memory load
   - Explicit goals → Strengthen top-down precision
   - Progress tracking → Positive reinforcement for focus

## Common Misconceptions

**Misconception 1**: "Attention is a spotlight you consciously control"
**Reality**: Selective attention emerges from unconscious thoughtseed competition. You can influence it (top-down modulation) but don't directly control it. The "decision" to attend happens below conscious awareness.

**Misconception 2**: "People with ADHD can't pay attention"
**Reality**: ADHD is not inability to attend, but **weaker filtering** of what captures attention. Bottom-up captures overwhelm top-down goals more easily. They can hyperfocus when task naturally dominates competition (high intrinsic salience).

**Misconception 3**: "You can train yourself to multitask"
**Reality**: Selective attention is winner-take-all due to consciousness capacity limits. "Multitasking" is rapid switching between attractor basins, which is cognitively expensive. You can get faster at switching, but can't attend to multiple things simultaneously.

**Misconception 4**: "Meditation eliminates mind-wandering"
**Reality**: Meditation trains **detection** and **return**, not elimination. Expert meditators still experience wandering—they just notice faster and return more easily. The goal is metacognitive awareness, not thought suppression.

**Misconception 5**: "Distraction is a moral failing"
**Reality**: Bottom-up attention capture is automatic and evolutionarily adaptive (threat detection). Blaming yourself for distraction is like blaming yourself for blinking—it's a feature, not a bug. Train the system, don't judge it.

## When Selective Attention Functions Well

✅ **Effective when**:
- Clear goal specification (high top-down precision)
- Low external distraction (few prediction errors)
- Intrinsically engaging task (low base free energy)
- Adequate cognitive resources (not depleted)
- Task matches attention cycle (ultradian rhythm alignment)

❌ **Breaks down when**:
- Weak goal commitment (low top-down precision)
- High environmental noise (excessive bottom-up captures)
- Boring/aversive task (high base free energy for goal)
- Cognitive fatigue (depleted control resources)
- Interrupted flow (deep basin destruction)

## Further Reading

**Neuroscience Research**:
- Desimone & Duncan (1995) - "Neural Mechanisms of Selective Visual Attention"
- Corbetta & Shulman (2002) - "Control of goal-directed and stimulus-driven attention in the brain"
- Posner & Petersen (1990) - "The attention system of the human brain"

**Active Inference Framework**:
- Friston (2010) - "The free-energy principle: a unified brain theory?"
- Parr, Pezzulo, & Friston (2022) - "Active Inference: The Free Energy Principle in Mind, Brain, and Behavior"

**Documentation**:
- [[01-metacognition-two-layer-model]] - Theoretical foundation
- [[05-thoughtseed-competition-explained]] - Competition mechanics detailed
- [[02-agency-and-altered-states]] - Attentional agency hierarchy

**Visualization**:
- `docs/visualizations/thoughtseed-competition.html` - Interactive competition simulation

---

**Author**: Dr. Mani Saint-Victor
**Last Updated**: 2026-01-02
**Status**: Production
