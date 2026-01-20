import pytest
from unittest.mock import AsyncMock, MagicMock

from api.models.sync import MemoryType
from api.services.memory_basin_router import MemoryBasinRouter


@pytest.mark.asyncio
async def test_basin_ingest_merges_narrative_relationships():
    memevolve = MagicMock()
    memevolve.extract_with_context = AsyncMock(
        return_value={
            "entities": [],
            "relationships": [
                {
                    "source": "Event:Launch",
                    "target": "Actor:Team",
                    "relation_type": "PARTICIPATED_IN",
                    "confidence": 0.9,
                    "status": "approved",
                }
            ],
        }
    )
    memevolve.ingest_relationships = AsyncMock(return_value={"ingested": 2, "errors": []})

    narrative_service = MagicMock()
    narrative_service.extract_relationships = AsyncMock(
        return_value=[
            {
                "source": "Event:Launch",
                "target": "Actor:Team",
                "relation_type": "PARTICIPATED_IN",
                "confidence": 0.95,
                "status": "approved",
            },
            {
                "source": "Narrative:Launch Arc",
                "target": "Stage:announce",
                "relation_type": "HAS_STAGE",
                "confidence": 0.7,
                "status": "approved",
            },
        ]
    )

    router = MemoryBasinRouter(
        memevolve_adapter=memevolve,
        narrative_service=narrative_service,
    )

    result = await router._ingest_with_basin_context(
        content="Team launched the product.",
        basin_name="experiential-basin",
        basin_context="Context",
        memory_type=MemoryType.EPISODIC,
        source_id="test",
    )

    assert result["ingested"]["ingested"] == 2
    memevolve.ingest_relationships.assert_called_once()
    call_args = memevolve.ingest_relationships.call_args.kwargs
    rels = call_args["relationships"]
    assert len(rels) == 2
    assert {rel["relation_type"] for rel in rels} == {"PARTICIPATED_IN", "HAS_STAGE"}
