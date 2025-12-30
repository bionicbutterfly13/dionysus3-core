# Quickstart: Belief Avatar System

**Feature**: 036-belief-avatar-system
**Date**: 2025-12-30

## Prerequisites

- Python 3.11+
- dionysus3-core running (`uvicorn api.main:app`)
- Neo4j via Graphiti (n8n webhooks)

## Development Setup

```bash
# Clone and install
cd /Volumes/Asylum/dev/dionysus3-core
pip install -e ".[dev]"

# Run API
uvicorn api.main:app --reload --port 8000
```

## API Usage Examples

### 1. Create a Journey

```bash
curl -X POST http://localhost:8000/belief-journey/journey/create \
  -H "Content-Type: application/json" \
  -d '{"participant_id": "pilot_001"}'
```

Response:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "participant_id": "pilot_001",
    "current_phase": "revelation",
    "current_lesson": "lesson_1_breakthrough_mapping"
  }
}
```

### 2. Identify a Limiting Belief

```bash
curl -X POST http://localhost:8000/belief-journey/beliefs/limiting/identify \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "I must always be exceptional—good enough is never enough",
    "pattern_name": "perfectionism_trap",
    "self_talk": ["I should have done better", "This isnt good enough"],
    "mental_blocks": ["Fear of delegation", "Analysis paralysis"],
    "protects_from": "Fear of being seen as mediocre"
  }'
```

### 3. Design an Experiment

```bash
curl -X POST http://localhost:8000/belief-journey/experiments/design \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "550e8400-e29b-41d4-a716-446655440000",
    "limiting_belief_id": "belief-uuid-here",
    "hypothesis": "Delegating this task will not result in failure",
    "action_to_take": "Delegate the quarterly report to my team lead",
    "context": "mid"
  }'
```

### 4. Identify a Replay Loop

```bash
curl -X POST http://localhost:8000/belief-journey/loops/identify \
  -H "Content-Type: application/json" \
  -d '{
    "journey_id": "550e8400-e29b-41d4-a716-446655440000",
    "trigger_situation": "After a meeting where I spoke assertively",
    "story_text": "I was too harsh. Everyone thinks I am difficult.",
    "emotion": "shame",
    "fear_underneath": "Fear of being rejected or disliked"
  }'
```

### 5. Get Journey Metrics

```bash
curl http://localhost:8000/belief-journey/journey/550e8400-e29b-41d4-a716-446655440000/metrics
```

Response:
```json
{
  "success": true,
  "data": {
    "journey_id": "550e8400-e29b-41d4-a716-446655440000",
    "current_phase": "revelation",
    "current_lesson": "lesson_1_breakthrough_mapping",
    "lessons_completed": 1,
    "limiting_beliefs": {
      "total": 3,
      "dissolved": 1,
      "dissolution_rate": 0.33
    },
    "empowering_beliefs": {
      "total": 2,
      "embodied": 0,
      "embodiment_rate": 0.0
    },
    "experiments": {
      "total": 4,
      "success_rate": 0.75
    },
    "replay_loops": {
      "total": 2,
      "resolved": 1,
      "avg_resolution_time_minutes": 15.5
    }
  }
}
```

## Avatar Simulation Skills

### Location

Skills are stored in:
```
/Volumes/Asylum/skills-library/personal/bionicbutterfly13/consciousness/
├── avatar-simulation.md
└── response-prediction.md
```

### Usage (Claude Code)

```
/avatar-simulation "Run the intro script through Claudia's experience"

/response-prediction "How will the avatar respond to: You're already amazing"
```

## Testing

```bash
# Run unit tests
pytest tests/unit/test_belief_tracking_service.py -v

# Run integration tests
pytest tests/integration/test_belief_journey_router.py -v

# Run all tests with coverage
pytest --cov=api.services.belief_tracking_service --cov=api.routers.belief_journey
```

## File Structure

```
api/
├── models/
│   └── belief_journey.py     # Pydantic models (existing)
├── services/
│   └── belief_tracking_service.py  # Core service (existing)
├── routers/
│   └── belief_journey.py     # REST endpoints (new)
└── main.py                   # Register router

tests/
├── integration/
│   └── test_belief_journey_router.py
└── unit/
    └── test_belief_tracking_service.py
```

## Common Workflows

### Complete Belief Transformation Cycle

1. **Create Journey** → `POST /journey/create`
2. **Identify Limiting Belief** → `POST /beliefs/limiting/identify`
3. **Map to Behaviors** → `POST /beliefs/limiting/{id}/map`
4. **Design Experiment** → `POST /experiments/design`
5. **Record Result** → `POST /experiments/{id}/record`
6. **Propose Empowering Belief** → `POST /beliefs/empowering/propose`
7. **Add Evidence** → `POST /beliefs/empowering/{id}/strengthen`
8. **Dissolve Old Belief** → `POST /beliefs/limiting/{id}/dissolve`
9. **Anchor to Habit** → `POST /beliefs/empowering/{id}/anchor`

### Replay Loop Resolution

1. **Identify Loop** → `POST /loops/identify`
2. **Apply Compassion** → `POST /loops/{id}/interrupt`
3. **Extract Lesson** → `POST /loops/{id}/resolve`

## Troubleshooting

### 404 Journey Not Found
Journey ID must be valid UUID. Check that journey was created first.

### 400 Belief Not In Journey
Belief ID must belong to the specified journey_id. Verify with `GET /journey/{id}`.

### Graphiti Connection Errors
Service continues without Neo4j persistence. Check n8n webhooks are running.
