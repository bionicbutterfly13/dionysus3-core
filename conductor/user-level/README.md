# User-Level Best Practices (Above Project)

This directory holds a **user-level** copy of session best practices so they apply to **all** your projects, not only this repo. Install into your home config for **Claude**, **Gemini**, or **Codex** as below.

**Source:** [Anthropic – Best Practices for Claude Code](https://code.claude.com/docs/en/best-practices). Same content as `.conductor/best-practices.md` in this repo.

---

## Claude (user level)

**Location:** `~/.claude/`

- Claude Code loads `~/.claude/CLAUDE.md` at the start of **every** session (all projects).
- To add best practices at user level (from this repo root):
  1. Ensure `~/.claude/` exists: `mkdir -p ~/.claude`
  2. Copy: `cp conductor/user-level/best-practices.md ~/.claude/best-practices.md`
  3. In `~/.claude/CLAUDE.md`, add at the top (or in a prominent section):
     ```markdown
     # User-level instructions (all projects)
     At session start, read and apply the best practices in this directory.
     See @~/.claude/best-practices.md for session practices (verify work, explore→plan→code, context management).
     ```
     If your tool supports `@path` imports, you can instead put only: `See @~/.claude/best-practices.md` and keep the full content in `best-practices.md`. Otherwise, paste the contents of `best-practices.md` into `~/.claude/CLAUDE.md`.

- **Result:** Every Claude session (any project) gets these practices unless the project overrides them.

---

## Gemini (user level)

**Location:** `~/.gemini/`

- Gemini CLI loads a **global context file** from `~/.gemini/<<context.fileName>>`. Default is `GEMINI.md`; you can add `best-practices.md`.
- To add best practices at user level (from this repo root):
  1. Ensure `~/.gemini/` exists: `mkdir -p ~/.gemini`
  2. Copy: `cp conductor/user-level/best-practices.md ~/.gemini/best-practices.md`
  3. In `~/.gemini/settings.json`, set context to load both your user GEMINI.md and best-practices:
     ```json
     {
       "context": {
         "fileName": ["GEMINI.md", "best-practices.md"]
       }
     }
     ```
     The CLI loads `~/.gemini/GEMINI.md` and `~/.gemini/best-practices.md` first (global), then project files. Create `~/.gemini/GEMINI.md` if you want user-level project instructions; use `best-practices.md` for the shared session practices.
  4. Run `/memory refresh` in a Gemini session to reload context after changes.

- **Result:** Every Gemini session (any project) gets these practices as part of the hierarchical context (user level above project level).

---

## Codex (user level)

**Location:** `~/.codex/`

- Codex loads global instructions from `~/.codex/AGENTS.md` (and optionally project `AGENTS.md`). There is no separate context filename list like Gemini's `context.fileName`.
- To add best practices at user level (from this repo root):
  1. Ensure `~/.codex/` exists: `mkdir -p ~/.codex`
  2. Copy: `cp conductor/user-level/best-practices.md ~/.codex/best-practices.md`
  3. In `~/.codex/AGENTS.md`, add at the top or in a prominent section:
     ```markdown
     # User-level instructions (all projects)
     At session start, read and apply the best practices in this directory.
     See @~/.codex/best-practices.md for session practices (verify work, explore→plan→code, context management).
     ```
     If your tool supports `@path` imports, reference `best-practices.md`; otherwise paste or summarize the contents into `~/.codex/AGENTS.md`.

- **Result:** Every Codex session (any project) gets these practices when AGENTS.md is loaded.

---

## Summary

| Tool   | User-level config        | How best practices apply |
|--------|---------------------------|---------------------------|
| Claude | `~/.claude/CLAUDE.md` (+ optional `~/.claude/best-practices.md`) | Add “read/apply @~/.claude/best-practices.md” or paste content into CLAUDE.md. |
| Gemini | `~/.gemini/settings.json` + `~/.gemini/best-practices.md` | Set `context.fileName` to include `best-practices.md`; CLI loads it globally before project context. |
| Codex  | `~/.codex/AGENTS.md` (+ optional `~/.codex/best-practices.md`) | Reference or paste best practices in AGENTS.md so they load at session start. |

After install, best practices apply **above** project-level instructions in every new session.
