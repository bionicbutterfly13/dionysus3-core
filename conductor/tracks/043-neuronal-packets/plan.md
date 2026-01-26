# Track 043: Neuronal Packets Integration

**Goal**: Reify the "Neuronal Packet" (50-200ms population spike) as the atomic unit of cognition in Dionysus 3.0.

## Connectivity Mandate (IO Map)
- **Host**: `dionysus-api`
- **Inlet**: `NemoriRiverFlow` (Event Creation)
- **Process**:
  - `ActiveInferenceService` (Entropy/Surprisal)
  - `MemoryBasinRouter` (Manifold Constraint)
- **Outlet**: `MemEvolveAdapter` (Consolidation -> Graphiti)
- **Feedback**: `PacketDynamics` metrics drive `ActiveInference` structure learning (Criticality).

## Context & constraints
- **Constraint**: Must use `DevelopmentEvent` as the base model.
- **Constraint**: Must not break existing event flow; fields are optional but recommended.
- **Reference**: `docs/science/neuronal_packets_architecture.md`.
- **Reference**: `ultrathink_review.md` (Quantization Requirement).

## Tasks
- [x] T001: Implement `PacketDynamics` model in `api/models/autobiographical.py`.
- [x] T002: Implement `PacketDynamics` generation logic in `api/services/nemori_river_flow.py`.
  - Logic: Estimate `duration_ms` from token count.
  - Logic: Calculate `spike_density`.
  - Logic: Assign default `phase_ratio`.
- [x] T002b: Implement **Input Quantization** (`create_packet_train`).
  - Logic: Split large inputs (>200 effective tokens) into sequence of `DevelopmentEvent`s.
  - Logic: Chain events via `parent_episode_id` or explicit `sequence_index`.
- [x] T003: Implement Entropy/Uncertainty calculation in `api/services/active_inference_service.py`.
- [x] T004: Create verification test `tests/unit/test_neuronal_packets.py`.

## Verification
- **Unit Test**: `test_neuronal_packets.py` verifies packet metrics are calculated and within biological ranges (50-500ms).
- **Integration**: Run `NemoriRiverFlow.ingest_context` and inspect output event.