# Procedural Metacognition

**Category**: Core Concept  
**Type**: Regulation System  
**Implementation**: OODA Loop + Active Inference (HOT tier)

---

## Definition

Procedural metacognition is the **dynamic, experiential layer** that regulates cognition in real-time. It's the "operating system task manager" that monitors and controls cognitive processes automatically.

## Key Characteristics

- **Dynamic System**: Continuously adapts during execution
- **Monitoring Function**: Bottom-up introspective awareness of current cognitive state
- **Control Function**: Volitional effort to adjust cognition based on monitoring feedback
- **Non-Conceptual**: Does NOT require language or conscious verbal concepts
- **Affective Signaling**: Communicates through felt metacognitive experiences
- **Pre-Verbal**: Present in non-human primates and pre-verbal infants

## Two Components

### 1. Monitoring (Assessment)
**What it does**: Bottom-up diagnostic awareness of current state

**Examples**:
- "I forgot that name" (memory monitoring)
- "I lost focus while reading" (attention monitoring)
- "I don't understand this explanation" (comprehension monitoring)
- "This feels wrong" (error detection)

**Pattern Recognition**:
- Detecting when attention drifts
- Noticing when understanding breaks down
- Sensing cognitive overload
- Feeling confusion or uncertainty

### 2. Control (Action)  
**What it does**: Top-down executive intervention to adjust cognition

**Examples**:
- Refocusing attention when mind wanders
- Changing strategies when current approach fails
- Skipping difficult questions to come back later
- "Focus back on breath" (meditation)
- "Try a different approach" (problem-solving)

**Metacognitive Regulation**:
- Adjusting effort allocation
- Switching cognitive strategies
- Reorienting attention
- Modifying precision weights

## Dionysus Implementation

```python
# Implemented in OODA loop with active inference
# HOT tier (fast, real-time access)

class HeartbeatAgent:
    """Procedural metacognition engine"""
    
    def __init__(self):
        self.planning_interval = 3  # Replan every 3 steps
        self.perception_agent = PerceptionAgent()  # OBSERVE (monitoring)
        self.reasoning_agent = ReasoningAgent()    # ORIENT (analysis)
        self.metacog_agent = MetacognitionAgent()  # DECIDE/ACT (control)
    
    async def step(self):
        # MONITORING: Assess current state
        observations = await self.perception_agent.observe()
        
        # MONITORING: Detect prediction errors
        surprise = self.calculate_surprise(observations)
        
        # CONTROL: If surprise high, trigger replanning
        if surprise > self.threshold or self.steps % self.planning_interval == 0:
            # Generate new plan (control intervention)
            plan = await self.metacog_agent.replan()
        
        # CONTROL: Execute next action
        await self.execute_action(plan.next_action)
```

### Storage Location
- **System**: HOT tier memory cache
- **Tier**: HOT (procedural, fast access)
- **Access Pattern**: Direct retrieval during execution
- **Update Frequency**: Continuous real-time updates

### Characteristics in Dionysus
- **Monitoring**: Perception + Reasoning agents (OBSERVE/ORIENT phases)
- **Control**: Metacognition agent (DECIDE/ACT phases)  
- **Signals**: Surprise scores, free energy, basin stability
- **No semantic translation**: Direct action from felt signals

## Contrast with Declarative Metacognition

| Aspect | Procedural | Declarative |
|--------|------------|-------------|
| **Nature** | Dynamic regulation | Static knowledge |
| **Function** | Operational (doing) | Informational (knowing) |
| **Access** | HOT tier (fast) | WARM tier (slow) |
| **Language** | Non-verbal, felt sense | Requires verbal concepts |
| **Example** | *Actually focusing* | "I know I should focus" |
| **System** | OODA loop + active inference | Graphiti semantic graph |
| **Speed** | Milliseconds | Seconds to minutes |

## Computer Analogy

**Procedural Metacognition = Operating System Task Manager**
- Real-time background monitoring (CPU temperature, memory usage)
- Automatic regulation (reallocate memory, close freezing apps)
- **Monitoring**: Diagnostic checks without user input
- **Control**: Automatic fixes when problems detected
- Often invisible: Runs without conscious commands
- Performance-oriented: Keeps system running smoothly

## OODA Loop Mapping

```
OBSERVE (Monitoring)
    ↓
    Perception agent senses environment
    Detects current cognitive state
    ↓
ORIENT (Monitoring + Analysis)
    ↓
    Reasoning agent evaluates prediction errors
    Calculates surprise and free energy
    Generates hypotheses
    ↓
DECIDE (Control)
    ↓
    Metacognition agent selects action
    Adjusts precision weights
    Allocates attention
    ↓
ACT (Control)
    ↓
    Execute selected action
    Apply cognitive intervention
    ↓
[CYCLE REPEATS]
```

## Metacognitive Feelings as Bridge

Procedural metacognition communicates its state through **metacognitive feelings**:

| Feeling | Monitoring Signal | Control Response |
|---------|------------------|------------------|
| **Confusion** | High surprise detected | Slow down, seek clarity |
| **Aha!** | Large free energy drop | Continue current path |
| **Effort** | High cognitive load | Allocate more resources |
| **Flow** | Stable low energy | Maintain current strategy |
| **Uncertainty** | Oscillating energy | Explore alternatives |

These feelings are NOT decorative - they **guide the control process**.

## Clinical Significance

### The Therapy Gap (Revisited)
Patients may have declarative knowledge but lack procedural competence:
- **Declarative**: "I understand deep breathing helps anxiety" 
- **Procedural**: *Actually executing breath regulation when triggered*

### Solution: Repetition Builds Procedural Skill
- **Practice**: Repeated execution strengthens HOT tier patterns
- **Embodiment**: Move from concept to automatic response
- **Non-Verbal**: Build felt sense, not just verbal understanding
- **Real-Time**: Train the system to regulate in the moment

### Meditation as Procedural Training
Meditation doesn't add new declarative knowledge - it trains procedural metacognition:
- **Monitoring**: Notice when attention drifts
- **Control**: Gently return focus to breath
- **Non-Conceptual**: Felt awareness without verbal labels
- **Repetition**: Builds automatic regulation capacity

## Altered States

### Psychedelic Precision Reweighting
Psychedelics modulate procedural metacognition:
- **↑ Monitoring precision** (amplify prediction errors)
- **↓ Control precision** (relax top-down priors)
- **Result**: Basin reorganization, novel connections
- **Window**: Increased plasticity for therapeutic content

```python
# Psychedelic-like state simulation
precision_weights["priors"] *= 0.5      # Reduce control
precision_weights["errors"] *= 1.5      # Amplify monitoring
```

## Related Concepts

- **[Declarative Metacognition](./declarative-metacognition.md)** - Static knowledge layer
- **[Metacognitive Feelings](./metacognitive-feelings.md)** - Felt signals
- **[OODA Loop](./ooda-loop.md)** - Implementation mechanism
- **[Active Inference](./active-inference.md)** - Computational framework
- **[HOT Tier](./hot-tier.md)** - Fast procedural storage

## Bidirectional Links

### This concept is referenced in:
- [01-metacognition-two-layer-model.md](../01-metacognition-two-layer-model.md)
- [02-agency-and-altered-states.md](../02-agency-and-altered-states.md)
- [04-smolagents-metatot-skills-integration.md](../04-smolagents-metatot-skills-integration.md)

### This concept references:
- [Declarative Metacognition](./declarative-metacognition.md)
- [Metacognitive Feelings](./metacognitive-feelings.md)
- [OODA Loop](./ooda-loop.md)

---

**Author**: Dr. Mani Saint-Victor  
**Last Updated**: 2026-01-01  
**Integration Event**: Metacognition Framework → Dionysus Architecture
