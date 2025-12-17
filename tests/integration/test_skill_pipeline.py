"""
Integration Tests: Skill Upsert/Practice Pipeline
Feature: 006-procedural-skills

End-to-end validation (optional):
- API (RemoteSyncService) -> n8n -> Neo4j
- Verification uses n8n cypher webhook (no direct Neo4j access)

This test is SKIPPED unless the required env vars are set.
"""

from __future__ import annotations

import os
import time
import uuid

import pytest


def _env_ok() -> bool:
    required = [
        "MEMORY_WEBHOOK_TOKEN",
        "N8N_SKILL_UPSERT_URL",
        "N8N_SKILL_PRACTICE_URL",
        "N8N_CYPHER_URL",
    ]
    return all(os.getenv(k) for k in required)


pytestmark = pytest.mark.skipif(
    not _env_ok(),
    reason="Skill pipeline requires n8n webhooks + token (set MEMORY_WEBHOOK_TOKEN, N8N_SKILL_UPSERT_URL, N8N_SKILL_PRACTICE_URL, N8N_CYPHER_URL).",
)


async def _retry(fn, *, attempts: int = 5, delay_s: float = 0.5):
    last_exc = None
    for _ in range(attempts):
        try:
            return await fn()
        except Exception as e:  # pragma: no cover
            last_exc = e
            time.sleep(delay_s)
    raise last_exc  # type: ignore[misc]


@pytest.mark.asyncio
async def test_skill_upsert_then_practice_roundtrip():
    from api.services.remote_sync import RemoteSyncService

    sync = RemoteSyncService()
    skill_id = f"test-skill-{uuid.uuid4().hex[:10]}"

    upsert_payload = {
        "skill_id": skill_id,
        "name": "Debugging",
        "description": "Find and fix bugs",
        "proficiency": 0.1,
        "decay_rate": 0.01,
    }

    upsert_res = await _retry(lambda: sync.skill_upsert(upsert_payload))
    assert upsert_res.get("success", True) is True

    async def _fetch_skill():
        q = """
        MATCH (s:Skill {skill_id: $skill_id})
        RETURN s.skill_id AS skill_id, s.proficiency AS proficiency, s.practice_count AS practice_count
        """
        return await sync.run_cypher(q, {"skill_id": skill_id}, mode="read")

    fetch = await _retry(_fetch_skill)
    records = fetch.get("records") or []
    assert records, "Expected Skill to exist after upsert"
    before = records[0]
    before_count = int(before.get("practice_count") or 0)
    before_prof = float(before.get("proficiency") or 0.0)

    practice_res = await _retry(
        lambda: sync.skill_practice({"skill_id": skill_id, "success": True, "delta": 0.05})
    )
    assert practice_res.get("success", True) is True

    fetch2 = await _retry(_fetch_skill)
    records2 = fetch2.get("records") or []
    assert records2
    after = records2[0]
    after_count = int(after.get("practice_count") or 0)
    after_prof = float(after.get("proficiency") or 0.0)

    assert after_count >= before_count + 1
    assert after_prof >= before_prof

    # Cleanup (best-effort)
    await sync.run_cypher(
        "MATCH (s:Skill {skill_id: $skill_id}) DETACH DELETE s",
        {"skill_id": skill_id},
        mode="write",
    )

