# Feature Specification: Smolagents Integration

**Feature Branch**: `009-smolagents-integration`
**Created**: 2025-12-26
**Status**: In Progress
**Priority**: High
**Input**: Smolagents Overview + Dionysus Core Architecture

## Overview

Integrate the **smolagents** framework into Dionysus to transition from a JSON-based action execution model to an autonomous, code-first cognitive architecture. This enables complex reasoning, native composability of tools, and multi-agent orchestration.

## Problem Statement

The legacy `ActionExecutor` uses structured JSON plans. While reliable, JSON is flat and cannot easily represent:
1.  **Loops**: "Keep searching until you find X."
2.  **Conditionals**: "If X is true, then reflect, otherwise recall."
3.  **Composability**: Nesting tool calls within a single decision step.

## Value Proposition

1.  **Code-First Agency**: Agents write Python code, reducing the "translation tax" between reasoning and execution.
2.  **Multi-Agent Orchestration**: Specialized agents (Perception, Reasoning, Metacognition) can collaborate on a single heartbeat cycle.
3.  **MCP Force Multiplier**: Automatically expose 30+ Dionysus tools to the agent via `ToolCollection.from_mcp()`.
4.  **Security**: Lay the groundwork for E2B/Blaxel sandboxed execution.

## Requirements

### Functional Requirements
- **FR-001**: Heartbeat DECIDE phase MUST use `CodeAgent` for decision making.
- **FR-002**: Agents MUST be able to use existing Dionysus services (Recall, Energy, Models) as tools.
- **FR-003**: System MUST support bridging `dionysus_mcp` tools into the `smolagents` framework.
- **FR-004**: Multi-agent orchestration MUST map to the ThoughtSeed 5-layer hierarchy.

### Technical Requirements
- **TR-001**: Use `litellm` for model-agnostic completions (defaulting to `gpt-5-nano`).
- **TR-002**: Implement async-to-sync bridges for tools wrapping async services.
- **TR-003**: Tools MUST handle connectivity failures gracefully with local fallbacks.

## Success Criteria
- **SC-001**: Heartbeat agent successfully completes a decision cycle using at least 2 tools.
- **SC-002**: MCP bridge correctly imports all 37+ tools from `dionysus_mcp`.
- **SC-003**: Decision latency remains under 5 seconds for a 5-step reasoning loop.