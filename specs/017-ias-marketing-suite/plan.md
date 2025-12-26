# Implementation Plan: IAS Marketing Suite Assets

**Branch**: `017-ias-marketing-suite` | **Date**: 2025-12-26 | **Spec**: [spec.md](./spec.md)

## Summary

Use the `MarketingAgent` (CodeAgent) to generate the remaining nurture emails and the $97 tripwire sales page, exporting them to the designated marketing assets directory.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: `smolagents`, `anthropic`  
**Architecture**: Agentic content generation  
**Storage**: Filesystem (`/Volumes/Arkham/Marketing/stefan/assets/`)

## Project Structure

```text
api/
└── agents/
    └── marketing_agent.py # Core generation logic
```