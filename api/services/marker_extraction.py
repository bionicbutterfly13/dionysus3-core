"""
Marker-based PDF extraction service with fallback chain.
Track: 062-document-ingestion-viz
Task: T062-002 - Create MarkerExtractionService

Extraction priority:
1. Marker (deep learning layout detection) - via subprocess to marker-env
2. PyMuPDF (structural text extraction)
3. Tesseract OCR (scanned documents)

Architecture:
- Marker runs in isolated venv (marker-env/) to avoid PyTorch bloat
- Subprocess calls to marker-env/bin/python
- Falls back to PyMuPDF/Tesseract if Marker unavailable
"""

import asyncio
import hashlib
import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("dionysus.services.marker_extraction")

# Path to isolated marker environment
MARKER_ENV_PATH = Path(__file__).parent.parent.parent / "marker-env"
MARKER_PYTHON = MARKER_ENV_PATH / "bin" / "python"


class ExtractionMethod(str, Enum):
    """Which extraction method was used."""
    MARKER = "marker"
    PYMUPDF = "pymupdf"
    TESSERACT = "tesseract"
    FAILED = "failed"


@dataclass
class Section:
    """Extracted document section."""
    title: Optional[str]
    content: str
    level: int  # Heading level (1-6, 0 for body text)
    page_start: int
    page_end: int
    bbox: Optional[List[float]] = None  # Bounding box if available


@dataclass
class Table:
    """Extracted table from document."""
    markdown: str
    page: int
    caption: Optional[str] = None


@dataclass
class Figure:
    """Extracted figure reference."""
    path: str
    page: int
    caption: Optional[str] = None


@dataclass
class MarkerResult:
    """Result of Marker extraction."""
    markdown: str
    sections: List[Section] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    figures: List[Figure] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    method: ExtractionMethod = ExtractionMethod.MARKER
    page_count: int = 0
    word_count: int = 0
    extraction_time_ms: int = 0


@dataclass
class ExtractionResult:
    """Full extraction result with metadata."""
    doc_id: str
    filename: str
    content_hash: str
    result: MarkerResult
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    fallback_used: bool = False
    error_message: Optional[str] = None


class MarkerExtractionService:
    """
    PDF extraction service using Marker with fallback chain.

    Marker handles:
    - Multi-column layouts
    - Tables (converted to markdown)
    - LaTeX equations
    - Figures with captions
    - Headers/footers removal
    """

    def __init__(self, output_dir: Optional[str] = None, use_gpu: bool = False):
        """
        Initialize extraction service.

        Args:
            output_dir: Directory for extracted artifacts (figures, etc.)
            use_gpu: Whether to use GPU acceleration for Marker
        """
        self.output_dir = Path(output_dir) if output_dir else Path(tempfile.gettempdir()) / "dionysus_extractions"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.use_gpu = use_gpu
        self._marker_available: Optional[bool] = None

    def _check_marker_available(self) -> bool:
        """Check if Marker is installed in marker-env."""
        if self._marker_available is not None:
            return self._marker_available

        # Check if marker-env exists and has marker installed
        if not MARKER_PYTHON.exists():
            self._marker_available = False
            logger.warning(f"Marker env not found at {MARKER_PYTHON}")
            return False

        try:
            # Check if marker is importable in the isolated env
            result = subprocess.run(
                [str(MARKER_PYTHON), "-c", "import marker; print('ok')"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self._marker_available = result.returncode == 0 and "ok" in result.stdout
            if self._marker_available:
                logger.info("Marker available in marker-env")
            else:
                logger.warning(f"Marker not installed in marker-env: {result.stderr}")
        except subprocess.TimeoutExpired:
            self._marker_available = False
            logger.warning("Marker check timed out")
        except Exception as e:
            self._marker_available = False
            logger.warning(f"Marker check failed: {e}")

        return self._marker_available

    async def extract_pdf(self, pdf_path: str) -> MarkerResult:
        """
        Extract PDF to structured markdown using Marker via subprocess.

        Marker runs in isolated marker-env to keep PyTorch deps separate.

        Args:
            pdf_path: Path to PDF file

        Returns:
            MarkerResult with markdown and structured sections
        """
        import time
        start_time = time.time()

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        if not self._check_marker_available():
            raise RuntimeError("Marker is not available. Use extract_with_fallback() instead.")

        # Create output directory for this document
        doc_output = self.output_dir / pdf_path.stem
        doc_output.mkdir(parents=True, exist_ok=True)

        logger.info(f"Extracting {pdf_path.name} with Marker (subprocess)")

        try:
            # Run Marker via subprocess
            # marker command: marker_single <input_pdf> <output_dir>
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: subprocess.run(
                    [
                        str(MARKER_PYTHON), "-m", "marker.scripts.marker_single",
                        str(pdf_path),
                        str(doc_output),
                        "--output_format", "markdown",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout for large PDFs
                )
            )

            if result.returncode != 0:
                logger.error(f"Marker failed: {result.stderr}")
                raise RuntimeError(f"Marker extraction failed: {result.stderr}")

            # Find the output markdown file
            md_files = list(doc_output.glob("*.md"))
            if not md_files:
                raise RuntimeError(f"Marker produced no output in {doc_output}")

            # Read the markdown output
            markdown = md_files[0].read_text()

            # Extract sections from markdown
            sections = self._parse_sections(markdown)

            # Extract tables
            tables = self._extract_tables(markdown)

            # Count pages (estimate from sections or metadata)
            page_count = max(s.page_end for s in sections) if sections else 1

            extraction_time = int((time.time() - start_time) * 1000)

            return MarkerResult(
                markdown=markdown,
                sections=sections,
                tables=tables,
                figures=[],  # Marker extracts inline
                metadata={
                    "source": str(pdf_path),
                    "extractor": "marker-subprocess",
                    "output_dir": str(doc_output),
                },
                method=ExtractionMethod.MARKER,
                page_count=page_count,
                word_count=len(markdown.split()),
                extraction_time_ms=extraction_time,
            )

        except subprocess.TimeoutExpired:
            logger.error(f"Marker timed out processing {pdf_path}")
            raise RuntimeError("Marker extraction timed out (>5 minutes)")
        except Exception as e:
            logger.error(f"Marker extraction failed: {e}")
            raise

    async def extract_with_pymupdf(self, pdf_path: str) -> MarkerResult:
        """
        Fallback extraction using PyMuPDF.

        Simpler than Marker but handles most PDFs.
        """
        import time
        start_time = time.time()

        import fitz  # PyMuPDF

        pdf_path = Path(pdf_path)
        doc = fitz.open(str(pdf_path))

        all_text = []
        sections = []
        current_page = 0

        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")
            all_text.append(page_text)

            # Simple section detection based on font size
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        # Detect headers by font size
                        font_size = span.get("size", 12)
                        text = span.get("text", "").strip()
                        if font_size > 14 and len(text) > 3 and len(text) < 100:
                            sections.append(Section(
                                title=text,
                                content="",  # Will be filled in post-processing
                                level=1 if font_size > 18 else 2,
                                page_start=page_num + 1,
                                page_end=page_num + 1,
                            ))

        doc.close()

        markdown = "\n\n".join(all_text)
        extraction_time = int((time.time() - start_time) * 1000)

        return MarkerResult(
            markdown=markdown,
            sections=sections,
            tables=[],
            figures=[],
            metadata={
                "source": str(pdf_path),
                "extractor": "pymupdf",
            },
            method=ExtractionMethod.PYMUPDF,
            page_count=len(all_text),
            word_count=len(markdown.split()),
            extraction_time_ms=extraction_time,
        )

    async def extract_with_tesseract(self, pdf_path: str) -> MarkerResult:
        """
        OCR fallback using Tesseract.

        For scanned documents where text extraction fails.
        """
        import time
        start_time = time.time()

        import fitz
        from PIL import Image
        import pytesseract

        pdf_path = Path(pdf_path)
        doc = fitz.open(str(pdf_path))

        all_text = []

        for page_num, page in enumerate(doc):
            # Convert page to image
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

            # OCR the image
            text = pytesseract.image_to_string(img)
            all_text.append(text.strip())

        doc.close()

        markdown = "\n\n".join(all_text)
        extraction_time = int((time.time() - start_time) * 1000)

        return MarkerResult(
            markdown=markdown,
            sections=[],  # OCR doesn't preserve structure well
            tables=[],
            figures=[],
            metadata={
                "source": str(pdf_path),
                "extractor": "tesseract",
                "dpi": 300,
            },
            method=ExtractionMethod.TESSERACT,
            page_count=len(all_text),
            word_count=len(markdown.split()),
            extraction_time_ms=extraction_time,
        )

    async def extract_with_fallback(self, pdf_path: str) -> ExtractionResult:
        """
        Extract PDF using best available method with automatic fallback.

        Fallback chain:
        1. Marker (if available and succeeds)
        2. PyMuPDF (if Marker fails or unavailable)
        3. Tesseract OCR (if text extraction yields nothing)

        Args:
            pdf_path: Path to PDF file

        Returns:
            ExtractionResult with content and extraction metadata
        """
        pdf_path = Path(pdf_path)

        # Generate document ID and content hash
        with open(pdf_path, "rb") as f:
            content_hash = hashlib.sha256(f.read()).hexdigest()
        doc_id = f"{pdf_path.stem}_{content_hash[:8]}"

        result = None
        fallback_used = False
        error_message = None

        # Try Marker first
        if self._check_marker_available():
            try:
                result = await self.extract_pdf(pdf_path)
                logger.info(f"Marker extraction successful: {result.word_count} words")
            except Exception as e:
                logger.warning(f"Marker failed, falling back: {e}")
                error_message = f"Marker failed: {e}"
                fallback_used = True
        else:
            fallback_used = True

        # Fallback to PyMuPDF
        if result is None:
            try:
                result = await self.extract_with_pymupdf(pdf_path)
                logger.info(f"PyMuPDF extraction: {result.word_count} words")

                # If PyMuPDF gets almost no text, try OCR
                if result.word_count < 50:
                    logger.warning(f"PyMuPDF yielded little text ({result.word_count} words), trying OCR")
                    result = await self.extract_with_tesseract(pdf_path)
                    logger.info(f"Tesseract extraction: {result.word_count} words")

            except Exception as e:
                logger.error(f"PyMuPDF failed: {e}")
                error_message = f"PyMuPDF failed: {e}"

                # Final fallback to OCR
                try:
                    result = await self.extract_with_tesseract(pdf_path)
                except Exception as ocr_error:
                    logger.error(f"All extraction methods failed: {ocr_error}")
                    result = MarkerResult(
                        markdown="",
                        method=ExtractionMethod.FAILED,
                        metadata={"error": str(ocr_error)},
                    )
                    error_message = f"All methods failed: {ocr_error}"

        return ExtractionResult(
            doc_id=doc_id,
            filename=pdf_path.name,
            content_hash=content_hash,
            result=result,
            fallback_used=fallback_used,
            error_message=error_message,
        )

    def _parse_sections(self, markdown: str) -> List[Section]:
        """
        Parse markdown into sections based on headers.
        """
        import re

        sections = []
        lines = markdown.split("\n")
        current_section: Optional[Section] = None
        content_lines: List[str] = []

        header_pattern = re.compile(r"^(#{1,6})\s+(.+)$")

        for i, line in enumerate(lines):
            match = header_pattern.match(line)
            if match:
                # Save previous section
                if current_section:
                    current_section.content = "\n".join(content_lines).strip()
                    sections.append(current_section)
                    content_lines = []

                # Start new section
                level = len(match.group(1))
                title = match.group(2).strip()
                current_section = Section(
                    title=title,
                    content="",
                    level=level,
                    page_start=1,  # Marker doesn't always provide page info
                    page_end=1,
                )
            else:
                content_lines.append(line)

        # Don't forget last section
        if current_section:
            current_section.content = "\n".join(content_lines).strip()
            sections.append(current_section)
        elif content_lines:
            # Document with no headers
            sections.append(Section(
                title=None,
                content="\n".join(content_lines).strip(),
                level=0,
                page_start=1,
                page_end=1,
            ))

        return sections

    def _extract_tables(self, markdown: str) -> List[Table]:
        """
        Extract markdown tables from content.
        """
        import re

        tables = []
        # Simple table detection: lines starting with |
        table_pattern = re.compile(r"(\|.+\|[\r\n]+)+", re.MULTILINE)

        for match in table_pattern.finditer(markdown):
            table_md = match.group(0).strip()
            if "|" in table_md and "-" in table_md:  # Has header separator
                tables.append(Table(
                    markdown=table_md,
                    page=1,  # Can't determine page from markdown
                    caption=None,
                ))

        return tables


# Singleton instance
_service: Optional[MarkerExtractionService] = None


def get_marker_service(output_dir: Optional[str] = None) -> MarkerExtractionService:
    """Get or create the marker extraction service singleton."""
    global _service
    if _service is None:
        _service = MarkerExtractionService(output_dir=output_dir)
    return _service


async def extract_document(pdf_path: str) -> ExtractionResult:
    """
    Convenience function to extract a document.

    Args:
        pdf_path: Path to PDF file

    Returns:
        ExtractionResult with extracted content
    """
    service = get_marker_service()
    return await service.extract_with_fallback(pdf_path)
