# Specification 057: Treur Cognitive Architecture (3-Level Model)

## Overview
Implementation of Jan Treur's Multi-Order Adaptive Architecture for the Dionysus Consciousness Engine. This architecture defines three distinct levels of cognition: Base (Episodic), Adaptation (Semantic/Learning), and Control (Metacognition).

---

## Layer 1: Base (Episodic Reality)
**Function**: Raw perception, simulation, and episodic storage.
**Components**:
- **Nodes**: `Episode`, `Entity`, `Relation`.
- **Data Flow**: Perception -> Graphiti Extraction -> Neo4j Level 1.
- **Reflection**: Upward Reflection -> Activates Semantics (Level 2).

### Schema (Graphiti/Neo4j)
```cypher
(:Episode)-[:CONTAINS_ENTITY]->(:Entity)
(:Entity)-[:RELATION {type: "..."}]->(:Entity)
(:Episode)-[:ACTIVATES {strength: 0.x}]->(:Semantic)
```

---

## Layer 2: Adaptation (Semantic Learning)
**Function**: Learning, memory consolidation, and schema inference.
**Components**:
- **Nodes**: `Semantic`, `Schema`, `RW_Node` (Reified Weight).
- **Algorithms**:
    - **Ebbinghaus Consolidation**: Exponential decay based on time/rehearsal.
    - **Hebbian Learning**: $\Delta w = \eta \times pre \times post$.
    - **AutoSchemaKG**: Inferring structure from relations.
- **Reflection**: Downward Reflection -> Received from Level 3.

### The "Reified Weight" (RW) Node
To enable Level 3 control over learning, weights are nodes, not just edges.
```cypher
(:Semantic)-[:SOURCE_OF]->(:RW_Node)-[:TARGET_OF]->(:Semantic)
// The RW_Node holds the 'current_weight', 'plasticity', and 'history'
```

---

## Layer 3: Control (Metacognitive Governance)
**Function**: Monitoring, regulation, and model switching.
**Components**:
- **Nodes**: `MentalModel`, `AttractorBasin`, `ControlFactor`, `SurpriseEvent`.
- **Algorithms**:
    - **Active Inference**: Minimize Free Energy ($F = Surprise + Complexity$).
    - **Basin Switching**: Escape basin if $F$ exceeds threshold.
- **Reflection**: Downward Reflection -> Modulates Level 2 RW Nodes.

### Schema
```cypher
(:ControlFactor)-[:MODULATES {strength: 0.x}]->(:MentalModel)
(:MentalModel)-[:MEMBER_OF_BASIN]->(:AttractorBasin)
(:MentalModel)-[:GOVERNS]->(:Semantic)
```

---

## Implementation Roadmap (Conductor Track)

### Phase 1: Schema Refactor
- [ ] Define `ControlFactor` and `AttractorBasin` node types in Graphiti.
- [ ] Implement "Virtual" RW Nodes (edges with properties) first, to avoid graph explosion, unless "Meta-Plasticity" is strictly required. *Decision: Start with virtual, upgrade to Reified only for specific critical paths.*

### Phase 2: Algorithms
- [ ] Implement `EbbinghausDecay` service.
- [ ] Implement `BasinSwitching` logic in `ActiveInferenceService`.

### Phase 3: Visualization (Quartz)
- [ ] Visualize the 3 tiers in the Quartz Dashboard.
