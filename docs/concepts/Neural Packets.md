# Neural Packets

**Category:** Biological Cognition Pattern
**Related:** [[Multi-Tier Memory Architecture]], [[Attractor Basin Dynamics]], [[Fractal Metacognition]]
**Status:** Core Design Pattern (spec 030)

## The Brain Doesn't Stream. It Bursts.

Your neurons don't fire continuously. They synchronize into **discrete packets** - coordinated bursts of activity that carry meaning as a unit.

This isn't a bug. It's the *fundamental information architecture* of biological intelligence.

And most AI systems completely ignore it.

## How Neural Packets Work

### In Biology

**Gamma oscillations** (30-100 Hz) bind distributed neural activity into coherent "packets":

1. Neurons across different brain regions fire in sync
2. The synchronized burst carries information *as a pattern*, not as individual spikes
3. The packet travels through circuits, maintaining coherence
4. Downstream systems receive discrete, bounded information chunks

**Why this matters:** Your brain processes ~40 packets/second. Not 40 individual neuron spikes. 40 *synchronized ensembles*.

That's why you can hold 7±2 items in working memory. Not 7 neurons. 7 packets.

### In Dionysus

**Spec:** `specs/030-neuronal-packet-mental-models/`

We implement neural packets as **thoughtseeds** (spec 038):

```python
class Thoughtseed:
    """
    Discrete information packet with:
    - Bounded scope (what it represents)
    - Activation dynamics (when it fires)
    - Decay curve (how it fades)
    - Resonance patterns (what it connects to)
    """
```

Unlike traditional embeddings (static vectors), thoughtseeds:
- **Evolve** based on context
- **Decay** without reinforcement
- **Synchronize** with related packets
- **Compete** for working memory slots

See: [[Multi-Tier Memory Architecture]] for how packets move between memory tiers.

## The Infrastructure Parallel

From [[2025-12-31-infrastructure-liberation]]:

**After:** Discrete containers (Dionysus API + SilverBullet, 91MB, started on-demand)

Same principle as neural packets:
- **Bounded:** Each container has clear scope
- **Synchronized:** API and journal work together, nothing else
- **Efficient:** Zero waste between active bursts

This is [[Fractal Metacognition]] - the pattern that works for neurons works for Docker containers works for cognitive processes.

## Active Inference + Neural Packets

**Active inference** says: minimize surprise by predicting the next sensory input.

**Neural packets** say: predictions arrive in discrete, synchronized bursts.

Combined: Your brain predicts the next *packet*, not the next neuron spike.

That's why **rhythms** matter in cognition:
- Alpha waves (8-13 Hz): Idle state, awaiting next packet
- Theta waves (4-8 Hz): Memory retrieval, replaying packet sequences
- Gamma bursts (30-100 Hz): Attention, binding current packet

Dionysus implements this through the **Heartbeat Agent** (OODA loop with `planning_interval=3`):

```python
class HeartbeatAgent:
    """
    Periodic replanning creates rhythm.
    Not continuous reasoning - discrete decision packets.
    """
```

Every 3 cycles: generate new decision packet. Between cycles: execute current packet.

## Why Traditional AI Misses This

Most systems process:
1. **Continuous streams** (token-by-token generation)
2. **Isolated vectors** (embeddings with no temporal dynamics)
3. **Infinite context** (attention over entire history)

None of these match biology.

Your brain uses:
1. **Discrete packets** (gamma bursts, not token streams)
2. **Dynamic patterns** (neural assemblies, not static vectors)
3. **Bounded working memory** (7±2 packets, not infinite attention)

Neural packets aren't just "more biologically plausible." They're **computationally efficient**.

Processing 40 packets/second with 7 active in working memory = ~280 computational units to track.

Processing continuous token streams with full attention = millions of operations per forward pass.

## SEO Knowledge Gap: "Neural Packet Information Processing"

Searches:
- "Neural packet" → Computer networking (TCP/IP packets)
- "Gamma oscillations AI" → Neuroscience papers, no implementations
- "Discrete information bursts cognition" → Zero results

**The gap:** Nobody's bridging gamma oscillation research to production AI architectures.

This is the white space. This knowledge web fills it.

## Application to [LEGACY_AVATAR_HOLDER]s

The [[Replay Loop]] uses neural packet dynamics:

**Problem:** You're overwhelmed by continuous emotional processing.

**Pattern:** Your brain isn't *meant* to process emotions continuously. It processes in packets:
- Gamma burst: "I feel threatened"
- Packet complete
- Alpha idle: Process, integrate
- Next gamma burst: "What triggered that?"

**Agitation:** Continuous emotional vigilance (hypervigilance) fights neural packet rhythm. You're trying to stream when biology wants to burst.

**Solution:** The Replay Loop teaches packet-based emotional processing:
1. Notice the feeling (gamma burst)
2. Name it (packet encoding)
3. Let it settle (theta integration)
4. Move to next packet

Not suppression. Not continuous analysis. **Rhythmic processing.**

That's why it works. It matches how your brain actually operates.

## Implementation Details

From `api/models/metacognitive_particle.py`:

```python
class MetacognitiveParticle:
    """
    Thought particle with:
    - activation_level (current burst strength)
    - decay_rate (how fast it fades)
    - resonance_map (what it synchronizes with)
    """
```

These aren't metaphors. They're computational primitives that implement neural packet dynamics in code.

See: [[Attractor Basin Dynamics]] for how packets settle into stable states.

## Research Foundation

- Buzsáki & Draguhn (2004): "Neuronal oscillations in cortical networks"
- Fries (2005): "A mechanism for cognitive dynamics: neuronal communication through neuronal coherence"
- Spec 030: Neuronal Packet Mental Models implementation
- Spec 038: Thoughtseeds Framework (packet-based active inference)

## Links

- Implementation: `specs/030-neuronal-packet-mental-models/spec.md`
- Code: `api/models/metacognitive_particle.py`
- Related: [[Multi-Tier Memory Architecture]], [[Fractal Metacognition]]
- Application: [[Replay Loop]]

---

*Neural packets are the information atoms of consciousness. Everything else composes from them.*
