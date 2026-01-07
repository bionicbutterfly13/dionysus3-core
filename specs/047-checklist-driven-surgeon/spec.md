# Feature Specification: Checklist-Driven Surgeon Metaphor

**Feature Branch**: `047-checklist-driven-surgeon`  
**Created**: 2025-12-31  
**Status**: Draft  
**Input**: User description: "this is a metaphor:Checklist-Driven Surgeon. use spec kit specs"

## User Scenarios & Testing

### User Story 1 - Rigorous Problem Decomposition (Priority: P1)

As an operator, I want the system to deconstruct my complex query into atomic components before attempting to solve it, so that it avoids misunderstanding constraints.

**Why this priority**: Core of the 'Surgeon' metaphor is knowing exactly what the 'patient' (problem) needs before 'cutting' (output).

**Independent Test**: Can be tested by providing a complex, multi-constraint prompt and verifying that the `ReasoningAgent` uses the `understand_question` tool first.

**Acceptance Scenarios**:

1. **Given** a complex query, **When** the OODA cycle starts, **Then** the `reasoning` agent invokes `understand_question`.
2. **Given** the output of `understand_question`, **When** the agent proceeds, **Then** it references the identified components in its next steps.

---

### User Story 2 - Self-Correction and Verification (Priority: P2)

As an operator, I want the system to critically examine its own reasoning trace before finalizing an answer, so that hallucinations and logical leaps are caught internally.

**Why this priority**: Surgeons perform a 'count' (verification) before closing a procedure to ensure no errors were left behind.

**Independent Test**: Can be tested by providing a problem where the initial reasoning contains a subtle error and verifying that `examine_answer` identifies it.

**Acceptance Scenarios**:

1. **Given** a reasoning trace, **When** the agent is about to conclude, **Then** it invokes `examine_answer`.
2. **Given** a critique from `examine_answer`, **When** flaws are found, **Then** the agent invokes `backtracking` to revise the approach.

---

### User Story 3 - Grounded Analogical Reasoning (Priority: P3)

As an operator, I want the system to recall analogous solved examples before solving a new problem, so that its reasoning is grounded in proven patterns.

**Why this priority**: Professional surgeons rely on established medical literature and past cases (analogies) to guide complex procedures.

**Independent Test**: Can be tested by providing a domain-specific problem and verifying that the agent invokes `recall_related`.

**Acceptance Scenarios**:

1. **Given** a problem context, **When** the reasoning phase begins, **Then** the agent invokes `recall_related` to find similar cases.

---

### Edge Cases

- What happens when `examine_answer` finds a fatal flaw that cannot be backtracked easily? (System should escalate to Metacognition for goal revision).
- How does system handle contradictory analogous examples from `recall_related`? (System should use active inference currency to weigh precision).

## Requirements

### Functional Requirements

- **FR-001**: Implement the `understand_question` tool to deconstruct user intent.
- **FR-002**: Implement the `recall_related` tool for analogical grounding.
- **FR-003**: Implement the `examine_answer` tool for internal self-critique.
- **FR-004**: Implement the `backtracking` tool for error recovery.
- **FR-005**: Update the `ConsciousnessManager` prompt to mandate the use of these tools for complex tasks (High Entropy).
- **FR-006**: Update `ManagedReasoningAgent` description to reflect its role as a "Checklist-Driven Surgeon".

### Key Entities

- **ReasoningTrace**: The temporal sequence of thoughts and tool calls representing the "procedure".
- **Critique**: The structured output of `examine_answer` identifying flaws and strengths.
- **Analogy**: A previously solved case used to ground current reasoning.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of high-entropy tasks (complexity > 0.7) trigger at least two tools from the "Surgeon" suite.
- **SC-002**: Reduction in "hallucination-to-final-output" rate by 50% through internal verification.
- **SC-003**: Agent narrative explicitly mentions the "Checklist-Driven Surgeon" protocol when explaining its rationale for verification.
