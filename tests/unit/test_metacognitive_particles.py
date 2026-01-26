import pytest
from time import sleep
from datetime import datetime
from api.models.metacognitive_particle import MetacognitiveParticle

def test_particle_creation():
    """Test basic creation and defaults."""
    p = MetacognitiveParticle(
        content="I think therefore I am",
        source_agent="descartes_agent",
        precision=0.9
    )
    assert p.id is not None
    assert isinstance(p.timestamp, datetime)
    assert p.resonance_score == 0.0
    assert p.is_active is True

def test_precision_validation():
    """Test precision clamping/validation."""
    import pydantic
    with pytest.raises(pydantic.ValidationError):
        MetacognitiveParticle(
            content="Test",
            source_agent="test",
            precision=10.0
        )

def test_decay_logic():
    """Test resonance decay."""
    p = MetacognitiveParticle(content="Fade away", source_agent="time", resonance_score=0.5)
    p.decay(rate=0.2) # 0.5 * 0.8 = 0.4
    assert p.resonance_score == 0.4
    
    # Heavy decay to kill it
    p.decay(rate=0.9)
    assert p.resonance_score < 0.05
    assert p.is_active is False

def test_reinforce_logic():
    """Test resonance reinforcement."""
    p = MetacognitiveParticle(content="Pay attention", source_agent="focus", resonance_score=0.5)
    p.reinforce(amount=0.2)
    assert p.resonance_score == 0.7
    
    p.reinforce(amount=10.0)
    assert p.resonance_score == 1.0 # Clamped
