# Feature 055: Developmental Mastery Validation

## Status: Draft

## Problem Statement

The current developmental construction implementation in `BiologicalAgencyService` has a critical flaw: **it pretends to validate capability mastery but actually doesn't.**

### What Doesn't Work But Pretends To

From `_get_mastered_capabilities()`:

```python
def _get_mastered_capabilities(self, agent: BiologicalAgentState) -> set:
    mastered = set()
    # Add capabilities from all stages up to current
    for stage in self._developmental_sequence[:agent.developmental_stage]:
        mastered.update(stage.capabilities_unlocked)
    return mastered
```

**The Problem**: This creates a circular dependency:
1. Agent reaches stage N → unlocks capabilities {A, B, C}
2. `_get_mastered_capabilities()` returns {A, B, C} because agent is at stage N
3. `advance_development()` checks if {A, B, C} are mastered → they are (by definition)
4. Agent advances to N+1 without ever demonstrating competence

**Tomasello's Requirement** (2025):
> "it is necessary for each step in the sequence to be stable and adaptive in its own right, or else the species or organism perishes along the way."

The current implementation violates this principle. Unlocking a capability is not the same as mastering it.

### Missing Components

1. **Performance Metrics**: No measurement of how well an agent performs a capability
2. **Competence Thresholds**: No minimum performance required for mastery
3. **Stability Validation**: No check that performance is consistent over time
4. **Regression Detection**: No monitoring for capability degradation
5. **Context-Dependent Assessment**: No recognition that competence varies by domain

## Proposed Solution

### Mastery Validation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  DevelopmentalMasteryService                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ PerformanceTracker  │  │ MasteryValidator    │              │
│  ├─────────────────────┤  ├─────────────────────┤              │
│  │ - Record attempts   │  │ - Check thresholds  │              │
│  │ - Calculate metrics │  │ - Validate stability│              │
│  │ - Detect regression │  │ - Context weighting │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    CapabilityAssessment                     ││
│  ├─────────────────────────────────────────────────────────────┤│
│  │ capability_id: str                                          ││
│  │ attempt_count: int                                          ││
│  │ success_rate: float      # 0.0 - 1.0                        ││
│  │ recent_performance: List[float]  # sliding window           ││
│  │ stability_score: float   # variance-based                   ││
│  │ mastery_status: MasteryStatus  # unlocked/developing/mastered││
│  │ context_scores: Dict[str, float]  # domain-specific         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Mastery Status Enum

```python
class MasteryStatus(str, Enum):
    UNLOCKED = "unlocked"      # Capability available but not yet attempted
    DEVELOPING = "developing"  # Some attempts, performance improving
    MASTERED = "mastered"      # Meets threshold consistently
    REGRESSING = "regressing"  # Was mastered, performance declining
    BLOCKED = "blocked"        # Prerequisites not met
```

### Mastery Criteria

For a capability to be considered "mastered":

1. **Minimum Attempts**: At least N attempts recorded (default: 5)
2. **Success Rate**: Success rate ≥ threshold (default: 0.8)
3. **Stability**: Performance variance ≤ threshold (default: 0.1)
4. **Recency**: Recent performance matches historical (no regression)

### Integration with Developmental Construction

```python
def advance_development(self, agent_id: str) -> Optional[DevelopmentalStage]:
    agent = self._ensure_agent(agent_id)
    next_stage = self._get_next_stage(agent)
    
    if not next_stage:
        return None
    
    # NEW: Validate actual mastery, not just stage membership
    mastery_service = get_developmental_mastery_service()
    
    for prereq in next_stage.prerequisites:
        assessment = mastery_service.get_capability_assessment(agent_id, prereq)
        
        if assessment.mastery_status != MasteryStatus.MASTERED:
            logger.info(
                f"Agent {agent_id} cannot advance: "
                f"{prereq} status is {assessment.mastery_status.value} "
                f"(success_rate={assessment.success_rate:.2f}, "
                f"stability={assessment.stability_score:.2f})"
            )
            return None
    
    # Advance only when all prerequisites truly mastered
    agent.developmental_stage = next_stage.stage_number
    return next_stage
```

### Recording Capability Attempts

```python
async def record_capability_attempt(
    self,
    agent_id: str,
    capability_id: str,
    success: bool,
    context: str = "default",
    metrics: Optional[Dict[str, float]] = None
) -> CapabilityAssessment:
    """
    Record an attempt to use a capability and update mastery status.
    
    This should be called after every decision/action that exercises
    a specific capability. For example:
    
    - After a go/no-go decision → record "go_no_go_decisions"
    - After inhibiting a response → record "inhibit_prepotent_responses"
    - After revising a belief → record "revise_beliefs"
    """
```

### Stability Calculation

```python
def _calculate_stability(self, recent_performance: List[float]) -> float:
    """
    Calculate stability score based on performance variance.
    
    Stable performance (low variance) → high stability score
    Erratic performance (high variance) → low stability score
    
    Uses coefficient of variation (CV) normalized to [0, 1]:
    stability = 1 - min(1.0, CV)
    """
    if len(recent_performance) < 3:
        return 0.0  # Not enough data for stability assessment
    
    mean = sum(recent_performance) / len(recent_performance)
    if mean == 0:
        return 0.0
    
    variance = sum((x - mean) ** 2 for x in recent_performance) / len(recent_performance)
    std_dev = variance ** 0.5
    cv = std_dev / mean
    
    return max(0.0, 1.0 - min(1.0, cv))
```

### Regression Detection

```python
def _detect_regression(
    self,
    assessment: CapabilityAssessment,
    new_performance: float
) -> bool:
    """
    Detect if an agent is regressing on a mastered capability.
    
    Regression occurs when:
    1. Capability was previously MASTERED
    2. Recent performance drops significantly below historical
    
    This triggers REGRESSING status and may block further advancement.
    """
    if assessment.mastery_status != MasteryStatus.MASTERED:
        return False
    
    # Compare recent window to historical average
    historical_mean = sum(assessment.recent_performance) / len(assessment.recent_performance)
    regression_threshold = 0.7  # Drop below 70% of historical
    
    return new_performance < historical_mean * regression_threshold
```

## Acceptance Criteria

- [ ] `DevelopmentalMasteryService` tracks capability attempts and performance
- [ ] `CapabilityAssessment` model with success rate, stability, mastery status
- [ ] `MasteryStatus` enum with lifecycle states
- [ ] `advance_development()` validates actual mastery before progression
- [ ] Regression detection flags capability degradation
- [ ] Context-dependent scoring for domain-specific competence
- [ ] Integration with existing `BiologicalAgencyService`
- [ ] Sliding window for recent performance (configurable size)
- [ ] Configurable thresholds for mastery criteria
- [ ] Unit tests for mastery validation logic
- [ ] Integration tests for developmental progression with real data

## Non-Goals

- Machine learning-based capability prediction
- Automatic capability curriculum design
- Cross-agent competence comparison

## Configuration

```python
class MasteryConfig(BaseModel):
    min_attempts: int = 5
    success_rate_threshold: float = 0.8
    stability_threshold: float = 0.7
    recent_window_size: int = 10
    regression_threshold: float = 0.7
```

## Dependencies

- `api/models/biological_agency.py` - `DevelopmentalStage`, `BiologicalAgentState`
- `api/services/biological_agency_service.py` - Integration point

## Migration Path

1. Create `DevelopmentalMasteryService` with new models
2. Instrument existing decision points to record capability attempts
3. Run in "shadow mode" - track mastery but don't block advancement
4. Analyze data to tune thresholds
5. Enable blocking mode with validated thresholds

## References

- Tomasello, M. (2025). How to make artificial agents more like natural agents. *Trends in Cognitive Sciences*.
- Tomasello, M. (2024). *Agency and Cognitive Development*. Oxford University Press.
- Skill acquisition and expertise literature (Ericsson, Anderson)
