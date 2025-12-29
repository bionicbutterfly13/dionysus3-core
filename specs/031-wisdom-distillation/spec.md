# Feature Specification: Wisdom Distillation (The System Soul)

**Feature Branch**: `feature/031-wisdom-distillation`
**Status**: In-Progress
**Input**: Port the "Wisdom Distillation" logic to turn raw trajectories and MoSAEIC data into an "Effective Worldview."

## Overview
Dionysus 3 collects high-fidelity data, but it remains fragmented. This feature implements the **Distillation Layer** that synthesizes raw extracts into canonical **Mental Models**, **Attractor Basins**, and **Strategic Principles**. This is the process of building the "System Soul" and the "Eyes of the Avatar."

## User Scenarios & Testing

### User Story 1 - Canonical Principle Extraction (Priority: P1)
As the system, I want to iterate through fragmented session insights and merge them into a single, high-confidence "Strategic Principle" node in Neo4j, so I have a consistent worldview.

**Independent Test**: Provide 3 raw extracts with slight variations of the "Archon-first" rule. Verify the distiller creates ONE canonical `StrategicPrinciple` node with 100% confidence and links to all 3 sources.

### User Story 2 - Avatar Worldview Alignment (Priority: P1)
As a user, I want the system to explain a new task through the lens of my avatar's worldview, using the distilled case studies and principles.

**Independent Test**: Query the system for "How should we handle this crisis?". Verify the response cites a distilled `CaseStudy` and an `AttractorBasin` (e.g., "Split Self").

## Functional Requirements
- **FR-031-001**: Implement the `WisdomDistiller` agent that deduplicates and synthesizes raw JSON extracts.
- **FR-031-002**: Map distilled units to Neo4j: `(:MentalModel)`, `(:StrategicPrinciple)`, `(:CaseStudy)`, `(:WorldviewUnit)`.
- **FR-031-003**: Implement a "Richness Score" that measures how well a distilled unit captures the psychological nuance of the MoSAEIC windows.
- **FR-031-004**: Integrate with `WorldviewIntegrationService` to make distilled units the "Priors" for future OODA loops.

## Success Criteria
- **SC-001**: Total node count for "MentalModels" is reduced by >50% after distillation (proving successful deduplication).
- **SC-002**: Every distilled unit carries a `provenance_chain` linking back to at least one raw session.
- **SC-003**: The system's "Voice" (via `MarketingAgent`) becomes 20% more consistent with the "Analytical Empath" filters.