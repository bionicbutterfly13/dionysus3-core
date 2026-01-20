import pytest
from unittest.mock import AsyncMock, MagicMock

from api.models.concept_extraction import (
    ConceptExtractionLevel,
    ExtractedConcept,
    LevelExtractionResult,
)
from api.services.narrative_extraction_service import (
    NarrativeExtractionService,
    Text2StoryExtractor,
    _relationships_from_narratives,
    _relationships_from_text2story,
    get_narrative_extraction_service,
)


class DummyText2StoryExtractor:
    async def extract_relationships(self, content: str) -> list[dict]:
        return [
            {
                "source": "Event:Launch",
                "target": "Actor:Team",
                "relation_type": "PARTICIPATED_IN",
                "confidence": 0.9,
                "status": "approved",
                "evidence": "Team launched the product.",
            }
        ]


class FailingText2StoryExtractor:
    async def extract_relationships(self, content: str) -> list[dict]:
        raise RuntimeError("text2story unavailable")


@pytest.mark.asyncio
async def test_text2story_used_when_available():
    llm_extractor = MagicMock()
    llm_extractor.extract = AsyncMock()

    service = NarrativeExtractionService(
        text2story_extractor=DummyText2StoryExtractor(),
        llm_extractor=llm_extractor,
    )

    relationships = await service.extract_relationships("Team launched the product.")

    assert relationships[0]["relation_type"] == "PARTICIPATED_IN"
    llm_extractor.extract.assert_not_called()


@pytest.mark.asyncio
async def test_fallback_to_llm_on_text2story_failure():
    narrative_concept = ExtractedConcept(
        concept_id="n-1",
        level=ConceptExtractionLevel.NARRATIVE,
        name="Heroic Arc",
        description="Call -> Trial -> Return",
        confidence=0.7,
        concept_type="narrative",
        narrative_elements={
            "argument_flow": ["call", "trial", "return"],
            "persuasive_strategy": "emotional_appeal",
            "narrative_type": "story_arc",
        },
    )
    level_result = LevelExtractionResult(
        level=ConceptExtractionLevel.NARRATIVE,
        concepts=[narrative_concept],
        extraction_time=0.2,
        content_length=100,
    )

    llm_extractor = MagicMock()
    llm_extractor.extract = AsyncMock(return_value=level_result)

    service = NarrativeExtractionService(
        text2story_extractor=FailingText2StoryExtractor(),
        llm_extractor=llm_extractor,
    )

    relationships = await service.extract_relationships("A heroic tale.")

    rel_types = {rel["relation_type"] for rel in relationships}
    assert "HAS_STAGE" in rel_types
    assert "USES_STRATEGY" in rel_types


def test_relationships_from_narratives_supports_types():
    narrative_concept = ExtractedConcept(
        concept_id="n-2",
        level=ConceptExtractionLevel.NARRATIVE,
        name="Method Arc",
        description="Method steps",
        confidence=0.8,
        concept_type="narrative",
        narrative_elements={
            "argument_flow": ["premise", "evidence"],
            "persuasive_strategy": "logical_progression",
            "narrative_type": "methodology",
        },
    )

    relationships = _relationships_from_narratives(
        [narrative_concept],
        min_confidence=0.6,
    )

    rel_types = {rel["relation_type"] for rel in relationships}
    assert rel_types == {"HAS_STAGE", "USES_STRATEGY", "IS_TYPE"}


def test_relationships_from_text2story_maps_events_and_relations():
    raw = {
        "relationships": [
            {
                "source": "Hero",
                "target": "Trial",
                "relation": "faces",
                "confidence": 0.9,
                "evidence": "Hero faces a trial.",
            }
        ],
        "events": [
            {"name": "Launch", "participants": ["Team"], "confidence": 0.75}
        ],
    }

    relationships = _relationships_from_text2story(raw)
    rel_types = {rel["relation_type"] for rel in relationships}
    assert "FACES" in rel_types
    assert "PARTICIPATED_IN" in rel_types


@pytest.mark.asyncio
async def test_text2story_extractor_uses_module_extract(monkeypatch):
    class StubModule:
        @staticmethod
        def extract(text, language="en"):
            return {
                "events": [{"event": "Signal", "agents": ["System"], "confidence": 0.8}],
                "relations": [{"head": "Signal", "tail": "System", "predicate": "triggers"}],
            }

    monkeypatch.setattr(
        "api.services.narrative_extraction_service.importlib.import_module",
        lambda name: StubModule(),
    )

    extractor = Text2StoryExtractor()
    relationships = await extractor.extract_relationships("System triggered signal.")

    rel_types = {rel["relation_type"] for rel in relationships}
    assert "TRIGGERS" in rel_types
    assert "PARTICIPATED_IN" in rel_types


def test_get_narrative_extraction_service_singleton():
    service_a = get_narrative_extraction_service()
    service_b = get_narrative_extraction_service()
    assert service_a is service_b
