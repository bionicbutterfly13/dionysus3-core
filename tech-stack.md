# Tech Stack

## Core
- Language: Python 3.x
- Framework: FastAPI
- LLM Orchestration: `api.services.llm_service` (OpenAI/Anthropic)
- Knowledge Graph: Neo4j via Graphiti
- Memory Gateway: MemEvolve adapter

## NLP
- spaCy (dependency parsing)
- Text2Story (English-only narrative extraction; optional import with fallback)

## Testing
- pytest
- pytest-asyncio
- pytest-cov

## Change Log
- 2026-01-18: Added Text2Story (English-only) with LLM fallback for narrative ingestion.
