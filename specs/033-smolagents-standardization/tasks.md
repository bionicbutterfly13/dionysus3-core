# Tasks: Smolagents Standardization & Hardening

**Input**: spec.md, sleepy-yawning-bear.md
**Status**: In-Progress

## Phase 0: Infrastructure & Scaffolding
- [x] T001 Mount Docker socket in `docker-compose.yml`
- [x] T002 Create `Dockerfile.agent-sandbox` (Alpine + Numerical libs)
- [x] T003 Create `api/agents/resource_gate.py` (Semaphores + Timeout helper)

## Phase 1: Tier 0 Security Hardening
- [x] T004 Remove `trust_remote_code=True` from `HeartbeatAgent`
- [ ] T005 Implement `run_agent_with_timeout` in `HeartbeatAgent`
- [ ] T006 Refactor `ConsciousnessManager` to use Docker sandbox
- [ ] T007 Refactor `KnowledgeAgent` to use Docker sandbox
- [ ] T008 Refactor `AvatarResearcher` to use Docker sandbox

## Phase 2: Tier 1 Architecture Migration (Leaf Agents)
- [ ] T009 Migrate `PerceptionAgent` to `ToolCallingAgent`
- [ ] T010 Migrate `ReasoningAgent` to `ToolCallingAgent`
- [ ] T011 Migrate `MetacognitionAgent` to `ToolCallingAgent`
- [ ] T012 Migrate `MarketingAgent` to `ToolCallingAgent`
- [ ] T013 Migrate `PainAnalyst` to `ToolCallingAgent`
- [ ] T014 Migrate `ObjectionHandler` to `ToolCallingAgent`
- [ ] T015 Migrate `VoiceExtractor` to `ToolCallingAgent`

## Phase 3: Tier 2 Observability
- [x] T016 Implement `AgentAuditCallback` for n8n webhooks
- [x] T017 Implement `AgentMemoryService` for Neo4j trajectory persistence
- [x] T018 Wire token usage tracking into all agents

## Phase 4: Tier 3 Reliability
- [x] T019 Implement `LiteLLMRouterModel` (Nano -> Mini -> Ollama)
- [x] T020 Remove `nest_asyncio` from all tools (Thread-per-tool pattern)
- [x] T021 Add planning intervals to `ConsciousnessManager`

## Phase 5: Tier 4 Tool Improvements
- [ ] T022 Add Pydantic output validation to all tools
- [ ] T023 Convert `Graphiti` and `Rollback` tools to Class-based tools
