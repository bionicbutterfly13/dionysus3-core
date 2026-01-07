# Biological Agency Architecture

## Overview

Biological agency architecture implements Tomasello's evolutionary account of agentive organization, providing a three-tier control systems model for natural agents.

## Core Concept

From Tomasello (2025):

> "biological organisms have evolved as decision-making agents to interact with and modify their environments, which requires an integrated organizational architecture that unifies (i) goals, (ii) attention/cognition, and (iii) behavioral decision making into a control system."

The architecture distinguishes between three evolutionary tiers of agency, each adding new capabilities while preserving the foundation of the previous tier.

## The Three Tiers

### Tier 1: Goal-Directed Agents

**Evolutionary model**: Lizard-like organisms facing unpredictable prey capture.

**Capabilities**:
- Perception-based goal representations
- Go/no-go behavioral decisions
- Basic feedback loop (perceive → decide → act)

**Decision type**: Binary - either act or don't act.

```python
# Example Tier 1 decision
decision = service.process_tier1_decision(
    agent_id="agent-1",
    perception=PerceptionState(
        affordances=["approach_food"],
        obstacles=[]
    ),
    goals=GoalState(active_goals=["acquire_food"])
)
# Result: GO or NO-GO
```

### Tier 2: Intentional Agents

**Evolutionary model**: Mammal-like organisms facing social competition.

**Capabilities** (builds on Tier 1):
- Executive self-regulation (additional control system tier)
- Inhibit prepotent responses
- Resist attention distractors
- Simulate potential actions and outcomes
- Either/or decision-making

**Decision type**: Select from simulated alternatives.

```python
# Example Tier 2 decision with simulation
decision, executive = service.process_tier2_decision(
    agent_id="agent-1",
    perception=perception_state,
    goals=goal_state,
    alternatives=["approach_directly", "circle_around", "wait"]
)
# Executive state tracks simulation results
```

### Tier 3: Rational/Metacognitive Agents

**Evolutionary model**: Great ape-like organisms facing contest competition.

**Capabilities** (builds on Tier 2):
- Metacognitive regulation (monitors executive tier)
- Assess own competence and limitations
- Devise metacognitive strategies
- Computational rationality (effort allocation)
- Flexible belief revision
- Evaluate decision trees (not just alternatives)
- Revise decisions with new information

**Decision type**: Evaluate and select from decision paths.

```python
# Example Tier 3 decision with metacognition
decision, metacog = service.process_tier3_decision(
    agent_id="agent-1",
    perception=perception_state,
    goals=goal_state,
    decision_tree=[
        {"id": "path1", "action": "collaborate", "risk": 0.2},
        {"id": "path2", "action": "compete", "risk": 0.6}
    ]
)
# Metacognitive state tracks competence, strategies, effort
```

## Shared Agency (Human-Specific)

Beyond the three tiers, humans evolved unique forms of shared agency:

### Joint Agency

Collaborative goal pursuit with partners:
- Joint goals, decisions, and attention
- Joint commitments (prevents defection)
- Cooperative communication
- Partner reliability assessment

```python
joint = service.form_joint_agency(
    initiator_id="agent-1",
    partner_ids=["agent-2", "agent-3"],
    joint_goal="solve_complex_problem"
)
```

### Collective Agency

Cultural/institutional coordination:
- Collective goals and knowledge
- Conventions and norms
- Institutional roles
- Linguistic coordination
- Perspective-taking

```python
collective = service.create_collective_agency(
    culture_id="research_lab",
    collective_goal="advance_knowledge",
    conventions=["share_findings", "peer_review"],
    norms=["cite_sources", "replicate_results"]
)
```

## Developmental Construction

Key principle from Tomasello:

> "it is necessary for each step in the sequence to be stable and adaptive in its own right, or else the species or organism perishes along the way."

Agents progress through stages, each requiring mastery of prerequisites:

```python
# Check developmental status
status = service.get_developmental_status("agent-1")
# Returns: stage, mastered capabilities, next prerequisites

# Attempt advancement
next_stage = service.advance_development("agent-1")
# Returns new stage if prerequisites met, None otherwise
```

## Integration with Dionysus Architecture

### OODA Loop Mapping

| OODA Phase | Biological Agency Component |
|------------|----------------------------|
| OBSERVE    | PerceptionState            |
| ORIENT     | GoalState + relevance      |
| DECIDE     | Tier-appropriate decision  |
| ACT        | Selected action execution  |

```python
decision = service.integrate_ooda_cycle(
    agent_id="agent-1",
    observe_data={"situations": [...], "affordances": [...]},
    orient_analysis={"active_goals": [...], "priorities": {...}},
    decide_context={"decision_tree": [...]}
)
```

### Related Concepts

- [[procedural-metacognition]] - Tier 2/3 executive/metacognitive control
- [[ooda-loop]] - Control system decision cycle
- [[thoughtseed-competition]] - Parallel action selection
- [[attractor-basin]] - Goal state attractors

## Implementation

**Models**: `api/models/biological_agency.py`
**Service**: `api/services/biological_agency_service.py`

## References

Tomasello, M. (2025). How to make artificial agents more like natural agents. *Trends in Cognitive Sciences*, 29(9), 783-786. https://doi.org/10.1016/j.tics.2025.07.004

Tomasello, M. (2022). *The Evolution of Agency: From Lizards to Humans*. MIT Press.

Tomasello, M. (2024). *Agency and Cognitive Development*. Oxford University Press.

## See Also

- [Wu, 2023] - Movements of the Mind: attention, intention, action
- [Gershman et al., 2015] - Computational rationality
- [Call & Tomasello, 2024] - Primate Cognition (2nd ed.)
