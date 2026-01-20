import pytest
from unittest.mock import MagicMock, patch
from api.services.relatio_narrative_service import RelatioNarrativeService

@pytest.fixture
def mock_spacy():
    """Mock the spacy model and pipeline."""
    with patch("spacy.load") as mock_load:
        mock_nlp = MagicMock()
        mock_load.return_value = mock_nlp
        yield mock_nlp

@pytest.fixture
def service(mock_spacy):
    """Initialize service with mocked spacy."""
    # We also mock spacy.util.is_package to avoid download attempt
    with patch("spacy.util.is_package", return_value=True):
        return RelatioNarrativeService()

def test_extract_svo_triplets_empty(service):
    """Test extraction with empty text."""
    result = service.extract_svo_triplets("")
    assert result == []

def test_extract_svo_triplets_success(service):
    """Test successful SVO extraction using native Spacy logic."""
    # Create mock tokens
    # Sentence: "The hero defeats the villain."
    # Tokens: The(det), hero(nsubj), defeats(VERB), the(det), villain(dobj), .(punct)
    
    mock_verb = MagicMock()
    mock_verb.text = "defeats"
    mock_verb.pos_ = "VERB"
    
    mock_subj = MagicMock()
    mock_subj.text = "hero"
    mock_subj.dep_ = "nsubj"
    
    mock_obj = MagicMock()
    mock_obj.text = "villain"
    mock_obj.dep_ = "dobj"
    
    # Set children for the verb
    mock_verb.children = [mock_subj, mock_obj]
    
    # Mock the doc to iterate over these tokens
    # We include non-verb tokens to ensure filtering works, but finding children is key
    mock_doc = [mock_subj, mock_verb, mock_obj]
    
    service.nlp.return_value = mock_doc
    
    result = service.extract_svo_triplets("The hero defeats the villain.")
    
    assert len(result) == 1
    assert result[0] == {
        "agent": "hero", 
        "action": "defeats", 
        "patient": "villain"
    }

def test_cluster_entities_simple(service):
    """Test simple clustering (unique extraction)."""
    triplets = [
        {"agent": "Hero", "action": "hits", "patient": "Monster"},
        {"agent": "Hero", "action": "runs", "patient": "Home"},
        {"agent": "Villain", "action": "hits", "patient": "Hero"}
    ]
    
    clusters = service.cluster_entities(triplets)
    
    assert set(clusters["agents"]) == {"Hero", "Villain"}
    assert set(clusters["patients"]) == {"Monster", "Home", "Hero"}
    assert clusters["narrative_count"] == 3
