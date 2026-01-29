import os

from api.services.relatio_narrative_service import RelatioNarrativeService


def test_relatio_service_disables_spacy_when_flag_set(monkeypatch):
    monkeypatch.setenv("DIONYSUS_DISABLE_SPACY", "1")
    service = RelatioNarrativeService()
    assert service.nlp is None
    assert service.extract_svo_triplets("Alice wrote the plan.") == []
