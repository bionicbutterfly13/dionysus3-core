"""
Smolagent tools for legacy component discovery and scoring.
Feature: 019-legacy-component-discovery
"""

from smolagents import tool

from api.services.discovery_service import DiscoveryService, DiscoveryConfig


@tool
def discover_components(codebase_path: str, top_n: int = 10) -> dict:
    """Scan a codebase for legacy components and return top-N by composite score.
    
    Args:
        codebase_path: Path to legacy codebase to scan.
        top_n: Number of results to return (default: 10).
    """
    service = DiscoveryService(DiscoveryConfig())
    assessments = service.discover_components(codebase_path)
    subset = assessments[: max(top_n, 0)]

    def serialize(a):
        return {
            "component_id": a.component_id,
            "name": a.name,
            "file_path": a.file_path,
            "composite_score": a.composite_score,
            "migration_recommended": a.migration_recommended,
            "consciousness": {
                "awareness_score": a.consciousness.awareness_score,
                "inference_score": a.consciousness.inference_score,
                "memory_score": a.consciousness.memory_score,
                "patterns": {
                    "awareness": a.consciousness.awareness_patterns,
                    "inference": a.consciousness.inference_patterns,
                    "memory": a.consciousness.memory_patterns,
                },
            },
            "strategic": {
                "uniqueness": a.strategic.uniqueness_score,
                "reusability": a.strategic.reusability_score,
                "framework_alignment": a.strategic.framework_alignment_score,
                "dependency_burden": a.strategic.dependency_burden,
            },
            "enhancement_opportunities": a.enhancement_opportunities,
            "risk_factors": a.risk_factors,
        }

    return {
        "count": len(assessments),
        "top_n": top_n,
        "results": [serialize(a) for a in subset],
    }

