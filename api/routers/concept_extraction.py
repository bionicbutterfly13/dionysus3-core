"""
Concept Extraction Router - REST API for five-level concept extraction.

Provides endpoints for:
- Full five-level extraction pipeline
- Single-level extraction
- Concept retrieval by document ID
- Storage to Graphiti knowledge graph
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.models.concept_extraction import (
    ConceptExtractionLevel,
    FiveLevelExtractionResult,
    LevelExtractionResult,
)
from api.services.concept_extraction import (
    get_concept_extraction_service,
    register_all_extractors,
)


router = APIRouter(prefix="/api/concepts", tags=["concept-extraction"])


# --------------------------------------------------------------------------
# Request/Response Models
# --------------------------------------------------------------------------


class ExtractionRequest(BaseModel):
    """Request for concept extraction."""

    content: str = Field(..., description="Text content to extract concepts from")
    document_id: Optional[str] = Field(
        default=None,
        description="Document identifier for tracking",
    )
    context: Optional[dict] = Field(
        default=None,
        description="Additional context (e.g., domain hints, source info)",
    )


class SingleLevelExtractionRequest(BaseModel):
    """Request for single-level extraction."""

    content: str = Field(..., description="Text content to extract concepts from")
    level: ConceptExtractionLevel = Field(
        ..., description="Extraction level (ATOMIC, RELATIONAL, etc.)"
    )
    document_id: Optional[str] = Field(
        default=None,
        description="Document identifier for tracking",
    )
    context: Optional[dict] = Field(
        default=None,
        description="Additional context",
    )
    include_lower_concepts: bool = Field(
        default=False,
        description="Run all lower levels first and pass concepts up",
    )


class StoreRequest(BaseModel):
    """Request to store extraction results in Graphiti."""

    extraction_result: dict = Field(
        ..., description="FiveLevelExtractionResult as dict"
    )
    group_id: Optional[str] = Field(
        default=None,
        description="Graphiti group ID for partitioning",
    )


class StoreResponse(BaseModel):
    """Response from storing extraction results."""

    stored_entities: int = Field(..., description="Number of entities stored")
    stored_relationships: int = Field(
        ..., description="Number of relationships stored"
    )
    errors: list[str] = Field(
        default_factory=list, description="Any errors encountered"
    )


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------


@router.post("/extract", response_model=FiveLevelExtractionResult)
async def extract_concepts(request: ExtractionRequest):
    """
    Run the full five-level concept extraction pipeline.

    Extracts concepts at all five levels:
    1. ATOMIC - Individual terms, entities, definitions
    2. RELATIONAL - Connections, causality, dependencies
    3. COMPOSITE - Complex multi-part ideas and systems
    4. CONTEXTUAL - Domain paradigms, theoretical frameworks
    5. NARRATIVE - Argument flows, story progressions

    Each level receives concepts from all lower levels to build
    hierarchical understanding.
    """
    try:
        service = await get_concept_extraction_service(auto_register=True)
        result = await service.extract_all(
            content=request.content,
            context=request.context or {},
            document_id=request.document_id or "",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/{level}", response_model=LevelExtractionResult)
async def extract_single_level(
    level: ConceptExtractionLevel,
    request: ExtractionRequest,
    include_lower_concepts: bool = Query(
        default=False,
        description="Run lower levels first and pass concepts up",
    ),
):
    """
    Extract concepts at a specific level.

    If include_lower_concepts is True, runs all levels below the
    requested level first and passes accumulated concepts up.
    """
    try:
        service = await get_concept_extraction_service(auto_register=True)

        lower_concepts = None
        if include_lower_concepts:
            # Build concepts from lower levels
            level_order = [
                ConceptExtractionLevel.ATOMIC,
                ConceptExtractionLevel.RELATIONAL,
                ConceptExtractionLevel.COMPOSITE,
                ConceptExtractionLevel.CONTEXTUAL,
                ConceptExtractionLevel.NARRATIVE,
            ]

            target_index = level_order.index(level)
            all_concepts = []

            for lower_level in level_order[:target_index]:
                extractor = service.get_extractor(lower_level)
                if extractor:
                    lower_result = await extractor.extract(
                        content=request.content,
                        context=request.context or {},
                        lower_level_concepts=all_concepts if all_concepts else None,
                    )
                    all_concepts.extend(lower_result.concepts)

            lower_concepts = all_concepts if all_concepts else None

        # Extract at requested level
        extractor = service.get_extractor(level)
        if not extractor:
            raise HTTPException(
                status_code=400,
                detail=f"No extractor registered for level {level.value}",
            )

        result = await extractor.extract(
            content=request.content,
            context=request.context or {},
            lower_level_concepts=lower_concepts,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/store", response_model=StoreResponse)
async def store_extraction_results(request: StoreRequest):
    """
    Store extraction results in Graphiti knowledge graph.

    Maps concepts to entity types based on extraction level and
    creates relationships between concepts.
    """
    try:
        service = await get_concept_extraction_service(auto_register=True)

        # Reconstruct FiveLevelExtractionResult from dict
        result = FiveLevelExtractionResult(**request.extraction_result)

        # Get Graphiti service
        from api.services.graphiti_service import get_graphiti_service

        graphiti = await get_graphiti_service()

        # Store in Graphiti
        store_result = await service.store_in_graphiti(
            result=result,
            graphiti_service=graphiti,
            group_id=request.group_id,
        )

        return StoreResponse(
            stored_entities=store_result.get("stored_entities", 0),
            stored_relationships=store_result.get("stored_relationships", 0),
            errors=store_result.get("errors", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/levels")
async def list_extraction_levels():
    """
    List available extraction levels and their descriptions.
    """
    return {
        "levels": [
            {
                "name": level.name,
                "index": level.value,
                "description": {
                    ConceptExtractionLevel.ATOMIC: "Individual terms, entities, definitions",
                    ConceptExtractionLevel.RELATIONAL: "Connections, causality, dependencies",
                    ConceptExtractionLevel.COMPOSITE: "Complex multi-part ideas and systems",
                    ConceptExtractionLevel.CONTEXTUAL: "Domain paradigms, theoretical frameworks",
                    ConceptExtractionLevel.NARRATIVE: "Argument flows, story progressions",
                }.get(level, ""),
            }
            for level in ConceptExtractionLevel
        ]
    }


@router.get("/health")
async def health_check():
    """
    Check concept extraction service health.

    Returns registered extractors and their status.
    """
    try:
        service = await get_concept_extraction_service(auto_register=True)
        registered_levels = []

        for level in ConceptExtractionLevel:
            extractor = service.get_extractor(level)
            registered_levels.append(
                {
                    "level": level.value,
                    "registered": extractor is not None,
                    "extractor_class": (
                        extractor.__class__.__name__ if extractor else None
                    ),
                }
            )

        return {
            "healthy": True,
            "extractors": registered_levels,
            "all_levels_registered": all(
                e["registered"] for e in registered_levels
            ),
        }
    except Exception as e:
        return {"healthy": False, "error": str(e)}
