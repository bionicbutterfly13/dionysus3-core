"""
Document lifecycle management service with SQLite registry.
Track: 062-document-ingestion-viz
Task: T062-004 - Create document registry (SQLite)

Manages document state from upload through processing to completion.
"""

import asyncio
import hashlib
import logging
import os
import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import aiosqlite
from pydantic import BaseModel, Field

logger = logging.getLogger("dionysus.services.document_lifecycle")


class DocumentStatus(str, Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Document(BaseModel):
    """Document metadata model."""
    doc_id: UUID
    filename: str
    original_filename: str
    content_hash: str
    file_size: int
    upload_time: datetime
    status: DocumentStatus = DocumentStatus.UPLOADED
    processing_started: Optional[datetime] = None
    processing_completed: Optional[datetime] = None
    error_message: Optional[str] = None
    extraction_result_path: Optional[str] = None
    graphiti_group_id: Optional[str] = None
    chunk_count: int = 0
    entity_count: int = 0
    retry_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentCreateRequest(BaseModel):
    """Request to create a new document record."""
    original_filename: str
    content_hash: str
    file_size: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentUpdateRequest(BaseModel):
    """Request to update document status."""
    status: Optional[DocumentStatus] = None
    error_message: Optional[str] = None
    extraction_result_path: Optional[str] = None
    graphiti_group_id: Optional[str] = None
    chunk_count: Optional[int] = None
    entity_count: Optional[int] = None


class DocumentLifecycleService:
    """
    Service for managing document lifecycle with SQLite persistence.

    Features:
    - Document registration and tracking
    - Status transitions with timestamps
    - Retry logic with exponential backoff
    - Partial completion tracking
    - Cleanup on delete
    """

    def __init__(
        self,
        db_path: str = "data/documents.db",
        upload_dir: str = "data/uploads",
        results_dir: str = "data/extraction_results",
    ):
        """
        Initialize document lifecycle service.

        Args:
            db_path: Path to SQLite database
            upload_dir: Directory for uploaded files
            results_dir: Directory for extraction results
        """
        self.db_path = Path(db_path)
        self.upload_dir = Path(upload_dir)
        self.results_dir = Path(results_dir)

        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure database is initialized."""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    doc_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    upload_time TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'uploaded',
                    processing_started TEXT,
                    processing_completed TEXT,
                    error_message TEXT,
                    extraction_result_path TEXT,
                    graphiti_group_id TEXT,
                    chunk_count INTEGER DEFAULT 0,
                    entity_count INTEGER DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash)
            """)
            await db.commit()

        self._initialized = True
        logger.info(f"Document registry initialized at {self.db_path}")

    async def create_document(
        self,
        file_content: bytes,
        original_filename: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """
        Create a new document record and save the file.

        Args:
            file_content: Raw file bytes
            original_filename: Original filename from upload
            metadata: Optional metadata

        Returns:
            Created Document record
        """
        await self._ensure_initialized()

        # Generate document ID and hash
        doc_id = uuid4()
        content_hash = hashlib.sha256(file_content).hexdigest()

        # Check for duplicate
        existing = await self.get_by_hash(content_hash)
        if existing:
            logger.info(f"Document with hash {content_hash[:8]} already exists: {existing.doc_id}")
            return existing

        # Save file
        ext = Path(original_filename).suffix or ".pdf"
        filename = f"{doc_id}{ext}"
        file_path = self.upload_dir / filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        # Create record
        doc = Document(
            doc_id=doc_id,
            filename=filename,
            original_filename=original_filename,
            content_hash=content_hash,
            file_size=len(file_content),
            upload_time=datetime.utcnow(),
            status=DocumentStatus.UPLOADED,
            metadata=metadata or {},
        )

        # Save to database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO documents (
                    doc_id, filename, original_filename, content_hash, file_size,
                    upload_time, status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(doc.doc_id),
                    doc.filename,
                    doc.original_filename,
                    doc.content_hash,
                    doc.file_size,
                    doc.upload_time.isoformat(),
                    doc.status.value,
                    str(doc.metadata),
                ),
            )
            await db.commit()

        logger.info(f"Created document {doc_id}: {original_filename}")
        return doc

    async def get_document(self, doc_id: UUID) -> Optional[Document]:
        """Get document by ID."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM documents WHERE doc_id = ?", (str(doc_id),)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_document(row)
        return None

    async def get_by_hash(self, content_hash: str) -> Optional[Document]:
        """Get document by content hash (for deduplication)."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM documents WHERE content_hash = ?", (content_hash,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return self._row_to_document(row)
        return None

    async def list_documents(
        self,
        status: Optional[DocumentStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Document]:
        """List documents with optional status filter."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if status:
                query = "SELECT * FROM documents WHERE status = ? ORDER BY upload_time DESC LIMIT ? OFFSET ?"
                params = (status.value, limit, offset)
            else:
                query = "SELECT * FROM documents ORDER BY upload_time DESC LIMIT ? OFFSET ?"
                params = (limit, offset)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_document(row) for row in rows]

    async def update_document(
        self,
        doc_id: UUID,
        update: DocumentUpdateRequest,
    ) -> Optional[Document]:
        """Update document fields."""
        await self._ensure_initialized()

        updates = []
        params = []

        if update.status is not None:
            updates.append("status = ?")
            params.append(update.status.value)

            # Update timestamps based on status
            if update.status == DocumentStatus.PROCESSING:
                updates.append("processing_started = ?")
                params.append(datetime.utcnow().isoformat())
            elif update.status in (DocumentStatus.COMPLETED, DocumentStatus.FAILED):
                updates.append("processing_completed = ?")
                params.append(datetime.utcnow().isoformat())

        if update.error_message is not None:
            updates.append("error_message = ?")
            params.append(update.error_message)

        if update.extraction_result_path is not None:
            updates.append("extraction_result_path = ?")
            params.append(update.extraction_result_path)

        if update.graphiti_group_id is not None:
            updates.append("graphiti_group_id = ?")
            params.append(update.graphiti_group_id)

        if update.chunk_count is not None:
            updates.append("chunk_count = ?")
            params.append(update.chunk_count)

        if update.entity_count is not None:
            updates.append("entity_count = ?")
            params.append(update.entity_count)

        if not updates:
            return await self.get_document(doc_id)

        params.append(str(doc_id))

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE documents SET {', '.join(updates)} WHERE doc_id = ?",
                params,
            )
            await db.commit()

        return await self.get_document(doc_id)

    async def increment_retry(self, doc_id: UUID) -> int:
        """Increment retry count and return new value."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE documents SET retry_count = retry_count + 1 WHERE doc_id = ?",
                (str(doc_id),),
            )
            await db.commit()

            async with db.execute(
                "SELECT retry_count FROM documents WHERE doc_id = ?", (str(doc_id),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def delete_document(self, doc_id: UUID) -> bool:
        """
        Delete document and all associated artifacts.

        Removes:
        - Database record
        - Uploaded file
        - Extraction results
        """
        await self._ensure_initialized()

        doc = await self.get_document(doc_id)
        if not doc:
            return False

        # Delete uploaded file
        file_path = self.upload_dir / doc.filename
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")

        # Delete extraction results
        if doc.extraction_result_path:
            result_path = Path(doc.extraction_result_path)
            if result_path.exists():
                if result_path.is_dir():
                    shutil.rmtree(result_path)
                else:
                    result_path.unlink()
                logger.info(f"Deleted results: {result_path}")

        # Delete database record
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM documents WHERE doc_id = ?", (str(doc_id),)
            )
            await db.commit()

        logger.info(f"Deleted document {doc_id}")
        return True

    async def get_file_path(self, doc_id: UUID) -> Optional[Path]:
        """Get the file path for a document."""
        doc = await self.get_document(doc_id)
        if doc:
            return self.upload_dir / doc.filename
        return None

    async def get_pending_documents(self, limit: int = 10) -> List[Document]:
        """Get documents pending processing (uploaded or queued)."""
        await self._ensure_initialized()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT * FROM documents
                WHERE status IN ('uploaded', 'queued')
                ORDER BY upload_time ASC
                LIMIT ?
                """,
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_document(row) for row in rows]

    async def get_stats(self) -> Dict[str, int]:
        """Get document statistics by status."""
        await self._ensure_initialized()

        stats = {}
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT status, COUNT(*) FROM documents GROUP BY status"
            ) as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    stats[row[0]] = row[1]

            async with db.execute("SELECT COUNT(*) FROM documents") as cursor:
                row = await cursor.fetchone()
                stats["total"] = row[0] if row else 0

        return stats

    def _row_to_document(self, row: aiosqlite.Row) -> Document:
        """Convert database row to Document model."""
        import json

        return Document(
            doc_id=UUID(row["doc_id"]),
            filename=row["filename"],
            original_filename=row["original_filename"],
            content_hash=row["content_hash"],
            file_size=row["file_size"],
            upload_time=datetime.fromisoformat(row["upload_time"]),
            status=DocumentStatus(row["status"]),
            processing_started=datetime.fromisoformat(row["processing_started"]) if row["processing_started"] else None,
            processing_completed=datetime.fromisoformat(row["processing_completed"]) if row["processing_completed"] else None,
            error_message=row["error_message"],
            extraction_result_path=row["extraction_result_path"],
            graphiti_group_id=row["graphiti_group_id"],
            chunk_count=row["chunk_count"],
            entity_count=row["entity_count"],
            retry_count=row["retry_count"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )


# Singleton instance
_service: Optional[DocumentLifecycleService] = None


def get_document_service() -> DocumentLifecycleService:
    """Get or create the document lifecycle service singleton."""
    global _service
    if _service is None:
        _service = DocumentLifecycleService()
    return _service
