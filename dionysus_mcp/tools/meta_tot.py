"""
Meta-ToT MCP Tools
Feature: 041-meta-tot-engine
"""

import logging
from typing import Any, Dict, Optional

from api.models.meta_tot import MetaToTResult
from api.services.meta_tot_decision import get_meta_tot_decision_service
from api.services.meta_tot_engine import get_meta_tot_engine
from api.services.meta_tot_trace_service import get_meta_tot_trace_service

logger = logging.getLogger("dionysus.mcp.meta_tot")


async def meta_tot_run_tool(
    task: str,
    context: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run Meta-ToT reasoning and return decision, result, and trace."""
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
        return {"decision": decision.model_dump(), "result": result.model_dump()}

    engine = get_meta_tot_engine()
    result, trace = await engine.run(task, context or {}, config_overrides=config, decision=decision)
    payload = {"decision": decision.model_dump(), "result": result.model_dump()}
    if trace is not None:
        payload["trace"] = trace.model_dump()
    return payload


async def meta_tot_trace_tool(trace_id: str) -> Dict[str, Any]:
    """Retrieve a Meta-ToT trace by id."""
    service = get_meta_tot_trace_service()
    trace = await service.get_trace(trace_id)
    if trace is None:
        return {"error": f"Trace {trace_id} not found"}
    return trace.model_dump()


META_TOT_RUN_DEFINITION = {
    "name": "meta_tot_run",
    "description": "Run Meta-ToT reasoning with active inference scoring.",
    "parameters": {
        "task": {
            "type": "string",
            "description": "Task or problem statement for Meta-ToT",
            "required": True,
        },
        "context": {
            "type": "object",
            "description": "Optional context for reasoning",
            "required": False,
        },
        "config": {
            "type": "object",
            "description": "Optional Meta-ToT configuration overrides",
            "required": False,
        },
    },
}

META_TOT_TRACE_DEFINITION = {
    "name": "meta_tot_trace",
    "description": "Retrieve Meta-ToT trace by id.",
    "parameters": {
        "trace_id": {
            "type": "string",
            "description": "Meta-ToT trace id",
            "required": True,
        }
    },
}
