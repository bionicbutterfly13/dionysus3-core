# Quickstart: Metacognitive Particles Integration

**Feature**: 040-metacognitive-particles
**Date**: 2025-12-30

---

## Overview

This feature adds metacognitive capabilities to Dionysus agents:
- **Particle Classification**: Identify cognitive process types
- **Mental Actions**: Modulate attention and precision
- **Sense of Agency**: Measure self-attribution of actions
- **Epistemic Gain**: Detect "Aha!" learning moments
- **Procedural Metacognition**: Monitor and control cognition

---

## Quick Setup

### Prerequisites

```bash
# Ensure dependencies
pip install scipy numpy pydantic

# Verify existing infrastructure
python -c "from api.models.markov_blanket import MarkovBlanket; print('OK')"
python -c "from api.agents.metacognition_agent import MetacognitionAgent; print('OK')"
```

### Environment Variables

```bash
# Optional configuration
export METACOGNITIVE_MAX_DEPTH=5           # Max nesting levels
export EPISTEMIC_GAIN_THRESHOLD=0.3        # Uncertainty reduction threshold
export EPISTEMIC_GAIN_ADAPTIVE=false       # Enable adaptive threshold
export PRECISION_MIN=0.01                  # Minimum precision bound
export PRECISION_MAX=100.0                 # Maximum precision bound
```

---

## Usage Examples

### 1. Classify a Cognitive Process

```python
from api.services.particle_classifier import ParticleClassifier
from api.models.markov_blanket import MarkovBlanketPartition

classifier = ParticleClassifier()

# Create blanket from agent
blanket = MarkovBlanketPartition(
    external_paths={"env-001", "env-002"},
    sensory_paths={"sensor-001"},
    active_paths={"action-001"},
    internal_paths={"belief-001", "belief-002"}
)

# Classify
particle_type, confidence = await classifier.classify(
    agent_id="my-agent",
    blanket=blanket
)

print(f"Type: {particle_type}, Confidence: {confidence:.2f}")
# Output: Type: cognitive, Confidence: 0.95
```

### 2. Execute Mental Action (Precision Modulation)

```python
from api.agents.metacognition_agent import MetacognitionAgent

with MetacognitionAgent() as agent:
    result = await agent.mental_action(
        target_agent="perception",
        modulation={
            "precision_delta": -0.15  # Decrease confidence
        }
    )

    print(f"Prior precision: {result['prior_state']['precision']}")
    print(f"New precision: {result['new_state']['precision']}")
```

### 3. Compute Sense of Agency

```python
from api.services.agency_service import AgencyService
from api.models.metacognitive_particle import MetacognitiveParticle

agency_svc = AgencyService()

# Get particle (from classification)
particle = await get_particle_for_agent("my-agent")

# Compute agency strength
strength = await agency_svc.compute_agency_strength(particle)

print(f"Agency strength: {strength:.4f}")
# 0.0 = no agency sense
# Higher = stronger agency sense

has_agency = await agency_svc.has_agency(particle)
print(f"Has agency: {has_agency}")
```

### 4. Detect Epistemic Gain

```python
from api.services.epistemic_gain_service import EpistemicGainService
from api.models.belief_state import BeliefState
import numpy as np

gain_svc = EpistemicGainService()

# Prior belief (high uncertainty)
prior = BeliefState(
    mean=[0.5, 0.5],
    precision=np.array([[0.1, 0], [0, 0.1]])  # Low precision = high uncertainty
)

# Posterior belief (low uncertainty after learning)
posterior = BeliefState(
    mean=[0.8, 0.2],
    precision=np.array([[10.0, 0], [0, 10.0]])  # High precision = low uncertainty
)

# Check for epistemic gain
event = await gain_svc.check_gain(prior, posterior, threshold=0.3)

if event:
    print(f"Aha! Magnitude: {event.magnitude:.2f}")
    print(f"Noetic quality: {event.noetic_quality}")
else:
    print("No significant epistemic gain detected")
```

### 5. Procedural Metacognition

```python
from api.services.procedural_metacognition import ProceduralMetacognition

meta = ProceduralMetacognition()

# Monitor cognitive state
assessment = await meta.monitor(agent_id="reasoning-agent")

print(f"Progress: {assessment.progress:.0%}")
print(f"Confidence: {assessment.confidence:.2f}")
print(f"Issues: {assessment.issues}")

# Get control actions if needed
if assessment.issues:
    actions = await meta.control(assessment)
    for action in actions:
        print(f"Recommended: {action.action_type} on {action.target_agent}")
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/metacognition/classify` | Classify cognitive process |
| POST | `/api/v1/metacognition/mental-action` | Execute mental action |
| GET | `/api/v1/metacognition/agency/{agent_id}` | Get agency strength |
| POST | `/api/v1/metacognition/epistemic-gain/check` | Check for "Aha!" moment |
| GET | `/api/v1/metacognition/monitoring/{agent_id}` | Get cognitive assessment |
| POST | `/api/v1/metacognition/control` | Apply control action |

---

## Integration with ThoughtSeeds

```python
from api.services.thoughtseed_particle_bridge import ThoughtSeedParticleBridge

bridge = ThoughtSeedParticleBridge()

# Convert ThoughtSeed to MetacognitiveParticle
particle = await bridge.thoughtseed_to_particle(thoughtseed)

# Convert back
restored_seed = await bridge.particle_to_thoughtseed(particle)

# Verify round-trip consistency
assert thoughtseed.id == restored_seed.id
```

---

## Testing

```bash
# Run unit tests
pytest tests/unit/test_particle_classifier.py -v
pytest tests/unit/test_agency_service.py -v
pytest tests/unit/test_epistemic_gain.py -v

# Run integration tests
pytest tests/integration/test_metacognitive_flow.py -v
pytest tests/integration/test_thoughtseed_particle_bridge.py -v
```

---

## Troubleshooting

### "Cognitive core limit reached"

The system enforces maximum nesting depth (default 5 levels).

```python
# Check current limit
import os
max_depth = int(os.getenv("METACOGNITIVE_MAX_DEPTH", "5"))
print(f"Max nesting depth: {max_depth}")
```

### "Precision out of bounds"

Precision values are bounded to [0.01, 100.0].

```python
# Values are automatically clamped
from api.models.belief_state import clamp_precision
safe_precision = clamp_precision(requested_value)
```

### "Agency computation failed"

Ensure the particle has been properly classified first.

```python
# Classification required before agency computation
if particle.type == ParticleType.COGNITIVE:
    # Basic cognitive particles have no agency sense
    agency = 0.0
else:
    agency = await agency_svc.compute_agency_strength(particle)
```

---

## Next Steps

1. Review full API documentation: `contracts/metacognitive_api.yaml`
2. Explore data model: `data-model.md`
3. Check implementation plan: `plan.md`
