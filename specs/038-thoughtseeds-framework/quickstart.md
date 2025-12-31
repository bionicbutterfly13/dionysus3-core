# Quickstart: Thoughtseeds Enhancement

## Setup
1. Ensure Neo4j is running.
2. Verify `scipy` and `numpy` are installed.
3. Run initialization scripts to seed `BASAL` priors.

## Testing the Loop
1. Trigger a manual heartbeat: `POST /api/heartbeat/trigger`
2. Observe logs for EFE calculations:
   - "EFE Calculation: Uncertainty=X, Divergence=Y, Total=Z"
3. Verify `InnerScreen` projection:
   - Check `EpisodicMemory` for "Thought Projected to Screen" entries.

## Manual Uncertainty Injection
1. Set a goal with no relevant memories.
2. Verify agent chooses `RECALL` or `RESEARCH` tools (Epistemic dominance).
