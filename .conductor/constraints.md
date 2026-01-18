# Technical Constraints & Standards

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

## "Ultrathink" Protocols
- **Depth**: Code must reflect the "System Soul" (Analytical Empath).
- **Identity**: System must maintain "Voice" consistency.
