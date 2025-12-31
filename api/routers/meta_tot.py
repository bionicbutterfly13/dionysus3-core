"""
Meta-ToT API Router
Feature: 041-meta-tot-engine
"""

from fastapi import APIRouter, HTTPException

from api.models.meta_tot import MetaToTRunRequest, MetaToTRunResponse, MetaToTResult
from api.services.meta_tot_decision import get_meta_tot_decision_service
from api.services.meta_tot_engine import get_meta_tot_engine
from api.services.meta_tot_trace_service import get_meta_tot_trace_service

router = APIRouter(prefix="/api/meta-tot", tags=["meta-tot"])


@router.post("/run", response_model=MetaToTRunResponse)
async def run_meta_tot(request: MetaToTRunRequest) -> MetaToTRunResponse:
    decision_service = get_meta_tot_decision_service()
    decision = decision_service.decide(request.task, request.context)

    if not decision.use_meta_tot:
        result = MetaToTResult(
            session_id="skipped",
            best_path=[],
            confidence=0.0,
            metrics={"skipped": True},
            decision=decision,
            trace_id=None,
        )
        return MetaToTRunResponse(decision=decision, result=result)

    engine = get_meta_tot_engine()
    result, trace = await engine.run(
        request.task,
        request.context,
        config_overrides=request.config,
        decision=decision,
    )
    return MetaToTRunResponse(decision=decision, result=result, trace=trace)


@router.get("/traces/{trace_id}")
async def get_meta_tot_trace(trace_id: str):
    service = get_meta_tot_trace_service()
    trace = await service.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail=f"Trace {trace_id} not found")
    return trace
