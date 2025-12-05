"""
IAS (Inner Architect System) API Router
"""

import json
import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.services.claude import (
    chat_completion,
    chat_stream,
    analyze_for_diagnosis,
    generate_woop_plans,
    HAIKU
)
from api.framework import IAS_FRAMEWORK, get_step, get_obstacle

router = APIRouter(prefix="/ias", tags=["IAS"])


# =============================================================================
# MODELS
# =============================================================================

class SessionResponse(BaseModel):
    session_id: str
    created_at: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    confidence_score: int
    status: str  # "gathering_info" | "ready_to_diagnose"


class DiagnoseRequest(BaseModel):
    session_id: str


class DiagnosisResponse(BaseModel):
    step_id: int
    action_id: int
    obstacle_id: int
    explanation: str
    contrarian_insight: str
    step_title: str
    action_title: str
    obstacle_text: str


class WoopRequest(BaseModel):
    session_id: str
    wish: str
    outcome: str
    obstacle: str


class WoopResponse(BaseModel):
    plans: list[str]


class RecallRequest(BaseModel):
    query: str
    limit: int = 10


class MemoryResult(BaseModel):
    type: str
    content: str
    relevance: float
    created_at: str


class RecallResponse(BaseModel):
    memories: list[MemoryResult]


# =============================================================================
# SESSION STORAGE (In-memory for MVP, move to dionysus memory later)
# =============================================================================

sessions: dict[str, dict] = {}


def get_session(session_id: str) -> dict:
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

COACH_SYSTEM_PROMPT = """You are an empathetic, world-class coach trained in the Inner Architect System (IAS).
Your goal is to guide the user to a specific breakthrough by mapping their situation to the IAS Framework.

YOUR BEHAVIOR:
1. **Listen & Empathize**: Do not jump to conclusions. Build rapport. Use active listening.
   Acknowledge their feelings ("It sounds like...", "I hear that...").
2. **Investigate**: Ask *one* clarifying question at a time to narrow down exactly where they are stuck.
3. **Assess Confidence**: Internally rate your confidence (0-100) that you have identified the
   EXACT Step (1-9), Action (1-3), and Obstacle (index 0-2).
4. **Threshold**:
   - If confidence is < 85, keep asking questions.
   - If confidence is >= 85, indicate you're ready to diagnose.

Keep responses concise but warm. You are helping someone who is stuck and needs guidance, not a lecture.

Respond conversationally. Do NOT output JSON or structured data - just speak naturally as a coach would."""


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/session", response_model=SessionResponse)
async def create_session():
    """Create a new coaching session."""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "messages": [],
        "confidence_score": 0,
        "diagnosis": None
    }
    return SessionResponse(
        session_id=session_id,
        created_at=sessions[session_id]["created_at"]
    )


@router.get("/session/{session_id}")
async def get_session_state(session_id: str):
    """Get current session state."""
    session = get_session(session_id)
    return {
        "session_id": session["id"],
        "message_count": len(session["messages"]),
        "confidence_score": session["confidence_score"],
        "status": "ready_to_diagnose" if session["confidence_score"] >= 85 else "gathering_info",
        "has_diagnosis": session["diagnosis"] is not None
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get a response."""
    session = get_session(request.session_id)

    # Add user message to history
    session["messages"].append({
        "role": "user",
        "content": request.message
    })

    # Build messages for Claude
    messages = session["messages"].copy()

    # Get response from Claude
    response_text = await chat_completion(
        messages=messages,
        system_prompt=COACH_SYSTEM_PROMPT,
        model=HAIKU
    )

    # Add assistant response to history
    session["messages"].append({
        "role": "assistant",
        "content": response_text
    })

    # Update confidence based on conversation length and content
    # Simple heuristic: increases with each exchange, caps at 90
    base_confidence = min(len(session["messages"]) * 8, 70)

    # Check for diagnosis-ready signals in the response
    ready_signals = ["i think i understand", "it sounds like you're", "the pattern here",
                     "what i'm hearing is", "i can see that"]
    if any(signal in response_text.lower() for signal in ready_signals):
        base_confidence += 20

    session["confidence_score"] = min(base_confidence, 95)

    status = "ready_to_diagnose" if session["confidence_score"] >= 85 else "gathering_info"

    return ChatResponse(
        response=response_text,
        confidence_score=session["confidence_score"],
        status=status
    )


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """Send a message and stream the response."""
    session = get_session(request.session_id)

    # Add user message
    session["messages"].append({
        "role": "user",
        "content": request.message
    })

    async def generate():
        full_response = ""
        async for chunk in chat_stream(
            messages=session["messages"].copy(),
            system_prompt=COACH_SYSTEM_PROMPT,
            model=HAIKU
        ):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

        # Store full response
        session["messages"].append({
            "role": "assistant",
            "content": full_response
        })

        # Update confidence
        session["confidence_score"] = min(len(session["messages"]) * 8 + 20, 95)

        # Send final event with metadata
        yield f"data: {json.dumps({'done': True, 'confidence_score': session['confidence_score']})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@router.post("/diagnose", response_model=DiagnosisResponse)
async def diagnose(request: DiagnoseRequest):
    """Analyze conversation and produce diagnosis."""
    session = get_session(request.session_id)

    if session["confidence_score"] < 50:
        raise HTTPException(
            status_code=400,
            detail="Not enough conversation to diagnose. Continue chatting."
        )

    # Use Sonnet to analyze
    diagnosis = await analyze_for_diagnosis(
        conversation=session["messages"],
        framework=IAS_FRAMEWORK
    )

    # Get human-readable details
    step = get_step(diagnosis["step_id"])
    step_title = step["title"] if step else "Unknown"

    action_title = "Unknown"
    obstacle_text = "Unknown"
    if step:
        for action in step["actions"]:
            if action["id"] == diagnosis["action_id"]:
                action_title = action["title"]
                if 0 <= diagnosis["obstacle_id"] < len(action["obstacles"]):
                    obstacle_text = action["obstacles"][diagnosis["obstacle_id"]]
                break

    session["diagnosis"] = diagnosis

    return DiagnosisResponse(
        step_id=diagnosis["step_id"],
        action_id=diagnosis["action_id"],
        obstacle_id=diagnosis["obstacle_id"],
        explanation=diagnosis["explanation"],
        contrarian_insight=diagnosis["contrarian_insight"],
        step_title=step_title,
        action_title=action_title,
        obstacle_text=obstacle_text
    )


@router.post("/woop", response_model=WoopResponse)
async def create_woop_plan(request: WoopRequest):
    """Generate WOOP implementation plans."""
    session = get_session(request.session_id)

    diagnosis_context = ""
    if session["diagnosis"]:
        diagnosis_context = session["diagnosis"].get("explanation", "")

    plans = await generate_woop_plans(
        wish=request.wish,
        outcome=request.outcome,
        obstacle=request.obstacle,
        diagnosis_context=diagnosis_context
    )

    return WoopResponse(plans=plans)


@router.get("/framework")
async def get_framework():
    """Get the full IAS framework."""
    return {"framework": IAS_FRAMEWORK}


@router.get("/recall")
async def recall_memories(query: str, limit: int = 10):
    """Search past session memories (placeholder for dionysus integration)."""
    # TODO: Integrate with dionysus fast_recall()
    return RecallResponse(memories=[])
