"""
Journey and Session models for session continuity feature.

These models represent the data structures for tracking conversations
across multiple sessions linked to a device's journey.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Message and Diagnosis Models (T007)
# =============================================================================

class Message(BaseModel):
    """A single message in a session conversation."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="When message was sent")


class Diagnosis(BaseModel):
    """IAS diagnosis result for a session."""
    step_id: int = Field(..., description="Step in the journey")
    action_id: int = Field(..., description="Action identifier")
    obstacle_id: int = Field(..., description="Obstacle identifier")
    explanation: str = Field(..., description="Diagnosis explanation")
    contrarian_insight: str = Field(..., description="Alternative perspective")


# =============================================================================
# Journey Models (T006)
# =============================================================================

class JourneyBase(BaseModel):
    """Base fields for Journey."""
    device_id: UUID = Field(..., description="Device identifier from ~/.dionysus/device_id")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")


class JourneyCreate(JourneyBase):
    """Schema for creating a new journey."""
    pass


class Journey(JourneyBase):
    """Full journey model with all fields."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Journey UUID")
    created_at: datetime = Field(..., description="Journey creation time")
    updated_at: datetime = Field(..., description="Last modification time")


class JourneyWithStats(Journey):
    """Journey with computed statistics."""
    session_count: int = Field(0, description="Number of sessions in this journey")
    is_new: bool = Field(False, description="True if journey was just created")


# =============================================================================
# Session Models (T007)
# =============================================================================

class SessionBase(BaseModel):
    """Base fields for Session."""
    journey_id: UUID = Field(..., description="FK to journeys.id")
    messages: list[Message] = Field(default_factory=list, description="Conversation messages")


class SessionCreate(SessionBase):
    """Schema for creating a new session."""
    pass


class Session(SessionBase):
    """Full session model with all fields."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Session UUID")
    created_at: datetime = Field(..., description="Session start time")
    updated_at: datetime = Field(..., description="Last message time")
    summary: Optional[str] = Field(None, description="Auto-generated summary for search")
    diagnosis: Optional[Diagnosis] = Field(None, description="IAS diagnosis if completed")
    confidence_score: int = Field(0, ge=0, le=100, description="Diagnosis confidence 0-100")


class SessionSummary(BaseModel):
    """Lightweight session representation for timeline queries."""
    session_id: UUID
    created_at: datetime
    summary: Optional[str]
    has_diagnosis: bool
    relevance_score: Optional[float] = None


# =============================================================================
# Session Event Models (T085)
# =============================================================================

class SessionEventType(str, Enum):
    """Types of session events to track."""
    DECISION = "decision"
    COMMITMENT = "commitment"
    TASK_COMPLETED = "task_completed"
    TOOL_USE = "tool_use"
    USER_FEEDBACK = "user_feedback"
    SYSTEM_STATUS = "system_status"


class SessionEvent(BaseModel):
    """A granular event within a session (decisions, actions, etc.)."""
    model_config = ConfigDict(use_enum_values=True)

    id: UUID = Field(default_factory=lambda: UUID(int=0), description="Event UUID")
    session_id: Optional[UUID] = Field(None, description="FK to sessions.id")
    event_type: SessionEventType = Field(..., description="Type of event")
    content: str = Field(..., description="Event description or payload")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Context metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When event occurred")


# =============================================================================
# JourneyDocument Models (T008)
# =============================================================================

class JourneyDocumentBase(BaseModel):
    """Base fields for JourneyDocument."""
    journey_id: UUID = Field(..., description="FK to journeys.id")
    document_type: str = Field(..., description="Type: 'woop_plan', 'file_upload', 'artifact', 'note'")
    title: Optional[str] = Field(None, description="Document title")
    content: Optional[str] = Field(None, description="Document content or file path")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")


class JourneyDocumentCreate(JourneyDocumentBase):
    """Schema for creating a new journey document."""
    pass


class JourneyDocument(JourneyDocumentBase):
    """Full journey document model with all fields."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Document UUID")
    created_at: datetime = Field(..., description="Creation time")


class DocumentSummary(BaseModel):
    """Lightweight document representation for timeline queries."""
    document_id: UUID
    document_type: str
    title: Optional[str]
    created_at: datetime


# =============================================================================
# Query Models
# =============================================================================

class JourneyHistoryQuery(BaseModel):
    """Query parameters for searching journey history."""
    journey_id: UUID = Field(..., description="Journey to search within")
    query: Optional[str] = Field(None, description="Keyword search on session summaries")
    from_date: Optional[datetime] = Field(None, description="Start of time range filter")
    to_date: Optional[datetime] = Field(None, description="End of time range filter")
    limit: int = Field(10, ge=1, le=100, description="Max results to return")
    include_documents: bool = Field(False, description="Include linked documents in results")


class JourneyHistoryResponse(BaseModel):
    """Response for journey history queries."""
    journey_id: UUID
    sessions: list[SessionSummary]
    documents: list[DocumentSummary] = Field(default_factory=list)
    total_results: int


class TimelineEntry(BaseModel):
    """A single entry in the journey timeline (session or document)."""
    entry_type: str = Field(..., description="'session' or 'document'")
    entry_id: UUID = Field(..., description="Session or document ID")
    created_at: datetime
    # Session-specific fields (optional)
    summary: Optional[str] = None
    has_diagnosis: bool = False
    # Document-specific fields (optional)
    document_type: Optional[str] = None
    title: Optional[str] = None


class JourneyTimelineResponse(BaseModel):
    """Response for journey timeline with interleaved sessions and documents."""
    journey_id: UUID
    entries: list[TimelineEntry] = Field(default_factory=list)
    total_entries: int = 0
