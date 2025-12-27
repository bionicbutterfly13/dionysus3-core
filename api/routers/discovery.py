"""
Discovery API router

Feature: 019-legacy-component-discovery
"""

from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.services.discovery_service import DiscoveryService, DiscoveryConfig, ComponentAssessment


router = APIRouter(prefix="/api/discovery", tags=["discovery"])


class ConsciousnessResponse(BaseModel):
    awareness_score: float
    inference_score: float
    memory_score: float
    patterns: dict[str, List[str]]


class StrategicResponse(BaseModel):
    uniqueness: float
    reusability: float
    framework_alignment: float
    dependency_burden: float


class AssessmentResponse(BaseModel):
    component_id: str
    name: str
    file_path: str
    composite_score: float
    migration_recommended: bool
    consciousness: ConsciousnessResponse
    strategic: StrategicResponse
    enhancement_opportunities: List[str]
    risk_factors: List[str]


class DiscoveryRequest(BaseModel):
    codebase_path: str = Field(..., description="Path to legacy codebase")
    top_n: int = Field(default=10, ge=1, le=100)


class DiscoveryResponse(BaseModel):
    count: int
    results: List[AssessmentResponse]


def _serialize(assessment: ComponentAssessment) -> AssessmentResponse:
    return AssessmentResponse(
        component_id=assessment.component_id,
        name=assessment.name,
        file_path=assessment.file_path,
        composite_score=assessment.composite_score,
        migration_recommended=assessment.migration_recommended,
        consciousness=ConsciousnessResponse(
            awareness_score=assessment.consciousness.awareness_score,
            inference_score=assessment.consciousness.inference_score,
            memory_score=assessment.consciousness.memory_score,
            patterns={
                "awareness": assessment.consciousness.awareness_patterns,
                "inference": assessment.consciousness.inference_patterns,
                "memory": assessment.consciousness.memory_patterns,
            },
        ),
        strategic=StrategicResponse(
            uniqueness=assessment.strategic.uniqueness_score,
            reusability=assessment.strategic.reusability_score,
            framework_alignment=assessment.strategic.framework_alignment_score,
            dependency_burden=assessment.strategic.dependency_burden,
        ),
        enhancement_opportunities=assessment.enhancement_opportunities,
        risk_factors=assessment.risk_factors,
    )


@router.post("/run", response_model=DiscoveryResponse)
async def run_discovery(request: DiscoveryRequest) -> DiscoveryResponse:
    service = DiscoveryService(DiscoveryConfig())
    try:
        assessments = service.discover_components(request.codebase_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    top = assessments[: request.top_n]
    return DiscoveryResponse(
        count=len(assessments),
        results=[_serialize(a) for a in top],
    )

