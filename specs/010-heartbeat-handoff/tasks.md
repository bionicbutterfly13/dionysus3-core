# Tasks: Heartbeat Agent Handoff

**Input**: Design documents from `/specs/010-heartbeat-handoff/`
**Prerequisites**: spec.md (required)

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Verify `smolagents` and `mcp` connectivity in the environment
- [ ] T002 Configure agent prompt templates in `api/agents/heartbeat_agent.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T003 Implement `ContextBuilder` to gather Energy, Goals, and Trajectories into a single JSON snapshot
- [ ] T004 Update `HeartbeatAgent` to load tools via `ToolCollection.from_mcp`

---

## Phase 3: User Story 1 - Autonomous OODA Execution (Priority: P1) 🎯 MVP

**Goal**: Full delegation of decision logic to smolagents.

**Independent Test**: Trigger manual heartbeat, verify tool usage in logs.

### Implementation for User Story 1

- [ ] T005 Refactor `HeartbeatService._make_decision` to call `HeartbeatAgent.decide()`
- [ ] T006 DELETE legacy `_make_default_decision` and `_make_decision` procedural code
- [ ] T007 Implement `_execute_agent_plan` to process tool outputs back into system state
- [ ] T008 Move hardcoded model IDs to environment variable config in all agents

---

## Phase 4: User Story 2 - Trajectory-Aware Reasoning (Priority: P2)

**Goal**: Agent reasons over recent experiences.

### Implementation for User Story 2

- [ ] T008 Add `get_unconsumed_trajectories` to `MemEvolveAdapter`
- [ ] T009 Update `ContextBuilder` to include unconsumed trajectories
- [ ] T010 Implement trajectory "marking" (processed_at) after agent reasoning
- [ ] T011 [P] Implement transactional 'read-and-lock' for trajectories to prevent race conditions between heartbeat cycles

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T011 Update `ARCHITECTURE.md` to reflect agentic handoff
- [ ] T012 Add performance monitoring for agent cycle time