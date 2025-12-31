"""
Class-based tools for Meta-ToT reasoning.
Feature: 041-meta-tot-engine
"""

import logging
from typing import Any, Dict, Optional

from pydantic import BaseModel
from smolagents import Tool

from api.agents.resource_gate import async_tool_wrapper
from api.models.meta_tot import MetaToTDecision, MetaToTResult, MetaToTTracePayload
from api.services.meta_tot_decision import get_meta_tot_decision_service
from api.services.meta_tot_engine import get_meta_tot_engine

logger = logging.getLogger("dionysus.meta_tot_tools")


class MetaToTDecisionOutput(BaseModel):
    decision: MetaToTDecision


class MetaToTRunOutput(BaseModel):
    decision: MetaToTDecision
    result: MetaToTResult
    trace: Optional[MetaToTTracePayload] = None


class MetaToTDecisionTool(Tool):
    name = "meta_tot_decide"
    description = "Decide whether to activate Meta-ToT based on complexity and uncertainty."

    inputs = {
        "task": {
            "type": "string",
            "description": "Task or problem statement to evaluate."
        },
        "context": {
            "type": "object",
            "description": "Optional context for decision scoring.",
            "nullable": True,
        },
    }
    output_type = "any"

    def forward(self, task: str, context: Optional[Dict[str, Any]] = None) -> dict:
        service = get_meta_tot_decision_service()
        decision = service.decide(task, context or {})
        return MetaToTDecisionOutput(decision=decision).model_dump()


class MetaToTRunTool(Tool):
    name = "meta_tot_run"
    description = "Run Meta-ToT reasoning with active inference scoring and return selected path."

    inputs = {
        "task": {
            "type": "string",
            "description": "Task or problem statement for Meta-ToT."
        },
        "context": {
            "type": "object",
            "description": "Optional context for reasoning and scoring.",
            "nullable": True,
        },
        "config": {
            "type": "object",
            "description": "Optional Meta-ToT configuration overrides.",
            "nullable": True,
        }
    }
    output_type = "any"

    def forward(self, task: str, context: Optional[Dict[str, Any]] = None, config: Optional[Dict[str, Any]] = None) -> dict:
        decision_service = get_meta_tot_decision_service()
        decision = decision_service.decide(task, context or {})

        if not decision.use_meta_tot:
            result = MetaToTResult(
                session_id="skipped",
                best_path=[],
                confidence=0.0,
                metrics={"skipped": True},
                decision=decision,
                trace_id=None,
            )
            return MetaToTRunOutput(decision=decision, result=result).model_dump()

        async def _run():
            engine = get_meta_tot_engine()
            return await engine.run(task, context or {}, config_overrides=config, decision=decision)

        try:
            result, trace = async_tool_wrapper(_run)()
            return MetaToTRunOutput(decision=decision, result=result, trace=trace).model_dump()
        except Exception as exc:
            logger.error(f"Meta-ToT run failed: {exc}")
            fallback = MetaToTResult(
                session_id="failed",
                best_path=[],
                confidence=0.0,
                metrics={"error": str(exc)},
                decision=decision,
                trace_id=None,
            )
            return MetaToTRunOutput(decision=decision, result=fallback).model_dump()


meta_tot_decide = MetaToTDecisionTool()
meta_tot_run = MetaToTRunTool()
