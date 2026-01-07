"""
Beautiful Loop API router.
"""

from __future__ import annotations

from fastapi import APIRouter

from api.models.beautiful_loop import (
    BindingEvaluationRequest,
    BindingEvaluationResponse,
    BeautifulLoopConfig,
    BeautifulLoopConfigUpdate,
    CoherenceResponse,
    DepthResponse,
    EpistemicState,
    PrecisionErrorsRequest,
    PrecisionErrorsResponse,
    PrecisionForecastRequest,
    PrecisionProfile,
    UnifiedRealityModel,
)
from api.services.bayesian_binder import get_bayesian_binder
from api.services.epistemic_field_service import get_epistemic_field_service
from api.services.hyper_model_service import get_hyper_model_service
from api.services.unified_reality_model import get_unified_reality_model

router = APIRouter(prefix="/api/v1/beautiful-loop", tags=["beautiful-loop"])


@router.post("/precision/forecast", response_model=PrecisionProfile)
async def forecast_precision_profile(request: PrecisionForecastRequest) -> PrecisionProfile:
    service = get_hyper_model_service()
    return service.forecast_precision_profile(
        context=request.context,
        internal_states=request.internal_states,
        recent_errors=request.recent_errors,
    )


@router.post("/precision/errors", response_model=PrecisionErrorsResponse)
async def record_precision_errors(request: PrecisionErrorsRequest) -> PrecisionErrorsResponse:
    service = get_hyper_model_service()
    learning_delta = service.record_precision_errors(request.errors)
    return PrecisionErrorsResponse(recorded_count=len(request.errors), learning_delta=learning_delta)


@router.get("/precision/profile", response_model=PrecisionProfile)
async def get_precision_profile() -> PrecisionProfile:
    service = get_hyper_model_service()
    return service.get_current_profile()


@router.post("/binding/evaluate", response_model=BindingEvaluationResponse)
async def evaluate_binding(request: BindingEvaluationRequest) -> BindingEvaluationResponse:
    binder = get_bayesian_binder()
    return binder.evaluate(
        candidates=request.candidates,
        precision_profile=request.precision_profile,
        binding_capacity=request.binding_capacity,
    )


@router.get("/reality-model", response_model=UnifiedRealityModel)
async def get_reality_model() -> UnifiedRealityModel:
    return get_unified_reality_model().get_model()


@router.get("/reality-model/coherence", response_model=CoherenceResponse)
async def get_reality_model_coherence() -> CoherenceResponse:
    model = get_unified_reality_model().get_model()
    return CoherenceResponse(
        coherence_score=model.coherence_score,
        bound_inference_count=len(model.bound_inferences),
    )


@router.get("/epistemic/state", response_model=EpistemicState)
async def get_epistemic_state() -> EpistemicState:
    service = get_epistemic_field_service()
    return service.get_epistemic_state()


@router.get("/epistemic/depth", response_model=DepthResponse)
async def get_epistemic_depth() -> DepthResponse:
    service = get_epistemic_field_service()
    state = service.get_epistemic_state()
    return DepthResponse(depth_score=state.depth_score, luminosity_factors=state.luminosity_factors)


@router.get("/config", response_model=BeautifulLoopConfig)
async def get_config() -> BeautifulLoopConfig:
    binder = get_bayesian_binder()
    hyper_model = get_hyper_model_service()
    return BeautifulLoopConfig(binding=binder.config, hyper_model=hyper_model.config)


@router.patch("/config", response_model=BeautifulLoopConfig)
async def update_config(update: BeautifulLoopConfigUpdate) -> BeautifulLoopConfig:
    binder = get_bayesian_binder()
    hyper_model = get_hyper_model_service()

    if update.binding is not None:
        binder.config = update.binding
    if update.hyper_model is not None:
        hyper_model.config = update.hyper_model

    return BeautifulLoopConfig(binding=binder.config, hyper_model=hyper_model.config)
