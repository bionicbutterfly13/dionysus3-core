# Implementation Plan: Procedural Memory as Skills

**Feature**: `006-procedural-skills`  
**Prerequisites**: `specs/006-procedural-skills/spec.md`

## Phase 0: Clarifications (complete before implementation)

- Confirm canonical identifier fields:
  - `Skill.skill_id` is the stable ID (string/UUID).
  - `Document.document_id` is stable ID.
  - `Session.id` is stable ID.
- Confirm whether `Context` is a dedicated label with its own properties, or an existing label reused.

## Phase 1: Contracts (n8n + API)

- Add traversal contract `query_type=skill_graph` under `/webhook/memory/v1/traverse`.
- Ensure `POST /api/memory/traverse` passes through `query_type` + `params` without direct Neo4j access.
- Document required env vars:
  - `N8N_TRAVERSE_URL`
  - `N8N_CYPHER_URL`
  - `MEMORY_WEBHOOK_TOKEN`

## Phase 2: Schema (Neo4j)

- Add constraints and indexes for `Skill`:
  - Unique constraint on `Skill.skill_id`
  - Index on `Skill.name`
  - Optional: index on `Skill.proficiency`

## Phase 3: Integration (optional follow-on)

- Add skill upsert workflow (n8n) for creating/updating skills from procedural learning events.
- Add practice update workflow (n8n) to increment `practice_count`, update `last_practiced`, and decay older skills.

## Phase 4: Validation

- Contract test: `/api/memory/traverse` accepts `skill_graph` and forwards to n8n.
- Integration test: requires n8n + Neo4j running; validate traversal returns expected structure.

