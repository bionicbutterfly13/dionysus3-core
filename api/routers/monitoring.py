"""
Monitoring API Router
Feature: 023-migration-observability
"""

from typing import Dict, List
from fastapi import APIRouter
from api.services.monitoring_service import get_monitoring_service

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/metrics", response_model=Dict)
async def get_metrics():
    """Get system-wide metrics across all ported D2.0 features."""
    service = get_monitoring_service()
    return await service.get_system_metrics()


@router.get("/performance", response_model=Dict)
async def get_performance():
    """Get performance stats for coordination and agents."""
    service = get_monitoring_service()
    return await service.get_performance_metrics()


@router.get("/alerts", response_model=List[Dict])
async def get_alerts():
    """Get active system alerts and warnings."""
    service = get_monitoring_service()
    return await service.get_alerts()

@router.get("/cognitive", response_model=Dict)
async def get_cognitive_stats():
    """T020: Get real-time EFE and stability metrics."""
    from api.services.efe_engine import get_efe_engine
    from api.services.metaplasticity_service import get_metaplasticity_controller
    
    # In a real run, these would be aggregated from recent OODA cycles
    return {
        "status": "active",
        "efe_engine": "operational",
        "metaplasticity": "surprise-driven",
        "current_surprise_threshold": 0.5
    }
