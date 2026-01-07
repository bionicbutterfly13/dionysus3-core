"""
Dionysus-Core API Server

FastAPI HTTP layer for web/mobile clients.
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
# Load environment variables early
load_dotenv()

from fastapi import FastAPI, Request

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from api.routers import ias, heartbeat, models, memory, skills, sync, session, memevolve, maintenance, avatar, discovery, coordination, rollback, kg_learning, monitoring, mosaeic, graphiti, monitoring_pulse, network_state, belief_journey, agents, meta_tot, metacognition, consciousness, beautiful_loop
from api.models.network_state import get_network_state_config
from api.services.journal_service import start_journal_scheduler
import asyncio

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger("dionysus.api")




@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting Dionysus API server...")

    # Start Background Journaler
    asyncio.create_task(start_journal_scheduler())
    try:
        from api.services.meta_tot_decision import get_meta_tot_decision_service

        await get_meta_tot_decision_service().warmup()
        logger.info("Meta-ToT thresholds warmup complete.")
    except Exception as exc:
        logger.warning(f"Meta-ToT thresholds warmup skipped: {exc}")
    
    # Note: PostgreSQL removed. Using Graphiti/Neo4j for persistence.
    # Services requiring db_pool need migration to Graphiti.
    yield
    # Shutdown
    print("Shutting down Dionysus API server...")


# Create FastAPI app
app = FastAPI(
    title="Dionysus Core API",
    description="AI consciousness and memory system with IAS coaching",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Add your production frontend domains here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    thresholds: dict[str, float] | dict[str, str] | None = None
    status = "healthy"
    try:
        from api.services.meta_tot_decision import get_meta_tot_decision_service

        thresholds = await get_meta_tot_decision_service().get_thresholds_snapshot()
    except Exception as exc:
        thresholds = {"error": str(exc)}
        status = "degraded"
    return {
        "status": status,
        "service": "dionysus-core",
        "meta_tot_thresholds": thresholds,
    }


# Include routers
app.include_router(ias.router)
app.include_router(heartbeat.router)
app.include_router(models.router)
app.include_router(memory.router)
app.include_router(skills.router)
app.include_router(sync.router)
app.include_router(session.router)
app.include_router(memevolve.router)
app.include_router(maintenance.router)
app.include_router(avatar.router)
app.include_router(discovery.router)
app.include_router(coordination.router)
app.include_router(rollback.router)
app.include_router(kg_learning.router)
app.include_router(monitoring.router)
app.include_router(mosaeic.router)
app.include_router(monitoring_pulse.router)
app.include_router(graphiti.router)
app.include_router(belief_journey.router)
app.include_router(agents.router)
app.include_router(meta_tot.router)
app.include_router(metacognition.router)
app.include_router(consciousness.router)
app.include_router(beautiful_loop.router)

# Network state router (conditional on feature flag) - T007
if get_network_state_config().network_state_enabled:
    app.include_router(network_state.router)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
