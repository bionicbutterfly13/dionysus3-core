<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# prd for gemini antigravity project

I couldn't locate a specific document titled "Gemini Antigravity Project PRD" in your Notion workspace. The search results show various product development pages, context engineering documents, and AI-related projects, but none specifically mention an "antigravity" project associated with Gemini.

This could mean:

- The document might be named differently than expected
- It may be located in a database that requires a more specific search
- The project might be referenced within another document rather than having its own dedicated PRD page
- It may not yet exist in your Notion workspace

Could you provide any additional details about this project? For example:

- Is this related to Google's Gemini AI model?
- Do you recall any other keywords or the approximate timeframe when it was created?
- Is it possibly nested within a specific teamspace or parent page?

This would help me conduct a more targeted search to locate the PRD you're looking for.

---

# It is related to Gemini and google's antigravity platform.  I want deep research to find out what is available and how to best organize a notion workspace to store an effective prd that I can customize for my prject brownfield is there a skill or prompt or template that Ican use with gemini antigravity and conductor spec driven development

Based on my research, I can provide you with comprehensive guidance on Google Antigravity, Conductor, spec-driven development, and how to organize an effective Notion workspace for your Brownfield project PRD.

## Google Antigravity Overview

Google Antigravity is an **agentic development platform** (not just an IDE) launched in November 2025 alongside Gemini 3. It represents a fundamental shift from code assistance to autonomous task orchestration, allowing AI agents to plan, execute, and verify complex development tasks across your editor, terminal, and browser.[^2_1][^2_2][^2_3]

### Key Features

**Agent-First Architecture**: Agents work in a dedicated space separate from the editor, generating **Artifacts** (task lists, implementation plans, screenshots, browser recordings) that you can review and comment on without interrupting execution.[^2_1]

**Spec-Driven Development Integration**: Antigravity natively supports spec-driven development through AGENTS.md, Antigravity.md, and SPECS.md files that guide agent behavior and ensure long-term context retention.[^2_4][^2_5]

**Model Optionality**: Supports Gemini 3 Pro (with generous rate limits), Claude Sonnet 4.5, and OpenAI models, all at no cost for individuals during public preview.[^2_1]

## Conductor \& Spec-Driven Development

**Google Conductor** is a context-driven development framework for Gemini CLI that formalizes specifications and plans in Markdown files stored directly in your repository. This creates a "gravity-free" environment where product ideas flow from model → spec → agent → UI → code → runtime → governance.[^2_6][^2_7][^2_4]

### Core Concept

Spec-Driven Development (SDD) treats specifications as **executable, first-class code objects** that:

- Agents read and update automatically[^2_4]
- Generate acceptance tests, model evaluation plans, and system diagrams[^2_4]
- Enforce safety constraints and policy boundaries[^2_4]
- Enable reproducibility, auditability, and governance[^2_4]


### Key Markdown Files for Antigravity

**AGENTS.md**: Defines boundaries, restrictions, security constraints, and how agents should behave in your workspace[^2_5][^2_8]

**SPECS.md**: Contains detailed requirements, acceptance criteria, and functional specifications[^2_9][^2_5]

**Antigravity.md**: Includes implementation plans, workflows, and project-specific instructions[^2_5]

**GEMINI.md**: Global configuration file in `~/.gemini/` that Antigravity automatically loads[^2_8]

## Notion Workspace Structure for PRD

Here's an optimized Notion structure for spec-driven development PRDs that integrates with Antigravity:

### Database Schema

**Projects Database** with properties:

- **Name** (Title): Project name (e.g., "Brownfield Project")
- **Status** (Select): Planning, Spec Complete, In Development, Testing, Deployed
- **Priority** (Select): P0 (Critical), P1 (High), P2 (Medium), P3 (Low)
- **Spec Type** (Multi-select): Product, Technical, Implementation
- **Phase** (Select): Discovery, Design, Development, QA, Launch
- **Owner** (Person): Project lead/PM
- **Start Date** (Date): Project kickoff
- **Target Date** (Date): Expected completion
- **Related Specs** (Relation): Link to Specs database
- **Implementation Tasks** (Relation): Link to Tasks database

**Specs Database** with properties:

- **Name** (Title): Spec title
- **Type** (Select): PRD, Technical Brief, Requirements, Research Log
- **Project** (Relation): Links back to Projects
- **Version** (Number): Track spec iterations
- **Last Updated** (Last Edited Time)
- **Status** (Select): Draft, Review, Approved, Implemented
- **Export Path** (URL): Link to exported markdown for Antigravity

**Implementation Plans Database** with properties:

- **Name** (Title): Plan name
- **Linked Spec** (Relation): Parent specification
- **Phase** (Select): Not Started, In Progress, Complete
- **Completion %** (Number)
- **Tasks** (Relation): Link to Tasks database

**Tasks Database** with properties:

- **Task Name** (Title)
- **Status** (Select): To Do, In Progress, Blocked, Complete
- **Priority** (Select): P0, P1, P2, P3
- **Implementation Plan** (Relation)
- **Estimated Effort** (Select): Small, Medium, Large
- **Component** (Multi-select): Database, API, Frontend, Integration, Testing


### PRD Page Template Structure

```markdown
# [Project Name] - Product Requirements Document

## Executive Summary
[2-3 sentence overview]

## Specification Details
- **Type**: Product Spec
- **Version**: 1.0
- **Status**: Draft
- **Owner**: [Name]
- **Last Updated**: [Date]

## Problem Statement
[What problem are we solving?]

## Goals & Success Metrics
- Primary Goal: [Measurable outcome]
- Key Metrics: [List KPIs]

## User Stories
### User Persona 1
- **Story**: As a [role], I want [action] so that [benefit]
- **Acceptance Criteria**:
  - [ ] Criterion 1
  - [ ] Criterion 2

## Functional Requirements
### Feature 1: [Name]
- **Description**: [Details]
- **Priority**: P0
- **Dependencies**: [List]
- **Acceptance Criteria**: [Testable conditions]

## Non-Functional Requirements
- **Performance**: [Targets]
- **Security**: [Requirements]
- **Scalability**: [Needs]
- **Compliance**: [Standards]

## Technical Constraints
- Tech Stack: [List]
- Integration Points: [Systems]
- Data Requirements: [Schemas]

## Implementation Phases
### Phase 1: [Name]
- **Goal**: [Outcome]
- **Tasks**: [Link to task database]
- **Timeline**: [Duration]

## Risks & Mitigation
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| [Risk] | High | Medium | [Strategy] |

## Export for Antigravity
[Toggle section containing markdown-formatted specs ready for AGENTS.md/SPECS.md]
```


## Workflow Integration

### Step 1: Create PRD in Notion

Use the template above to document your Brownfield project specifications in Notion's structured format with proper linking and databases.[^2_10]

### Step 2: Export to Markdown

Create a toggle section in your Notion PRD with markdown-formatted specs that can be directly copied to your codebase.[^2_10]

### Step 3: Structure Repository Files

```
/your-project
├── .gemini/
│   └── GEMINI.md          # Global config (load AGENTS.md automatically)
├── AGENTS.md              # Agent behavior, boundaries, security
├── SPECS.md               # Product requirements from Notion
├── TECH_BRIEF.md          # Architecture, tech stack, constraints
├── REQUIREMENTS.md         # Detailed feature requirements
├── IMPLEMENTATION_PLAN.md  # Execution roadmap
└── Antigravity.md         # Project-specific workflows
```


### Step 4: Configure GEMINI.md

Add this rule to automatically load your specs:[^2_8]

```markdown
# Global Antigravity Configuration

## Project Context Loading
- Check for the presence of AGENTS.md files in the project workspace
- Load SPECS.md for product requirements
- Load TECH_BRIEF.md for technical context
- There may be additional AGENTS.md in sub-folders with specific instructions
```


### Step 5: Sync Back to Notion

As agents complete work, update your Notion databases:

- Mark implementation plan phases as complete
- Update task statuses
- Document research logs and findings
- Link generated artifacts[^2_10]


## Brownfield Project Template

For your specific Brownfield project, here's a starter AGENTS.md template:

```markdown
# Brownfield Project - Agent Guidelines

## Project Context
This is a brownfield refactoring/enhancement project with existing codebase constraints.

## Boundaries & Restrictions
- DO NOT modify legacy modules without explicit approval
- MUST maintain backward compatibility with existing APIs
- MUST follow existing code style and patterns
- MUST document all changes in CHANGELOG.md

## Security Requirements
- All database queries must use parameterized statements
- API endpoints require authentication middleware
- Sensitive data must be encrypted at rest
- Log all security-relevant events

## Testing Requirements
- Unit test coverage minimum 80%
- Integration tests for all new API endpoints
- Regression tests for modified legacy code
- Performance benchmarks for critical paths

## Workflow
1. Review SPECS.md for requirements
2. Analyze existing codebase structure
3. Generate implementation plan in IMPLEMENTATION_PLAN.md
4. Create tasks broken down by component
5. Execute with regular artifact checkpoints
6. Generate test suites automatically
7. Document findings in research logs
```

This comprehensive approach creates a seamless bridge between Notion's organizational capabilities and Antigravity's agentic execution, enabling truly spec-driven development for your Brownfield project.[^2_10][^2_4]
<span style="display:none">[^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_17][^2_18][^2_19]</span>

<div align="center">⁂</div>

[^2_1]: https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/

[^2_2]: https://blog.google/products/gemini/gemini-3/

[^2_3]: https://en.wikipedia.org/wiki/Google_Antigravity

[^2_4]: https://www.linkedin.com/pulse/google-gemini-anti-gravity-spec-driven-development-ajit-jaokar-fegme

[^2_5]: https://www.youtube.com/watch?v=g-jYIbf6nbo

[^2_6]: https://developers.googleblog.com/conductor-introducing-context-driven-development-for-gemini-cli/

[^2_7]: https://www.infoq.com/news/2026/01/google-conductor/

[^2_8]: https://aiengineerguide.com/blog/make-antigravity-use-agents-md-automatically/

[^2_9]: https://www.reddit.com/r/ClaudeCode/comments/1op8b6i/why_we_shifted_to_specdriven_development_and_how/

[^2_10]: https://mcpservers.org/claude-skills/notion/notion-spec-to-implementation

[^2_11]: https://www.youtube.com/watch?v=MAUpppfg9Go

[^2_12]: https://www.youtube.com/watch?v=EWJ_C4s9w5o

[^2_13]: https://www.constellationr.com/blog-news/insights/google-launches-gemini-3-google-antigravity-generative-ui-features

[^2_14]: https://www.linkedin.com/posts/lachezar-vladikov_conductor-context-driven-dev-activity-7408153173581930496-XVMn

[^2_15]: https://discuss.ai.google.dev/t/conductor-should-be-integrated-into-antigravity-to-ensure-long-term-context-retention/113384

[^2_16]: https://github.blog/ai-and-ml/generative-ai/spec-driven-development-using-markdown-as-a-programming-language-when-building-with-ai/

[^2_17]: https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html

[^2_18]: https://developer.microsoft.com/blog/spec-driven-development-spec-kit

[^2_19]: https://www.notion.com/templates/product-spec-golden


---

# what is a gravity free environment:"gravity-free".  is this mentioned in google's gemini docs?

Based on my research of Google's official documentation, the term **"gravity-free environment"** does not appear as an official technical term in Google's Gemini or Antigravity documentation.[^3_1][^3_2]

## What "Gravity-Free" Likely Refers To

The metaphorical concept appears to come from **third-party interpretations** of how Antigravity works, not from Google's official terminology. In the LinkedIn article I cited earlier, the author described a "gravity-free" workflow as:[^3_3]

> "This creates a 'gravity-free' environment where product ideas flow from model → spec → agent → UI → code → runtime → governance"

This is a **creative metaphor** suggesting:

- **Frictionless flow**: Ideas move seamlessly through the development pipeline without manual handoffs
- **Reduced resistance**: Agents handle context-switching between surfaces (editor, terminal, browser) autonomously
- **Elevated abstraction**: Developers operate at task-level rather than being "weighed down" by implementation details


## Google's Official Terminology

Google's actual documentation uses these terms instead:[^3_2][^3_1]

### Agent-First Development

The platform prioritizes autonomous AI agents that can "plan, execute, and verify complex, end-to-end software tasks".[^3_2]

### Multi-Surface Autonomy

Agents can "operate across all of these surfaces simultaneously and autonomously" - meaning editor, terminal, and browser.[^3_1][^3_2]

### Asynchronous Interaction

The Manager view allows you to "spawn, orchestrate, and observe multiple agents across multiple workspaces in parallel", working asynchronously rather than synchronously.[^3_2]

### Task-Level Abstraction

Google emphasizes moving from "individual prompts and tool calls" to "higher abstractions" where you interface with agents at the task level.[^3_1][^3_2]

### Liftoff

The consistent branding metaphor Google uses is **"liftoff"** and **"experience liftoff"**, referring to:[^3_1][^3_2]

- Launching your development work
- Elevating from code-level to task-level thinking
- The name "Antigravity" itself suggesting freedom from constraints


## Why the Platform is Called "Antigravity"

Google explains the name represents their vision to "ultimately enable anyone with an idea to experience liftoff and build that idea into reality". The antigravity metaphor suggests:[^3_2]

- **Lifting off from constraints**: Breaking free from traditional IDE limitations
- **Weightlessness**: Reducing the burden of context-switching and manual orchestration
- **Upward momentum**: Elevating developer productivity through autonomous agents

So while "gravity-free environment" isn't Google's official language, it's a reasonable metaphor that captures the essence of what Antigravity aims to achieve—a development experience free from the "gravitational pull" of manual, surface-by-surface task execution.[^3_1][^3_2]
<span style="display:none">[^3_10][^3_11][^3_12][^3_4][^3_5][^3_6][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://antigravity.google/blog/introducing-google-antigravity

[^3_2]: https://blog.google/products/gemini/gemini-3/

[^3_3]: https://www.linkedin.com/pulse/google-gemini-anti-gravity-spec-driven-development-ajit-jaokar-fegme

[^3_4]: https://antigravity.google

[^3_5]: https://codelabs.developers.google.com/getting-started-google-antigravity

[^3_6]: https://antigravity-ide.com

[^3_7]: https://antigravityide.help

[^3_8]: https://en.wikipedia.org/wiki/Google_Antigravity

[^3_9]: https://lilys.ai/en/notes/google-antigravity-20260106/use-unlimited-antigravity-free

[^3_10]: https://dev.to/fabianfrankwerner/an-honest-review-of-google-antigravity-4g6f

[^3_11]: https://dev.to/blamsa0mine/google-antigravity-public-preview-what-it-is-how-it-works-and-what-the-limits-really-mean-4pe

[^3_12]: https://www.datastudios.org/post/google-antigravity-free-access-and-gemini-3-trials-availability-limits-and-what-users-can-access


---

# ok so research ideal prd structure that incorporates conductor

Based on comprehensive research of Google's Conductor documentation and best practices from the AI development community, here's the ideal PRD structure that incorporates Conductor's context-driven development philosophy:

## Conductor PRD Framework

Conductor uses a **three-layer architecture** with persistent Markdown files that live in your repository. The structure emphasizes planning before implementation and maintaining context across sessions.[^4_1][^4_2]

### Core File Structure

```
/your-project
├── .conductor/
│   ├── context.md          # Project-level context (setup phase)
│   ├── constraints.md      # Technical constraints & standards
│   └── workflow.md         # Team workflow preferences
├── tracks/
│   ├── feature-name/
│   │   ├── spec.md         # Feature specification
│   │   └── plan.md         # Implementation plan with checkboxes
│   └── another-feature/
│       ├── spec.md
│       └── plan.md
```


## Ideal PRD Structure for Conductor

### 1. Project Context File (`context.md`)

This is created during `/conductor:setup` and serves as the foundation:[^4_2][^4_1]

```markdown
# Project Context: [Project Name]

## Project Overview
**Type**: [New/Brownfield/Migration]
**Primary Goal**: [One-sentence description]
**Target Users**: [Who uses this]

## Architecture Overview
### Tech Stack
- **Frontend**: [Framework, version]
- **Backend**: [Language, framework]
- **Database**: [Type, version]
- **Infrastructure**: [Cloud provider, key services]

### Key Components
1. **[Component Name]**: [Purpose and location]
2. **[Component Name]**: [Purpose and location]

### Critical Dependencies
- [Dependency 1]: [Why it matters]
- [Dependency 2]: [Why it matters]

## Project Guidelines
### Code Standards
- Style guide: [Link or description]
- Linting: [Rules]
- Testing philosophy: [Approach]

### Architecture Principles
- [Principle 1]: [Description]
- [Principle 2]: [Description]

## Domain Knowledge
### Business Context
[Key business rules, terminology, workflows]

### Historical Decisions
[Important past decisions that inform future work]
```


### 2. Constraints File (`constraints.md`)

Team-wide technical standards:[^4_1][^4_2]

```markdown
# Technical Constraints & Standards

## Testing Strategy
- **Unit Tests**: [Coverage requirement, framework]
- **Integration Tests**: [When required, approach]
- **E2E Tests**: [Scenarios covered]

## Security Requirements
- Authentication: [Method]
- Authorization: [RBAC/ABAC]
- Data protection: [Encryption standards]
- Vulnerability scanning: [Tools, frequency]

## Performance Requirements
- API response time: [< X ms]
- Database query limits: [Guidelines]
- Bundle size: [Maximum]

## Code Review Standards
- Approval requirements: [Number]
- Automated checks: [List]
- Documentation requirements: [What needs docs]

## Deployment Constraints
- Backward compatibility: [Required/Not required]
- Migration strategy: [Zero-downtime/Maintenance window]
- Rollback procedures: [Approach]
```


### 3. Track Specification (`spec.md`)

Created when running `/conductor:newTrack` for each feature:[^4_3][^4_2][^4_1]

```markdown
# Spec: [Feature Name]

## Goal
[Business outcome in non-technical language. What problem does this solve? 
Who benefits? What measurable outcomes do we expect?][page:4]

**Success Metrics**:
- [Metric 1]: [Target]
- [Metric 2]: [Target]

## Context
**Related To**: [Parent epic, product area]
**Priority**: [P0/P1/P2/P3]
**Estimated Complexity**: [Small/Medium/Large]
**Stakeholders**: [PM, Designer, Tech Lead]

## Current Implementation
[Document what exists today that relates to this feature][page:4]

### Relevant Files & Components
**File**: `path/to/file.js`
**Reason**: [Why this needs to change]
**Current Code**:
```javascript
// Current implementation snippet
function currentApproach() {
  // ...
}
```

**File**: `path/to/another/file.py`
**Reason**: [Why this is relevant]
**Current Code**:

```python
# Current pattern
class CurrentPattern:
    pass
```


### Database Schema

[Current tables, relationships affected]

### API Contracts

[Existing endpoints that may change]

## Proposed Solution

[How we'll solve the problem, considering current constraints][page:4]

### Approach

[High-level technical approach]

### Why This Solution?

- **Advantages**: [Benefits]
- **Trade-offs**: [Limitations acknowledged]
- **Alternatives Considered**: [Other options and why rejected]


### Changes Required

#### Backend Changes

- **File**: `service/handler.go`
    - **Change**: [What will change]
    - **Reason**: [Why necessary]


#### Frontend Changes

- **Component**: `Dashboard.tsx`
    - **Change**: [What will change]
    - **Reason**: [Why necessary]


#### Database Changes

- **Migration**: [Description]
- **Backward Compatibility**: [Yes/No and strategy]


### External Impacts

- API changes: [Breaking/Non-breaking]
- Third-party integrations: [Affected systems]
- User-facing changes: [What users will notice]


## Acceptance Criteria

- [ ] [Testable criterion 1]
- [ ] [Testable criterion 2]
- [ ] [Performance requirement met]
- [ ] [Security requirement met]
- [ ] [Tests written and passing]
- [ ] [Documentation updated]


## Out of Scope

[Explicitly state what this does NOT include]

## Risks \& Mitigations

| Risk | Impact | Likelihood | Mitigation |
| :-- | :-- | :-- | :-- |
| [Risk] | High | Low | [Strategy] |

## Open Questions

- [ ] [Question 1]
- [ ] [Question 2]

```

### 4. Implementation Plan (`plan.md`)

Conductor generates this and tracks progress via checkboxes:[^4_2][^4_3][^4_1]

```markdown
# Implementation Plan: [Feature Name]

**Status**: [Not Started/In Progress/Blocked/Complete]
**Started**: [Date]
**Last Updated**: [Auto-updated]

## Phase 1: Setup & Preparation
### Database & Schema
- [ ] Create migration file `YYYY-MM-DD-feature-name.sql`
- [ ] Add migration to version control
- [ ] Test migration rollback procedure
- [ ] Update schema documentation

**Checkpoint 1**: Database changes verified ✓

### Dependencies
- [ ] Update package.json with [library@version]
- [ ] Run dependency audit
- [ ] Update lockfile

## Phase 2: Backend Implementation
### Core Logic
- [ ] Extend `TelemetryAPI` in `telemetry-service.js`
  - Add regional traffic aggregation endpoints
  - Implement 5-minute data caching layer
- [ ] Create unit tests for telemetry aggregation
- [ ] Verify test coverage > 80%

### API Layer
- [ ] Create new endpoint `POST /api/v2/allocate-cdn`
- [ ] Implement rate limiting (100 req/min)
- [ ] Add authentication with rotational keys
- [ ] Write integration tests for endpoint

**Checkpoint 2**: Backend APIs functional ✓

## Phase 3: Frontend Implementation
### UI Components
- [ ] Update `Dashboard.tsx` to call new endpoint
- [ ] Add loading states
- [ ] Add error handling
- [ ] Create unit tests with React Testing Library

### State Management
- [ ] Add Redux actions for CDN allocation
- [ ] Update reducers
- [ ] Test state transitions

**Checkpoint 3**: Frontend integrated ✓

## Phase 4: Integration & Testing
### Integration Tests
- [ ] End-to-end test: CDN allocation flow
- [ ] Test error scenarios (API down, timeout)
- [ ] Load test with 1000 concurrent requests

### Performance Validation
- [ ] Verify API response < 200ms
- [ ] Check database query performance
- [ ] Monitor memory usage

**Checkpoint 4**: All tests passing ✓

## Phase 5: Deployment
### Pre-deployment
- [ ] Code review approved by 2 reviewers
- [ ] Security scan passed
- [ ] Staging environment tested
- [ ] Rollback plan documented

### Deployment Steps
- [ ] Deploy database migration
- [ ] Deploy backend service (blue-green)
- [ ] Deploy frontend build
- [ ] Verify monitoring alerts

### Post-deployment
- [ ] Monitor error rates for 24 hours
- [ ] Check performance metrics
- [ ] Update documentation
- [ ] Close related tickets

**Final Checkpoint**: Feature deployed successfully ✓

## Notes & Decisions
[Agent and human can add notes during implementation]

### [Date] - Technical Decision
**Decision**: [What was decided]
**Rationale**: [Why]
**Alternative**: [What was considered]
```


## Conductor Workflow Commands

The three-step workflow:[^4_4][^4_1][^4_2]

1. **Setup**: `/conductor:setup` - Creates `context.md`, `constraints.md`, `workflow.md`
2. **Track Creation**: `/conductor:newTrack` - Generates `spec.md` and `plan.md` for a feature
3. **Implementation**: `/conductor:implement` - Agent executes the plan, checking off tasks

## Key Principles for Conductor PRDs

**Plan Before Build**: Resist code-first instincts; invest in context-rich specifications[^4_3][^4_1]

**Persistent Context**: All specs live in repository, not chat logs[^4_1][^4_2]

**Resumable Work**: Checkboxes in `plan.md` allow pausing/resuming without context loss[^4_2][^4_1]

**Team Consistency**: Shared `constraints.md` ensures all AI contributions follow team standards[^4_1][^4_2]

**Brownfield Friendly**: Conductor explicitly documents current implementation before proposing changes[^4_3][^4_2]

This structure transforms your repository into a "single source of truth that drives every agent interaction with deep, persistent project awareness", perfectly aligning with Conductor's context-driven philosophy for your Brownfield project.[^4_2]
<span style="display:none">[^4_10][^4_11][^4_12][^4_5][^4_6][^4_7][^4_8][^4_9]</span>

<div align="center">⁂</div>

[^4_1]: https://www.infoq.com/news/2026/01/google-conductor/

[^4_2]: https://www.youtube.com/watch?v=MAUpppfg9Go

[^4_3]: https://www.youtube.com/watch?v=EWJ_C4s9w5o

[^4_4]: https://www.youtube.com/watch?v=TT9LtLeI5nk

[^4_5]: https://developers.googleblog.com/conductor-introducing-context-driven-development-for-gemini-cli/

[^4_6]: https://github.com/hridaya423/conductor-tasks

[^4_7]: https://growthx.club/learn/templates/prd-googles-product-requirement-template

[^4_8]: https://ona.com/stories/software-conductors-handbook

[^4_9]: https://concordion.org/documenting/java/markdown/

[^4_10]: https://www.leanware.co/insights/prd-template-google-docs

[^4_11]: https://atalupadhyay.wordpress.com/2025/12/23/google-conductor-context-driven-development-for-ai-assisted-coding/

[^4_12]: https://spec-md.com

