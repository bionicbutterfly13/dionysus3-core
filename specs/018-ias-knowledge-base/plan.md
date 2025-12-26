# Implementation Plan: IAS Knowledge Base Maintenance

**Branch**: `018-ias-knowledge-base` | **Date**: 2025-12-26 | **Spec**: [spec.md](./spec.md)

## Summary

Use the `KnowledgeAgent` (CodeAgent) to maintain the audiobook manuscript and structured avatar data in Neo4j, ensuring conceptual consistency across all KB assets.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `smolagents`, `graphiti-core`, `neo4j`  
**Architecture**: Agent-managed graph updates  
**Storage**: Neo4j (Avatar Graph) + Filesystem (Audiobook)

## Project Structure

```text
api/
└── agents/
    └── knowledge_agent.py # Core KB logic
```