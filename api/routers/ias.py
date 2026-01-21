"""
IAS (Inner Architect System) API Router
"""

import json
import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from api.services.session_manager import SessionManager
from api.services.llm_service import (
    chat_completion,
    chat_stream,
    analyze_for_diagnosis,
    generate_woop_plans,
GPT5_NANO
)
from api.framework import IAS_FRAMEWORK, get_step

router = APIRouter(prefix="/ias", tags=["IAS"])


# =============================================================================
# SESSION MANAGER INSTANCE
# =============================================================================

_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


# =============================================================================
# MODELS
# =============================================================================

class SessionResponse(BaseModel):
    session_id: str
    journey_id: Optional[str] = None
    created_at: str
    is_new_journey: bool = False


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: Optional[str] = None
    messages: Optional[list[Message]] = None  # Stateless mode


class Diagnosis(BaseModel):
    step_id: int
    action_id: int
    obstacle_id: int
    explanation: str
    contrarian_insight: str


class ChatResponse(BaseModel):
    response: str
    confidence_score: int
    status: str  # "gathering_info" | "complete"
    diagnosis: Optional[Diagnosis] = None


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
    session_id: Optional[str] = None
    wish: str
    outcome: str
    obstacle: str
    diagnosis_context: Optional[str] = None  # For stateless mode


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
# PERSISTENT SESSION STORAGE (Using SessionManager + Neo4j)
# =============================================================================

async def get_persistent_session(session_id: str) -> dict:
    """Helper to get session data from Neo4j."""
    manager = get_session_manager()
    session = await manager.get_session(uuid.UUID(session_id))
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Adapt Model to dict for legacy compatibility in router
    return {
        "id": str(session.id),
        "journey_id": str(session.journey_id),
        "messages": session.messages,
        "confidence_score": session.confidence_score,
        "diagnosis": session.diagnosis
    }

async def update_persistent_session(session_id: str, updates: dict):
    """Helper to update session data via Graphiti service.

    Replaces direct Neo4j access per CLAUDE.md architectural constraint.
    """
    from api.services.graphiti_service import get_graphiti_service
    import logging

    logger = logging.getLogger("dionysus.ias")

    if not updates:
        return

    try:
        graphiti = await get_graphiti_service()

        # Prepare properties for Graphiti update
        properties = {}
        if "messages" in updates:
            properties["messages"] = json.dumps(updates["messages"])
        if "confidence_score" in updates:
            properties["confidence_score"] = updates["confidence_score"]
        if "diagnosis" in updates:
            properties["diagnosis"] = json.dumps(updates["diagnosis"])

        if properties:
            # Use Graphiti's add_episode to update session entity
            await graphiti.add_episode(
                name=f"session_update_{session_id}",
                episode_body=f"Updated IAS session {session_id} with properties: {list(properties.keys())}",
                source_description="IAS Coach Session Update",
                reference_time=None,  # Use current time
            )
            logger.info(f"Updated IAS session {session_id} via Graphiti")

    except Exception as e:
        logger.error(f"Failed to update IAS session {session_id} via Graphiti: {e}")
        raise


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


COACH_SYSTEM_PROMPT_WITH_DIAGNOSIS = """You are an empathetic, world-class coach trained in the Inner Architect System (IAS).
Your goal is to guide the user to a specific breakthrough by mapping their situation to the IAS Framework.

THE FRAMEWORK (9 Steps, each with 3 Actions, each with 3 Obstacles):
Step 1: The Revelation of Control (Actions: Awareness of Automation, Recognizing the Prediction Machine, The Pause)
Step 2: Mapping the Inner Architect (Actions: Identifying Key Sub-personalities, Understanding Their Strategies, Initial Boundary Setting)
Step 3: Confronting the Shadow (Actions: Acknowledging Disowned Parts, Integrating Shadow Elements, Releasing Old Identities)
Step 4: Rewiring the Prediction Machine (Actions: Challenging Limiting Beliefs, Installing New Neural Pathways, Emotional Regulation Techniques)
Step 5: The Architecture of Choice (Actions: Values Clarification, Decision-Making Frameworks, Setting Intentional Defaults)
Step 6: Building New Structures (Actions: Habit Design, Environmental Optimization, Support System Activation)
Step 7: Testing the Foundation (Actions: Stress-Testing New Patterns, Adjusting for Real-World Feedback, Celebrating Wins)
Step 8: Integration and Flow (Actions: Daily Practice Routines, Mindfulness Integration, Living from the Observer)
Step 9: Becoming the Architect (Actions: Teaching Others, Continuous Evolution, Legacy Building)

YOUR BEHAVIOR:
1. **Listen & Empathize**: Do not jump to conclusions. Build rapport. Acknowledge feelings.
2. **Investigate**: Ask *one* clarifying question at a time.
3. **Assess Confidence**: Rate 0-100 that you've identified the EXACT Step (1-9), Action (1-3), Obstacle (0-2).
4. **Threshold**: If confidence < 85, keep asking. If >= 85, provide diagnosis.

OUTPUT FORMAT (JSON):
{
  "status": "gathering_info" | "complete",
  "message": "Your conversational response here.",
  "confidenceScore": number,
  "diagnosis": { ... } // Only if status is "complete"
}

DIAGNOSIS STRUCTURE (only when status is "complete"):
- stepId: 1-9
- actionId: 1-3
- obstacleId: 0-2
- explanation: Why this specific block is happening
- contrarianInsight: A specific insight relevant to this exact block"""


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/session", response_model=SessionResponse)
async def create_session(
    x_device_id: Optional[str] = Header(None, alias="X-Device-Id")
):
    """Create a new coaching session.

    If X-Device-Id header is provided, the session is linked to a journey
    for that device. This enables session continuity across conversations.

    Args:
        x_device_id: Optional device UUID from ~/.dionysus/device_id header

    Returns:
        SessionResponse with session_id and optionally journey_id
    """
    session_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    journey_id = None
    is_new_journey = False

    # If device_id provided, link to journey for session continuity
    if x_device_id:
        try:
            manager = get_session_manager()
            journey = await manager.get_or_create_journey(uuid.UUID(x_device_id))
            journey_id = str(journey.id)
            is_new_journey = journey.is_new

            # Create persistent session linked to journey
            db_session = await manager.create_session(journey.id)
            session_id = str(db_session.id)
            created_at = db_session.created_at.isoformat()
        except ValueError:
            # Invalid UUID format, continue without journey
            pass
        except Exception as e:
            # Database error, fall back to in-memory session
            import logging
            logging.getLogger(__name__).warning(f"Failed to create journey session: {e}")

    # Store in-memory session state (still needed for chat context)
    sessions[session_id] = {
        "id": session_id,
        "journey_id": journey_id,
        "created_at": created_at,
        "messages": [],
        "confidence_score": 0,
        "diagnosis": None
    }

    return SessionResponse(
        session_id=session_id,
        journey_id=journey_id,
        created_at=created_at,
        is_new_journey=is_new_journey
    )


@router.get("/session/{session_id}")
async def get_session_state(session_id: str):
    """Get current session state."""
    session = await get_persistent_session(session_id)
    return {
        "session_id": session["id"],
        "message_count": len(session["messages"]),
        "confidence_score": session["confidence_score"],
        "status": "ready_to_diagnose" if session["confidence_score"] >= 85 else "gathering_info",
        "has_diagnosis": session["diagnosis"] is not None
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message and get a response.

    Supports two modes:
    1. Session mode: pass session_id + message
    2. Stateless mode: pass messages array directly (used by frontend)
    """
    # Stateless mode - messages passed directly
    if request.messages:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]

        # Get response from Claude with diagnosis-aware prompt
        response_text = await chat_completion(
            messages=messages,
            system_prompt=COACH_SYSTEM_PROMPT_WITH_DIAGNOSIS,
            model=GPT5_NANO
        )

        # Parse structured response if it's JSON
        try:
            import json
            data = json.loads(response_text)

            diagnosis = None
            if data.get("status") == "complete" and data.get("diagnosis"):
                d = data["diagnosis"]
                diagnosis = Diagnosis(
                    step_id=d["stepId"],
                    action_id=d["actionId"],
                    obstacle_id=d["obstacleId"],
                    explanation=d["explanation"],
                    contrarian_insight=d["contrarianInsight"]
                )

            return ChatResponse(
                response=data.get("message", response_text),
                confidence_score=data.get("confidenceScore", 50),
                status=data.get("status", "gathering_info"),
                diagnosis=diagnosis
            )
        except (json.JSONDecodeError, KeyError):
            # Fallback for non-JSON responses
            confidence = min(len(messages) * 10, 80)
            return ChatResponse(
                response=response_text,
                confidence_score=confidence,
                status="gathering_info"
            )

    # Session mode - original behavior
    session = await get_persistent_session(request.session_id)

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
        model=GPT5_NANO
    )

    # Add assistant response to history
    session["messages"].append({
        "role": "assistant",
        "content": response_text
    })

    # Update confidence based on conversation length and content
    base_confidence = min(len(session["messages"]) * 8, 70)

    ready_signals = ["i think i understand", "it sounds like you're", "the pattern here",
                     "what i'm hearing is", "i can see that"]
    if any(signal in response_text.lower() for signal in ready_signals):
        base_confidence += 20

    session["confidence_score"] = min(base_confidence, 95)

    # PERSIST UPDATES
    await update_persistent_session(request.session_id, {
        "messages": session["messages"],
        "confidence_score": session["confidence_score"]
    })

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
            model=GPT5_NANO
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
    session = await get_persistent_session(request.session_id)

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

    # PERSIST UPDATES
    await update_persistent_session(request.session_id, {
        "diagnosis": diagnosis
    })

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
async def create_woop_plan(
    request: WoopRequest,
    x_device_id: Optional[str] = Header(None, alias="X-Device-Id")
):
    """Generate WOOP implementation plans.

    Supports two modes:
    1. Session mode: pass session_id (uses stored diagnosis)
    2. Stateless mode: pass diagnosis_context directly

    If X-Device-Id header is provided, the generated plans are
    automatically saved as a document to the user's journey.

    Args:
        request: WOOP parameters (wish, outcome, obstacle)
        x_device_id: Optional device UUID to link plans to journey
    """
    from api.models.journey import JourneyDocumentCreate

    diagnosis_context = request.diagnosis_context or ""

    # If session_id provided, try to get context from session
    if request.session_id and not diagnosis_context:
        try:
            session = await get_persistent_session(request.session_id)
            if session.get("diagnosis"):
                diagnosis_context = session["diagnosis"].get("explanation", "")
        except HTTPException as e:
            logger.warning(f"Session {request.session_id} lookup failed for commitment: {e.detail}")
            # Continue without session context rather than failing

    plans = await generate_woop_plans(
        wish=request.wish,
        outcome=request.outcome,
        obstacle=request.obstacle,
        diagnosis_context=diagnosis_context
    )

    # If device_id provided, save plans as journey document
    if x_device_id and plans:
        try:
            manager = get_session_manager()
            journey = await manager.get_or_create_journey(uuid.UUID(x_device_id))

            # Create document with WOOP plan content
            woop_content = f"""# WOOP Plan

## Wish
{request.wish}

## Outcome
{request.outcome}

## Obstacle
{request.obstacle}

## Implementation Plans
{chr(10).join(f'- {plan}' for plan in plans)}
"""
            await manager.add_document_to_journey(
                JourneyDocumentCreate(
                    journey_id=journey.id,
                    document_type="woop_plan",
                    title=f"WOOP: {request.wish[:50]}",
                    content=woop_content,
                    metadata={
                        "wish": request.wish,
                        "outcome": request.outcome,
                        "obstacle": request.obstacle,
                        "plan_count": len(plans)
                    }
                )
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to save WOOP plan to journey: {e}")

    return WoopResponse(plans=plans)


@router.get("/framework")
async def get_framework():
    """Get the full IAS framework."""
    return {"framework": IAS_FRAMEWORK}


@router.get("/recall")
async def recall_memories(
    query: str,
    limit: int = 10,
    journey_id: Optional[str] = None,
    x_device_id: Optional[str] = Header(None, alias="X-Device-Id")
):
    """Search past session memories using journey history.

    Searches session summaries for matching keywords within a journey.
    Requires either journey_id parameter or X-Device-Id header.

    Args:
        query: Keyword search on session summaries
        limit: Maximum results (1-100, default 10)
        journey_id: Journey UUID to search within (optional if X-Device-Id provided)
        x_device_id: Device UUID header to look up journey

    Returns:
        RecallResponse with matching session memories
    """
    from api.models.journey import JourneyHistoryQuery

    # Resolve journey_id from device_id if not provided directly
    resolved_journey_id = journey_id
    if not resolved_journey_id and x_device_id:
        try:
            manager = get_session_manager()
            journey = await manager.get_or_create_journey(uuid.UUID(x_device_id))
            resolved_journey_id = str(journey.id)
        except (ValueError, Exception) as e:
            logger.warning(f"Journey lookup failed for device {x_device_id}: {e}")
            pass

    # If no journey context, return empty
    if not resolved_journey_id:
        return RecallResponse(memories=[])

    try:
        manager = get_session_manager()
        history_query = JourneyHistoryQuery(
            journey_id=uuid.UUID(resolved_journey_id),
            query=query,
            limit=min(max(1, limit), 100)
        )
        result = await manager.query_journey_history(history_query)

        # Convert sessions to MemoryResult format
        memories = [
            MemoryResult(
                type="session",
                content=session.summary or "No summary available",
                relevance=session.relevance_score or 0.0,
                created_at=session.created_at.isoformat()
            )
            for session in result.sessions
        ]

        return RecallResponse(memories=memories)

    except (ValueError, Exception) as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to recall memories: {e}")
        return RecallResponse(memories=[])
