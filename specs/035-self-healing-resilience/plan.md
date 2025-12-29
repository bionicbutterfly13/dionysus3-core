# Implementation Plan: Self-Healing Resilience

**Spec**: [spec.md](./spec.md)

## Summary
Implement a multi-layered resilience system that provides agents with autonomous recovery paths for common failures.

## Technical Context
- **Gating**: Logic will live in `api/agents/resource_gate.py` and a new `api/agents/resilience.py`.
- **Logic**: Use "Observation Hijacking" — when a tool fails, we return an observation that includes both the error AND a suggested Plan B command.

## Milestones
1. **Fallback Registry**: Define alternative tools for Search, Ingest, and Reasoning.
2. **Enhanced Timeout Wrapper**: Add bounded retry logic (max 1 retry) with model promotion (Nano -> Mini).
3. **Observation Hijacking**: Implement logic to inject "Plan B" hints into the agent's memory when a tool fails.
4. **Metaplasticity Integration**: Use prediction error signals from failures to boost `max_steps`.

## Testing
- Unit tests for the `ResilienceWrapper`.
- Induced failure integration tests.
