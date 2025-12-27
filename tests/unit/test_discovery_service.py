import os
import pytest
from pathlib import Path
from api.services.discovery_service import DiscoveryService, DiscoveryConfig

@pytest.fixture
def temp_codebase(tmp_path):
    """Create a dummy legacy codebase for testing."""
    # A component with high consciousness signals
    conscious_file = tmp_path / "conscious_agent.py"
    conscious_file.write_text("""
class LegacyAgent:
    def __init__(self):
        self.awareness = []
        self.memory = {}

    def observe(self, data):
        # awareness pattern
        pass

    def reason(self, observation):
        # inference pattern
        return "decision"

    def recall(self, key):
        # memory pattern
        return self.memory.get(key)
""")

    # A component with low signals
    boring_file = tmp_path / "utils.py"
    boring_file.write_text("""
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
""")

    # A component with strategic but no consciousness signals (should be filtered)
    strategic_only = tmp_path / "tool_wrapper.py"
    strategic_only.write_text("""
import os
import json

class FastAPITool:
    def run(self):
        pass
""")

    return tmp_path

def test_discovery_basic(temp_codebase):
    service = DiscoveryService()
    results = service.discover_components(str(temp_codebase))
    
    # Should find LegacyAgent and its methods
    # Boring utils and strategic-only tool should be filtered because no consciousness patterns
    names = [r.name for r in results]
    assert "LegacyAgent" in names
    assert "observe" in names
    assert "reason" in names
    assert "recall" in names
    assert "add" not in names
    assert "subtract" not in names
    assert "FastAPITool" not in names

def test_threshold_gating(temp_codebase):
    # High threshold should recommend nothing
    service_high = DiscoveryService(DiscoveryConfig(quality_threshold=0.99))
    results_high = service_high.discover_components(str(temp_codebase))
    for r in results_high:
        assert r.migration_recommended is False

    # Low threshold should recommend everything found
    service_low = DiscoveryService(DiscoveryConfig(quality_threshold=0.1))
    results_low = service_low.discover_components(str(temp_codebase))
    for r in results_low:
        assert r.migration_recommended is True

def test_config_env_vars(temp_codebase, monkeypatch):
    monkeypatch.setenv("DISCOVERY_QUALITY_THRESHOLD", "0.85")
    monkeypatch.setenv("DISCOVERY_CONSCIOUSNESS_WEIGHT", "0.5")
    
    config = DiscoveryConfig()
    assert config.quality_threshold == 0.85
    assert config.consciousness_weight == 0.5
    assert config.strategic_weight == 0.3 # default

def test_enhancements_and_risks(temp_codebase):
    service = DiscoveryService()
    results = service.discover_components(str(temp_codebase))
    
    # LegacyAgent (the class) should have some patterns
    agent_assessment = next(r for r in results if r.name == "LegacyAgent")
    assert len(agent_assessment.enhancement_opportunities) > 0
    
    # Observe method should have awareness signals
    observe_assessment = next(r for r in results if r.name == "observe")
    assert "awareness_amplification" in observe_assessment.enhancement_opportunities
