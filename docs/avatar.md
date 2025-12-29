# Avatar Knowledge Graph & Researcher Agent

The Avatar system is designed to deeply analyze user voice, pains, and objections to build a canonical "Avatar" profile used for high-converting marketing and empathetic coaching.

## Core Agents
- **PainAnalyst**: Extracts intensity and triggers of user pain points.
- **ObjectionHandler**: Maps counter-narratives and resistance patterns.
- **VoiceExtractor**: Identifies unique linguistic patterns and emotional tones.
- **AvatarResearcher**: Orchestrates the above agents to build a coherent knowledge graph.

## API Endpoints

### 1. Ingest Ground Truth
Ingest authoritative documents (e.g., IAS-copy-brief.md) to seed the graph.
`POST /api/v1/avatar/ingest/ground-truth`
Payload: `{ "file_path": "data/ground-truth/IAS-copy-brief.md" }`

### 2. Analyze Content
Extract avatar insights from raw text or transcripts.
`POST /api/v1/avatar/analyze/content`
Payload: `{ "text": "...", "source_id": "session_123" }`

### 3. Query Avatar Graph
Query the Graphiti-backed avatar knowledge graph.
`POST /api/v1/avatar/query`
Payload: `{ "query": "What are the primary triggers for burnout?", "limit": 10 }`

### 4. Build Profile
Generate a comprehensive avatar profile based on aggregated insights.
`POST /api/v1/avatar/profile`
Payload: `{ "avatar_name": "Analytical Empath" }`

## Usage Example
```python
import httpx

async def get_avatar_profile():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/avatar/profile",
            json={"avatar_name": "Analytical Empath"}
        )
        return response.json()
```
