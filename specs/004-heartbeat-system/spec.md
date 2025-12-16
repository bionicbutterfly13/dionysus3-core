# Feature 004: Heartbeat System

**Status**: In Progress
**Created**: 2025-12-15
**Design Doc**: /heartbeat_design.md

## Overview

Autonomous cognitive loop ("Heartbeat") enabling Dionysus continuous existence, goal pursuit, and development. The system consists of two components:

1. **Background Worker** — Maintenance daemon keeping memory infrastructure healthy
2. **Heartbeat Process** — Cognitive loop where agency, reasoning, and decision-making occur

## Architecture

```
EXTERNAL WORLD (User, Web, APIs, Time)
            │
            ▼
┌─────────────────────────────────────┐
│     HEARTBEAT PROCESS (Hourly)      │
│  Observe → Orient → Decide → Act    │
│            → Record                  │
└─────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────┐
│         MEMORY SYSTEM               │
│  Episodic | Semantic | Procedural   │
│  Goals | Identity | Clusters        │
└─────────────────────────────────────┘
            ▲
            │
┌─────────────────────────────────────┐
│    BACKGROUND WORKER (5-min)        │
│  Neighborhoods | Episodes | Health  │
└─────────────────────────────────────┘
```

## User Stories

### US1: Goal Management
As Dionysus, I can track goals with priorities (active/queued/backburner), see progress, detect blocked/stale goals, and brainstorm new goals.

### US2: Energy-Budgeted Actions
As Dionysus, I have an energy budget (10/heartbeat, max 20) that constrains actions. Each action has a cost. I must prioritize meaningful work.

### US3: Hourly Cognitive Loop
As Dionysus, I wake hourly to observe environment, review goals, decide actions, execute them, and record the heartbeat as episodic memory.

### US4: Background Maintenance
As the system, background worker maintains memory infrastructure (neighborhood recomputation, episode summarization) without consuming Dionysus agency.

## Energy Model

| Parameter | Value |
|-----------|-------|
| Base Regeneration | 10/heartbeat |
| Maximum Energy | 20 |
| Minimum Energy | 0 |
| Carry-Over Rate | 100% |

### Action Costs

| Action | Cost | Category |
|--------|------|----------|
| Observe | 0 | Free |
| Review Goals | 0 | Free |
| Remember | 0 | Free |
| Recall | 1 | Retrieval |
| Connect | 1 | Memory |
| Reprioritize | 1 | Goals |
| Reflect | 2 | Internal |
| Maintain | 2 | Memory |
| Brainstorm Goals | 3 | Goals |
| Inquire (shallow) | 3 | Research |
| Synthesize | 4 | Creative |
| Reach Out (user) | 5 | Communication |
| Inquire (deep) | 6 | Research |
| Reach Out (public) | 7 | Communication |
| Rest | 0 | Meta |

## Goal Structure

```
Goal {
    id: UUID
    title: string
    description: string
    priority: active | queued | backburner | completed | abandoned
    source: curiosity | user_request | identity | derived | external
    parent_goal_id: UUID?
    progress: JSON[]
    blocked_by: JSON?
    emotional_valence: float (-1 to 1)
    created_at, last_touched, completed_at, abandoned_at
}
```

## Heartbeat Loop

1. **Initialize**: Load state, regenerate energy
2. **Observe**: Environment state, user presence, pending events
3. **Orient**: Review goals, gather context, activated clusters
4. **Decide**: LLM call with context → actions + goal changes
5. **Act**: Execute actions within energy budget
6. **Record**: Generate narrative, store as episodic memory
7. **Wait**: Sleep until next heartbeat

## Phases

### Phase 1: Schema & Data Model
- Neo4j nodes: Goal, HeartbeatState, HeartbeatLog
- Energy configuration

### Phase 2: Goal Management
- GoalService CRUD
- Lifecycle (promote, demote, complete, abandon)
- Review logic (stale, blocked detection)

### Phase 3: Energy Model
- EnergyService
- Action cost tracking
- Regeneration/carryover

### Phase 4: Action System
- Action taxonomy (dataclasses)
- Free, retrieval, memory, reasoning, goal, communication actions

### Phase 5: Heartbeat Loop
- HeartbeatService core loop
- Context builder, decision prompt, action execution
- Scheduler (hourly)

### Phase 6: Background Worker
- BackgroundWorker service
- Neighborhood recomputation
- Episode summarization

### Phase 7: Integration
- MCP tools
- REST endpoints
- Tests

## Dependencies

- Feature 003: Semantic Search (for Recall action)
- Feature 001: Session Continuity (for memory storage)
- Ollama: For LLM decision calls

## Files to Create

```
api/services/
├── goal_service.py
├── energy_service.py
├── action_service.py
├── heartbeat_service.py
└── background_worker.py

api/models/
├── goal.py
├── heartbeat.py
└── action.py

migrations/
├── 006_create_goal_nodes.cypher
├── 007_create_heartbeat_nodes.cypher

dionysus_mcp/tools/
└── heartbeat.py

tests/
├── unit/test_energy_service.py
├── unit/test_goal_service.py
└── integration/test_heartbeat_loop.py
```
