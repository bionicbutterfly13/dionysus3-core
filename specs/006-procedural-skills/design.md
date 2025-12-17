# Design Notes: Procedural Memory as Skills

## Why `Skill` is procedural memory

Procedural memory is not an “idea” (ThoughtSeed). It is an executable capability that:
- improves with practice (`proficiency`, `practice_count`)
- decays with disuse (`decay_rate`, `last_practiced`)
- composes and decomposes (`HAS_SUBSTEP`)
- depends on prerequisites (`REQUIRES`)
- transfers across applicability contexts (`APPLIES_TO`)
- has provenance (`LEARNED_FROM`)

## Integration boundaries

- Neo4j remains the source of truth for all memory graph data.
- The application never connects to Neo4j directly; all Cypher flows through n8n webhooks.
- `skill_graph` traversal is exposed as a vetted query through `/webhook/memory/v1/traverse`.

## Open questions (tracked in plan.md)

- Do we standardize `Context` as a dedicated label with a stable `context_id`?
- Do we want `Skill` nodes to link to `ThoughtSeed` (ideation → skill formation), or keep them separate with only shared provenance via `Document/Session`?

