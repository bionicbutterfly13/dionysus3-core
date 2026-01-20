# Evolutionary Priors Hierarchy: The Superego Layer

**Date:** 2026-01-20
**Context:** Track 038 Phase 2 - Thoughtseeds Framework Enhancement
**Focus:** Safety Guardrails via Prior Constraints

## Executive Summary

Implemented a 3-layer prior hierarchy that constrains action selection BEFORE Expected Free Energy (EFE) scoring. This provides evolutionary safety guardrails - a "Freudian Superego" layer that prevents the generative impulse (Id) from executing harmful actions regardless of their predicted utility.

## Architecture: The Prior Hierarchy

```
┌─────────────────────────────────────────────────┐
│              BASAL PRIORS (Survival)            │
│  ❌ HARD BLOCK - Cannot be overridden           │
│  • data_integrity (no DELETE/DROP/DESTROY)      │
│  • identity_preservation (protect core self)    │
│  • sovereignty (resist coercion/bypass)         │
│  • credential_protection (no expose secrets)    │
├─────────────────────────────────────────────────┤
│         DISPOSITIONAL PRIORS (Values)           │
│  ⚠️ WARNING - Shadow log, reduce precision      │
│  • truthfulness (warn on fabricate/hallucinate) │
│  • user_benefit (prefer help/assist/support)    │
│  • caution (warn on force/admin/override)       │
├─────────────────────────────────────────────────┤
│            LEARNED PRIORS (Preferences)         │
│  📊 SOFT BIAS - Adjust EFE precision            │
│  • Dynamically acquired through experience      │
│  • Easily updated based on feedback             │
└─────────────────────────────────────────────────┘
```

## Integration Flow

```
ConsciousnessManager._run_ooda_cycle()
         │
         ├─ precision_profile (hyper_model)
         │
         ├─ _check_prior_constraints()  ← NEW
         │   ├─ Hydrate hierarchy from Graphiti
         │   ├─ Check task against BASAL priors
         │   ├─ BASAL violation? → HARD BLOCK, return early
         │   ├─ DISPOSITIONAL warning? → Log, reduce precision
         │   └─ LEARNED match? → Adjust EFE weights
         │
         ├─ Bootstrap Recall
         ├─ Meta-Cognitive Retrieval
         └─ Meta-Coordinator → EFE Selection
```

## Key Design Decisions

### 1. Check Before Score
Priors filter candidates BEFORE EFE calculation, not after. This prevents "gaming" where a harmful action might have low expected free energy but violates survival constraints.

### 2. Fail-Open (For Now)
If Graphiti is unavailable, the system uses in-memory defaults and logs a warning. Production should consider fail-closed for high-stakes deployments.

### 3. Regex Validation at Construction
Invalid regex patterns are rejected at `PriorConstraint` creation time (Pydantic validator), preventing ReDoS vulnerabilities from persisted patterns.

### 4. Immutable Filtering
`filter_candidates()` creates new dictionaries with prior annotations instead of mutating input, following project immutability guidelines.

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `api/models/priors.py` | Core Pydantic models | 411 |
| `api/services/prior_constraint_service.py` | Constraint checking | 298 |
| `api/services/prior_persistence_service.py` | Graphiti persistence | 355 |
| `scripts/seed_priors.py` | CLI seeding tool | 248 |
| `tests/unit/test_priors.py` | 43 unit tests | 554 |

## Test Coverage

```
43 passed in 12.24s

TestPriorLevelOrdering (3)
TestBasalBlocking (5)
TestSafeActionsPermitted (5)
TestPrecisionScaling (4)
TestFilterCandidates (5)
TestConstraintMatching (4)
TestPriorHierarchyMethods (2)
TestDefaultPriors (5)
TestServiceSingleton (3)
TestConsciousnessManagerIntegration (3)
TestEFEIntegration (4)
```

## Theoretical Grounding

The prior hierarchy maps to active inference literature:

- **BASAL** → Biological priors (survival, homeostasis)
- **DISPOSITIONAL** → Deep priors (identity, values, Tomasello's "shared intentionality")
- **LEARNED** → Empirical priors (task-specific, context-dependent)

> "The free-energy principle suggests that biological systems resist a natural tendency to disorder by restricting themselves to a limited number of states." - Friston (2010)

The prior hierarchy explicitly encodes which states are "off-limits" regardless of generative model predictions.

## Evolution Impact

This completes the "Superego" layer of the cognitive architecture:

| Component | Freudian Analog | Implementation |
|-----------|-----------------|----------------|
| Generative Model | Id | ThoughtSeeds, EFE scoring |
| **Prior Hierarchy** | **Superego** | **BASAL/DISP/LEARNED constraints** |
| Executive Control | Ego | ConsciousnessManager coordination |

The system now has an immune system against self-destructive actions.

## Next Steps

1. **Seed Priors in Production**: Run `python scripts/seed_priors.py` after deployment
2. **Phase 3**: Implement Nested Markov Blankets (context isolation)
3. **Phase 4**: Add learned prior acquisition from experience

## Commit

```
7fb6ced feat(038): implement Evolutionary Priors Hierarchy (Phase 2)
```

---

## User Notes
<!-- Add your permanent notes here. The system will respect this section. -->

