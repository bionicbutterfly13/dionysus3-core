# Best Practices for Agent Sessions

**Source:** [Anthropic – Best Practices for Claude Code](https://code.claude.com/docs/en/best-practices).  
**Role:** Loaded at session start and applied whenever agents plan, code, or verify.

---

## 1. Give agents a way to verify their work

- **Include tests, expected output, or success criteria** so the agent can check itself. This is the single highest-leverage improvement.
- Without clear verification, the agent may produce something that looks right but does not work; you become the only feedback loop.
- Prefer: "Implement X; here are example inputs/outputs; run the tests after implementing."
- For fixes: "Fix this error [paste]. Verify the build/tests succeed. Address the root cause, do not suppress the error."

---

## 2. Explore first, then plan, then code

- **Separate research and planning from implementation** to avoid solving the wrong problem.
- Workflow: **(1) Explore** – read files, answer questions, no edits. **(2) Plan** – produce a concrete plan (files, flow, steps). **(3) Implement** – code and tests against the plan. **(4) Commit** – descriptive commit and, when relevant, PR.
- When the scope is clear and the change is small (typo, log line, rename), skip the plan and implement directly.
- Plan when: approach is uncertain, many files change, or the code is unfamiliar. If the diff can be described in one sentence, planning is optional.

---

## 3. Provide specific context

- **Precise instructions reduce rework.** Reference specific files, constraints, and patterns.

| Do | Example |
|----|--------|
| Scope the task | "In `foo.py`, add tests for the logged-out edge case; avoid mocks." |
| Point to sources | "Look at `ExecutionFactory`’s git history and summarize how its API evolved." |
| Reuse patterns | "Follow the pattern in `HotDogWidget.php` to add a calendar widget (month/year, pagination)." |
| Describe symptom + location + “done” | "Login fails after timeout. Check `src/auth/`, especially token refresh. Add a failing test, then fix it." |

- Vague prompts are acceptable when exploring and you can afford to correct later.

---

## 4. Use rich content

- **@path** – reference files so the agent reads them before replying.
- **Paste images** – screenshots, UI, diagrams.
- **URLs** – docs and API references (use permissions/allowlists for frequent domains).
- **Pipe data** – e.g. `cat error.log | claude`, or your CLI’s pipe/headless mode (Codex, Gemini, etc.).
- **Defer to the agent** – "Pull what you need via Bash, MCP, or file reads."

---

## 5. Configure the environment

- **Project instructions (CLAUDE.md, GEMINI.md, AGENTS.md, etc.):** Keep them short. Include what the agent **cannot** infer from code: commands, style rules, workflow, gotchas. Prune regularly; if a rule is ignored, the file may be too long.
- **Permissions / sandbox:** Use allowlists or sandboxing so safe, repetitive actions don’t require repeated approval. Use `--dangerously-skip-permissions` only in isolated, offline environments.
- **CLI tools:** Prefer `gh`, `aws`, `gcloud`, etc. over raw API calls when context efficiency matters.
- **MCP, hooks, skills, subagents:** Use them for tools, automation, and domain knowledge so main context stays focused.

---

## 6. Communicate effectively

- **Ask codebase questions** like a senior engineer: "How does logging work?" "How do I add an API endpoint?" "What does line 134 do?" "What edge cases does X handle?"
- **For large features:** Have the agent interview you (technical design, UI/UX, edge cases, tradeoffs), then produce a spec. Start a **new session** to implement from that spec so context is clean.

---

## 7. Manage the session

- **Course-correct early:** Stop or rewind as soon as the agent goes off track. After several failed corrections on the same issue, **clear context** and restart with a better, more specific prompt.
- **Manage context aggressively:** Clear context between unrelated tasks (Claude: `/clear`; Gemini: `/memory refresh` or new session; Codex: new session or restart). Long sessions full of irrelevant conversation and file content hurt performance.
- **Use subagents for investigation:** "Use a subagent to investigate X" keeps exploration out of the main context; the main thread stays for planning and implementation.
- **Rewind with checkpoints:** Use rewind/checkpoints to restore conversation or code. Try risky changes; if they fail, rewind and try another approach.
- **Resume conversations:** Use continue/resume and name sessions (e.g. "oauth-migration") so workstreams have stable, findable context.

---

## 8. Automate and scale

- **Headless:** Use your CLI’s headless mode (e.g. `claude -p "prompt"`, Codex, Gemini equivalent) in CI, hooks, or scripts. Use `--output-format json` or `stream-json` when feeding downstream tools.
- **Parallel sessions:** Use multiple sessions for different workstreams, or a Writer/Reviewer pattern (one writes, another reviews in a fresh context).
- **Fan-out:** For big migrations, generate a task list, then loop with headless prompts per item; use allowed-tools flags to limit what each run can do.

---

## 9. Avoid common failure patterns

| Pattern | Fix |
|--------|-----|
| **Kitchen-sink session** – one task, then unrelated asks, then back. Context full of noise. | Clear context between unrelated tasks (e.g. Claude `/clear`, Gemini new session or `/memory refresh`, Codex new session). |
| **Correcting repeatedly** – same mistake, many corrections. Context full of failed attempts. | After ~2 failed corrections, clear context and restart with a sharper prompt that encodes what you learned. |
| **Over-long project instructions** – agent skips or forgets important rules. | Prune. Remove what the agent already does; turn critical rules into hooks if they must be guaranteed. |
| **Trust without verify** – plausible-looking implementation that fails on edge cases. | Always add verification (tests, scripts, screenshots). If it can’t be verified, don’t ship it. |
| **Unbounded exploration** – "investigate X" with no scope; agent reads hundreds of files. | Narrow the investigation or use a subagent so the main context is not filled. |

---

## 10. Develop intuition

- These practices are starting points, not rigid rules. Sometimes you should keep context, skip planning, or use a vague prompt on purpose.
- When output is good, note what helped (prompt shape, context, mode). When it’s bad, ask why: noisy context? vague prompt? task too big?
- Over time, adapt these patterns to your team and codebase.

---

## Integration with Conductor

- **Before code:** Read `.conductor/constraints.md` and follow all constraints.
- **Plan vs execute:** Use Conductor plan/spec and TDD (red → green → refactor). For small, clear fixes, implement directly.
- **Verification:** Prefer tests and concrete success criteria; avoid shipping without a way to verify.
- **Context:** Use Conductor tracks and plan.md to keep work scoped; clear or separate sessions when switching workstreams.
