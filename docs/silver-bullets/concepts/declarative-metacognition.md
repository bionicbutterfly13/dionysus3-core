# Declarative Metacognition

**Category**: Core Concept  
**Type**: Knowledge Layer  
**Implementation**: Graphiti Semantic Graph (WARM tier)

---

## Definition

Declarative metacognition is the **semantic, informational layer** of self-awareness. It represents explicit knowledge ABOUT how the mind works - the "user manual" of cognition.

## Key Characteristics

- **Static Library**: Fixed knowledge base that doesn't change during execution
- **Language-Dependent**: Requires conceptual articulation and understanding
- **Informational Function**: Provides knowledge, not real-time regulation
- **Strategic Storage**: Contains heuristics, mental shortcuts, learned strategies
- **Conscious Access**: Can be explicitly verbalized and discussed

## Examples

- "I know multitasking reduces my performance"
- "I learn better visually than auditorily"  
- "Working memory has limited capacity of 7±2 items"
- "I need breaks every 90 minutes for optimal focus"

## Dionysus Implementation

```python
# Stored in Graphiti semantic knowledge graph
# WARM tier (slower, reflective retrieval)

graphiti_service.add_entity(
    entity_type="CognitiveStrategy",
    properties={
        "name": "pomodoro_technique",
        "description": "25-minute focus intervals with 5-minute breaks",
        "effectiveness": 0.85,
        "domain": "attention_management"
    }
)
```

### Storage Location
- **System**: Graphiti temporal knowledge graph
- **Tier**: WARM (semantic, durable)
- **Access Pattern**: Query-based retrieval when planning
- **Update Frequency**: Accumulated over time through learning

### Characteristics in Dionysus
- **Entities**: Concepts like "memory," "attention," "reasoning"
- **Relationships**: How cognitive processes connect and interact
- **Lifetime**: Persistent across sessions
- **Usage**: Consulted during ORIENT phase of OODA loop

## Contrast with Procedural Metacognition

| Aspect | Declarative | Procedural |
|--------|-------------|------------|
| **Nature** | Static knowledge | Dynamic regulation |
| **Function** | Informational (knowing) | Operational (doing) |
| **Access** | WARM tier (slow) | HOT tier (fast) |
| **Language** | Requires verbal concepts | Non-verbal, felt sense |
| **Example** | "I know I should focus" | *Actually focusing* |
| **System** | Graphiti semantic graph | OODA loop + active inference |

## Computer Analogy

**Declarative Metacognition = User Manual**
- Technical specifications
- Error codes and troubleshooting instructions
- Feature documentation
- What you READ when you need information
- Static reference consulted when planning

## Clinical Significance

### The Therapy Gap
Many patients possess extensive declarative metacognitive knowledge:
- "I understand my trauma triggers"
- "I know deep breathing helps anxiety"
- "I recognize my cognitive distortions"

But lack **procedural competence** (ability to actually regulate in the moment).

### Solution
Effective therapy must translate declarative knowledge into procedural skill through:
- **Repetition**: Practice until automatic
- **Embodiment**: Move from concept to felt experience
- **Multi-tier storage**: Store in BOTH Graphiti (declarative) AND HOT tier (procedural)

## Related Concepts

- **[Procedural Metacognition](./procedural-metacognition.md)** - Dynamic regulation layer
- **[Metacognitive Feelings](./metacognitive-feelings.md)** - Bridge between layers
- **[Graphiti](./graphiti.md)** - Storage implementation
- **[WARM Tier](./warm-tier.md)** - Semantic memory storage

## Bidirectional Links

### This concept is referenced in:
- [01-metacognition-two-layer-model.md](../01-metacognition-two-layer-model.md)
- [04-smolagents-metatot-skills-integration.md](../04-smolagents-metatot-skills-integration.md)
- [Skills Library](./skills-library.md)

### This concept references:
- [Procedural Metacognition](./procedural-metacognition.md)
- [Graphiti](./graphiti.md)
- [WARM Tier](./warm-tier.md)

---

**Author**: Dr. Mani Saint-Victor  
**Last Updated**: 2026-01-01  
**Integration Event**: Metacognition Framework → Dionysus Architecture
