"""
Monitoring API Router
Feature: 023-migration-observability
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, Header, Depends
from api.services.monitoring_service import get_monitoring_service

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


def get_monitoring_service_with_trace(x_trace_id: Optional[str] = Header(None)):
    import uuid
    service = get_monitoring_service()
    service.trace_id = x_trace_id or str(uuid.uuid4())
    return service


@router.get("/metrics", response_model=Dict)
async def get_metrics(service = Depends(get_monitoring_service_with_trace)):
    """Get system-wide metrics across all ported D2.0 features."""
    return await service.get_system_metrics()


@router.get("/performance", response_model=Dict)
async def get_performance(service = Depends(get_monitoring_service_with_trace)):
    """Get performance stats for coordination and agents."""
    return await service.get_performance_metrics()


@router.get("/alerts", response_model=List[Dict])
async def get_alerts(service = Depends(get_monitoring_service_with_trace)):
    """Get active system alerts and warnings."""
    return await service.get_alerts()

@router.get("/cognitive", response_model=Dict)
async def get_cognitive_stats(service = Depends(get_monitoring_service_with_trace)):
    """T020: Get real-time EFE and stability metrics."""
    from api.services.efe_engine import get_efe_engine
    from api.services.metaplasticity_service import get_metaplasticity_controller
    
    # In a real run, these would be aggregated from recent OODA cycles
    return {
        "status": "active",
        "efe_engine": "operational",
        "metaplasticity": "surprise-driven",
        "current_surprise_threshold": 0.5,
        "trace_id": service.trace_id
    }

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
