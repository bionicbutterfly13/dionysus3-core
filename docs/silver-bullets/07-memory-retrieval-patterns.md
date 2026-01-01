# Memory Retrieval Patterns - Episodic, Semantic, Procedural, Strategic

**Core Insight**: Each memory tier has distinct retrieval characteristics optimized for different cognitive operations.

---

## 📍 Navigation

**← Back to**: [00-INDEX.md](./00-INDEX.md)

**Related Documents**:
- [01-metacognition-two-layer-model.md](./01-metacognition-two-layer-model.md) - Memory architecture overview
- [04-smolagents-metatot-skills-integration.md](./04-smolagents-metatot-skills-integration.md) - Agent memory access

---

## 1. Episodic Memory Retrieval (When & Context)

### Access Pattern: Timeline Queries

**What gets retrieved**: Specific events with temporal context, emotional state, and causal sequences

**Example Queries**:
```
User: "What metacognition work did we do today?"
System: Timeline retrieval from autobiographical memory...

RESULTS:
📅 2026-01-01T10:00:00Z: Metacognition theory integration requested
   - Context: User wanted full knowledge graph ingestion
   - Attractor basins: [cognitive_science, consciousness, systems_theory]
   - Emotional state: engaged_curiosity
   - Surprise: 0.3, Confidence: 0.8

📅 2026-01-01T11:30:00Z: Meta-ToT analysis completed
   - Decision: ralph-orchestrator (single implementation)
   - Reasoning: VPS-native, multi-agent, least bloat
   - Emotional state: aha_moment
   - Surprise: 0.2, Confidence: 0.95

📅 2026-01-01T13:00:00Z: Silver bullets documentation created
   - Artifacts: 6 main docs + interactive visualization
   - Emotional state: flow_state
   - Free energy: 1.2 (stable attractor basin)
```

### Retrieval Mechanism

**Storage Location**: Multi-tier HOT tier + Autobiographical timeline

**Access Method**:
```python
# Fast recency-based access
recent_events = await hot_tier.query(
    start_time=datetime.now() - timedelta(hours=24),
    end_time=datetime.now(),
    filter_by="attractor_basins",
    values=["cognitive_science", "consciousness"]
)

# Timeline reconstruction
timeline = await autobiographical_memory.get_timeline(
    date="2026-01-01",
    include_emotional_state=True,
    include_surprise_scores=True
)
```

**Why This Matters**:
- **Context restoration**: "I was working on X before interruption, now continue"
- **Causal tracking**: "Why did I decide to use ralph-orchestrator?" → Trace back to Meta-ToT analysis
- **Emotional continuity**: "I felt flow during silver bullets creation" → Reinforces that strategy

**Speed**: ~10ms (HOT tier), ~100ms (WARM tier archives)

---

## 2. Semantic Memory Retrieval (What & Relationships)

### Access Pattern: Conceptual Queries

**What gets retrieved**: Definitions, properties, and relationship graphs

**Example Queries**:
```
User: "Explain declarative metacognition"
System: Graphiti knowledge graph traversal...

RESULTS:
📦 Entity: Declarative Metacognition
   Type: concept
   Definition: Static library of explicit knowledge about the mind

   Properties:
   - Function: informational, semantic layer
   - Characteristics: [language-dependent, explicit, conceptual]
   - Example: "I know multitasking reduces performance"
   - Storage tier: WARM (Graphiti)
   - Analogy: "User manual for the mind"

   Relationships (outbound):
   🔗 DIFFERS_FROM → Procedural Metacognition
      - Dimension: static vs dynamic, knowing vs doing
      - Clinical: "therapy gap" (patients know but can't regulate)

   🔗 STORED_IN → Graphiti WARM Tier
      - Access pattern: reflective_retrieval
      - Speed: 100-500ms

   Relationships (inbound):
   🔗 smolagents ← PROVIDES_DECLARATIVE_KNOWLEDGE
   🔗 Consciousness Pipeline ← INTEGRATES
```

### Retrieval Mechanism

**Storage Location**: Graphiti temporal knowledge graph (WARM tier)

**Access Method**:
```python
# Single concept lookup
concept = await graphiti_service.get_entity(
    name="Declarative Metacognition",
    include_relationships=True,
    depth=2  # Get neighbors of neighbors
)

# Graph traversal
path = await graphiti_service.find_path(
    start="Declarative Metacognition",
    end="OODA Loop",
    max_hops=4
)

# Semantic search
similar = await graphiti_service.search(
    query="How does metacognition relate to consciousness?",
    limit=10,
    min_relevance=0.7
)
```

**Why This Matters**:
- **Conceptual understanding**: "What IS thoughtseed competition?" → Full definition + relationships
- **Knowledge navigation**: "How does X relate to Y?" → Path through concept graph
- **Contradiction detection**: If new fact conflicts with existing entity, flag for review

**Speed**: ~100-500ms (Graphiti graph traversal)

---

## 3. Procedural Memory Retrieval (How & Skills)

### Access Pattern: Automatic Triggering

**What gets retrieved**: Execution patterns that run WITHOUT explicit queries

**Example Scenario**:
```
Agent State: HeartbeatAgent executing task

Internal State Change:
- surprise_score: 0.4 → 0.8 (SPIKE detected)
- confidence: 0.7 → 0.3 (DROP detected)
- free_energy: 1.5 → 3.2 (INCREASE detected)

AUTOMATIC RETRIEVAL TRIGGERED:
⚙️  Pattern: metacognition_control (from HOT tier)
   Condition: high_surprise AND low_confidence
   Action: generate_new_thoughtseeds()

Execution:
1. Pause current plan
2. ORIENT phase: Generate 5 new thoughtseed candidates
3. Meta-ToT evaluation: Select winner via free energy minimization
4. DECIDE phase: Adopt new plan from winning thoughtseed
5. Resume execution with updated strategy

NO USER QUERY NEEDED - Pattern auto-fired based on internal state
```

### Retrieval Mechanism

**Storage Location**: HOT tier (in-memory, <1ms access)

**Access Method**:
```python
# Pattern auto-loaded at agent initialization
patterns = await hot_tier.get_all_patterns()
agent.register_patterns(patterns)

# Real-time monitoring triggers retrieval
async def agent_step_callback(state):
    # Check all pattern conditions
    for pattern in agent.patterns:
        if pattern.matches(state):
            # AUTOMATIC execution
            await pattern.execute(agent, state)

# Example pattern structure
{
    "name": "metacognition_control",
    "trigger": {
        "surprise": {"operator": ">", "threshold": 0.7},
        "confidence": {"operator": "<", "threshold": 0.3}
    },
    "action": "generate_new_thoughtseeds",
    "priority": "high"
}
```

**Why This Matters**:
- **No latency**: Pattern fires in <1ms when conditions met
- **No conscious deliberation**: Like reflexes, runs automatically
- **Real-time regulation**: Keeps agent stable during turbulence

**Speed**: <1ms (HOT tier in-memory hash lookup)

---

## 4. Strategic Memory Retrieval (Why & Meta-Learning)

### Access Pattern: Similarity-Based Suggestions

**What gets retrieved**: Proven strategies for similar contexts

**Example Scenario**:
```
Current Situation:
- Task: "Integrate new psychedelic research into knowledge graph"
- Context: Academic theory, complex concepts, needs multi-tier storage
- Challenges: Deployment blockers possible, time constraints

SIMILARITY MATCH:
🧠 Previous Strategy: "Documentation pivot when implementation blocked"
   Context similarity: 0.87 (high match)

   Original context:
   - Task: Integrate metacognition theory
   - Challenge: VPS missing dependencies
   - Action taken: Created silver bullets instead of running script
   - Outcome: SUCCESS
   - Metrics: 6 artifacts, 30 concepts, high user satisfaction

   Confidence: 0.82 (strategy worked before)

SYSTEM SUGGESTION:
💡 "Consider using parallel agents + silver bullets approach"
   Rationale:
   - Similar complexity (theory integration)
   - Similar risk (deployment blockers)
   - Proven success rate: 92%
   - Expected time: 3-4 hours
   - Artifacts: ~5-7 documents

User can ACCEPT (use strategy) or REJECT (try different approach)
```

### Retrieval Mechanism

**Storage Location**: Meta-cognitive learning layer (strategic memory)

**Access Method**:
```python
# Context embedding for similarity search
current_context_embedding = await meta_learner.embed_context({
    "task_type": "theory_integration",
    "domain": "neuroscience",
    "constraints": ["time_limited", "deployment_risk"],
    "goals": ["knowledge_preservation", "multi_tier_storage"]
})

# Find similar past situations
similar_strategies = await meta_learner.find_similar_contexts(
    embedding=current_context_embedding,
    min_similarity=0.7,
    limit=5
)

# Rank by success rate + similarity
ranked = meta_learner.rank_strategies(
    candidates=similar_strategies,
    weights={"success_rate": 0.6, "similarity": 0.4}
)

# Present top suggestion
suggestion = ranked[0]
if suggestion.confidence > 0.75:
    await agent.suggest_strategy(suggestion)
```

**Why This Matters**:
- **Avoid repeating mistakes**: "Last time I tried X in this context, it failed"
- **Leverage past wins**: "This strategy worked before, likely to work again"
- **Faster decision-making**: No need to re-analyze, use proven playbook

**Speed**: ~500ms (embedding + similarity search)

---

## Multi-Tier Retrieval Benefits

### 1. Speed Hierarchy (Latency Optimization)

```
Procedural (HOT):    <1ms    - Reflexive, no deliberation
Episodic (HOT):      ~10ms   - Recent context restoration
Semantic (WARM):     ~100ms  - Conceptual lookup
Strategic (compute): ~500ms  - Similarity search + ranking
```

**Why**: Different cognitive operations need different speeds
- Emergency regulation (procedural) needs <1ms
- "What was I doing?" (episodic) tolerates 10ms
- "What does this mean?" (semantic) tolerates 100ms
- "What strategy should I use?" (strategic) tolerates 500ms

### 2. Information Richness (Granularity Optimization)

```
Procedural: MINIMAL (condition → action)
   Example: "IF surprise > 0.7 THEN generate_thoughtseeds()"

Episodic: CONTEXTUAL (event + emotions + causal)
   Example: "At 13:00, created silver bullets because VPS blocked, felt flow"

Semantic: RELATIONAL (entity + properties + connections)
   Example: "Declarative differs from Procedural via static/dynamic, stored in WARM vs HOT"

Strategic: META-LEVEL (strategy + context + outcomes + learning)
   Example: "Parallel agents worked because X, next time use when Y"
```

**Why**: Match information depth to retrieval purpose
- Pattern execution needs minimal data (fast)
- Understanding needs full context (rich)

### 3. Temporal Coherence (Memory Lifecycle)

```
HOT tier (Procedural):
├─ TTL: 1 hour
├─ Eviction: LRU (least recently used)
└─ Purpose: Active working patterns

WARM tier (Semantic + Episodic archives):
├─ TTL: Indefinite
├─ Compression: After 30 days
└─ Purpose: Long-term knowledge

Strategic layer:
├─ TTL: Indefinite
├─ Updates: Continuous (meta-learning)
└─ Purpose: Adaptive improvement
```

**Why**: Different memories have different lifespans
- Execution patterns age quickly (conditions change)
- Facts remain stable (concepts don't change daily)
- Strategy effectiveness updates continuously (feedback loop)

### 4. Adaptive Improvement (Meta-Learning Loop)

```
CYCLE:
1. Execute using procedural patterns (HOT tier)
2. Record outcome in episodic memory
3. Extract insights into semantic memory
4. Update strategic priors based on success/failure
5. Next similar situation → Better strategy suggested

EXAMPLE:
Iteration 1: "Try X strategy" → Failed → Record failure
Iteration 2: "Try Y strategy" → Success → Record success
Iteration 3: Similar context → System suggests Y (learned from experience)
```

**Why**: System gets smarter over time without explicit reprogramming

---

## Practical Retrieval Examples

### Example 1: Agent Confusion Recovery

```
[Agent executing task: "Implement OAuth2 authentication"]

Step 1: PROCEDURAL MONITORING (auto-triggered)
   - free_energy: 3.5 (HIGH - approaching confusion)
   - Pattern match: "metacognition_monitoring"
   - Action: Check basin stability
   - Result: Current basin unstable

Step 2: EPISODIC RETRIEVAL (context restoration)
   Query: "What was I trying to do before confusion?"
   Result: "Implement OAuth2, 15 minutes ago started with JWT, then got complex"
   Insight: Complexity creep detected

Step 3: SEMANTIC LOOKUP (concept check)
   Query: "What is OAuth2 vs JWT?"
   Result: "OAuth2 = authorization framework, JWT = token format"
   Insight: Scope mismatch - user wanted simple auth, OAuth2 is overkill

Step 4: STRATEGIC SUGGESTION
   Query: "What worked for authentication in the past?"
   Result: "JWT approach succeeded in 3/4 similar contexts"
   Suggestion: "Simplify to JWT, abandon OAuth2"

Step 5: PROCEDURAL CONTROL (auto-execution)
   - Generate new thoughtseed: "Use JWT tokens"
   - Meta-ToT evaluation: JWT wins (lower F)
   - Adopt new plan
   - Resume execution

TOTAL TIME: ~650ms (fast recovery)
```

### Example 2: Theory Integration Task

```
[User: "Integrate new psychedelic research into knowledge graph"]

Step 1: STRATEGIC RETRIEVAL (proactive suggestion)
   Context match: "theory integration" (similarity: 0.89)
   Suggestion: "Use parallel agents + silver bullets based on metacognition success"
   User: ACCEPT

Step 2: EPISODIC RECALL (workflow pattern)
   Query: "How did metacognition integration work?"
   Timeline:
   - Agent 1: Updated CLAUDE.md
   - Agent 2: Created skill docs
   - Agent 3: Updated audiobook outline
   - Main context: Stayed clean, wrote silver bullets

Step 3: PROCEDURAL EXECUTION (apply pattern)
   - Launch 3 background agents for psychedelic theory
   - Main agent writes silver bullets
   - Agents report back when done

Step 4: SEMANTIC INTEGRATION (store concepts)
   - Entities: Precision Weighting, Basin Reorganization, 5-HT2A Receptor
   - Relationships: Psychedelics → AMPLIFY → Monitoring
   - Properties: dosage ranges, mechanisms, clinical outcomes

Step 5: META-LEARNING UPDATE (record success)
   - Strategy: "parallel agents + silver bullets"
   - Context: "psychedelic research integration"
   - Outcome: SUCCESS
   - Update: confidence += 0.05
   - Next time: Even higher confidence in this approach

RESULT: Efficient execution using proven pattern
```

---

## Integration with Dionysus Architecture

### Memory Tier Mapping

```
┌─────────────────────────────────────────────────┐
│  CONSCIOUSNESS INTEGRATION PIPELINE             │
│  (Unified entry point for all memory tiers)     │
└──────────────┬──────────────────────────────────┘
               │
     ┌─────────┼─────────┬─────────────┬──────────┐
     ↓         ↓         ↓             ↓          ↓
┌─────────┐ ┌──────┐ ┌──────────┐ ┌──────────────┐
│ HOT     │ │ WARM │ │ Graphiti │ │ Meta-Learner │
│ Tier    │ │ Tier │ │ (Semantic)│ │ (Strategic)  │
├─────────┤ ├──────┤ ├──────────┤ ├──────────────┤
│Procedural│ │Episodic│ │Entities │ │Strategy DB   │
│Patterns  │ │Timeline│ │Relations│ │Success rates │
│<1ms      │ │~10ms │ │~100ms   │ │~500ms        │
└─────────┘ └──────┘ └──────────┘ └──────────────┘
```

### Agent Access Patterns

```python
# HeartbeatAgent with all memory tiers

class HeartbeatAgent(ToolCallingAgent):
    async def step(self):
        # 1. PROCEDURAL: Auto-fire patterns (no latency)
        state = self.get_state()
        for pattern in self.procedural_patterns:
            if pattern.matches(state):
                await pattern.execute()

        # 2. EPISODIC: Restore context if needed
        if self.context_lost:
            recent = await episodic.get_recent(hours=1)
            self.restore_context(recent)

        # 3. SEMANTIC: Look up concepts during reasoning
        if self.needs_definition:
            concept = await graphiti.get_entity(self.current_term)
            self.incorporate_knowledge(concept)

        # 4. STRATEGIC: Get suggestions at decision points
        if self.uncertain:
            strategies = await meta_learner.suggest(self.context)
            best = strategies[0]
            self.consider_strategy(best)

        # 5. Execute action
        return await super().step()
```

---

## Performance Characteristics

| Tier | Latency | Throughput | Use Case |
|------|---------|------------|----------|
| Procedural (HOT) | <1ms | 100K ops/sec | Real-time regulation |
| Episodic (HOT) | ~10ms | 10K ops/sec | Context restoration |
| Semantic (WARM) | ~100ms | 1K ops/sec | Conceptual lookup |
| Strategic (compute) | ~500ms | 100 ops/sec | Strategy suggestion |

**Optimization Strategy**:
- Hot paths use HOT tier (procedural)
- Cold paths use WARM tier (semantic)
- Decision points use strategic layer
- Timeline queries use episodic

---

## 🔗 Bidirectional Links

### This Document Links To:
- [00-INDEX.md](./00-INDEX.md) - Navigation hub
- [01-metacognition-two-layer-model.md](./01-metacognition-two-layer-model.md) - Memory architecture
- [04-smolagents-metatot-skills-integration.md](./04-smolagents-metatot-skills-integration.md) - Agent integration

### Documents That Link Here:
- [00-INDEX.md](./00-INDEX.md) - Main index
- [01-metacognition-two-layer-model.md](./01-metacognition-two-layer-model.md) - References retrieval patterns

---

**Author**: Mani Saint-Victor, MD
**Date**: 2026-01-01
**Integration Event**: Memory Retrieval Patterns Documentation
