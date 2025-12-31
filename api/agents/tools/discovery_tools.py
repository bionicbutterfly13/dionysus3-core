"""
Class-based tools for legacy component discovery and scoring.
Feature: 019-legacy-component-discovery
Tasks: T4.1, T4.2
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from smolagents import Tool

from api.services.discovery_service import DiscoveryService, DiscoveryConfig

class ConsciousnessScore(BaseModel):
    awareness_score: float
    inference_score: float
    memory_score: float
    patterns: Dict[str, List[str]]

class StrategicScore(BaseModel):
    uniqueness: float
    reusability: float
    framework_alignment: float
    dependency_burden: float

class ComponentAssessment(BaseModel):
    component_id: str
    name: str
    file_path: str
    composite_score: float
    migration_recommended: bool
    consciousness: ConsciousnessScore
    strategic: StrategicScore
    enhancement_opportunities: List[str]
    risk_factors: List[str]

class DiscoveryOutput(BaseModel):
    count: int = Field(0, description="Total number of components discovered")
    top_n: int = Field(0, description="Number of results requested")
    results: List[ComponentAssessment] = Field(default_factory=list, description="Serialized assessment details")
    error: Optional[str] = Field(None, description="Error message if discovery failed")

class DiscoverComponentsTool(Tool):
    name = "discover_components"
    description = "Scan a codebase for legacy components and return top-N by composite score."
    
    inputs = {
        "codebase_path": {
            "type": "string",
            "description": "Path to legacy codebase to scan."
        },
        "top_n": {
            "type": "integer",
            "description": "Number of results to return (default: 10).",
            "default": 10,
            "nullable": True
        }
    }
    output_type = "any"

    def forward(self, codebase_path: str, top_n: int = 10) -> dict:
        from api.agents.resilience import wrap_with_resilience
        try:
            service = DiscoveryService(DiscoveryConfig())
            assessments = service.discover_components(codebase_path)
            subset = assessments[: max(top_n, 0)]

            def serialize(a) -> ComponentAssessment:
                return ComponentAssessment(
                    component_id=a.component_id,
                    name=a.name,
                    file_path=a.file_path,
                    composite_score=a.composite_score,
                    migration_recommended=a.migration_recommended,
                    consciousness=ConsciousnessScore(
                        awareness_score=a.consciousness.awareness_score,
                        inference_score=a.consciousness.inference_score,
                        memory_score=a.consciousness.memory_score,
                        patterns={
                            "awareness": a.consciousness.awareness_patterns,
                            "inference": a.consciousness.inference_patterns,
                            "memory": a.consciousness.memory_patterns,
                        },
                    ),
                    strategic=StrategicScore(
                        uniqueness=a.strategic.uniqueness_score,
                        reusability=a.strategic.reusability_score,
                        framework_alignment=a.strategic.framework_alignment_score,
                        dependency_burden=a.strategic.dependency_burden,
                    ),
                    enhancement_opportunities=a.enhancement_opportunities,
                    risk_factors=a.risk_factors,
                )

            output = DiscoveryOutput(
                count=len(assessments),
                top_n=top_n,
                results=[serialize(a) for a in subset]
            )
            return output.model_dump()
        except Exception as e:
            return DiscoveryOutput(
                error=wrap_with_resilience(f"Discovery failed: {e}")
            ).model_dump()

# Export tool instance
discover_components = DiscoverComponentsTool()
