# Plan: RMBC Operationalization

## Phase 1: Structural Extraction (The "Source Code")

- [x] **Step 1: Extract Unique Mechanisms (`03-UNIQUE MECHANISMS`).**
    - [x] Target: `/Volumes/Arkham/Marketing/stefan/Stefan Georgi - RMBC II/03-UNIQUE MECHANISMS/*.pdf`
    - [x] Action: Extract text, identify UMS/UMP logic.
    - [x] Output: `specs/marketing_rhapsodies/03_mechanisms.md`.

- [x] **Step 2: Extract Brief 20 (`05-BRIEF 20`).**
    - [x] Target: `/Volumes/Arkham/Marketing/stefan/Stefan Georgi - RMBC II/05-BRIEF 20/*.pdf`
    - [x] Action: Extract question logic.
    - [x] Output: `specs/marketing_rhapsodies/05_brief_20.md`.

## Phase 2: Semantic Distillation (The "Rulebook")

- [x] **Step 3: Update `061-rmbc-methodology.SKILL.md`.**
    - [x] Integrate Mechanism types (Actual, Metaphorical, etc.).
    - [x] Integrate the 20-Question Brief structure as a "Script" (Updated to New Brief 25-point structure).

## Phase 3: The Copy-Coordination Workflow (The "Engine")

- [x] **Step 5: Implement Draft Assembly (Template Slotting).**
    - [x] Create `scripts/rmbc_draft_assembly.py`.
    - [x] Implementation: "Mad Libs" slotting of Brief JSON into VSL Template.

- [x] **Step 6: Implement Audio Validation.**
    - [x] Create `scripts/rmbc_voice_validation.py`.
    - [x] Integration with ElevenLabs confirmed.
