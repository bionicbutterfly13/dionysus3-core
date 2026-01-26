# Technical Constraints & Standards

## Pre-Code Requirement (Mandatory)

- **Before writing or changing any code**, agents must read this file and follow all constraints below. If unsure, stop and re-read.

## Testing Strategy

- **Unit Tests**: Required for all new Services and Agents.
- **Integration Tests**: Required for MCP tools and Neo4j interactions.
- **E2E Tests**: Critical for the OODA loop (Heartbeat).

## Security Requirements

- **Authentication**: Webhook signatures (HMAC-SHA256) for n8n communication.
- **Environment**: No hardcoded API keys. Use `.env`.
- **VPS**: SSH Tunnel required for Neo4j access (localhost:7687 -> VPS:7687).

## Performance Requirements

- **Inference**: Optimized for `gpt-5-nano` (or equivalent efficient models).
- **Graph**: Index critical paths (Entity IDs, Timestamps).
- **Startup**: API must be healthy within 30 seconds.

## Deployment Constraints

- **Docker**: All services must be containerized.
- **Migration**: Schema changes must be additive or explicitly migrated via scripts.
- **Rollback**: Feature 021 implements rollback safety nets.

## Integration & Depth Policy (No Orphan Code)

**Mandatory.** All feature work **and any code you touch** must satisfy this policy. Verify against it before marking tasks complete and when reviewing commits.

- **No orphan code or stubs.** Do not add services, endpoints, or modules that are never invoked, that return hardcoded placeholders, or that have no callers in the live codebase. Every new piece of code must be reachable from an existing entry point (API, agent, callback, scheduled job, or other integrated component).
- **No disconnected features.** Every feature must have **explicit integration points**: where it attaches to the existing system, what it consumes, and what it produces. Code that "does something in isolation" but is never wired into the OODA loop, APIs, memory systems, or other core flows is rejected.
- **No garbage plug-and-play.** Do not wire in new code, add callers, or change integration points without understanding and documenting the flow. Every attachment must have clear **inlets** (what this code receives and from where) and **outlets** (what it produces and where it sends). Verify the piece fits the pipeline before and after your change.
- **Code you touch must have clear inlet/outlet.** When you **open or modify** any file—new or existing—apply the same standard. If that code **lacks** clear inlet/outlet documentation and you cannot see how it fits the pipeline:
  - **Figure out where it goes.** Trace callers and callees, routers, services, and data flow until you understand attachment points, inputs, and outputs.
  - **Document it.** Add or update module- or function-level comments (or the track's `plan.md` Integration / IO Map) with: **Inlets:** what this code receives and from where; **Outlets:** what it produces and where it sends.
  - **Ensure integrity.** Confirm the code actually fits the pipeline (is invoked, consumes real inputs, produces used outputs). If it does not—orphan, stub, or dead path—fix or remove it; do not leave it as undocumented, half-wired "plug and play."
- **Evaluate commits for depth and integration.** When completing a task or reviewing a PR, check that the change:
  - Implements real behavior (not TODOs or stub implementations).
  - Is integrated: called from routers, agents, services, or tests that exercise the full path.
  - Persists or reads data through approved paths (e.g. Graphiti, n8n webhooks, API) where applicable—not via one-off or local-only mechanisms.
  - Leaves touched code with clear inlet/outlet documentation where it was missing.
- **Document integration in the plan.** For every feature track, `plan.md` **must** include an **Integration (IO Map)** section that specifies:
  - **Attachment points:** Exact files, routers, or services where the feature plugs in (e.g. `api/routers/beautiful_loop.py`, `ConsciousnessManager.run_cycle`).
  - **Inputs:** What the feature receives and from where (e.g. context from `HeartbeatAgent`, precision profile from `HyperModelService`, webhook payload from n8n).
  - **Outputs:** What it produces and where it sends results (e.g. `UnifiedRealityModel` updates, EventBus events, API responses, Graphiti writes).

Create or update this section when the track is created; revise it if attachment points or data flow change during implementation.

## "Ultrathink" Protocols

- **Depth**: Code must reflect the "System Soul" (Analytical Empath).
- **Identity**: System must maintain "Voice" consistency.
