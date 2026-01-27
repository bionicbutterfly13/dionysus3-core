
# Implementation Plan - RMBC & Bullet Campaign System Operationalization

This plan details the "Ultrathink" strategy for ingesting the specialized marketing methodologies (RMBC 2.0, Bullet Campaign, Perry Marshall) and operationalizing them into the Dionysus Cognitive Architecture.

## 1. Architectural Reasoning ("The Ultrathink")

### Psychological Resonance (The "Why")
The "Analytical Empath" (ADHD High Performer) avatar struggles with *starting* and *sequencing* but excels at *editing* and *polishing*. Static PDFs increase friction.
*   **The Solution**: Invert the workflow. Instead of the user reading PDFs to write copy, the System ingests the PDFs to *interview* the user.
*   **Cognitive Offloading**: The System holds the "Structure" (Attractor Basin). The User provides the "Substance" (Flow).

### Technical Architecture
*   **Graphiti as the Mental Model**: We will not just fuzzy-search text. We will model `Mechanism`, `PainPoint`, `Objection`, and `Transformation` as first-class graph entities. 
*   **Audio-First Validation**: Utilizing the newly integrated ElevenLabs service, the system will read drafts back to the user to validate rhythm and "breathlessness" (Perry Marshall's voice rule).

## 2. Ingestion Strategy (The "How")

We will treat the course materials not as "documents" but as "programming code" for the agent's behavior.

### Phase 1: Structural Extraction (Current Status: 15%)
*   **Objective**: Extract raw text from all critical PDFs in `/Volumes/Arkham/Marketing/stefan/Stefan Georgi - RMBC II`.
*   **Target Modules**:
    1.  `02-DEEP RESEARCH`: 5 Phases of Awareness, Market Mining. (Partially Done)
    2.  `03-UNIQUE MECHANISMS`: UMP/UMS Logic, The "Old Mechanism" Flaw.
    3.  `05-BRIEF 20`: The 20-Question Brief Questionnaire (The "Source Code" of the copy).
    4.  `15-EMAIL MARKETING`: Sequence logic.

### Phase 1.5: Bullet Campaign & Fascination System (COMPLETED)
*   **"Ultrathink" Bullet Campaign Strategy** (`036-bullet-campaign-strategy.SKILL.md`)
    - [x] **Distinguish Concepts:** Explicitly separate "Campaigns" from "Fascinations".
    - [x] **Create Fascinations Skill:** `062-copywriting-fascinations.SKILL.md` (Pure Copywriting).
    - [x] **Refine Campaign Skill:** `036` updated with Neuro-Computational Analysis & Graphiti Schema.
    - [x] **SDK Integration:** Hybrid strategy defined.
*   **Automated Pipeline**: 
    - Refine `generic_pdf_extract.py` to target key files recursively.
    - Output: Cleaned Markdown files in `specs/marketing_rhapsodies/`.

### Phase 2: Semantic Distillation
*   **Objective**: Convert defined methodology into *Rules* and *Templates*.
*   **Artifacts**:
    - `061-rmbc-methodology.SKILL.md`: The rulebook for the agent.
    - `060-marketing-templates.json`: JSON structures for VSLs and Emails that the `CopyAgent` can fill.

## 3. Implementation Strategy (The "Active System")

### Phase 3: The "Copy-Coordination" Workflow
Create a dedicated Conductor Track (`060-marketing-skills-system`) that orchestrates the following loop:

1.  **The Interrogation (Brief Builder)**:
    - User initiates: "Start New Promo".
    - Agent (using `05-BRIEF 20` logic) interviews user: "Who is the villain? What is the Old Mechanism?"
    - Agent stores answers in Graphiti as `(Concept)-[:IS_MECHANISM_OF]->(Product)`.

2.  **The Assembly (Draft Gen)**:
    - Agent selects a template (e.g., "60-Second Lead").
    - Agent slots in the Graphiti data.
    - Agent produces `draft_v1.md`.

3.  **The Validation (Audio & Logic)**:
    - System runs "Perry Marshall Voice Check" (Reading Grade Level < 5, U:I Ratio).
    - System uses **ElevenLabs** to read the copy aloud to the user.
    - User listens for "clunky" parts -> Re-edit -> Repeat.

## 4. Immediate Execution Plan

1.  **Complete Extraction**: Extract `03-UNIQUE MECHANISMS` and `05-BRIEF 20` PDF content.
2.  **Update Skills**: Finalize `061-rmbc-methodology.SKILL.md` with "Mechanism" and "Brief" sections.
3.  **Graph Model**: Define the `CopyProject` schema in Graphiti (if needed for Phase 3).
