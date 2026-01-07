# Data Model: Meta-ToT Engine Integration

## MetaToTSession
Represents a single Meta-ToT reasoning run.

**Attributes**:
- id (string)
- problem (string)
- context_summary (string)
- started_at (timestamp)
- completed_at (timestamp, optional)
- best_action (string)
- best_path (list of node ids)
- metrics (object: total_prediction_error, total_free_energy, processing_time)
- decision_id (string, optional)
- trace_id (string, optional)

**Relationships**:
- MetaToTSession 1..* MetaToTNode (contains)
- MetaToTSession 1..1 MetaToTDecision (selected_mode)
- MetaToTSession 1..1 MetaToTTrace (trace)

## MetaToTNode
Represents a single branch node in the thought tree.

**Attributes**:
- id (string)
- session_id (string)
- parent_id (string, optional)
- depth (integer)
- node_type (enum: root, exploration, challenge, evolution, integration, leaf)
- cpa_domain (string)
- thought (string)
- score (float)
- visit_count (integer)
- value_estimate (float)
- prediction_error (float)
- free_energy (float)
- is_selected (boolean)

**Relationships**:
- MetaToTNode 0..* MetaToTNode (children)

## ActiveInferenceState
Captures active inference currency for a node or session.

**Attributes**:
- id (string)
- session_id (string)
- prediction_error (float)
- free_energy (float)
- surprise (float)
- precision (float)
- beliefs (object)
- reasoning_level (integer)
- parent_state_id (string, optional)

## MetaToTDecision
Represents threshold-based reasoning mode selection.

**Attributes**:
- id (string)
- task (string)
- complexity_score (float)
- uncertainty_score (float)
- thresholds (object)
- selected_mode (string)
- rationale (string)

## MetaToTTrace
Stores the trace payload for later review.

**Attributes**:
- id (string)
- session_id (string)
- created_at (timestamp)
- trace_payload (object)
