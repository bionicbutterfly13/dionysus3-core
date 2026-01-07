# Multi-Tier Memory Architecture

**Category:** System Design Pattern
**Branch:** 047-multi-tier-memory
**Related:** [[Neural Packets]], [[Fractal Metacognition]], [[Attractor Basin Dynamics]]
**Status:** Active Development

## Your Brain Doesn't Have "Memory." It Has Memory *Systems*.

Working memory (7±2 items, seconds).
Episodic memory (personal experiences, hours to years).
Semantic memory (facts and concepts, permanent).

**Different structures. Different dynamics. Different purposes.**

Most AI systems treat memory as one homogeneous thing - a vector database with similarity search.

That's not how consciousness works.

## The Three Tiers

### Working Memory (Tier 1)
**Biological analog:** Prefrontal cortex sustained activity
**Time constant:** Seconds to minutes
**Capacity:** 7±2 [[Neural Packets]]
**Function:** Active reasoning, immediate context

```python
class WorkingMemory:
    """
    Bounded capacity (7 slots)
    Rapid decay (30s without rehearsal)
    High activation cost
    """
```

**Example:** Right now you're holding this concept ("multi-tier memory") in working memory along with ~6 other thoughts. Try to add an 8th - something drops out.

That's not a bug. That's the architecture.

### Episodic Memory (Tier 2)
**Biological analog:** Hippocampus + cortical replay
**Time constant:** Hours to months
**Capacity:** Thousands of episodes
**Function:** Session continuity, experience replay

```python
class EpisodicMemory:
    """
    Event sequences with context
    Consolidation through replay
    Decay based on relevance
    Attractor basin formation (repeated patterns strengthen)
    """
```

**Example:** The session-reconstruct hook queries episodic memory at conversation start. It retrieves packets from recent sessions that match current attractor basins.

See: [[2025-12-31-infrastructure-liberation]] for today's episodic entry.

### Semantic Memory (Tier 3)
**Biological analog:** Distributed cortical networks
**Time constant:** Permanent (with rehearsal)
**Capacity:** Effectively unlimited
**Function:** Conceptual knowledge, stable representations

```python
class SemanticMemory:
    """
    Abstracted concepts (not specific episodes)
    Knowledge graph structure
    Cross-referenced via Neo4j
    No temporal decay (only relevance drift)
    """
```

**Example:** This concept page. It's not an episode ("we implemented multi-tier memory on Dec 31"). It's a semantic abstraction ("here's how multi-tier memory works").

Episodes → Semantic via repeated exposure and abstraction.

## Why Tiers Matter

### Problem 1: Context Switching Cost
Without tiers, every query searches *all* memory.

That's like your brain scanning your entire lifetime of experiences every time you try to remember where you left your keys.

Tiers enable **graduated search**:
1. Check working memory (instant)
2. If not found, check episodic memory (recent context)
3. If still not found, query semantic memory (general knowledge)

**Result:** O(n) → O(log n) search complexity.

### Problem 2: Interference
Store everything in one tier → recent noise drowns out stable knowledge.

**Example:** You're learning Python. You try 50 different syntax patterns in one day.

- **Without tiers:** All 50 patterns stored equally → confusion
- **With tiers:**
  - Working memory holds current attempt
  - Episodic memory stores the session's exploration
  - Semantic memory crystallizes *only the patterns that worked*

The tiers act as **filters**. Not all information deserves permanent storage.

### Problem 3: Cognitive Load
One memory system = one meta-question: "Should I remember this?"

Multi-tier = different questions:
- Working: "Is this relevant to my current task?"
- Episodic: "Will this matter for session continuity?"
- Semantic: "Is this a pattern I'll reuse?"

[[Fractal Metacognition]] - same meta-pattern (evaluate relevance), different time constants.

## Active Inference Implementation

From commit dc0aaf8: "Multi-tier memory lifecycle and active inference planning"

Each tier minimizes **free energy** (prediction error) at its timescale:

**Working memory:**
- Predicts: "What information do I need in the next 30 seconds?"
- Surprise: New information arrives that doesn't match current task
- Action: Swap out low-activation packet, load new packet

**Episodic memory:**
- Predicts: "What context will I need when I resume this session?"
- Surprise: Session patterns don't match expected attractor basin
- Action: Consolidate new episode, update basin weights

**Semantic memory:**
- Predicts: "What concepts are stable across sessions?"
- Surprise: Concept usage drops over time
- Action: Decay relevance (but don't delete - this is semantic knowledge)

See: [[Attractor Basin Dynamics]] for how patterns stabilize across tiers.

## The Affordance Context Service

New in 047-multi-tier-memory: `api/services/affordance_context_service.py`

**Affordances:** Actions available in the current context.

The service queries all three tiers:
1. **Working memory:** What am I trying to do *right now*?
2. **Episodic memory:** What have I done in *similar situations*?
3. **Semantic memory:** What are *general strategies* for this problem type?

Then synthesizes affordances: "Given current goal + past patterns + general knowledge, these actions make sense."

This is [[Meta Tree of Thought]] with memory: the branching strategy depends on **which tier provides the strongest signal**.

## Infrastructure Parallel

From [[2025-12-31-infrastructure-liberation]]:

**Before:** Monolithic memory (Archon tracking everything)
**After:** Tiered memory (TodoWrite for working context, SilverBullet for episodic/semantic)

Same pattern:
- **Working:** Current session todos (transient, task-specific)
- **Episodic:** Journal entries (session records, time-stamped)
- **Semantic:** Concept pages (timeless knowledge, cross-linked)

We didn't just implement multi-tier memory in code. We implemented it in **our workflow**.

That's [[Fractal Metacognition]] - the architecture we build reflects the architecture we are.

## SEO Knowledge Gap: "Multi-Tier Memory AI Architecture"

Searches:
- "Multi-tier memory" → Enterprise storage (disk/cache hierarchies)
- "Episodic memory AI" → RAG systems (single-tier vector search)
- "Biological memory tiers artificial intelligence" → Academic papers, no code

**The gap:** Nobody's publishing production implementations of biologically-inspired multi-tier memory for cognitive systems.

This spec (047) is filling that gap. This knowledge web is the documentation.

## Code Structure

```
api/models/memory_tier.py          # Base tier abstraction
api/services/multi_tier_service.py # Tier coordination
api/services/affordance_context_service.py  # Cross-tier affordance synthesis
```

Tier interface is **fractal** (see [[Fractal Metacognition]]):

```python
class MemoryTier:
    def store(self, packet: NeuralPacket) -> None
    def retrieve(self, query: Query) -> List[NeuralPacket]
    def decay(self) -> None
    def promote(self, packet: NeuralPacket, target_tier: MemoryTier) -> None
```

Same methods. Different time constants. Clean abstraction.

## Application to Analytical Empaths

The [[Replay Loop]] uses multi-tier memory:

**Working memory:** "I'm feeling anxious about this interaction"
- Immediate, conscious, high activation cost

**Episodic memory:** "I felt this way last time someone criticized my work"
- Pattern recognition, session-to-session continuity

**Semantic memory:** "I have an attachment style where criticism triggers fear of abandonment"
- Abstracted knowledge, stable across contexts

The breakthrough happens when **episodic patterns promote to semantic knowledge**.

"This keeps happening" (episodic) → "This is *who I am*" (semantic, but often wrong)

The Replay Loop interrupts this:
1. Make episodic patterns visible
2. Prevent automatic promotion to semantic identity
3. Choose which patterns *deserve* semantic storage

Same multi-tier architecture. Applied to psychological memory instead of computational memory.

## Research Foundation

- Atkinson & Shiffrin (1968): "Human memory: A proposed system and its control processes" (foundational multi-store model)
- Baddeley (2000): "The episodic buffer: a new component of working memory?"
- Tulving (1972): "Episodic and semantic memory" (tier distinction)
- Spec 047: Multi-tier memory lifecycle implementation

## Links

- Spec: `specs/047-multi-tier-memory/spec.md`
- Implementation: `api/services/multi_tier_service.py`
- Related: [[Neural Packets]], [[Fractal Metacognition]], [[Attractor Basin Dynamics]]
- Application: [[Replay Loop]]

---

*Consciousness isn't one memory. It's orchestrated tiers, each operating at its own timescale, synthesizing into coherent experience.*
