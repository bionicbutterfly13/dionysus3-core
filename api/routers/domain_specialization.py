"""
Domain Specialization Router.

REST API endpoints for domain specialization services:
- Domain analysis for text content
- Concept lookup
- Cross-domain mapping
- Academic structure analysis

Migrated from Dionysus 2.0.
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.models.domain_specialization import (
    AcademicStructure,
    DomainAnalysisRequest,
    DomainAnalysisResult,
)
from api.services.domain_specialization import get_domain_specialization_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/domain", tags=["domain-specialization"])


class ConceptLookupRequest(BaseModel):
    """Request to lookup a concept."""

    term: str = Field(..., min_length=1, description="Concept term to look up")


class ConceptLookupResponse(BaseModel):
    """Response from concept lookup."""

    found: bool = Field(..., description="Whether the concept was found")
    concept: Optional[dict[str, Any]] = Field(
        default=None, description="Concept data if found"
    )


class CrossDomainRequest(BaseModel):
    """Request for cross-domain mapping."""

    term: str = Field(..., min_length=1, description="Term to find mapping for")


class CrossDomainResponse(BaseModel):
    """Response from cross-domain mapping lookup."""

    found: bool = Field(..., description="Whether a mapping was found")
    mapping: Optional[dict[str, Any]] = Field(
        default=None, description="Mapping data if found"
    )


class AcademicAnalysisRequest(BaseModel):
    """Request for academic structure analysis."""

    content: str = Field(..., min_length=1, description="Text content to analyze")


class TextAnalysisRequest(BaseModel):
    """Request for simple text domain analysis."""

    content: str = Field(..., min_length=1, description="Text content to analyze")
    include_prompts: bool = Field(
        default=False, description="Include specialized extraction prompts"
    )


@router.post("/analyze", response_model=DomainAnalysisResult)
async def analyze_domain_content(request: DomainAnalysisRequest) -> DomainAnalysisResult:
    """Analyze text content for domain specialization.

    Performs comprehensive domain analysis including:
    - Neuroscience and AI concept detection
    - Academic structure recognition
    - Cross-domain mapping
    - Quality metrics calculation
    """
    try:
        service = await get_domain_specialization_service()
        context = {
            "domain_focus": request.domain_focus,
            "max_concepts": request.max_concepts,
        }

        result = await service.analyze_domain_content(request.content, context)

        # Optionally strip prompts to reduce response size
        if not request.include_prompts:
            result.specialized_prompts = {}

        return result

    except Exception as e:
        logger.error(f"Domain analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/simple")
async def analyze_text_simple(request: TextAnalysisRequest) -> dict[str, Any]:
    """Simplified domain analysis endpoint.

    Returns a lightweight analysis with:
    - Primary domain
    - Concept counts
    - Basic quality metrics
    """
    try:
        service = await get_domain_specialization_service()
        result = await service.analyze_domain_content(
            request.content,
            context={"domain_focus": ["neuroscience", "artificial_intelligence"]},
        )

        response = {
            "success": result.success,
            "primary_domain": result.primary_domain,
            "neuroscience_concept_count": len(result.neuroscience_concepts),
            "ai_concept_count": len(result.ai_concepts),
            "cross_domain_bridge_count": len(result.cross_domain_mappings),
            "terminology_density": result.terminology_density,
            "complexity_score": result.complexity_score,
            "processing_time": result.processing_time,
        }

        if request.include_prompts:
            response["prompts"] = result.specialized_prompts

        return response

    except Exception as e:
        logger.error(f"Simple analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/concept/lookup", response_model=ConceptLookupResponse)
async def lookup_concept(request: ConceptLookupRequest) -> ConceptLookupResponse:
    """Look up a concept in the terminology databases.

    Searches both neuroscience and AI databases for the term,
    including synonyms and abbreviations.
    """
    try:
        service = await get_domain_specialization_service()
        concept = service.find_concept(request.term)

        return ConceptLookupResponse(found=concept is not None, concept=concept)

    except Exception as e:
        logger.error(f"Concept lookup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/concept/cross-domain", response_model=CrossDomainResponse)
async def get_cross_domain_mapping(
    request: CrossDomainRequest,
) -> CrossDomainResponse:
    """Get cross-domain equivalent for a concept.

    Finds the analogous concept in the other domain
    (neuroscience <-> AI).
    """
    try:
        service = await get_domain_specialization_service()
        mapping = service.get_cross_domain_equivalent(request.term)

        return CrossDomainResponse(found=mapping is not None, mapping=mapping)

    except Exception as e:
        logger.error(f"Cross-domain mapping failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/academic/structure", response_model=AcademicStructure)
async def analyze_academic_structure(
    request: AcademicAnalysisRequest,
) -> AcademicStructure:
    """Analyze academic paper structure.

    Detects sections, citations, and calculates
    academic quality metrics.
    """
    try:
        service = await get_domain_specialization_service()
        structure = service.structure_recognizer.analyze_structure(request.content)

        return structure

    except Exception as e:
        logger.error(f"Academic structure analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases/stats")
async def get_database_stats() -> dict[str, Any]:
    """Get statistics about the terminology databases."""
    try:
        service = await get_domain_specialization_service()

        return {
            "neuroscience_concepts": len(service.neuro_db.concepts),
            "ai_concepts": len(service.ai_db.concepts),
            "cross_domain_mappings": len(service.cross_mapper.mappings) // 2,
            "databases": {
                "neuroscience": {
                    "concept_count": len(service.neuro_db.concepts),
                    "terms": list(service.neuro_db.concepts.keys()),
                },
                "ai": {
                    "concept_count": len(service.ai_db.concepts),
                    "terms": list(service.ai_db.concepts.keys()),
                },
            },
        }

    except Exception as e:
        logger.error(f"Database stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mappings/all")
async def get_all_mappings() -> dict[str, Any]:
    """Get all cross-domain mappings."""
    try:
        service = await get_domain_specialization_service()
        mappings = service.cross_mapper.get_all_mappings()

        return {
            "count": len(mappings),
            "mappings": [
                {
                    "source": m.source_concept,
                    "source_domain": m.source_domain.value,
                    "target": m.target_concept,
                    "target_domain": m.target_domain.value,
                    "mapping_type": m.mapping_type,
                    "strength": m.strength,
                    "description": m.description,
                }
                for m in mappings
            ],
        }

    except Exception as e:
        logger.error(f"Get all mappings failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check for domain specialization service."""
    try:
        service = await get_domain_specialization_service()

        return {
            "healthy": True,
            "service": "domain_specialization",
            "neuroscience_db_loaded": len(service.neuro_db.concepts) > 0,
            "ai_db_loaded": len(service.ai_db.concepts) > 0,
            "cross_mapper_loaded": len(service.cross_mapper.mappings) > 0,
        }

    except Exception as e:
        return {
            "healthy": False,
            "service": "domain_specialization",
            "error": str(e),
        }
