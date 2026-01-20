# Plan: Track 069 - VPS Gateway Enforcement

**Status**: In Progress

## Phase 1: Gateway Enforcement

- [x] **Task 1.1**: Enforce a single VPS communication gateway. (0cc56f7)
  - Add a VpsGateway client that validates allowed hosts and centralizes HTTP calls.
  - Update RemoteSyncService and AgentAuditCallback to use the gateway.
  - Add unit tests that fail if non-allowed hosts are used or direct VPS calls bypass the gateway.
