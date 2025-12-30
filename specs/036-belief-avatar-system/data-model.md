# Data Model: Belief Avatar System

**Feature**: 036-belief-avatar-system
**Date**: 2025-12-30
**Source**: `api/models/belief_journey.py` (existing)

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BeliefJourney                                │
│  (Aggregate Root)                                                    │
│  ─────────────────                                                   │
│  id: UUID                                                            │
│  participant_id: str?                                                │
│  current_phase: IASPhase                                             │
│  current_lesson: IASLesson                                           │
│  graphiti_group_id: str?                                             │
└─────────────────────────────────────────────────────────────────────┘
         │ 1          │ 1          │ 1          │ 1          │ 0..1
         │            │            │            │            │
         ▼ *          ▼ *          ▼ *          ▼ *          ▼ 1
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Limiting    │ │ Empowering  │ │ Belief      │ │ Replay      │ │ Support     │
│ Belief      │ │ Belief      │ │ Experiment  │ │ Loop        │ │ Circle      │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
      │                │                                              │
      │                │                                              │
      ▼ *              ▼ *                                            ▼ *
┌─────────────┐ ┌─────────────┐                              ┌─────────────┐
│ MOSAEIC     │ │ Vision      │                              │ Support     │
│ Capture     │ │ Element     │                              │ Circle      │
│             │ │             │                              │ Member      │
└─────────────┘ └─────────────┘                              └─────────────┘
```

## Entity Definitions

### BeliefJourney (Aggregate Root)

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | UUID | Primary key | auto-generated |
| participant_id | str? | External identifier | optional |
| current_phase | IASPhase | REVELATION/REPATTERNING/STABILIZATION | enum |
| current_lesson | IASLesson | 1-9 lessons | enum |
| lessons_completed | List[IASLesson] | Progress tracking | list |
| limiting_beliefs | List[LimitingBelief] | Child collection | embedded |
| empowering_beliefs | List[EmpoweringBelief] | Child collection | embedded |
| experiments | List[BeliefExperiment] | Child collection | embedded |
| replay_loops | List[ReplayLoop] | Child collection | embedded |
| mosaeic_captures | List[MOSAEICCapture] | Child collection | embedded |
| vision_elements | List[VisionElement] | Child collection | embedded |
| support_circle | SupportCircle? | Single child | embedded |
| total_experiments_run | int | Counter | ≥0 |
| beliefs_dissolved | int | Counter | ≥0 |
| beliefs_embodied | int | Counter | ≥0 |
| replay_loops_resolved | int | Counter | ≥0 |
| started_at | datetime | Creation timestamp | auto |
| last_activity_at | datetime | Update timestamp | auto |
| graphiti_group_id | str? | Neo4j episode group | optional |

### LimitingBelief

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | UUID | Primary key | auto-generated |
| journey_id | UUID | Parent reference | required |
| content | str | Belief statement | required |
| pattern_name | str? | Named pattern | optional |
| origin_memory | str? | Source memory | optional |
| origin_lesson | IASLesson? | When identified | optional |
| evidence_for | List[str] | Supporting evidence | list |
| evidence_against | List[str] | Counter evidence | list |
| self_talk | List[str] | Internal dialogue | list |
| mental_blocks | List[str] | Created blocks | list |
| self_sabotage_behaviors | List[str] | Driven behaviors | list |
| protects_from | str? | Emotional protection | optional |
| strength | float | 0.0-1.0 belief strength | 0.0 ≤ x ≤ 1.0 |
| status | BeliefStatus | IDENTIFIED→DISSOLVED | enum |
| blocks_desires | List[str] | Blocked desires | list |
| triggers_replay_loops | List[UUID] | Linked loops | references |
| replaced_by | UUID? | Empowering belief | optional |
| identified_at | datetime | Creation | auto |
| dissolved_at | datetime? | Completion | optional |

### EmpoweringBelief

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | UUID | Primary key | auto-generated |
| journey_id | UUID | Parent reference | required |
| content | str | Belief statement | required |
| bridge_version | str? | Softer version | optional |
| replaces_belief_id | UUID? | Limiting belief replaced | optional |
| experiments_run | List[UUID] | Testing experiments | references |
| evidence_collected | List[str] | Supporting evidence | list |
| embodiment_level | float | 0.0-1.0 integration | 0.0 ≤ x ≤ 1.0 |
| status | EmpoweringBeliefStatus | PROPOSED→EMBODIED | enum |
| habit_stack | str? | Daily habit link | optional |
| daily_checklist_items | List[str] | Behavior list | list |
| proposed_at | datetime | Creation | auto |
| first_tested_at | datetime? | First experiment | optional |
| embodied_at | datetime? | Full integration | optional |

### BeliefExperiment

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | UUID | Primary key | auto-generated |
| journey_id | UUID | Parent reference | required |
| limiting_belief_id | UUID? | Belief tested | optional |
| empowering_belief_id | UUID? | Belief tested | optional |
| hypothesis | str | Expected finding | required |
| action_taken | str | Behavior tried | required |
| context | str | Stakes level | low/mid/high |
| outcome | ExperimentOutcome? | Result type | enum |
| actual_result | str? | What happened | optional |
| emotional_response | str? | Feelings | optional |
| belief_shift_observed | str? | Shift noted | optional |
| limiting_belief_strength_before | float? | Pre-test | 0.0-1.0 |
| limiting_belief_strength_after | float? | Post-test | 0.0-1.0 |
| empowering_belief_strength_before | float? | Pre-test | 0.0-1.0 |
| empowering_belief_strength_after | float? | Post-test | 0.0-1.0 |
| designed_at | datetime | Creation | auto |
| executed_at | datetime? | Completion | optional |

### ReplayLoop

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | UUID | Primary key | auto-generated |
| journey_id | UUID | Parent reference | required |
| trigger_situation | str | What triggers | required |
| pattern_name | str? | Named pattern | optional |
| story_text | str | The story | required |
| story_snapshot | str? | One sentence | optional |
| emotion | str | Primary emotion | required |
| fear_underneath | str | Driving fear | required |
| compassionate_reflection | str? | Self-compassion | optional |
| lesson_found | str? | Extracted lesson | optional |
| comfort_offered | str? | Self-comfort | optional |
| next_step_taken | str? | Action taken | optional |
| status | ReplayLoopStatus | ACTIVE→RESOLVED | enum |
| occurrence_count | int | Times occurred | ≥1 |
| time_to_resolution_minutes | float? | Resolution time | optional |
| fed_by_belief_id | UUID? | Linked belief | optional |
| first_identified_at | datetime | Creation | auto |
| resolved_at | datetime? | Resolution | optional |

### MOSAEICCapture

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | UUID | Primary key | auto-generated |
| journey_id | UUID | Parent reference | required |
| high_pressure_context | str | Situation | required |
| timestamp | datetime | Capture time | auto |
| sensations | List[str] | Physical | list |
| actions | List[str] | Behaviors | list |
| emotions | List[str] | Feelings | list |
| impulses | List[str] | Urges | list |
| cognitions | List[str] | Thoughts | list |
| narrative_identified | str? | Story spotted | optional |
| connects_to_belief_id | UUID? | Linked belief | optional |

### VisionElement

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | UUID | Primary key | auto-generated |
| journey_id | UUID | Parent reference | required |
| description | str | Vision described | required |
| category | str | Domain | career/creative/... |
| values_aligned | List[str] | Values fulfilled | list |
| status | str | Progression | dream/pilot/active/achieved |
| first_step | str? | Next action | optional |
| requires_dissolution_of | List[UUID] | Blocking beliefs | references |
| envisioned_at | datetime | Creation | auto |
| achieved_at | datetime? | Completion | optional |

### SupportCircle

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | UUID | Primary key | auto-generated |
| journey_id | UUID | Parent reference | required |
| members | List[SupportCircleMember] | Circle members | embedded |
| total_members | int | Count | ≥0 |
| active_members | int | Active count | ≥0 |
| created_at | datetime | Creation | auto |

### SupportCircleMember

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| role | str | Member type | mentor/peer/mentee |
| name | str? | Identifier | optional |
| relationship_quality | float | 0.0-1.0 | 0.0 ≤ x ≤ 1.0 |
| check_in_frequency | str | Contact rate | weekly/biweekly/monthly/quarterly |
| last_contact | datetime? | Last touch | optional |
| value_provided | str? | Relationship value | optional |

## State Transitions

### BeliefStatus (LimitingBelief)

```
IDENTIFIED → MAPPED → TESTED → DISSOLVING → DISSOLVED
     │                    │
     └────────────────────┘ (can skip intermediate states)
```

### EmpoweringBeliefStatus

```
PROPOSED → TESTING → STRENGTHENING → EMBODIED
    │                      │
    └──────────────────────┘ (embodiment_level thresholds)
```

Thresholds:
- PROPOSED → TESTING: embodiment_level ≥ 0.3
- TESTING → STRENGTHENING: embodiment_level ≥ 0.6
- STRENGTHENING → EMBODIED: embodiment_level ≥ 0.85

### ReplayLoopStatus

```
ACTIVE → INTERRUPTED → RESOLVED
    │                     │
    │         DORMANT ────┘ (may resurface)
    └─────────┘
```

### IASPhase

```
REVELATION → REPATTERNING → STABILIZATION
(Lessons 1-3)  (Lessons 4-6)  (Lessons 7-9)
```

## Indexes (Neo4j via Graphiti)

- `journey_id` on all child entities (lookup by journey)
- `status` on LimitingBelief, EmpoweringBelief, ReplayLoop (filter by status)
- `graphiti_group_id` on BeliefJourney (episode correlation)
