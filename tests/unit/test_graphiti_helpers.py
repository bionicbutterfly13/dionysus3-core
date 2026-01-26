
import pytest
from api.models.memevolve import TrajectoryData, TrajectoryMetadata, TrajectoryStep
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

    def test_format_trajectory_text_includes_metadata_and_steps(self):
        trajectory = TrajectoryData(
            query="Find memory",
            result={"status": "ok"},
            metadata=TrajectoryMetadata(
                agent_id="agent-1",
                session_id="session-1",
                project_id="project-1",
            ),
            steps=[
                TrajectoryStep(
                    observation="Observed signal",
                    thought="Reasoned about it",
                    action="Stored memory",
                )
            ],
        )

        text = GraphitiService._format_trajectory_text(trajectory)

        assert "Agent: agent-1" in text
        assert "Session: session-1" in text
        assert "Project: project-1" in text
        assert "Query: Find memory" in text
        assert "Result: {'status': 'ok'}" in text
        assert "Step 1 Observation: Observed signal" in text
        assert "Step 1 Thought: Reasoned about it" in text
        assert "Step 1 Action: Stored memory" in text

    def test_format_trajectory_text_builds_steps_from_trajectory(self):
        trajectory = TrajectoryData(
            trajectory=[
                {"observation": "Obs A", "thought": "Think A", "action": "Act A"},
                {"observation": "Obs B"},
            ]
        )

        text = GraphitiService._format_trajectory_text(trajectory)

        assert "Step 1 Observation: Obs A" in text
        assert "Step 1 Thought: Think A" in text
        assert "Step 1 Action: Act A" in text
        assert "Step 2 Observation: Obs B" in text

    def test_format_trajectory_text_truncates_long_output(self):
        trajectory = TrajectoryData(
            steps=[TrajectoryStep(observation="X" * 200)]
        )

        text = GraphitiService._format_trajectory_text(trajectory, max_chars=80)

        assert text.endswith("[truncated]")
        assert len(text) <= 80 + len("\n[truncated]")

    def test_normalize_relationships_with_confidence(self):
        raw_relationships = [
            {
                "source": "A",
                "target": "B",
                "type": "EXTENDS",
                "confidence": 0.9,
                "evidence": "High confidence",
            },
            {
                "source": "C",
                "target": "D",
                "relation": "RELATES_TO",
                "confidence": 0.4,
                "evidence": "Low confidence",
            },
        ]

        normalized, approved_count, pending_count = (
            GraphitiService._normalize_relationships_with_confidence(
                raw_relationships,
                confidence_threshold=0.6,
            )
        )

        assert approved_count == 1
        assert pending_count == 1
        assert normalized[0]["status"] == "approved"
        assert normalized[1]["status"] == "pending_review"
