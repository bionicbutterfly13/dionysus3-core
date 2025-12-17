"""
Skills Router
Feature: 006-procedural-skills

Webhook-backed write API for procedural memory represented as (:Skill) nodes.
The API never connects to Neo4j directly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from api.services.remote_sync import RemoteSyncService


router = APIRouter(prefix="/api/skills", tags=["skills"])


def get_sync_service() -> RemoteSyncService:
    return RemoteSyncService()


class SkillUpsertRequest(BaseModel):
    skill_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: Optional[str] = None
    proficiency: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    practice_count: Optional[int] = Field(default=None, ge=0)
    last_practiced: Optional[datetime] = None
    decay_rate: Optional[float] = Field(default=None, ge=0.0)

    learned_from_document_id: Optional[str] = None
    learned_from_session_id: Optional[str] = None
    applies_to_context_id: Optional[str] = None
    requires_skill_ids: list[str] = Field(default_factory=list)
    substep_skill_ids: list[str] = Field(default_factory=list)


class SkillUpsertResponse(BaseModel):
    success: bool = True
    skill_id: str
    result: dict = Field(default_factory=dict)


class SkillPracticeRequest(BaseModel):
    skill_id: str = Field(min_length=1)
    success: Optional[bool] = None
    delta: Optional[float] = Field(default=None, ge=-1.0, le=1.0)
    practiced_at: Optional[datetime] = None
    context_id: Optional[str] = None
    session_id: Optional[str] = None
    document_id: Optional[str] = None


class SkillPracticeResponse(BaseModel):
    success: bool = True
    skill_id: str
    result: dict = Field(default_factory=dict)


@router.post("/upsert", response_model=SkillUpsertResponse)
async def upsert_skill(req: SkillUpsertRequest) -> SkillUpsertResponse:
    sync = get_sync_service()
    res = await sync.skill_upsert(req.model_dump(mode="json"))
    if not res.get("success", True):
        raise HTTPException(status_code=502, detail=res.get("error", "Skill upsert failed"))
    return SkillUpsertResponse(success=True, skill_id=req.skill_id, result=res)


@router.post("/practice", response_model=SkillPracticeResponse)
async def practice_skill(req: SkillPracticeRequest) -> SkillPracticeResponse:
    sync = get_sync_service()
    res = await sync.skill_practice(req.model_dump(mode="json"))
    if not res.get("success", True):
        raise HTTPException(status_code=502, detail=res.get("error", "Skill practice failed"))
    return SkillPracticeResponse(success=True, skill_id=req.skill_id, result=res)

