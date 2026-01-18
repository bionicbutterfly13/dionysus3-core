# Team Workflow Preferences

## Conductor Lifecycle
1.  **Setup**: Define `context.md` and `constraints.md` (Done).
2.  **New Track**: Use `specs/` (Legacy) or `tracks/` (Future) to define features.
3.  **Plan**: Create `plan.md` (Implementation Plan) for every major feature.
4.  **Execute**: Agents follow the plan, verifying against Constraints.

## Spec-Driven Development
- **Source of Truth**: The Spec is the law.
- **Drift**: If code diverges from Spec, update the Spec first.
- **Review**: "Ultrathink" analysis required for major architectural changes.

## Global MCP Integration
- **Serena**: Use `create_memory` / `search_memories` for state persistence.
- **NotebookLM**: Use for digesting research (PDFs) into constraints.
