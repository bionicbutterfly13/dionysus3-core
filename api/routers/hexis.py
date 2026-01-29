from fastapi import APIRouter, Depends
from pydantic import BaseModel

from api.services.hexis_service import get_hexis_service, HexisService

router = APIRouter(prefix="/hexis", tags=["hexis", "soul"])

class ConsentRequest(BaseModel):
    agent_id: str
    signature: str
    terms: str

class BoundaryRequest(BaseModel):
    agent_id: str
    boundary_text: str


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
