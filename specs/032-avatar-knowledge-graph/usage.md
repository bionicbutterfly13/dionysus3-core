# Avatar Knowledge Graph - API Usage Guide

## Overview

The Avatar Knowledge Graph API enables extraction and querying of avatar insights from content. It uses specialized AI agents to analyze pain points, objections, and voice patterns, storing results in a Neo4j knowledge graph via Graphiti.

## Base URL

```
/avatar
```

## Endpoints

### 1. Analyze Content

**POST /avatar/analyze/content**

Analyze raw text content for avatar insights. Runs PainAnalyst, ObjectionHandler, and VoiceExtractor agents in parallel.

```bash
curl -X POST http://localhost:8000/avatar/analyze/content \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I keep replaying conversations in my head for hours...",
    "source": "client_interview"
  }'
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| content | string | Yes | Raw text to analyze |
| source | string | No | Source identifier (default: "api_input") |

**Response:**
```json
{
  "success": true,
  "data": {
    "pain_points": [...],
    "objections": [...],
    "voice_patterns": [...]
  }
}
```

---

### 2. Analyze Document

**POST /avatar/analyze/document**

Analyze a document file from the filesystem.

```bash
curl -X POST http://localhost:8000/avatar/analyze/document \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/app/data/ground-truth/IAS-copy-brief.md",
    "document_type": "copy_brief"
  }'
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file_path | string | Yes | Path to document file |
| document_type | string | No | Type: copy_brief, email, interview, review |

---

### 3. Ingest Ground Truth

**POST /avatar/ingest/ground-truth**

Ingest a comprehensive "Ground Truth" avatar document. Builds the foundational avatar profile.

```bash
curl -X POST http://localhost:8000/avatar/ingest/ground-truth \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/app/data/ground-truth/IAS-copy-brief.md"
  }'
```

Use this for initial avatar setup with verified reference documents.

---

### 4. Research Question

**POST /avatar/research**

Answer a natural language research question about the avatar.

```bash
curl -X POST http://localhost:8000/avatar/research \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main pain points of analytical empaths?"
  }'
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| question | string | Yes | Natural language research question |

**Response:**
```json
{
  "success": true,
  "data": {
    "answer": "...",
    "sources": [...],
    "confidence": 0.85
  }
}
```

---

### 5. Generate Profile

**POST /avatar/profile**

Generate a comprehensive avatar profile from all stored knowledge.

```bash
curl -X POST http://localhost:8000/avatar/profile \
  -H "Content-Type: application/json" \
  -d '{
    "dimensions": "pain_points,objections,voice"
  }'
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dimensions | string | No | Dimensions to include (comma-separated or "all") |

---

### 6. Query Graph

**POST /avatar/query**

Direct semantic search of the avatar knowledge graph.

```bash
curl -X POST http://localhost:8000/avatar/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "replay loop emotional processing",
    "insight_types": "pain_point,pattern",
    "limit": 5
  }'
```

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | Yes | Natural language search query |
| insight_types | string | No | Filter by types (comma-separated) |
| limit | int | No | Maximum results (default: 10) |

---

### 7. Health Check

**GET /avatar/health**

Check avatar research system health.

```bash
curl http://localhost:8000/avatar/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "avatar_research",
  "agents": ["pain_analyst", "objection_handler", "voice_extractor", "avatar_researcher"]
}
```

---

## Typical Workflow

1. **Initialize**: Ingest ground truth document
   ```
   POST /avatar/ingest/ground-truth
   ```

2. **Enrich**: Analyze additional content (interviews, reviews, etc.)
   ```
   POST /avatar/analyze/content
   POST /avatar/analyze/document
   ```

3. **Query**: Research specific questions
   ```
   POST /avatar/research
   POST /avatar/query
   ```

4. **Export**: Generate comprehensive profile
   ```
   POST /avatar/profile
   ```

## Insight Types

The system extracts and stores these insight types:

- `pain_point` - Emotional/psychological pain points
- `objection` - Common objections and counter-narratives
- `voice_pattern` - Linguistic patterns and phrases
- `trigger` - Situational triggers
- `belief` - Core beliefs and worldviews
- `pattern` - Behavioral patterns

## Error Handling

All endpoints return errors in this format:

```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `200` - Success
- `404` - File not found (for document endpoints)
- `500` - Internal server error
