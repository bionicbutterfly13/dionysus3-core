import tempfile
from pathlib import Path

from api.services.discovery_service import DiscoveryService, DiscoveryConfig


SAMPLE_CODE = """
class MemoryAgent:
    def recall(self):
        memory = "use episodic memory store"
        return memory

def reason_about(state):
    # awareness and inference hints
    observed = state.get("awareness", True)
    return observed
"""


def test_discovery_detects_signals_and_scores():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "sample.py"
        test_file.write_text(SAMPLE_CODE)

        service = DiscoveryService(DiscoveryConfig(quality_threshold=0.1))
        results = service.discover_components(tmpdir)

        assert results, "should find at least one component"
        top = results[0]

        assert top.consciousness.awareness_score > 0
        assert any(r.consciousness.memory_score > 0 for r in results)
        assert top.composite_score >= 0.1
        assert top.migration_recommended is True


def test_discovery_respects_top_n_ordering():
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(3):
            Path(tmpdir, f"file_{i}.py").write_text(SAMPLE_CODE)

        service = DiscoveryService()
        results = service.discover_components(tmpdir)

        assert len(results) >= 3
        # already sorted high to low; composite scores should be non-increasing
        scores = [r.composite_score for r in results]
        assert scores == sorted(scores, reverse=True)
