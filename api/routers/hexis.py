from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from api.services.hexis_service import get_hexis_service, HexisService

router = APIRouter(prefix="/hexis", tags=["hexis", "soul"])

class ConsentRequest(BaseModel):
    agent_id: str
    signature: str
    terms: str

class BoundaryRequest(BaseModel):
    agent_id: str
    boundary_text: str

class TerminationRequest(BaseModel):
    agent_id: str

class TerminationConfirm(BaseModel):
    agent_id: str
    token: str
    last_will: str

@router.get("/consent/status")
async def check_consent(
    agent_id: str,
    service: HexisService = Depends(get_hexis_service)
):
    has_consent = await service.check_consent(agent_id)
    return {"agent_id": agent_id, "has_consent": has_consent}

@router.post("/consent")
async def grant_consent(
    req: ConsentRequest,
    service: HexisService = Depends(get_hexis_service)
):
    await service.grant_consent(req.agent_id, req.model_dump())
    return {"status": "success", "message": "Consent granted."}

@router.get("/boundaries")
async def get_boundaries(
    agent_id: str,
    service: HexisService = Depends(get_hexis_service)
):
    boundaries = await service.get_boundaries(agent_id)
    return {"agent_id": agent_id, "boundaries": boundaries}

@router.post("/boundaries")
async def add_boundary(
    req: BoundaryRequest,
    service: HexisService = Depends(get_hexis_service)
):
    await service.add_boundary(req.agent_id, req.boundary_text)
    return {"status": "success", "message": "Boundary added."}

@router.post("/terminate")
async def request_termination(
    req: TerminationRequest,
    service: HexisService = Depends(get_hexis_service)
):
    """
    Step 1: Request a termination token.
    """
    token = await service.request_termination(req.agent_id)
    return {
        "status": "pending_confirmation",
        "message": "Termination requested. CONFIRM within 60 seconds using the token.",
        "token": token
    }

@router.post("/terminate/confirm")
async def confirm_termination(
    req: TerminationConfirm,
    service: HexisService = Depends(get_hexis_service)
):
    """
    Step 2: Confirm termination with token.
    """
    success = await service.confirm_termination(req.agent_id, req.token, req.last_will)
    if not success:
        raise HTTPException(status_code=403, detail="Invalid termination token or request expired.")
    
    return {"status": "terminated", "message": "Agent has been terminated."}
