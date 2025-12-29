# Context State Recovery: Dionysus Core Evolution
**Date:** 2025-12-28
**Status:** Infrastructure Stabilized | Awaiting Systematic Ingestion

## 1. Core Architecture (The "Clean Room" State)
- **Primary LLM:** `openai/gpt-5-nano` (via LiteLLM). Configured to omit `max_tokens` to prevent truncation.
- **Embedding Model:** `text-embedding-3-small` (OpenAI).
- **Vector Dimensions:** Unified at **1536** across the entire pipeline.
- **Neo4j Index:** `memory_embedding` has been dropped and recreated with 1536 dimensions.
- **Current Database State:** **Empty.** Previous ingestion attempts rolled back due to dimension mismatches. It is now a clean slate ready for high-fidelity data.

## 2. Infrastructure & Connectivity
- **Networking:** `dionysus-api` is now joined to the `dionysus_default` external docker network.
- **n8n Access:** API communicates with n8n via `http://n8n:5678`. DNS resolution is verified.
- **Service Bridge:** `claude.py` has been fully replaced by `llm_service.py`. All imports are updated.
- **Monitoring:** `monitoring_pulse.py` and `journal_service.py` are active and enabled in `main.py`.
- **Documentation:** SilverBullet is running on VPS port 3000, bound to `127.0.0.1` (access via SSH tunnel `-L 3000:127.0.0.1:3000`).

## 3. Data Locations (VPS: 72.61.78.89)
- **Archives:** 709 conversation files at `/home/mani/dionysus-api/data/archives/`.
- **Ground Truth:** 5 strategy files at `/home/mani/dionysus-api/data/ground-truth/`.
- **Logs:** `wisdom_fleet.log` contains the trace for the background distillation process.

## 4. Immediate Next Steps (The Systematic Plan)
1. **Resume Wisdom Fleet:** Launch `scripts/run_wisdom_fleet.py` in the background to process the 709 archives (starting from batch 1 due to the clean-room state).
2. **Ingest Ground Truth:** Systematic ingestion of the 5 files in `data/ground-truth/` using the `smolagents` protocol.
3. **Verify Signal:** Confirm entities appear in the "New Knowledge Entities" section of the SilverBullet Daily Journal.
4. **Prime Directive Audit:** Ensure all extractions adhere to the "Fine-tuning for the next level" frame.

## 5. Critical Commands
- **Restart API:** `docker compose up -d --force-recreate dionysus-api`
- **Check Progress:** `tail -f wisdom_fleet.log`
- **Verify Graph:** `MATCH (n:Entity) RETURN count(n)`
