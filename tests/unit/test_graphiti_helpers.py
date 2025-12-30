
import pytest
from api.services.graphiti_service import GraphitiService

class TestGraphitiHelpers:
    """
    Contract tests for GraphitiService shared helpers.
    Ensures parsing and normalization logic remains stable across extractors.
    """

    def test_parse_json_response_valid(self):
        """Test parsing valid JSON from LLM response."""
        response = '```json\n{"entities": ["A"], "relationships": []}\n```'
        data = GraphitiService._parse_json_response(response)
        assert data == {"entities": ["A"], "relationships": []}

    def test_parse_json_response_raw(self):
        """Test parsing raw JSON without markdown blocks."""
        response = '{"entities": ["B"]}'
        data = GraphitiService._parse_json_response(response)
        assert data == {"entities": ["B"]}

    def test_parse_json_response_malformed(self):
        """Test parsing malformed JSON returns empty dict."""
        response = 'Not JSON'
        data = GraphitiService._parse_json_response(response)
        assert data == {}

    def test_normalize_extraction_memevolve_compat(self):
        """
        Verify _normalize_extraction produces the exact schema expected by MemEvolve.
        Schema: entities=[{name, type, description}], relationships=[{source, target, relation, evidence}]
        """
        payload = {
            "entities": [{"name": "E1", "type": "T1"}, {"name": "E2"}],
            "relationships": [
                {"source": "E1", "target": "E2", "relation": "R1", "evidence": "ev"},
                {"source": "E1"} # Missing target/relation
            ]
        }
        
        entities, relationships = GraphitiService._normalize_extraction(payload)
        
        # Check entities
        assert len(entities) == 2
        assert entities[0]["name"] == "E1"
        assert entities[0]["type"] == "T1"
        assert entities[1]["name"] == "E2"
        assert entities[1]["type"] == "concept" # Default
        
        # Check relationships
        assert len(relationships) == 1 # Second one skipped
        rel = relationships[0]
        assert rel["source"] == "E1"
        assert rel["target"] == "E2"
        assert rel["relation"] == "R1"
        assert "relation_type" not in rel # Ensure no schema drift for MemEvolve
