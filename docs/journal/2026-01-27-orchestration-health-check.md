---
title: "Orchestration Health Check — What’s Good, Broken, Works-But-Shouldn’t, Pretends-To"
date: 2026-01-27
tags: [conductor, ralph, wake-up, memory-layers, session-reconstruct, health-check]
---

# Orchestration Health Check

**Lens:** New orchestration architecture — Conductor (workflow, constraints, tracks, plan/spec), Ralph, wake-up (including second part and agent roster), memory layers (MemEvolve/Graphiti/Nemori + client SuperMemory/cognee), session-reconstruct, setup.sh, 149-agent roster.

**Date:** 2026-01-27

---

## 1. What’s good

- **Conductor structure**: `.conductor/constraints.md` and `conductor/workflow.md` exist and are referenced before code. TDD, plan tracking in `conductor/tracks/*/plan.md`, and feature-branch discipline are spelled out. Tracks have `spec.md` and `plan.md` with `[ ]` / `[~]` / `[x]` and commit SHA.

- **Wake-up rule**: `.cursor/rules/conductor-wake-up.mdc` is `alwaysApply: true` and enforces: read constraints → read workflow → output `Constraints and workflow loaded.` before any other action, then fulfill the user’s initial request. It also defines the “second part” (execute the request), the 149-agent roster at `~/.claude/agents/`, review-before-write, and Required Memory Setup (SuperMemory + cognee, `./setup.sh`).

- **Memory stack documentation**: `.conductor/constraints.md` documents Memory Stack Integration, MemEvolve Protocol, and outlet/injection points. `docs/journal/2026-01-27-memory-layers-client-server-implementation.md` describes server (MemEvolve, Graphiti, Nemori) vs client (SuperMemory + cognee MCP), the data-passing bridge (`POST /api/session/reconstruct`), and implementation-level detail (file:line, Cypher, wire formats).

- **Session-reconstruct API**: `api/routers/session.py` exposes `POST /api/session/reconstruct`; request includes `project_path`, `device_id`, `cues`; response includes `compact_context` and episodic memories. It uses `get_reconstruction_service()` and the 10-step reconstruction protocol. Health endpoint exists for session-reconstruct dependencies.

- **Client/server split**: README § Required Memory Setup states that SuperMemory + cognee are client-side (IDE/session MCP) and MemEvolve/Graphiti/Nemori are server-side. `setup.sh` installs SuperMemory MCP and cognee and configures MCP for VS Code / Claude Code / Cline/Cursor.

- **Ralph + Conductor in CLAUDE.md**: Ralph is described as mandatory for complex features (5+ tasks, architectural decisions, integration). Conductor + Ralph flow (tracks → Ralph coordination → spec verification → quality gates) is documented. Skills and `conductor/workflow.md` § Cross-Agent Coordination support multi-agent claiming (`[~]` + CLAIMED, `[x]` + SHA).

- **Three Towers alignment**: Constraints and wake-up require checking alignment with Graphiti Episode, MemEvolve Trajectory, and Nemori Narrative before writing memory-related code.

---

## 2. What’s broken

- **BeliefState in verification script**: `scripts/verification/test_active_inference_integration.py` imports `BeliefState` from `api.services.active_inference_service`. That module does not export `BeliefState` (it uses `BeliefState as CanonicalBeliefState` from `api.models.belief_state` internally). The script also uses `BeliefState(qs=np.array(...))`, while `api.models.belief_state.BeliefState` is defined with `mean` and `precision`, not `qs`. So the script fails on import and, if imports were fixed, would fail on constructor usage. **Fix:** Export `BeliefState` from the service and align constructor usage, or import from `api.models.belief_state` and adapt the tests; alternatively gate or move this script so pytest does not collect it when run from the repo root.

- **Pytest vs verification scripts**: `pyproject.toml` has `testpaths = ["tests", "."]`. Collecting from `"."` can pull in `scripts/verification/test_*.py`. Those scripts are written as standalone verification programs (e.g. Julia integration, print-based output), not pytest tests, and at least one has an invalid import. That makes collection fragile or failing. **Fix:** Restrict `testpaths` to `["tests"]` only, or exclude `scripts/` in pytest config so verification scripts are not collected.

---

## 3. What works but shouldn’t

- **ReconstructionService defaults to no Graphiti entity scan**: `get_reconstruction_service()` in `api/services/reconstruction_service.py` instantiates `ReconstructionService()` with no arguments. The constructor default is `graphiti_enabled=False`. Therefore the entity-scan path (`_scan_entities` when `graphiti_enabled` is True) is never run in normal usage. The memory-layers journal and reconstruction protocol describe entity scanning as part of reconstruction. So the current default contradicts the intended design. **Fix:** Either default `graphiti_enabled=True` where the deployment has Graphiti available, or make the default configurable via env and document it in README / constraints.

- **Two workflow files as “source of truth”**: AGENTS.md (and README) say “Source of truth: `.conductor/workflow.md` and `conductor/workflow.md`”. The two files differ: `.conductor/workflow.md` is short “Team Workflow Preferences” (Serena, NotebookLM, Spec-Driven); `conductor/workflow.md` is the full “Project Workflow” (TDD, plan.md, constraints, git notes, Cross-Agent Coordination). Treating both as equal sources of truth invites drift and ambiguity. **Fix:** Designate one as canonical (e.g. `conductor/workflow.md` for execution) and have the other explicitly defer to it, or merge and maintain a single workflow doc.

- **Verification scripts in the tree**: Scripts under `scripts/verification/test_*.py` look like tests but are built to be run by hand (e.g. `python scripts/verification/test_active_inference_integration.py`) and may depend on Julia or other heavy env. As long as `testpaths` includes `"."`, they can be collected by pytest, mixing them with unit tests. **Fix:** Either rename/move so they are not collected (e.g. `scripts/verification/run_*.py` or exclude via pytest), or turn them into proper pytest tests under `tests/` with appropriate markers/skips for external deps.

- **Cognee only in client tooling**: Cognee was removed from `pyproject.toml` and `requirements.txt`. It remains in `setup.sh` (`pip3 install cognee`) and in README / conductor-wake-up as “SuperMemory + cognee.” So the *app* does not depend on cognee; the *client* setup still does. If the intent is “cognee is client-only,” that’s consistent but should be explicit (e.g. “cognee is installed by setup.sh for MCP only, not in app deps”). If the intent was to drop cognee entirely, then setup.sh and docs still pretend it’s required. **Fix:** Align docs and setup.sh with the chosen policy (client-only vs removed) and state it clearly in README § Required Memory Setup.

---

## 4. What doesn’t but pretends to

- **Verification script as a passing test**: `test_active_inference_integration.py` assumes a working `BeliefState` import from the service and a `qs`-based constructor. Neither exists in the current API. The script “pretends” to be a test of active-inference integration but will fail on import or first use. Any automation or track (e.g. 096 mental-models-book-integration, 074 integrity-remediation) that assumes this script is a valid test is relying on something that does not hold.

- **Ralph as mandatory**: CLAUDE.md states Ralph is mandatory for complex features and describes Conductor + Ralph integration. The Ralph orchestrator lives in an external, .gitignored directory (`dionysus-ralph-orchestrator/`) and is not in CI or in-repo tooling. Compliance is advisory: nothing enforces “use Ralph for 5+ tasks.” So “mandatory” is policy, not mechanism. **Fix:** Either enforce Ralph in CI/tooling for qualifying tracks, or rephrase in CLAUDE.md as “strongly recommended” and document when to invoke it manually.

- **AGENTS.md as the full agent entrypoint**: AGENTS.md is short and only states “Conductor Protocol Required” plus a few bullets (constraints, workflow, TDD, plan.md). Wake-up, agent roster, Required Memory Setup, and “review relevant code before writing” live in conductor-wake-up.mdc and CLAUDE.md. Agents that are pointed only at AGENTS.md get an incomplete picture and may skip wake-up, roster awareness, or memory setup. **Fix:** Either expand AGENTS.md with a one-paragraph summary and pointers to conductor-wake-up.mdc and CLAUDE.md for wake-up/roster/memory, or make AGENTS.md explicitly say “After reading this, read .cursor/rules/conductor-wake-up.mdc and CLAUDE.md § Wake-Up / Required Memory Setup.”

---

## Summary table

| Category                 | Items |
|--------------------------|--------|
| **Good**                 | Conductor layout, wake-up rule, memory-stack docs, session-reconstruct API, client/server split, Ralph+Conductor in CLAUDE.md, Three Towers alignment |
| **Broken**               | BeliefState import/usage in `scripts/verification/test_active_inference_integration.py`; pytest collecting from `"."` and pulling in verification scripts |
| **Works but shouldn’t**  | ReconstructionService `graphiti_enabled=False` by default; two workflow files as dual source of truth; verification scripts collectable as tests; cognee only in client tooling while docs/setup still say “SuperMemory + cognee” |
| **Pretends to**          | Verification script as a valid test; Ralph “mandatory” without enforcement; AGENTS.md as complete agent entrypoint |

---

## Suggested next steps

1. **BeliefState**: Fix the verification script (import from `api.models.belief_state` and use `mean`/`precision`, or export from service and align API) or move/gate it so pytest does not depend on it.
2. **Pytest**: Set `testpaths = ["tests"]` or add an exclude for `scripts/` so verification scripts are not collected.
3. **ReconstructionService**: Introduce an env-based or config-based default for `graphiti_enabled` and document it; or change the default to `True` where Graphiti is always available.
4. **Workflow**: Choose one workflow file as canonical and have the other reference it, or merge into one.
5. **Cognee**: Decide “client-only” vs “removed” and update README, conductor-wake-up, and setup.sh accordingly.
6. **Ralph**: Either add enforcement (CI/tooling) for complex tracks or soften “mandatory” to “strongly recommended” in CLAUDE.md.
7. **AGENTS.md**: Add a short “next steps” block that points to conductor-wake-up.mdc and CLAUDE.md for wake-up, roster, and memory setup.
