# Operational Checklist: Checklist-Driven Surgeon

**Purpose**: Verification of the 'Surgeon' cognitive protocol.
**Created**: 2025-12-31
**Feature**: `/specs/047-checklist-driven-surgeon/spec.md`

## Tool Verification

- [x] CHK001 `understand_question` returns a structured breakdown.
- [x] CHK002 `recall_related` provides relevant analogous examples.
- [x] CHK003 `examine_answer` identifies potential reasoning flaws.
- [x] CHK004 `backtracking` proposes a viable path forward after failure.

## Integration Verification

- [x] CHK005 `ReasoningAgent` includes all four tools in its registry.
- [x] CHK006 `ConsciousnessManager` explicitly prompts for the 'Surgeon' protocol.
- [x] CHK007 `ConsciousnessIntegrationPipeline` captures tool usage events.

## Narrative Verification

- [ ] CHK008 Agent OODA logs contain phrases like "Following surgeon protocol..." or "Performing final verification count...".
- [ ] CHK009 System accurately escalating to backtracking when a critique finds flaws.

## Notes

- The protocol is active by default for all high-entropy tasks.
- Metrics for reduction in hallucination rates are tracked via `api/monitoring`.
