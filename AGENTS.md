## Conductor Protocol Required

All agents must follow the Conductor workflow for this repo.

**Agents are failing when they stop here.** This file is a minimal stub. Wake-up, agent roster, Required Memory Setup, and “review relevant code before writing” are **not** in this file—they live in `.cursor/rules/conductor-wake-up.mdc` and `CLAUDE.md`. If you only read AGENTS.md, you skip constraints → workflow → `Constraints and workflow loaded.`, the 149-agent roster, and SuperMemory/cognee setup, and you will fail. **After this, read** `.cursor/rules/conductor-wake-up.mdc` and `CLAUDE.md` § Wake-Up / Required Memory Setup / Ralph.

- **Pre-code requirement:** Before writing or changing any code, read `.conductor/constraints.md` and comply with all constraints.

- Source of truth: `.conductor/workflow.md` and `conductor/workflow.md`
- TDD is mandatory (red → green → refactor)
- Use plan tracking in `conductor/tracks/*/plan.md`
- Use feature branches per item and attach git notes per Conductor steps
