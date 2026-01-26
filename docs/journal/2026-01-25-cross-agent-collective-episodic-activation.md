# Cross-Agent Collective Episodic Memory: Activation Without Noise

**Date:** 2026-01-25  
**Context:** Cross-agent coordination, wake-up protocol, session reconstruction, Multi-Tier Memory  
**Focus:** How to activate *collective* episodic memory (many agents, one store) for an agent at wake-up **without noise**, and whether **branch access** is involved.

---

## The Problem

- **Collective episodic memory:** Multiple agents (Claude, Codex, Gemini, Cursor, etc.) produce episodes. One shared store (Graphiti, n8n/Neo4j, MemEvolve). Recall is over *everyone’s* episodes.
- **Noise:** Unscoped recall dumps unrelated episodes—other branches, other tracks, other agents’ work—into context. Token bloat, relevance collapse, confused reasoning.
- **Goal:** Activate only the **right** subset of collective memory at wake-up: relevant to *this* agent, *this* branch, *this* track, *now*.

---

## Does It Involve Branch Access?

**Yes—but only read-only.**

- **Branch access** = the agent (or the client calling the gateway) can read:
  - `git branch --show-current` → current branch (e.g. `feature/074-integrity-remediation`)
  - `git status`, `git log -1 --oneline` → optional extras
- **No write.** We never use branch access to push, merge, or modify git. Only to **scope retrieval**.

Branch (and track) become **retrieval keys**: “episodes that happened on *this* branch” or “associated with *this* track” are prioritized or filtered. Everything else is deprioritized or excluded → less noise.

---

## Brainstorm: Mechanisms

### 1. **Branch + track as retrieval scope**

- Add `branch` and `track_id` (e.g. `074`) to `ReconstructionContext` (and to any recall API that feeds wake-up).
- **At ingest:** When we store episodes (MemEvolve, consciousness core, n8n), tag them with `branch`, `track_id`, `agent_id` when available. Caller or ingest pipeline derives these from git + Conductor (e.g. `plan.md`, `tracks.md`).
- **At recall:** Filter episodic retrieval by `(branch, track_id)` first. Only then apply semantic similarity / resonance. Result: activation is **pre-scoped** to the current feature/track.

**Pros:** Strong noise reduction. **Cons:** Requires ingest and recall both to handle branch/track.

---

### 2. **Resonance boost for same-branch (no schema change)**

- Keep episodic schema as-is. Add `branch` and `track_id` to `ReconstructionContext` only.
- In **context resonance** (e.g. `_calculate_context_resonance`): if a fragment’s metadata contains `branch` / `track_id`, and it matches the context’s branch/track, add a strong bonus. Others get no bonus (or a penalty).
- Episodic scan still uses `project_name` + `cues`; we don’t filter explicitly. But same-branch/track fragments rank higher and dominate the top-k. Cross-branch fragments sink.

**Pros:** Minimal change; works with existing ingest. **Cons:** Noise reduced but not removed; still pulling cross-branch episodes into the candidate set.

---

### 3. **Cues = branch + track (no new fields)**

- Don’t add `branch` / `track_id` to the API. Client passes e.g. `cues: ["feature/074-integrity-remediation", "074", "integrity"]`.
- Existing cue-based resonance uses these. Episodes that mention the branch or track get higher cue resonance.

**Pros:** No backend changes. **Cons:** Coarse; any fragment mentioning “074” or “integrity” gets boosted, including off-branch work. Noisier than explicit scope.

---

### 4. **Headlines-first, expand on demand**

- First recall returns only **compact summaries** (e.g. “T014 completed on `feature/074-foo` by Claude”, “Phase 2 checkpoint”) with minimal payload.
- Agent gets a short “Recent work on this branch/track” block. Full episode payload only on a second, explicit request (e.g. “expand episode X”).

**Pros:** Low-token activation; less noise from verbose content. **Cons:** Requires two-phase recall and possibly UI/UX support.

---

### 5. **Gateway recall API: branch-aware**

- Extend recall endpoints (e.g. `/api/session/reconstruct`, MemEvolve `/recall`, or n8n recall webhook) with optional `branch`, `track_id`.
- Gateway (Dionysus API) passes these to Graphiti / n8n. Backend filters or re-ranks by branch/track before returning.

**Pros:** Single, consistent place to enforce scope. **Cons:** Depends on Neo4j/Graphiti/n8n supporting branch/track filters or metadata.

---

### 6. **Wake-up flow with branch-scoped activation**

1. Agent wakes.
2. Reads `AGENTS.md`, workflow, `plan.md`, `spec.md` ( Conductor wake-up ).
3. Runs `git branch --show-current`; infers `track_id` from branch name or `plan.md` / `tracks.md`.
4. Calls e.g. `POST /api/session/reconstruct` with `project_path`, `project_name`, `cues`, **`branch`**, **`track_id`**.
5. Receives **branch/track-scoped** episodic memories + `compact_context`.
6. Injects that into the session as “Collective episodic context (this branch/track): …”.

Noise stays low because retrieval is **pre-scoped** by branch (and track). Branch access is **read-only** and used only to build that scope.

---

## Summary

| Mechanism | Branch access? | Noise reduction | Effort |
|-----------|----------------|------------------|--------|
| Branch + track as retrieval scope | Read-only | Strong | Medium (ingest + recall) |
| Resonance boost same-branch | Read-only | Moderate | Low |
| Cues = branch/track | Read-only | Weak | None |
| Headlines-first, expand on demand | Optional | Strong (token-level) | Medium |
| Gateway recall API branch-aware | Read-only | Strong | Medium |
| Wake-up flow with branch-scoped activation | Read-only | Strong | Low once 1 or 5 in place |

**Recommendation:** Use **branch access** (read-only) to derive `branch` and `track_id`, and feed them into **retrieval scope** (1) and/or **gateway recall** (5). Add **resonance boost for same-branch** (2) as a lightweight complement. Optionally add **headlines-first** (4) to cap activation size. That yields collective episodic activation that is **scoped, low-noise, and branch-aware** without requiring git write access.

---

## User Notes

<!-- Add your permanent notes here. -->
