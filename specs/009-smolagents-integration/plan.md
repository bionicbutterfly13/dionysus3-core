# Implementation Plan: Smolagents Integration

**Status**: In Progress
**Project**: Smolagents Integration
**Associated Spec**: [spec.md](./spec.md)

## Phase 1: Foundation (COMPLETED)
- [x] **Setup Environment**: Add dependencies to `pyproject.toml`.
- [x] **Core Tools**: Port Recall, Reflect, Synthesize, and Energy handlers to `smolagents` Tools.
- [x] **PoC Agent**: Create `HeartbeatAgent` and verify with `gpt-5-nano`.
- [x] **MCP Bridge**: Verify `ToolCollection.from_mcp()` functionality.

## Phase 2: Multi-Agent Consciousness (NEXT)
- [ ] **Design Specialized Agents**:
    - `perception_agent`: Focus on raw observation and memory recall.
    - `reasoning_agent`: Focus on synthesis and goal analysis.
    - `metacognition_agent`: Focus on self-reflection and model revision.
- [ ] **Implement Orchestrator**: Create `ConsciousnessManager` to coordinate the OODA loop via the specialized agents.
- [ ] **ThoughtSeed Mapping**: Link agent outputs to the 5-layer hierarchy.

## Phase 3: Integration & Hardening
- [ ] **Heartbeat Hook**: Replace legacy `_make_decision` in `HeartbeatService` with the new agent.
- [ ] **Resilience**: Implement circuit breakers and more robust local caching for all tools.
- [ ] **Observability**: Add logging for agent reasoning traces.

## Phase 4: Production (Future)
- [ ] **Sandboxing**: Implement E2B/Blaxel for production-safe code execution.
- [ ] **Hub Publishing**: Push Dionysus tool collection to Hugging Face Hub.

## Verification Tasks
- [ ] Run `scripts/test_heartbeat_agent.py`.
- [ ] Run `scripts/test_mcp_bridge.py`.
- [ ] New: Create `scripts/test_multi_agent.py` to verify Phase 2.