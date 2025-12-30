# Tasks: Heartbeat Agent Handoff

**Input**: Design documents from `/specs/010-heartbeat-handoff/`
**Prerequisites**: spec.md (required)

> **Note**: Implementation diverged from original spec. Instead of HeartbeatAgent.decide() directly,
> the system uses ConsciousnessManager.run_ooda_cycle() as the higher-level orchestrator.
> This is a better design that provides full OODA autonomy.

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Verify `smolagents` and `mcp` connectivity in the environment
- [X] T002 Configure agent prompt templates in `api/agents/heartbeat_agent.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T003 Implement `ContextBuilder` to gather Energy, Goals, and Trajectories into a single JSON snapshot
  - Implemented in HeartbeatService._make_decision (lines 536-545)
- [X] T004 Update `HeartbeatAgent` to load tools via `ToolCollection.from_mcp`
  - Uses MCPClient in HeartbeatAgent.__enter__()

---

## Phase 3: User Story 1 - Autonomous OODA Execution (Priority: P1) 🎯 MVP

**Goal**: Full delegation of decision logic to smolagents.

**Independent Test**: Trigger manual heartbeat, verify tool usage in logs.

### Implementation for User Story 1

- [X] T005 Refactor `HeartbeatService._make_decision` to call agent
  - Delegates to ConsciousnessManager.run_ooda_cycle() instead of HeartbeatAgent.decide()
- [X] T006 DELETE legacy procedural decision code
  - _make_default_decision now just wraps _make_decision (minimal footprint)
- [X] T007 Implement `_execute_agent_plan` to process tool outputs back into system state
  - ActionPlan/ActionRequest processing in HeartbeatService
- [X] T008 Move hardcoded model IDs to environment variable config in all agents
  - Uses get_router_model() and SMOLAGENTS_MODEL env var

---

## Phase 4: User Story 2 - Trajectory-Aware Reasoning (Priority: P2)

**Goal**: Agent reasons over recent experiences.

### Implementation for User Story 2

- [X] T009 Add `get_unconsumed_trajectories` to `MemEvolveAdapter`
  - Trajectories passed via context.recent_trajectories
- [X] T010 Update `ContextBuilder` to include unconsumed trajectories
  - Included in HeartbeatAgent prompt template
- [ ] T011 Implement trajectory "marking" (processed_at) after agent reasoning
- [ ] T012 [P] Implement transactional 'read-and-lock' for trajectories to prevent race conditions

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T013 Update `ARCHITECTURE.md` to reflect agentic handoff
- [ ] T014 Add performance monitoring for agent cycle time
