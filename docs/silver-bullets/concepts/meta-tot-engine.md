# Meta-ToT Engine

**Category**: Core Concept
**Type**: Process
**Implementation**: `api/services/meta_tot_engine.py`, `api/models/meta_tot.py`

---

## Definition

The **Meta-ToT Engine** (Meta-Tree-of-Thought) is a Monte Carlo Tree Search (MCTS) system that generates multiple candidate thoughtseeds through systematic exploration of reasoning branches, scored via active inference free energy minimization.

It's a thoughtseed generation mechanism that explores the solution space like a chess engine explores moves—simulating multiple paths, scoring each by expected free energy, and using UCB1 (Upper Confidence Bound) to balance exploration and exploitation.

## Key Characteristics

- **MCTS-Based**: Uses Monte Carlo Tree Search for systematic exploration
- **Active Inference Scoring**: Free energy (F) as heuristic for branch quality
- **Parallel Generation**: Creates multiple competing thoughtseeds simultaneously
- **UCB1 Selection**: Balances exploration of new branches vs exploitation of promising paths
- **Domain-Phased Expansion**: Organizes search through CPA domains (explore, challenge, evolve, integrate)
- **Time-Bounded**: Configurable time budget prevents infinite search
- **Trace-Enabled**: Full reasoning tree recorded for post-hoc analysis

## How It Works

### Step-by-Step Process

1. **Initialization** (Root Node)
   - Problem/task becomes root node of search tree
   - Initial active inference state computed from problem complexity
   - Observation vector built from context (problem size, constraints, richness)

2. **Tree Expansion** (Breadth-First Growth)
   - For each depth level (default: 4 levels)
   - Rotate through CPA domains: explore → challenge → evolve → integrate
   - Generate candidate branches via LLM or fallback heuristics
   - Each candidate becomes child node with inherited active inference state
   - Branches limited by branching factor (default: 3 per node)

3. **MCTS Simulation** (Monte Carlo Rollouts)
   - Run multiple simulations (default: 32) within time budget
   - **Selection**: Pick path from root to leaf using UCB1 scores
   - **Evaluation**: Calculate reward = 1 / (1 + free_energy)
   - **Backpropagation**: Update value estimates along path
   - **UCB1 Formula**: `exploitation + exploration + prediction_bonus`

4. **Best Path Selection** (Winner-Take-All)
   - Traverse tree following highest value estimates
   - Selected path = sequence of node IDs from root to best leaf
   - Confidence = normalized action value from POMCP planner

5. **Basin Update** (Memory Integration)
   - Route selected path summary to memory basin
   - Store as STRATEGIC memory type
   - Enables long-term learning from reasoning patterns

### Visual Representation

```
                    ROOT (Problem)
                         |
      ┌──────────────────┼──────────────────┐
      |                  |                  |
   EXPLORE           EXPLORE            EXPLORE
   (F=1.2)           (F=2.1)            (F=3.5)
      |
 ┌────┼────┐
 |    |    |
CHALLENGE CHALLENGE CHALLENGE
(F=0.9) (F=1.5) (F=2.8)
 |
 ├─── EVOLVE (F=0.7) ← WINNER
 └─── EVOLVE (F=1.1)

Selection Criterion: Lowest Free Energy Path
Winner Path: ROOT → EXPLORE → CHALLENGE → EVOLVE (F=0.7)
Confidence: 0.85
```

**Energy landscape interpretation**:
- Lower nodes = Lower free energy = Better hypotheses
- Path selection follows energy gradient downhill
- Winner = deepest valley in the search tree

## Implementation

### Core MCTS Algorithm

**File**: `api/services/meta_tot_engine.py:288-314`

```python
async def _run_mcts(self, root_node: MetaToTNode, config: MetaToTConfig) -> None:
    """Monte Carlo Tree Search with active inference scoring."""
    start_time = time.time()
    for _ in range(config.simulation_count):
        if time.time() - start_time > config.time_budget_seconds:
            break

        # Selection: Follow UCB1 scores to leaf
        path = self._select_path(root_node, config.exploration_constant)
        leaf = path[-1]

        # Evaluation: Reward based on free energy
        reward = self._evaluate_leaf(leaf)
        prediction_error = leaf.active_inference_state.prediction_error

        # Backpropagation: Update all nodes in path
        for node in path:
            node.update_from_rollout(reward, prediction_error)
```

### UCB1 Score Calculation

**File**: `api/services/meta_tot_engine.py:53-61`

```python
def compute_ucb_score(
    self,
    total_parent_visits: int,
    exploration_constant: float = 2.0
) -> float:
    """UCB1 with active inference prediction bonus."""
    if self.visit_count == 0:
        return float("inf")  # Unexplored nodes prioritized

    exploitation = self.value_estimate
    exploration = exploration_constant * math.sqrt(
        math.log(max(total_parent_visits, 1)) / self.visit_count
    )
    prediction_bonus = 1.0 / (1.0 + self.active_inference_state.prediction_error)

    return exploitation + exploration + prediction_bonus
```

**Components**:
- **Exploitation**: `value_estimate` (average reward from previous rollouts)
- **Exploration**: UCB1 term (encourages trying less-visited nodes)
- **Prediction Bonus**: Active inference term (favors low prediction error)

### Node Update Rule

**File**: `api/services/meta_tot_engine.py:63-70`

```python
def update_from_rollout(
    self,
    reward: float,
    prediction_error: float,
    learning_rate: float = 0.1
) -> None:
    """Backpropagation with precision-weighted rewards."""
    self.visit_count += 1

    # Weight reward by prediction accuracy
    prediction_weight = 1.0 / (1.0 + prediction_error)
    weighted_reward = reward * prediction_weight

    # Incremental value update
    self.value_estimate += learning_rate * (weighted_reward - self.value_estimate)

    # Decrease uncertainty with visits
    self.uncertainty_estimate = 1.0 / math.sqrt(self.visit_count + 1)

    # Update active inference state
    self.active_inference_state.update_beliefs(prediction_error, learning_rate)

    # Score = final value estimate
    self.score = self.value_estimate
```

### Active Inference State

**File**: `api/models/meta_tot.py:15-44`

```python
class ActiveInferenceState(BaseModel):
    """Active inference currency state for Meta-ToT nodes."""

    state_id: str
    prediction_error: float = 0.0
    free_energy: float = 0.0
    surprise: float = 0.0
    precision: float = 1.0
    beliefs: Dict[str, float]
    prediction_updates: Dict[str, float]
    reasoning_level: int = 0
    parent_state_id: Optional[str] = None

    def compute_prediction_error(self, observation: Dict[str, float]) -> float:
        """Calculate weighted prediction error."""
        total_error = 0.0
        for key, observed_value in observation.items():
            predicted_value = self.beliefs.get(key, observed_value)
            error = abs(observed_value - predicted_value)
            total_error += error * self.precision

        self.prediction_error = total_error
        return total_error

    def update_beliefs(self, prediction_error: float, learning_rate: float = 0.1):
        """Active inference belief update."""
        for belief_key, belief_value in list(self.beliefs.items()):
            gradient = self.prediction_updates.get(belief_key, 0.0)
            belief_update = -learning_rate * gradient * prediction_error
            self.beliefs[belief_key] = max(0.0, min(1.0, belief_value + belief_update))

        # Free energy = prediction error + complexity penalty
        self.free_energy = prediction_error + 0.01 * len(self.beliefs)

        # Surprise = negative log likelihood
        self.surprise = -math.log(max(0.001, 1.0 - min(prediction_error, 0.99)))
```

### Configuration

**File**: `api/services/meta_tot_engine.py:74-93`

```python
@dataclass
class MetaToTConfig:
    max_depth: int = 4                    # Tree depth
    simulation_count: int = 32            # MCTS rollouts
    exploration_constant: float = 2.0     # UCB1 exploration weight
    branching_factor: int = 3             # Children per node
    time_budget_seconds: float = 5.0      # Max search time
    use_llm: bool = True                  # LLM vs fallback candidate generation
    llm_model: str = GPT5_NANO            # Model for branch generation
    persist_trace: bool = True            # Store reasoning trace
    random_seed: Optional[int] = None     # For reproducibility
```

### Integration with EFE Engine

**File**: `api/services/efe_engine.py:61-84`

Meta-ToT uses the Expected Free Energy Engine for scoring:

```python
# Each branch evaluated via EFE
efe = efe_engine.calculate_efe(
    prediction_probs=context_probs,
    thought_vector=branch_embedding,
    goal_vector=goal_embedding,
    precision=precision
)

# Reward for MCTS = inverse of free energy
reward = 1.0 / (1.0 + efe)
```

### Tests

**Unit Tests**: `tests/unit/test_metacognition_patterns_storage.py`
**Integration Tests**: `tests/integration/test_metacognition_semantic_storage.py`
**Specification**: `specs/041-meta-tot-engine/spec.md`

## Related Concepts

**Prerequisites** (understand these first):
- [[thoughtseed]] - What Meta-ToT generates (candidate hypotheses)
- [[free-energy]] - Scoring criterion for branches
- [[active-inference]] - Theoretical foundation for scoring

**Builds Upon** (this uses):
- [[prediction-error]] - Component of active inference state
- [[surprise-score]] - Uncertainty component
- [[precision-weighting]] - Confidence modulation of free energy

**Used By** (depends on this):
- [[thoughtseed-competition]] - Meta-ToT output feeds into competition
- [[attractor-basin]] - Winning paths create basins
- [[metacognitive-feelings]] - Large ΔF from Meta-ToT triggers insights

**Related** (similar or complementary):
- [[ooda-loop]] - Meta-ToT runs during ORIENT/DECIDE phases
- [[consciousness-stream]] - Meta-ToT enables multi-step deliberation
- [[declarative-metacognition]] - Meta-ToT searches declarative knowledge space

## Examples

### Example 1: Problem-Solving (Debugging)

**Problem**: "Test suite failing after database migration"

**Meta-ToT Exploration**:

```
ROOT: "Test suite failing after database migration"
├─ EXPLORE: "Check migration scripts for syntax errors" (F=1.5)
│  ├─ CHALLENGE: "Verify rollback works correctly" (F=2.1)
│  ├─ CHALLENGE: "Check foreign key constraints" (F=1.8)
│  └─ CHALLENGE: "Review migration logs" (F=1.2)
│     ├─ EVOLVE: "Search logs for 'ERROR' patterns" (F=0.9) ← WINNER
│     └─ EVOLVE: "Compare logs to previous migration" (F=1.4)
│
├─ EXPLORE: "Verify test database configuration" (F=2.3)
│  └─ CHALLENGE: "Check environment variables" (F=2.8)
│
└─ EXPLORE: "Review test isolation setup" (F=3.1)
```

**Selected Path**:
- ROOT → EXPLORE (check migration scripts) → CHALLENGE (review logs) → EVOLVE (search for ERROR patterns)
- **Confidence**: 0.87
- **Free Energy**: 0.9 (low, stable hypothesis)
- **Metacognitive Feeling**: Gradual understanding, confidence building

**Clinical Translation**:
"When debugging complex issues, your mind generates multiple hypotheses unconsciously. The 'search logs for errors' thought wins because it's both simple to execute AND likely to find the problem. This is why experienced developers often 'just know' where to look—their Meta-ToT has learned effective search patterns."

### Example 2: Therapeutic Reframe Search

**Problem**: Client stuck in rumination loop: "I always fail at relationships"

**Meta-ToT Exploration**:

```
ROOT: "Client belief: 'I always fail at relationships'"
├─ EXPLORE: "Identify cognitive distortion type" (F=1.3)
│  ├─ CHALLENGE: "Overgeneralization from 2-3 instances" (F=1.1)
│  │  ├─ EVOLVE: "Map timeline of actual relationships" (F=0.8)
│  │  └─ EVOLVE: "Find counterexample relationships" (F=1.2)
│  │
│  └─ CHALLENGE: "All-or-nothing thinking pattern" (F=1.5)
│
├─ EXPLORE: "Search for attachment pattern roots" (F=2.0)
│  ├─ CHALLENGE: "Early caregiver dynamics" (F=2.5)
│  └─ CHALLENGE: "Avoidant attachment activation" (F=2.8)
│
└─ EXPLORE: "Reframe as skill-building opportunity" (F=1.0)
   ├─ CHALLENGE: "'What if failure is data, not identity?'" (F=0.7) ← WINNER
   │  ├─ EVOLVE: "Frame as scientist testing hypotheses" (F=0.5) ← BEST
   │  └─ EVOLVE: "Each relationship teaches new skills" (F=0.9)
   │
   └─ CHALLENGE: "Separate behavior from self-concept" (F=1.3)
```

**Selected Path**:
- ROOT → EXPLORE (reframe as skill-building) → CHALLENGE ("failure is data") → EVOLVE (scientist metaphor)
- **Confidence**: 0.91
- **Free Energy**: 0.5 (very low, elegant reframe)
- **Metacognitive Feeling**: **Aha!** (large ΔF from 2.5 → 0.5)

**IAS Application**:
"Your analytical mind generates multiple ways to understand a stuck belief. The 'scientist testing hypotheses' reframe wins because it's both simple (one metaphor) AND accurate (matches your cognitive style). This is metacognition in action—your thinking about thinking found the best frame."

### Example 3: Architecture Decision (Technical Strategy)

**Problem**: "Design authentication system for multi-tenant SaaS API"

**Meta-ToT Exploration**:

```
ROOT: "Design authentication for multi-tenant SaaS"
├─ EXPLORE: "Token-based stateless auth" (F=1.2)
│  ├─ CHALLENGE: "JWT with tenant_id claim" (F=1.0)
│  │  ├─ EVOLVE: "Short-lived access + refresh tokens" (F=0.8)
│  │  │  ├─ INTEGRATE: "Redis for token blacklist on logout" (F=0.6) ← WINNER
│  │  │  └─ INTEGRATE: "Sliding window refresh strategy" (F=0.9)
│  │  └─ EVOLVE: "Asymmetric keys per tenant" (F=1.5)
│  │
│  └─ CHALLENGE: "API keys with rate limiting" (F=1.8)
│
├─ EXPLORE: "Session-based auth with Redis" (F=2.1)
│  └─ CHALLENGE: "Sticky sessions for multi-region" (F=2.8)
│
└─ EXPLORE: "OAuth2 delegation model" (F=2.5)
   └─ CHALLENGE: "PKCE flow for web apps" (F=3.2)
```

**Selected Path**:
- ROOT → EXPLORE (token-based) → CHALLENGE (JWT) → EVOLVE (access+refresh) → INTEGRATE (Redis blacklist)
- **Confidence**: 0.88
- **Free Energy**: 0.6 (stable, well-justified)
- **Basin Depth**: Deep (persists through implementation)

**Reasoning Trace Metrics**:
- Total branches explored: 13
- MCTS simulations: 32
- Processing time: 3.2s
- Total prediction error: 8.4
- Total free energy: 15.7

**Business Translation**:
"The Meta-ToT evaluated 13 different authentication strategies in 3 seconds. The JWT+Redis approach won because it balances simplicity (standard JWT) with accuracy (handles logout security). This systematic exploration prevents premature optimization and costly architectural mistakes."

### Example 4: Strategy Selection Under Uncertainty

**Problem**: "Marketing campaign underperforming, unclear cause"

**Meta-ToT with High Uncertainty** (Precision = 0.4):

```
ROOT: "Campaign underperforming, cause unknown"
├─ EXPLORE: "Analyze click-through rate data" (F=1.8, weighted=4.5)
├─ EXPLORE: "Survey target audience directly" (F=2.5, weighted=6.25)
├─ EXPLORE: "A/B test messaging variations" (F=1.2, weighted=3.0) ← WINNER
│  ├─ CHALLENGE: "Test emotional vs rational hooks" (F=0.9, weighted=2.25)
│  └─ CHALLENGE: "Test visual vs text emphasis" (F=1.1, weighted=2.75)
└─ EXPLORE: "Review competitor campaigns" (F=2.0, weighted=5.0)
```

**Effect of Low Precision** (uncertain context):
- Uncertainty term amplified: `(1/0.4) * Uncertainty = 2.5 * Uncertainty`
- Divergence term reduced: `0.4 * Divergence`
- **Result**: System favors exploration (A/B testing) over exploitation
- **Rationale**: When uncertain about root cause, gather more data before committing

**Contrast with High Precision** (Precision = 2.5, confident context):
```
Same problem, but we're confident about the issue:
├─ EXPLORE: "Analyze click-through rate data" (F=1.8, weighted=4.5)
├─ EXPLORE: "Fix identified conversion bottleneck" (F=0.8, weighted=2.0) ← WINNER
└─ EXPLORE: "A/B test messaging variations" (F=1.2, weighted=3.0)
```

**Effect of High Precision**:
- Uncertainty term reduced: `(1/2.5) * Uncertainty = 0.4 * Uncertainty`
- Divergence term amplified: `2.5 * Divergence`
- **Result**: System favors exploitation (fix known issue) over exploration
- **Rationale**: When confident about diagnosis, act decisively

## CPA Domain Expansion

Meta-ToT organizes search through four cognitive domains (CPA framework):

### 1. EXPLORE Domain
**Purpose**: Generate novel hypotheses, broaden search space
**Node Type**: `MetaToTNodeType.SEARCH`
**Strategy**: `ExplorationStrategy.SURPRISE_MAXIMIZATION`
**Example Branches**:
- "What if we try X?"
- "Alternative approach: Y"
- "Consider perspective Z"

### 2. CHALLENGE Domain
**Purpose**: Test robustness, find weaknesses
**Node Type**: `MetaToTNodeType.CHALLENGE`
**Strategy**: `ExplorationStrategy.UCB_PREDICTION_ERROR`
**Example Branches**:
- "What could go wrong with X?"
- "Counter-argument: Y"
- "Edge case: Z"

### 3. EVOLVE Domain
**Purpose**: Refine promising candidates
**Node Type**: `MetaToTNodeType.EVOLUTION`
**Strategy**: `ExplorationStrategy.THOMPSON_SAMPLING`
**Example Branches**:
- "Improved version of X"
- "X optimized for constraint Y"
- "Hybrid X+Z approach"

### 4. INTEGRATE Domain
**Purpose**: Synthesize into coherent solution
**Node Type**: `MetaToTNodeType.INTEGRATION`
**Strategy**: `ExplorationStrategy.FREE_ENERGY_MINIMIZATION`
**Example Branches**:
- "X integrated with existing system"
- "Unified framework combining X and Y"
- "Implementation plan for Z"

**Rotation Pattern**: `explore → challenge → evolve → integrate → explore → ...`

**Implementation**: `api/services/meta_tot_engine.py:385-392`

## Common Misconceptions

**Misconception 1**: "Meta-ToT searches all possible solutions"
**Reality**: Meta-ToT uses MCTS heuristics to explore promising branches deeply while sampling others lightly. It's guided search, not exhaustive enumeration. Time budget prevents infinite expansion.

**Misconception 2**: "The best technical solution always wins"
**Reality**: Meta-ToT optimizes for lowest free energy, which balances complexity AND accuracy. Sometimes a "good enough" simple solution beats a technically perfect but complex one.

**Misconception 3**: "Meta-ToT replaces human reasoning"
**Reality**: Meta-ToT generates candidate thoughtseeds that compete for conscious attention. Humans experience only the winner, not the search process. It augments unconscious hypothesis generation.

**Misconception 4**: "More simulations always improve results"
**Reality**: Diminishing returns after ~30-50 simulations for most problems. Time budget should balance search depth with responsiveness. Better to run Meta-ToT twice with 32 simulations than once with 100.

**Misconception 5**: "Meta-ToT is deterministic"
**Reality**: MCTS exploration includes stochastic sampling. Set `random_seed` in config for reproducibility in testing, but embrace variance in production for robustness.

## When to Use

### In Cognitive Architecture

✅ **Use Meta-ToT when**:
- Problem complexity is high (multiple viable approaches)
- Uncertainty is high (unclear which path is best)
- Stakes are high (costly to commit to wrong hypothesis)
- Need systematic exploration (avoid premature optimization)
- Want traceability (audit reasoning path)

❌ **Don't use when**:
- Simple problems with obvious solutions (overhead not justified)
- Time-critical decisions (use fast heuristics instead)
- Single viable option (no competition needed)
- Reflex behaviors (pattern-matching sufficient)

### Threshold Decision Logic

**File**: `specs/041-meta-tot-engine/spec.md:26-37`

Meta-ToT should activate only when **complexity OR uncertainty** exceeds threshold:

```python
def should_use_meta_tot(problem: str, context: Dict[str, Any]) -> bool:
    """Threshold decision for Meta-ToT activation."""
    complexity_score = estimate_complexity(problem, context)
    uncertainty_score = estimate_uncertainty(problem, context)

    # Thresholds (configurable)
    COMPLEXITY_THRESHOLD = 0.6   # 0-1 scale
    UNCERTAINTY_THRESHOLD = 0.7  # 0-1 scale

    return (complexity_score > COMPLEXITY_THRESHOLD or
            uncertainty_score > UNCERTAINTY_THRESHOLD)
```

**Rationale**: Preserves performance for routine tasks while enabling deep reasoning when beneficial.

### In Clinical Context (IAS)

✅ **Use to explain**:
- How insight moments arise (sudden ΔF drop in Meta-ToT search)
- Why some problems feel "stuck" (shallow basins, high F across all branches)
- How reframing works (Meta-ToT finds low-F alternative perspective)
- Why analytical empaths overthink (Meta-ToT runs continuously, deep trees)

❌ **Don't use to**:
- Force specific therapeutic conclusions (Meta-ToT explores, doesn't prescribe)
- Bypass emotional processing (cognition complements, doesn't replace affect)
- Pathologize normal deliberation (Meta-ToT is healthy metacognition)

### Implementation Guidance

**When implementing Meta-ToT**:

1. **Configure appropriately**: Start with defaults, tune based on problem domain
2. **Enable tracing**: Always persist traces in development/testing
3. **Monitor performance**: Track simulation count, time budget usage, branch quality
4. **Integrate with EFE**: Use precision weighting for exploration/exploitation balance
5. **Route to basins**: Store selected paths for long-term learning
6. **Handle failures**: Fallback to simpler reasoning if Meta-ToT errors

**Key implementation files**:
- MCTS core: `api/services/meta_tot_engine.py:129-314`
- UCB1 scoring: `api/services/meta_tot_engine.py:53-61`
- Active inference: `api/models/meta_tot.py:15-44`
- EFE integration: `api/services/efe_engine.py:61-84`
- Configuration: `api/services/meta_tot_engine.py:74-93`

## Computational Complexity

**Time Complexity**: O(b^d * s)
- `b` = branching factor (default: 3)
- `d` = max depth (default: 4)
- `s` = simulations (default: 32)
- Total nodes: ~3^4 = 81 nodes
- Total rollouts: 32 simulations
- **Typical runtime**: 2-5 seconds

**Space Complexity**: O(b^d)
- Stores all nodes in `node_storage` dictionary
- Trace payload: ~100-500 KB per run
- Manageable for depth ≤ 6

**Optimization Strategies**:
- Time budget prevents runaway search
- Branching factor limits exponential growth
- LLM candidate generation cached
- Pruning: Nodes with F > 5.0 not expanded further

## Further Reading

**Research Foundation**:
- Silver, D. et al. (2016). "Mastering the game of Go with deep neural networks and tree search." *Nature*
- Browne, C. et al. (2012). "A Survey of Monte Carlo Tree Search Methods." *IEEE Transactions on Computational Intelligence and AI in Games*
- Yao, S. et al. (2023). "Tree of Thoughts: Deliberate Problem Solving with Large Language Models." *arXiv*
- Friston, K. (2010). "The free-energy principle: a unified brain theory?" *Nature Reviews Neuroscience*

**Implementation Documentation**:
- [[specs/041-meta-tot-engine/spec.md]] - Original specification
- [[specs/041-meta-tot-engine/plan.md]] - Implementation plan
- [[specs/041-meta-tot-engine/tasks.md]] - Task breakdown
- [[specs/038-thoughtseeds-framework/]] - Thoughtseed integration context

**Related Silver Bullets**:
- [04-smolagents-metatot-skills-integration.md](../04-smolagents-metatot-skills-integration.md) - Agent architecture integration
- [05-thoughtseed-competition-explained.md](../05-thoughtseed-competition-explained.md) - Competition mechanism

**Interactive Resources**:
- [../visualizations/thoughtseed-competition.html](../visualizations/thoughtseed-competition.html) - Competition simulation (includes Meta-ToT output)

---

**Last Updated**: 2026-01-02
**Author**: Dr. Mani Saint-Victor, MD
**Maintainer**: Documentation Agent-13
**Status**: Production
