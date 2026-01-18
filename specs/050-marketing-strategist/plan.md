# Implementation Plan: Marketing Strategist Agent (Feature 050)

## Phase 1: Agent Definition
- [ ] **Step 1**: Create `api/agents/marketing_strategist.py` defining the `CodeAgent`.
- [ ] **Step 2**: Add specialized prompt engineering for the "[LEGACY_AVATAR_HOLDER]" mirror tone.

## Phase 2: Marketing Tools
- [ ] **Step 3**: Create `api/agents/tools/marketing_tools.py`.
- [ ] **Step 4**: Implement `get_marketing_framework` – retrieves templates from `/Volumes/Asylum/dev/email-sequence/`.
- [ ] **Step 5**: Implement `get_avatar_intel` – performs a targeted search in the Knowledge Graph for avatar-specific pain points.

## Phase 3: Manager Integration
- [ ] **Step 6**: Create `api/agents/managed/marketing.py` with the `ManagedMarketingStrategist` wrapper.
- [ ] **Step 7**: Update `api/agents/consciousness_manager.py` to initialize and register the agent.

## Phase 4: Verification
- [ ] **Step 8**: Create `tests/integration/test_marketing_agent.py`.
- [ ] **Step 9**: Verify OODA cycle delegation to the marketing strategist.

## Phase 5: Production
- [ ] **Step 10**: Draft the final New Year email and Substack article using the new agent.
