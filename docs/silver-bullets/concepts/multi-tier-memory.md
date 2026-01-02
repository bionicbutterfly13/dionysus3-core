# Multi-Tier Memory

**Category**: Core Concept
**Type**: Cognitive Architecture
**Implementation**: `api/services/graphiti_service.py`, `api/services/remote_sync.py`, `api/models/memory_tier.py`

---

## Definition

**Multi-tier memory** is a four-tier architecture that organizes information by temporal access patterns, mirroring human memory systems. Each tier represents a different balance between access speed and storage durability, enabling efficient session continuity and context preservation.

Think of it as a **library with different sections**—recent books on your desk (HOT), frequently-used references on nearby shelves (WARM), archived books in the basement (COLD), and permanent records in vault storage (FREEZE).

## Key Characteristics

- **Temporal Stratification**: Information automatically migrates between tiers based on access frequency and recency
- **Access-Speed Gradient**: HOT (microseconds) → WARM (milliseconds) → COLD (seconds) → FREEZE (minutes)
- **Lifecycle Management**: Automatic promotion, demotion, and pruning based on usage patterns
- **Biological Correspondence**: Maps to working memory, semantic memory, episodic memory, and archival storage
- **Non-Destructive**: Demotion preserves information; promotion creates cached copies
- **Observability**: Each tier provides inspection and debugging interfaces

## Memory Tiers

### HOT Tier: Procedural Metacognition

**Purpose**: Active inference state and real-time cognition

**Storage**: Redis (in-memory) or process memory
**Lifespan**: Current session only (seconds to hours)
**Access Time**: Microseconds
**Volatility**: Ephemeral, cleared on session end

**Contents**:
- Current OODA loop state (Observe → Orient → Decide → Act)
- Active thoughtseed competition results
- Procedural metacognition: attention allocation, resource budgets
- Real-time prediction errors and free energy calculations
- Step-by-step agent execution traces

**Code Reference**: `api/agents/callbacks/memory_callback.py:66-173`

```python
# HOT tier: Memory pruning during active reasoning
def memory_pruning_callback(memory_step: ActionStep, agent: Any) -> None:
    # Keeps only recent N steps in HOT tier (default: 3)
    # Older steps summarized to prevent context overflow
    if latest_step >= MEMORY_WINDOW:
        # Prune observations older than window
        summary = _summarize_observation(str(observation), prev_number)
```

---

### WARM Tier: Declarative Metacognition

**Purpose**: Semantic knowledge and temporal facts

**Storage**: Graphiti temporal knowledge graph (Neo4j)
**Lifespan**: Weeks to months
**Access Time**: Milliseconds
**Volatility**: Persistent with temporal versioning

**Contents**:
- Domain concepts and relationships
- Metacognitive patterns (reasoning strategies, decision heuristics)
- Attractor basin definitions and stability metrics
- Entity extraction and relationship facts
- Self-model representations (network states, role matrices)

**Code Reference**: `api/services/graphiti_service.py:224-275`

```python
# WARM tier: Graphiti temporal graph ingestion
async def ingest_message(
    self,
    content: str,
    source_description: str = "conversation",
    group_id: Optional[str] = None,
    valid_at: Optional[datetime] = None,
) -> dict[str, Any]:
    result = await graphiti.add_episode(
        name=f"episode_{uuid4().hex[:8]}",
        episode_body=content,
        source=EpisodeType.message,
        source_description=source_description,
        group_id=group,
        reference_time=timestamp,
    )
    # Extracts entities and relationships into temporal KG
```

**Temporal Versioning**: Facts have `valid_at` and `invalid_at` timestamps, allowing historical queries like "What did the agent believe about X on date Y?"

---

### COLD Tier: Episodic Memory

**Purpose**: Long-term episodic memories and session histories

**Storage**: Neo4j knowledge graph (via n8n webhooks)
**Lifespan**: Months to years
**Access Time**: Seconds
**Volatility**: Persistent, compressible

**Contents**:
- Full conversation episodes with timestamps
- Session summaries and project associations
- Trajectory data (multi-step agent runs)
- Memory nodes with session_id and project_id attribution
- Historical network state snapshots

**Code Reference**: `api/services/remote_sync.py:456-520`

```python
# COLD tier: Sync episodic memory to Neo4j
async def sync_memory_on_create(
    self,
    memory_data: dict[str, Any],
    queue_if_unavailable: bool = True,
) -> dict[str, Any]:
    payload = {
        "memory_id": memory_id,
        "content": memory_data.get("content", ""),
        "memory_type": memory_data.get("memory_type", "episodic"),
        "session_id": str(memory_data.get("session_id", "")),
        "project_id": memory_data.get("source_project", "default"),
        "created_at": memory_data.get("created_at", datetime.utcnow().isoformat()),
    }
    # Webhook to n8n → Neo4j storage
    await self._send_to_webhook(payload)
```

**Session Attribution**: Memories tagged with `session_id` enable session reconstruction across conversation boundaries.

---

### FREEZE Tier: Archival Storage

**Purpose**: Immutable records and compliance logs

**Storage**: S3 object storage or filesystem
**Lifespan**: Indefinite (years to permanent)
**Access Time**: Minutes
**Volatility**: Immutable, write-once

**Contents**:
- Complete audit trails (all agent actions)
- Regulatory compliance records
- Snapshot backups of entire system state
- Historical baselines for drift detection
- Raw data for future re-analysis

**Implementation Status**: Planned (not yet implemented in codebase)

**Design Pattern**: Write-once, append-only logs with compression and deduplication.

---

## Lifecycle Management

### Auto-Pruning (HOT Tier)

**Code**: `api/agents/callbacks/memory_callback.py:66-173`

**Trigger**: Every ActionStep during agent execution
**Window**: Last 3 steps (configurable via `AGENT_MEMORY_WINDOW`)
**Strategy**: Summarize observations older than window

```python
# From memory_callback.py:152-159
if pruned_count > 0:
    reduction = original_tokens - pruned_tokens
    logger.info(
        f"Memory pruned: {pruned_count} steps, "
        f"~{reduction} tokens saved ({reduction_pct:.0f}% reduction)"
    )
```

**Benefit**: Prevents context overflow during long-running agent loops (10+ steps)

---

### Promotion (COLD → WARM)

**Trigger**: High access frequency or explicit "pin" operation
**Strategy**: Copy to WARM tier while preserving COLD original

**Example**: Frequently-recalled episode → extracted as WARM-tier concept

---

### Demotion (WARM → COLD)

**Trigger**: Low access frequency over time threshold
**Strategy**: Retain in COLD tier, remove from WARM cache

**Example**: Unused concept definition → moved to episodic storage

---

### Archival (COLD → FREEZE)

**Trigger**: Age threshold or explicit archive command
**Strategy**: Compress and write to immutable storage

**Example**: Session older than 90 days → archived to S3

---

## Implementation

### Memory Tier Model

**Code**: `api/models/memory_tier.py:7-33`

```python
class MemoryTier(str, Enum):
    HOT = "hot"       # Session cache / Redis
    WARM = "warm"     # Neo4j Graph (Graphiti)
    COLD = "cold"     # Compressed archive / Vector

class TieredMemoryItem(BaseModel):
    id: str
    content: str
    memory_type: str = "semantic"
    tier: MemoryTier = MemoryTier.HOT

    # Temporal metadata
    created_at: datetime
    last_accessed: datetime
    importance_score: float

    # Attribution
    session_id: Optional[str] = None
    project_id: str = "default"
```

**Note**: FREEZE tier not yet in enum (future extension)

---

### Graphiti Service (WARM Tier)

**Code**: `api/services/graphiti_service.py:144-223`

**Initialization**:
```python
async def initialize(self) -> None:
    if _global_graphiti is None:
        _global_graphiti = Graphiti(
            uri=self.config.neo4j_uri,
            user=self.config.neo4j_user,
            password=self.config.neo4j_password,
        )
        # Build temporal indexes in background
        await _global_graphiti.build_indices_and_constraints()
```

**Operations**:
- `ingest_message()` - Add semantic content to temporal graph
- `search()` - Hybrid search (semantic + keyword + graph traversal)
- `execute_cypher()` - Direct Cypher with destruction gate safeguards

---

### Remote Sync Service (COLD Tier)

**Code**: `api/services/remote_sync.py:164-240`

**Queue Management**:
```python
class RemoteSyncService:
    def queue_memory(
        self,
        memory_id: str,
        operation: str,  # create, update, delete
        payload: dict[str, Any],
    ) -> QueueItem:
        # Exponential backoff retry logic
        # n8n webhook delivery with HMAC verification
```

**Recovery**:
```python
async def bootstrap_recovery(
    self,
    project_id: Optional[str] = None,
    since: Optional[str] = None,
) -> list[dict[str, Any]]:
    # Recover memories from Neo4j via n8n recall webhook
    # Rebuild local state after crash or migration
```

---

### Memory Router (API)

**Code**: `api/routers/memory.py:110-210`

**Endpoints**:
- `GET /api/memory/sessions/{session_id}` - Query by session
- `GET /api/memory/range` - Query by date range
- `GET /api/memory/search` - Keyword search with attribution
- `POST /api/memory/semantic-search` - Vector similarity search

---

## Related Concepts

**Prerequisites** (understand these first):
- [[declarative-metacognition]] - WARM tier stores declarative knowledge
- [[procedural-metacognition]] - HOT tier tracks procedural state

**Builds Upon** (this uses):
- [[attractor-basin]] - Basins stored in WARM tier, state in HOT tier
- [[thoughtseed-competition]] - Competition results cached in HOT tier

**Used By** (depends on this):
- [[basin-stability]] - Stability metrics span HOT/WARM tiers
- [[metacognitive-feelings]] - Generated from tier access patterns

**Related** (similar or complementary):
- [[prediction-error]] - Errors trigger HOT → WARM consolidation
- [[free-energy]] - Free energy calculations use multi-tier context

---

## Examples

### Example 1: Session Continuity (Clinical)

**Scenario**: Therapist reviewing client session history

```python
# COLD tier: Retrieve session memories
session_memories = await sync_service.query_by_session(
    session_id="abc123",
    include_metadata=True
)

# WARM tier: Extract patterns from session
patterns = await graphiti_service.search(
    query="maladaptive beliefs about self-worth",
    group_ids=["client_abc"]
)

# HOT tier: Active inference during current session
current_state = {
    "active_basin": "self-criticism-basin",
    "prediction_error": 0.72,
    "metacognitive_feeling": "uncertainty"
}
```

**Outcome**: Therapist sees longitudinal pattern (COLD) + semantic insights (WARM) + real-time state (HOT)

---

### Example 2: Auto-Pruning During Long Agent Run (Technical)

**Scenario**: Heartbeat agent with 15-step OODA cycle

**Before Pruning** (Step 10):
```
HOT tier memory: 10 full observations × 500 tokens = 5000 tokens
Context window: Approaching limit
```

**After Pruning** (Step 10):
```python
# Memory callback runs
# Keeps steps 8, 9, 10 in full
# Summarizes steps 1-7

HOT tier memory:
  - Steps 8-10: 1500 tokens (full)
  - Steps 1-7: 350 tokens (summarized)
  - Total: 1850 tokens (63% reduction)
```

**Outcome**: Agent completes 15-step cycle without context overflow

---

### Example 3: Temporal Knowledge Graph (WARM Tier)

**Scenario**: Tracking belief evolution over time

```python
# January 2025: Agent believes "Docker is essential"
await graphiti.add_episode(
    episode_body="Docker orchestration is critical for deployment",
    reference_time=datetime(2025, 1, 15),
    group_id="dionysus"
)

# March 2025: Belief changes after infrastructure liberation
await graphiti.add_episode(
    episode_body="Lean infrastructure is faster; Docker not needed",
    reference_time=datetime(2025, 3, 20),
    group_id="dionysus"
)

# Query: What did agent believe on Feb 1?
results = await graphiti.search(
    query="Docker necessity",
    group_ids=["dionysus"],
    # Temporal filter (implicit in Graphiti)
)
# Returns: "Docker is essential" (valid_at < Feb 1 < invalid_at)
```

**Outcome**: System can reconstruct historical beliefs, enabling meta-reasoning about belief change

---

### Example 4: Bootstrap Recovery (COLD → HOT)

**Scenario**: API restart after crash

```python
# System restarts with empty HOT tier
# Recover recent session context from COLD tier

memories = await sync_service.bootstrap_recovery(
    project_id="dionysus3-core",
    since="2026-01-01T00:00:00Z"
)

# Rebuild session context
for memory in memories:
    # Re-activate relevant basins
    await basin_router.route_memory(memory)

# HOT tier now populated with recent context
# Agent resumes with minimal disruption
```

---

## Common Misconceptions

**Misconception 1**: "Multi-tier memory requires manual tier selection"
**Reality**: Tier placement is automatic. System manages lifecycle based on access patterns. You interact with a unified memory API; tiering is transparent.

**Misconception 2**: "HOT tier is just a cache"
**Reality**: HOT tier is procedural metacognition—it tracks **how** the agent is reasoning, not just **what** it remembers. It's the active inference engine, not a data cache.

**Misconception 3**: "Demotion loses information"
**Reality**: Demotion is non-destructive. COLD tier retains full fidelity. WARM tier loses temporal immediacy but preserves semantic content.

**Misconception 4**: "All four tiers must be implemented simultaneously"
**Reality**: Tiers are additive. Current Dionysus has HOT (callbacks), WARM (Graphiti), and COLD (Neo4j). FREEZE is planned but optional.

**Misconception 5**: "Multi-tier memory is just database sharding"
**Reality**: This is cognitive architecture, not database optimization. Tiers mirror human memory systems (working, semantic, episodic, archival) and support active inference, not just data retrieval.

---

## When to Use

✅ **Use multi-tier memory when**:
- Building agents with long-running sessions (hours to days)
- Session continuity is critical (conversations spanning multiple API restarts)
- Context window management is a bottleneck (long OODA cycles)
- Historical reasoning required ("What did I believe last week?")
- Debugging complex agent behavior (inspect HOT/WARM/COLD separately)

❌ **Don't use when**:
- Stateless, single-shot requests (no session context needed)
- Memory footprint is tiny (all context fits in HOT tier)
- No temporal queries required (flat storage sufficient)
- Compliance/audit not required (FREEZE tier unnecessary)

---

## Tier Selection Heuristics

### Access Frequency

| Frequency | Recommended Tier |
|-----------|-----------------|
| Every step | HOT (procedural state) |
| Every session | WARM (semantic facts) |
| Cross-session queries | COLD (episodic history) |
| Audit/compliance | FREEZE (immutable logs) |

### Data Characteristics

| Characteristic | Tier |
|----------------|------|
| Volatile, transient | HOT |
| Semantic, relational | WARM |
| Episodic, timestamped | COLD |
| Immutable, compliance | FREEZE |

### Lifespan

| Lifespan | Tier |
|----------|------|
| Seconds to hours | HOT |
| Weeks to months | WARM |
| Months to years | COLD |
| Permanent | FREEZE |

---

## Architecture Benefits

### 1. Session Continuity

**Problem**: API restarts lose in-memory state
**Solution**: COLD tier persists session context; bootstrap recovery rebuilds HOT tier

### 2. Context Window Efficiency

**Problem**: Long agent runs exceed LLM context limits
**Solution**: HOT tier auto-pruning summarizes old observations; WARM tier provides semantic compression

### 3. Temporal Reasoning

**Problem**: Need to query historical beliefs ("What did agent think on date X?")
**Solution**: WARM tier temporal versioning with `valid_at`/`invalid_at` timestamps

### 4. Debugging Transparency

**Problem**: Agent behavior is opaque; hard to diagnose issues
**Solution**: Inspect HOT (current state), WARM (knowledge base), COLD (session history) independently

### 5. Biological Plausibility

**Problem**: Monolithic memory doesn't match neuroscience
**Solution**: HOT (working memory), WARM (semantic memory), COLD (episodic memory), FREEZE (archival) map to known memory systems

---

## Performance Characteristics

### Tier Access Latency

```
HOT:    O(1)      - Direct memory access
WARM:   O(log n)  - Graph index lookup
COLD:   O(n)      - Webhook + Cypher query
FREEZE: O(n²)     - S3 retrieval + decompression
```

### Storage Scaling

```
HOT:    Limited by RAM (typically <100 MB)
WARM:   Neo4j graph (scales to billions of nodes)
COLD:   Neo4j + compression (scales to TBs)
FREEZE: S3 (scales to PBs)
```

### Promotion/Demotion Cost

```
HOT → WARM:   Milliseconds (entity extraction)
WARM → COLD:  Seconds (graph query + serialization)
COLD → FREEZE: Minutes (compression + S3 upload)
```

---

## Integration with Other Systems

### OODA Loop (HOT Tier)

**Observe**: Sensor data enters HOT tier
**Orient**: HOT tier prediction error triggers WARM tier concept recall
**Decide**: Decision rationale cached in HOT tier
**Act**: Action results update HOT tier state

### Graphiti Temporal Graph (WARM Tier)

**Entity Extraction**: New episodes → entities/relationships in WARM tier
**Temporal Queries**: "What did agent know about X at time T?"
**Hybrid Search**: Semantic + keyword + graph traversal

### n8n Webhooks (COLD Tier)

**Ingestion**: n8n → Neo4j storage
**Recall**: n8n → Cypher query → JSON response
**Safety**: HMAC signature verification prevents unauthorized writes

---

## Future Extensions

### Planned: FREEZE Tier

**Storage**: S3-compatible object storage
**Trigger**: Age > 90 days or explicit archive command
**Format**: Compressed JSON with deduplication
**Access**: Read-only, for historical analysis and compliance

### Planned: Cross-Tier Search

**Query**: "Show me all mentions of 'attractor basin' across all tiers"
**Response**: HOT (current reasoning) + WARM (concept definition) + COLD (historical usage) + FREEZE (audit logs)

### Planned: Adaptive Tier Boundaries

**Current**: Fixed thresholds (e.g., MEMORY_WINDOW=3)
**Future**: Dynamic thresholds based on context complexity, task novelty, available resources

---

## Research Foundation

### Neuroscience Parallels

- **Working Memory** (HOT): Prefrontal cortex, 7±2 items, seconds
- **Semantic Memory** (WARM): Neocortex, conceptual knowledge, years
- **Episodic Memory** (COLD): Hippocampus, time-tagged experiences, lifetime
- **Archival** (FREEZE): External storage (books, notes), permanent

### Computational Models

- **Atkinson-Shiffrin Model** (1968): Sensory → Short-term → Long-term
- **Baddeley Working Memory** (1974): Phonological loop + visuospatial sketchpad
- **Tulving Episodic/Semantic** (1972): Distinction between event memory and fact memory

### Active Inference Integration

- **Precision Weighting** (HOT): Real-time attention allocation
- **Generative Models** (WARM): Conceptual priors for prediction
- **Free Energy Minimization**: Tiers optimize surprise reduction at different timescales

---

## Further Reading

- **Research**:
  - Atkinson, R.C. & Shiffrin, R.M. (1968). Human memory: A proposed system and its control processes.
  - Tulving, E. (1972). Episodic and semantic memory.
  - Baddeley, A.D. (1974). Working memory.
- **Documentation**:
  - [[01-metacognition-two-layer-model]] - Theoretical foundation for HOT/WARM distinction
  - [[declarative-metacognition]] - WARM tier knowledge representation
  - [[procedural-metacognition]] - HOT tier execution state
- **Specifications**:
  - `specs/034-network-self-modeling/spec.md` - Network state storage (WARM tier)
  - `specs/002-remote-persistence-safety/spec.md` - COLD tier sync architecture
- **Implementation**:
  - `api/models/memory_tier.py` - Tier definitions
  - `api/agents/callbacks/memory_callback.py` - HOT tier pruning
  - `api/services/graphiti_service.py` - WARM tier operations
  - `api/services/remote_sync.py` - COLD tier sync

---

**Author**: Dr. Mani Saint-Victor, MD
**Last Updated**: 2026-01-02
**Status**: Production
**Integration Event**: Remote Persistence Safety (002) + Thoughtseeds Framework (038) → Multi-Tier Memory Architecture
