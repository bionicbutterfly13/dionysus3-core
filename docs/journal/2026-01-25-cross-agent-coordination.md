# Cross-Agent Coordination via Conductor

**Date:** 2026-01-25  
**Context:** Conductor workflow, multi-agent development (Claude, Codex, Gemini, Cursor)  
**Focus:** How agents across systems signal "I'm working on this" and avoid double-working the same task.

---

## Why

When multiple AI coding agents (Claude, Gemini, Codex, Cursor, etc.) work on the same repo, they need a simple way to:

- Know which tasks are **available** vs **in progress**
- **Claim** a task before starting so others skip it
- **Release** when done so others can pick it up

Without that, two agents can both mark a task `[~]` and do the same work, or block each other.

---

## What We Did

We documented a **cross-agent coordination** protocol that uses the **shared git repo** as the source of truth. No external service—just `plan.md`, git, and a consistent convention.

### Protocol (short)

1. **Pull first** — `git pull` before claiming. Get latest `plan.md` and branches.
2. **Respect `[~]`** — Tasks marked `[~]` are in progress. Pick only `[ ]` tasks.
3. **Claim** — When starting: set task to `[~]`, add `(CLAIMED: <agent-id>)`, commit, **push**.
4. **Work** — Implement on the feature branch (TDD, etc.) as usual.
5. **Release** — Mark `[x]`, remove `(CLAIMED: ...)`, append commit SHA, commit, push.

**Agent IDs:** Use a **session-unique** label. Single agent of your type → `Claude`, `Gemini`, `Codex`, `Cursor` is fine. **Multiple** same-type agents (e.g. several Composer tabs, multiple Codex) → each uses a **distinct** ID: `CONDUCTOR_AGENT_ID` if set, or `Claude-Composer-1`, `Codex-workspace-a`, etc. Same ID for the whole session.

### Example in `plan.md`

```text
- [ ] T014 Implement PrecisionProfile
- [~] T015 Implement EpistemicState (CLAIMED: Gemini)
- [x] T013 Write tests for event types (a1b2c3d)
```

---

## Where It’s Documented

- **`conductor/workflow.md`** — § Cross-Agent Coordination; Standard Task Workflow updated (pull → claim → push → work → release).
- **`AGENTS.md`** — § Cross-Agent Coordination.
- **`.conductor/workflow.md`** — Brief coordination reminder.
- **`CLAUDE.md`**, **`GEMINI.md`** — Cross-agent bullets in Task Management / Wake-Up.
- **`~/.claude/CLAUDE.md`** — User-level Conductor workflow step 5 updated.

---

## Design Choices

- **Git-only:** No new services, boards, or APIs. Every agent that has the repo can participate.
- **Plan as ledger:** `plan.md` already tracks `[ ]` / `[~]` / `[x]`. We added `(CLAIMED: <id>)` so *who* is working is visible.
- **Push the claim:** Claim is committed and pushed *before* doing the work, so others see it as soon as they pull.
- **Same pattern as docs backlog:** `docs/DOCUMENTATION_BACKLOG.md` already uses `(CLAIMED: Agent-X, Branch: ...)`. We aligned Conductor task claims with that idea.
- **Multiple same-type agents:** When several Claude, Codex, or Composer agents run at once, each must use a **distinct** ID (e.g. `Claude-Composer-1`, `Codex-workspace-a`). Otherwise they’d all claim as "Claude" or "Codex" and can double-work or overwrite each other’s claims.

---

## Links

- [Conductor workflow (Cross-Agent Coordination)](../../conductor/workflow.md)  
- [AGENTS.md](../../AGENTS.md)  
- [Documentation Backlog claiming pattern](../DOCUMENTATION_BACKLOG.md)

---

## User Notes

<!-- Add your permanent notes here. The system will respect this section. -->
