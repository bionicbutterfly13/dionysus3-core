# Feature 054: Agency Architecture Unification

## Status: Draft

## Clarifications

### Session 2026-01-05

- Q: Migration strategy for existing consumers? → A: Breaking change (no external consumers)
- Q: Code cleanup approach? → A: Delete all unused code when replacing
- Q: KL divergence calculator selection? → A: Data-driven (Gaussian for parametric, Histogram for samples)

## Problem Statement

The codebase has THREE agency-related components with overlapping concerns and confusing naming:

| Component | Location | Purpose | Core Mechanism |
|-----------|----------|---------|----------------|
| `AgencyService` | `api/services/agency_service.py` | Compute agency strength | KL divergence (Gaussian) |
| `AgencyDetector` | `api/services/agency_detector.py` | Detect and attribute agency | KL divergence (histogram) |
| `BiologicalAgencyService` | `api/services/biological_agency_service.py` | Three-tier agentive architecture | Tomasello evolutionary model |

### What Works But Shouldn't

1. **Duplicate KL Divergence Computation**
   - `AgencyService.compute_agency_strength()` uses Gaussian closed-form
   - `AgencyDetector.calculate_agency_score()` uses histogram density estimation
   - Both compute D_KL[p(μ,a) || p(μ)p(a)] but with different methods
   - No shared abstraction or configurable strategy

2. **Confusing Naming**
   - All three use "Agency" but mean different things:
     - `AgencyService`: Statistical coupling measurement
     - `AgencyDetector`: Attribution classification (self/external)
     - `BiologicalAgencyService`: Evolutionary tier architecture
   - Developers must read implementation to understand purpose

3. **Missing Integration**
   - `BiologicalAgencyService` makes tier-based decisions but doesn't use `AgencyDetector` for attribution
   - `AgencyService` has a `get_agent_agency()` stub with TODO comment
   - No clear orchestration between components

4. **Model Duplication**
   - `api/models/agency.py`: `AgencyAttribution`, `AgencyAttributionType`
   - `api/models/biological_agency.py`: `AgencyTier`, `BiologicalAgentState`
   - Overlapping but not unified

## Proposed Solution

### Architecture Redesign

```
┌─────────────────────────────────────────────────────────────────┐
│                     UnifiedAgencyService                        │
│  (Orchestrates all agency concerns)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │ AgencyMeasurement   │  │ AgencyArchitecture  │              │
│  │ (Statistical)       │  │ (Structural)        │              │
│  ├─────────────────────┤  ├─────────────────────┤              │
│  │ - KLDivergenceCalc  │  │ - TierManager       │              │
│  │   ├─ Gaussian       │  │ - SharedAgency      │              │
│  │   └─ Histogram      │  │ - DevelopmentalCtrl │              │
│  │ - AttributionEngine │  │                     │              │
│  └─────────────────────┘  └─────────────────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Renaming

| Current Name | Proposed Name | Rationale |
|--------------|---------------|-----------|
| `AgencyService` | `AgencyMeasurementService` | Clarifies statistical focus |
| `AgencyDetector` | `AgencyAttributionEngine` | Clarifies classification focus |
| `BiologicalAgencyService` | `AgencyArchitectureService` | Clarifies structural focus |

### Integration Points

1. **Tier decisions inform attribution thresholds**
   - Tier 1 (goal-directed): Binary attribution, low confidence
   - Tier 2 (intentional): Attribution with simulation context
   - Tier 3 (metacognitive): Attribution with self-assessment

2. **Attribution informs tier promotion**
   - Consistent self-attribution → evidence of executive control
   - Pattern of deliberate decisions → evidence of metacognitive capability

3. **Shared measurement backend**
   - Abstract `KLDivergenceCalculator` interface
   - `GaussianKLCalculator` for analytical computation (when means/precisions available)
   - `HistogramKLCalculator` for sample-based estimation (when only raw samples available)
   - **Selection rule**: Auto-detect based on input type - parametric beliefs → Gaussian, raw arrays → Histogram

## Acceptance Criteria

- [ ] Single entry point for agency operations (`UnifiedAgencyService`)
- [ ] Clear naming that reflects component purpose
- [ ] Shared KL divergence abstraction with strategy pattern
- [ ] Integration between tier decisions and attribution
- [ ] Updated imports and references across codebase
- [ ] Documentation updated with architecture diagram
- [ ] Existing tests pass with new structure
- [ ] New integration tests for component coordination

## Non-Goals

- Changing the mathematical foundations (KL divergence, Tomasello model)
- Adding new agency detection algorithms
- Modifying the OODA loop integration

## Constraints

- **No backward compatibility required**: App has no external consumers; breaking changes are acceptable
- Old service files can be deleted after unification (no deprecation period needed)
- **Delete unused code**: When replacing services, remove all dead code rather than leaving deprecated stubs

## Dependencies

- `api/models/agency.py`
- `api/models/biological_agency.py`
- `api/services/agency_service.py`
- `api/services/agency_detector.py`
- `api/services/biological_agency_service.py`
- Any consumers of these services

## References

- Sandved-Smith & Da Costa (2024) - Agency strength via KL divergence
- Tomasello (2025) - Three-tier biological agency architecture
- Metacognitive Particles paper - Statistical dependence for agency detection
