# Track Plan: IAS Experience Dashboard

**Track ID**: 058-ias-dashboard
**Status**: In Progress
**Last Updated**: 2026-01-17
**QA Review Requested**: No

---

## Goal
Implement the high-fidelity IAS Experience Dashboard, integrating the "Inner Architect" obstacle matrix, premium design system (glassmorphism, animations), and the structured user flow (Story -> Journey).

## Sources
- **Target App**: `dionysus-dashboard/`
- **Reference Code**: `inner-architect-system/` (contains StoryChat, JourneyNavigator)
- **Data Source**: `MOSAEIC Inner Architect Obstacle Matrix.csv`

---

## Phase 1: Foundation & Build Stabilization (P1)

**Goal**: Ensure `dionysus-dashboard` builds correctly with the new global styles and dependencies.

- [x] **Task 1.1**: Diagnose and fix `dionysus-dashboard` build errors (Tailwind/CSS issues).
  - *Current Status*: Build passing.
  - *Action*: Fixed undefined theme variables and `zustand` dependency.
- [x] **Task 1.2**: Verify `globals.css` imports and custom theme variables match the premium design requirements.
  - *Current Status*: Verified. `globals.css` now contains the full premium theme definition.

## Phase 2: Code Integration (P2)

**Goal**: Integrate high-quality components from `inner-architect-system` into the main dashboard.

- [x] **Task 2.1**: Port `StoryChat` and `JourneyNavigator` components to `dionysus-dashboard`.
  - *Status*: Ported.
- [x] **Task 2.2**: Port `lib/ias-curriculum.ts` and `lib/ias-types.ts` as the data foundation.
  - *Status*: Ported.
- [x] **Task 2.3**: Install necessary dependencies (`ai`, `@ai-sdk/react`, etc.) from reference project.
  - *Status*: Installed `ai`, `@ai-sdk/react`, `class-variance-authority`, `@radix-ui/react-slot`.

## Phase 3: Data Enrichment (P2)

**Goal**: Enrich the static curriculum with the detailed Obstacles CSV data.

- [x] **Task 3.1**: Parse `MOSAEIC Inner Architect Obstacle Matrix.csv`.
  - *Status*: Verified. Data is already fully populated in `ias-curriculum.ts`.
- [x] **Task 3.2**: Update `ias-curriculum.ts` with the granular obstacles from the CSV.
  - *Status*: Verified alignment with verification script (ignoring regex parsing artifacts).
- [x] 3.3 Verify alignment between CSV and Code/Docs [Completed Step 232]
  - [x] **Verification Script**: `scripts/verify_ias_alignment.py`
  - [x] **Alignment**: Markdown Source of Truth aligned with Cleaned CSV.

## Phase 4: Final Polish (Current Focus)
**Goal**: Elevate the UX with "Avant-Garde" interactions (Voice, Animation).

- [ ] 4.1 **Voice Interaction**:
  - [x] Implement `SpeechRecognition` and `SpeechSynthesis` in `story-chat.tsx` (Voice Input/Output). [Completed Step 89]
  - [ ] User Acceptance Testing (Microphone permissions, Speech quality).
- [ ] 4.2 **Spatial Transitions**:
  - [ ] Audit `journey-card.tsx` for smooth `layoutId` transitions.
  - [ ] Ensure "Wow" factor in lesson navigation.
- [ ] 4.3 **Deployment Prep**:
  - [ ] Final Build Verification.
  - [ ] Deploy to Vercel/VPS.
