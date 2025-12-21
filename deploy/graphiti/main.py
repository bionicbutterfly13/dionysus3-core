"""
Graphiti Service - Standalone FastAPI application.

Temporal knowledge graph with entity extraction via OpenAI.
Deployed on VPS alongside Neo4j and n8n.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.graphiti_router import router as graphiti_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    print("Starting Graphiti service...")
    yield
    print("Shutting down Graphiti service...")


app = FastAPI(
    title="Graphiti Service",
    description="Temporal knowledge graph with entity extraction",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - allow n8n and external access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": "graphiti"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "graphiti",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/api/graphiti/ingest",
            "/api/graphiti/search",
            "/api/graphiti/health",
        ]
    }


# Include Graphiti router
app.include_router(graphiti_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8001)),
        reload=True
    )
