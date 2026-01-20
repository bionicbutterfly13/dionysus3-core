
import pytest
from uuid import uuid4
from api.models.thought import ThoughtSeed, ThoughtLayer, MarkovBlanket
from api.services.agent_memory_service import AgentMemoryService

@pytest.fixture
def memory_service():
    return AgentMemoryService()

@pytest.fixture
def mixed_thoughts():
    """Create a mix of thoughts with different blanket tags."""
    return [
        ThoughtSeed(
            content="I see a red ball",
            layer=ThoughtLayer.PERCEPTUAL,
            blanket_tag=MarkovBlanket.SENSORY
        ),
        ThoughtSeed(
            content="The ball is red because it reflects red light",
            layer=ThoughtLayer.CONCEPTUAL,
            blanket_tag=MarkovBlanket.INTERNAL
        ),
        ThoughtSeed(
            content="Pick up the ball",
            layer=ThoughtLayer.SENSORIMOTOR,
            blanket_tag=MarkovBlanket.ACTIVE
        ),
        ThoughtSeed(
            content="The user is looking at the screen",
            layer=ThoughtLayer.PERCEPTUAL,
            blanket_tag=MarkovBlanket.EXTERNAL
        )
    ]

def test_sensory_isolation(memory_service, mixed_thoughts):
    """SENSORY blanket should see SENSORY and EXTERNAL."""
    visible = memory_service.isolate_context(mixed_thoughts, MarkovBlanket.SENSORY)
    
    tag_set = {t.blanket_tag for t in visible}
    
    assert MarkovBlanket.SENSORY in tag_set
    assert MarkovBlanket.EXTERNAL in tag_set
    assert MarkovBlanket.INTERNAL not in tag_set
    assert MarkovBlanket.ACTIVE not in tag_set
    assert len(visible) == 2

def test_active_isolation(memory_service, mixed_thoughts):
    """ACTIVE blanket should see INTERNAL and ACTIVE."""
    visible = memory_service.isolate_context(mixed_thoughts, MarkovBlanket.ACTIVE)
    
    tag_set = {t.blanket_tag for t in visible}
    
    assert MarkovBlanket.INTERNAL in tag_set
    assert MarkovBlanket.ACTIVE in tag_set
    assert MarkovBlanket.SENSORY not in tag_set
    assert MarkovBlanket.EXTERNAL not in tag_set
    assert len(visible) == 2

def test_internal_isolation(memory_service, mixed_thoughts):
    """INTERNAL blanket should see everything EXCEPT raw EXTERNAL (hidden states)."""
    visible = memory_service.isolate_context(mixed_thoughts, MarkovBlanket.INTERNAL)
    
    tag_set = {t.blanket_tag for t in visible}
    
    assert MarkovBlanket.SENSORY in tag_set
    assert MarkovBlanket.INTERNAL in tag_set
    assert MarkovBlanket.ACTIVE in tag_set
    assert MarkovBlanket.EXTERNAL not in tag_set
    assert len(visible) == 3

def test_default_tagging(memory_service):
    """Untagged thoughts should default to INTERNAL."""
    # Create dict without blanket_tag
    raw_thought = {
        "content": "Untagged thought",
        "layer": "conceptual"
    }
    
    visible = memory_service.isolate_context([raw_thought], MarkovBlanket.INTERNAL)
    assert len(visible) == 1
    
    # Defaults to INTERNAL, so should NOT be visible to SENSORY
    visible_sensory = memory_service.isolate_context([raw_thought], MarkovBlanket.SENSORY)
    assert len(visible_sensory) == 0
