# Tasks: Heartbeat Agent Handoff

**Input**: Design documents from `/specs/010-heartbeat-handoff/`
**Prerequisites**: spec.md (required)

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Verify `smolagents` and `mcp` connectivity in the environment ✅ (verified in consolidation)
- [x] T002 Configure agent prompt templates in `api/agents/heartbeat_agent.py` ✅ (updated with trajectories)

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T003 Implement `ContextBuilder` to gather Energy, Goals, and Trajectories into a single JSON snapshot ✅ (already existed, verified)
- [x] T004 Update `HeartbeatAgent` to load tools via `ToolCollection.from_mcp` ✅ (already implemented)

---

## Phase 3: User Story 1 - Autonomous OODA Execution (Priority: P1) 🎯 MVP

**Goal**: Full delegation of decision logic to smolagents.

**Independent Test**: Trigger manual heartbeat, verify tool usage in logs.

### Implementation for User Story 1

- [x] T005 Refactor `HeartbeatService._make_decision` to call `HeartbeatAgent.decide()` ✅ (via AgentDecisionAdapter)
- [x] T006 DELETE legacy `_make_default_decision` and `_make_decision` procedural code ✅ (removed)
- [ ] T007 Implement `_execute_agent_plan` to process tool outputs back into system state
- [x] T008 Move hardcoded model IDs to environment variable config in all agents ✅ (SMOLAGENTS_MODEL env var)

---

## Phase 4: User Story 2 - Trajectory-Aware Reasoning (Priority: P2)

**Goal**: Agent reasons over recent experiences.

### Implementation for User Story 2

- [x] T008 Add `get_unconsumed_trajectories` to `MemEvolveAdapter` ✅ (already in ContextBuilder)
- [x] T009 Update `ContextBuilder` to include unconsumed trajectories ✅ (added to _context_to_dict)
- [ ] T010 Implement trajectory "marking" (processed_at) after agent reasoning
- [ ] T011 [P] Implement transactional 'read-and-lock' for trajectories to prevent race conditions between heartbeat cycles

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T011 Update `ARCHITECTURE.md` to reflect agentic handoff
- [ ] T012 Add performance monitoring for agent cycle time