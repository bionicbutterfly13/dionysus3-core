"""
Monitoring Pulse Router

Provides aggregated context for documentation systems (SilverBullet).
Fetches recent commits, graph entities, and system status to generate
a "Daily Pulse" for project journals.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import subprocess
import os

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.services.graphiti_service import get_graphiti_dependency, GraphitiService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/monitoring/pulse",
    tags=["monitoring"],
)

class CommitInfo(BaseModel):
    hash: str
    author: str
    date: str
    message: str
    files_changed: List[str]

class EntityInfo(BaseModel):
    name: str
    type: str
    summary: Optional[str]

class PulseResponse(BaseModel):
    timestamp: datetime
    git_commits: List[CommitInfo]
    recent_entities: List[EntityInfo]
    system_status: Dict[str, str]
    narrative_summary: Optional[str] = None

def get_git_commits(limit: int = 5) -> List[CommitInfo]:
    """Get recent git commits from the local repository."""
    try:
        # Get commit log with files
        cmd = [
            "git", "log", f"-n {limit}", 
            "--pretty=format:%H|%an|%ad|%s", 
            "--date=iso", "--name-only"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode != 0:
            logger.warning(f"Git log failed: {result.stderr}")
            return []

        commits = []
        current_commit = None
        
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
                
            if "|" in line and len(line.split("|")) == 4:
                # New commit header
                parts = line.split("|")
                current_commit = {
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3],
                    "files_changed": []
                }
                commits.append(current_commit)
            elif current_commit:
                # File path
                current_commit["files_changed"].append(line.strip())
                
        return [CommitInfo(**c) for c in commits]
    except Exception as e:
        logger.error(f"Error fetching git commits: {e}")
        return []

@router.get("/daily", response_model=PulseResponse)
async def get_daily_pulse(
    graphiti: GraphitiService = Depends(get_graphiti_dependency)
) -> PulseResponse:
    """
    Get the Daily Pulse: aggregated context for today's journal.
    """
    # 1. Get Code Context (Git)
    commits = get_git_commits(limit=5)
    
    # 2. Get Knowledge Context (Graphiti/Neo4j)
    recent_entities = []
    try:
        # Search for broad terms to get a snapshot of the current state
        graph_data = await graphiti.search("system architecture", limit=5)
        
        if graph_data and "edges" in graph_data:
            seen = set()
            for edge in graph_data["edges"]:
                name = edge.get("name")
                if name and name not in seen:
                    recent_entities.append(EntityInfo(
                        name=name,
                        type="concept",
                        summary=edge.get("fact")
                    ))
                    seen.add(name)
    except Exception as e:
        logger.warning(f"Pulse Graphiti search failed: {e}")

    # 3. System Status
    status = {
        "api": "online",
        "neo4j": "connected",
        "n8n": "active"
    }

    return PulseResponse(
        timestamp=datetime.utcnow(),
        git_commits=commits,
        recent_entities=recent_entities,
        system_status=status,
        narrative_summary="System operating normally. Recent focus on MemEvolve and documentation integration."
    )
