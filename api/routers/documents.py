"""
Document upload and management REST API.
Track: 062-document-ingestion-viz
Task: T062-003 - Create document upload router

Endpoints:
- POST /api/documents/upload - Upload PDF for processing
- POST /api/documents/{doc_id}/process - Trigger processing
- GET /api/documents/{doc_id}/status - Check processing status
- GET /api/documents/{doc_id}/results - Get extraction results
- GET /api/documents - List all documents
- DELETE /api/documents/{doc_id} - Remove document
"""

import asyncio
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from api.services.document_lifecycle import (
    Document,
    DocumentStatus,
    DocumentUpdateRequest,
    get_document_service,
)
from api.services.marker_extraction import (
    ExtractionResult,
    get_marker_service,
)

logger = logging.getLogger("dionysus.routers.documents")

router = APIRouter(prefix="/api/documents", tags=["documents"])


# Response models
class UploadResponse(BaseModel):
    """Response for document upload."""
    doc_id: UUID
    filename: str
    status: DocumentStatus
    message: str


class StatusResponse(BaseModel):
    """Response for status check."""
    doc_id: UUID
    status: DocumentStatus
    processing_started: Optional[str] = None
    processing_completed: Optional[str] = None
    error_message: Optional[str] = None
    chunk_count: int = 0
    entity_count: int = 0


class ResultsResponse(BaseModel):
    """Response for extraction results."""
    doc_id: UUID
    status: DocumentStatus
    markdown: Optional[str] = None
    sections: list = Field(default_factory=list)
    tables: list = Field(default_factory=list)
    word_count: int = 0
    extraction_method: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Response for document list."""
    documents: list[Document]
    total: int


class StatsResponse(BaseModel):
    """Response for document stats."""
    total: int
    by_status: dict


# Background processing task
async def process_document_background(doc_id: UUID):
    """Background task to process uploaded document."""
    logger.info(f"Starting background processing for {doc_id}")

    doc_service = get_document_service()
    marker_service = get_marker_service()

    # Update status to processing
    await doc_service.update_document(
        doc_id,
        DocumentUpdateRequest(status=DocumentStatus.PROCESSING)
    )

    try:
        # Get file path
        file_path = await doc_service.get_file_path(doc_id)
        if not file_path or not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {doc_id}")

        # Extract content (with fallback chain)
        result: ExtractionResult = await marker_service.extract_with_fallback(str(file_path))

        # Save extraction results
        results_dir = doc_service.results_dir / str(doc_id)
        results_dir.mkdir(parents=True, exist_ok=True)

        # Save markdown
        md_path = results_dir / "content.md"
        md_path.write_text(result.result.markdown)

        # Update document record
        await doc_service.update_document(
            doc_id,
            DocumentUpdateRequest(
                status=DocumentStatus.COMPLETED,
                extraction_result_path=str(results_dir),
                chunk_count=len(result.result.sections),
            )
        )

        logger.info(f"Completed processing {doc_id}: {result.result.word_count} words")

    except Exception as e:
        logger.error(f"Processing failed for {doc_id}: {e}")

        # Check retry count
        retry_count = await doc_service.increment_retry(doc_id)

        if retry_count < 3:
            logger.info(f"Scheduling retry {retry_count}/3 for {doc_id}")
            # Exponential backoff: 1s, 4s, 16s
            await asyncio.sleep(4 ** (retry_count - 1))
            await process_document_background(doc_id)
        else:
            await doc_service.update_document(
                doc_id,
                DocumentUpdateRequest(
                    status=DocumentStatus.FAILED,
                    error_message=str(e)
                )
            )


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_process: bool = Query(True, description="Automatically start processing"),
):
    """
    Upload a PDF document for processing.

    - **file**: PDF file to upload
    - **auto_process**: If true, immediately queue for processing
    """
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    # Read file content
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    if len(content) > 100 * 1024 * 1024:  # 100MB limit
        raise HTTPException(status_code=400, detail="File too large (max 100MB)")

    # Create document record
    doc_service = get_document_service()
    doc = await doc_service.create_document(
        file_content=content,
        original_filename=file.filename,
        metadata={"content_type": file.content_type}
    )

    # Queue for processing if auto_process
    if auto_process:
        await doc_service.update_document(
            doc.doc_id,
            DocumentUpdateRequest(status=DocumentStatus.QUEUED)
        )
        background_tasks.add_task(process_document_background, doc.doc_id)
        message = "Document uploaded and queued for processing"
    else:
        message = "Document uploaded. Call /process to start extraction."

    return UploadResponse(
        doc_id=doc.doc_id,
        filename=doc.original_filename,
        status=doc.status if not auto_process else DocumentStatus.QUEUED,
        message=message
    )


@router.post("/{doc_id}/process")
async def process_document(
    doc_id: UUID,
    background_tasks: BackgroundTasks,
):
    """
    Trigger processing for an uploaded document.

    Use this if auto_process was disabled on upload.
    """
    doc_service = get_document_service()
    doc = await doc_service.get_document(doc_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status == DocumentStatus.PROCESSING:
        raise HTTPException(status_code=409, detail="Document already processing")

    if doc.status == DocumentStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Document already processed")

    # Queue for processing
    await doc_service.update_document(
        doc_id,
        DocumentUpdateRequest(status=DocumentStatus.QUEUED)
    )
    background_tasks.add_task(process_document_background, doc_id)

    return {"message": "Processing started", "doc_id": str(doc_id)}


@router.get("/{doc_id}/status", response_model=StatusResponse)
async def get_document_status(doc_id: UUID):
    """Get the current processing status of a document."""
    doc_service = get_document_service()
    doc = await doc_service.get_document(doc_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return StatusResponse(
        doc_id=doc.doc_id,
        status=doc.status,
        processing_started=doc.processing_started.isoformat() if doc.processing_started else None,
        processing_completed=doc.processing_completed.isoformat() if doc.processing_completed else None,
        error_message=doc.error_message,
        chunk_count=doc.chunk_count,
        entity_count=doc.entity_count,
    )


@router.get("/{doc_id}/results", response_model=ResultsResponse)
async def get_document_results(doc_id: UUID):
    """Get extraction results for a completed document."""
    doc_service = get_document_service()
    doc = await doc_service.get_document(doc_id)

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.status != DocumentStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Document not ready. Status: {doc.status}"
        )

    # Load results
    from pathlib import Path

    results_path = Path(doc.extraction_result_path) if doc.extraction_result_path else None

    markdown = ""
    if results_path and (results_path / "content.md").exists():
        markdown = (results_path / "content.md").read_text()

    return ResultsResponse(
        doc_id=doc.doc_id,
        status=doc.status,
        markdown=markdown,
        word_count=len(markdown.split()) if markdown else 0,
        extraction_method=doc.metadata.get("extraction_method"),
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    status: Optional[DocumentStatus] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """List all documents with optional status filter."""
    doc_service = get_document_service()
    documents = await doc_service.list_documents(status=status, limit=limit, offset=offset)

    return DocumentListResponse(
        documents=documents,
        total=len(documents)
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get document processing statistics."""
    doc_service = get_document_service()
    stats = await doc_service.get_stats()

    return StatsResponse(
        total=stats.get("total", 0),
        by_status={k: v for k, v in stats.items() if k != "total"}
    )


@router.delete("/{doc_id}")
async def delete_document(doc_id: UUID):
    """Delete a document and all associated artifacts."""
    doc_service = get_document_service()

    # Check if document exists
    doc = await doc_service.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Don't delete while processing
    if doc.status == DocumentStatus.PROCESSING:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete document while processing"
        )

    # Delete
    success = await doc_service.delete_document(doc_id)

    if success:
        return {"message": "Document deleted", "doc_id": str(doc_id)}
    else:
        raise HTTPException(status_code=500, detail="Delete failed")
