#!/usr/bin/env python3
"""
Academic Paper Ingestion Pipeline

Extracts content from PDFs and ingests into Neo4j knowledge graph with RAG embeddings.

Usage:
    # Development (Graphiti)
    python scripts/ingest_paper.py docs/papers/pdfs/nehrer-2025.pdf

    # Production (n8n webhooks)
    python scripts/ingest_paper.py docs/papers/pdfs/nehrer-2025.pdf --production

    # With custom citation key
    python scripts/ingest_paper.py docs/papers/pdfs/kavi-2025.pdf --citation-key kavi2025

Author: Mani Saint-Victor, MD
Date: 2026-01-03
"""

import asyncio
import logging
import re
import os
import json
import hmac
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
import argparse

# PDF processing
try:
    import pdfplumber
    import fitz  # PyMuPDF
except ImportError:
    print("Missing dependencies. Install: pip install pdfplumber PyMuPDF")
    exit(1)

# Embeddings (LiteLLM already in project)
from litellm import aembedding
import numpy as np

# Tokenization
try:
    import tiktoken
except ImportError:
    print("Missing tiktoken. Install: pip install tiktoken")
    exit(1)

# HTTP for n8n webhooks
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# STAGE 1: PDF PROCESSING
# ============================================================================

class PDFProcessor:
    """Extracts content and metadata from academic PDFs."""

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.metadata = {}
        self.sections = []
        self.equations = []
        self.figures = []

    async def extract_metadata(self) -> Dict[str, Any]:
        """
        Extract DOI, authors, title, abstract, citations.

        Returns:
            {
                "doi": "10.3390/e27010062",
                "title": "Introducing ActiveInference.jl...",
                "authors": ["Nehrer, S. W.", "Laursen, J. E.", ...],
                "abstract": "...",
                "year": 2025,
                "journal": "Entropy",
                "citations": ["Friston2010", ...],
                "keywords": [...]
            }
        """
        logger.info("Extracting metadata...")

        doc = fitz.open(self.pdf_path)
        raw_metadata = doc.metadata
        first_page = doc[0].get_text()

        # Extract DOI (regex pattern: 10.xxxx/...)
        doi_match = re.search(r'10\.\d{4,}/[\w\.\-/]+', first_page)
        doi = doi_match.group(0) if doi_match else None

        # Extract title (heuristic: first large/bold text)
        title = self._extract_title(first_page, raw_metadata)

        # Extract authors (heuristic: names before abstract)
        authors = self._extract_authors(first_page)

        # Extract abstract (section between "Abstract" and "Introduction")
        abstract = self._extract_abstract(first_page)

        # Extract year (from metadata or first page)
        year = self._extract_year(raw_metadata, first_page)

        # Extract journal
        journal = raw_metadata.get("subject") or self._extract_journal(first_page)

        # Extract keywords
        keywords = self._extract_keywords(first_page)

        # Extract citations (all pages)
        citations = self._extract_citations(doc)

        doc.close()

        metadata = {
            "doi": doi,
            "title": title,
            "authors": authors,
            "abstract": abstract,
            "year": year,
            "journal": journal,
            "citations": citations,
            "keywords": keywords,
            "pdf_path": str(self.pdf_path)
        }

        logger.info(f"Metadata extracted: {title} ({year})")
        return metadata

    def _extract_title(self, first_page: str, raw_metadata: dict) -> str:
        """Extract title from first page or metadata."""
        # Try metadata first
        if raw_metadata.get("title"):
            return raw_metadata["title"]

        # Heuristic: First non-whitespace line is usually title
        lines = [line.strip() for line in first_page.split('\n') if line.strip()]
        return lines[0] if lines else "Unknown Title"

    def _extract_authors(self, first_page: str) -> List[str]:
        """Extract author names from first page."""
        # Heuristic: Look for patterns like "Author1, A., Author2, B."
        # This is simplified - real implementation would need more robust parsing
        author_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s+[A-Z]\.(?:\s+[A-Z]\.)?)'
        authors = re.findall(author_pattern, first_page)
        return authors[:10] if authors else ["Unknown Author"]  # Limit to 10

    def _extract_abstract(self, first_page: str) -> str:
        """Extract abstract text."""
        # Look for "Abstract" section
        abstract_match = re.search(
            r'Abstract[:\s]+(.*?)(?:Introduction|Keywords|1\.|$)',
            first_page,
            re.DOTALL | re.IGNORECASE
        )
        if abstract_match:
            return abstract_match.group(1).strip()
        return "Abstract not found"

    def _extract_year(self, raw_metadata: dict, first_page: str) -> int:
        """Extract publication year."""
        # Try metadata
        if raw_metadata.get("creationDate"):
            year_match = re.search(r'\d{4}', raw_metadata["creationDate"])
            if year_match:
                return int(year_match.group(0))

        # Try first page (look for 4-digit year)
        year_match = re.search(r'\b(19|20)\d{2}\b', first_page)
        if year_match:
            return int(year_match.group(0))

        return datetime.now().year  # Fallback

    def _extract_journal(self, first_page: str) -> Optional[str]:
        """Extract journal name."""
        # Heuristic: Look for common journal patterns
        journal_pattern = r'(Journal of|Proceedings of|ACM|IEEE)\s+[\w\s]+'
        journal_match = re.search(journal_pattern, first_page)
        return journal_match.group(0) if journal_match else None

    def _extract_keywords(self, first_page: str) -> List[str]:
        """Extract keywords."""
        keyword_match = re.search(
            r'Keywords[:\s]+(.*?)(?:\n\n|\d+\.|Introduction)',
            first_page,
            re.DOTALL | re.IGNORECASE
        )
        if keyword_match:
            keywords_text = keyword_match.group(1)
            # Split by comma, semicolon, or bullet points
            keywords = re.split(r'[,;•·]', keywords_text)
            return [kw.strip() for kw in keywords if kw.strip()]
        return []

    def _extract_citations(self, doc) -> List[str]:
        """Extract citations from References section."""
        # Look for "References" section in last few pages
        references_text = ""
        for page in doc[-3:]:  # Check last 3 pages
            text = page.get_text()
            if "References" in text or "Bibliography" in text:
                references_text += text

        # Extract citation keys (simplified - just extract years and first authors)
        citation_pattern = r'([A-Z][a-z]+(?:\s+et\s+al\.)?)[\s,]+(\d{4})'
        citations = re.findall(citation_pattern, references_text)

        # Format as "Author2020" style
        citation_keys = [f"{author.replace(' et al.', '')}{year}" for author, year in citations]
        return list(set(citation_keys))[:50]  # Limit to 50, deduplicate

    async def extract_sections(self) -> List[Dict[str, Any]]:
        """
        Extract text by section with hierarchy.

        Returns:
            [
                {
                    "title": "Introduction",
                    "level": 1,
                    "content": "...",
                    "page_start": 1,
                    "page_end": 3
                },
                ...
            ]
        """
        logger.info("Extracting sections...")

        with pdfplumber.open(self.pdf_path) as pdf:
            sections = []
            current_section = None

            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue

                for line in text.split('\n'):
                    line = line.strip()

                    # Detect section headers
                    if self._is_section_header(line):
                        if current_section:
                            sections.append(current_section)

                        current_section = {
                            "title": line,
                            "level": self._detect_level(line),
                            "content": "",
                            "page_start": page_num,
                            "page_end": page_num
                        }
                    elif current_section:
                        current_section["content"] += line + "\n"
                        current_section["page_end"] = page_num

            # Add last section
            if current_section:
                sections.append(current_section)

        logger.info(f"Extracted {len(sections)} sections")
        return sections

    def _is_section_header(self, line: str) -> bool:
        """Detect if line is a section header."""
        # Heuristics:
        # 1. Numbered sections: "1. Introduction", "2.1 Background"
        # 2. All caps: "INTRODUCTION"
        # 3. Title case with no punctuation at end
        if re.match(r'^\d+\.?\s+[A-Z]', line):  # Numbered
            return True
        if line.isupper() and len(line.split()) <= 5:  # All caps, short
            return True
        if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', line):  # Title case
            return True
        return False

    def _detect_level(self, line: str) -> int:
        """Detect section level (1, 2, 3, etc.)."""
        # Count dots in numbering: "2.1.3" -> level 3
        numbering = re.match(r'^(\d+(?:\.\d+)*)', line)
        if numbering:
            return len(numbering.group(1).split('.'))
        return 1  # Default top-level

    async def extract_equations(self) -> List[Dict[str, Any]]:
        """
        Extract equations (placeholder - full OCR implementation needed).

        For full implementation, use pix2tex or mathpix API.

        Returns:
            [
                {
                    "number": "Eq 1",
                    "latex": "F = D_{KL}[q(s) || p(o,s)]",
                    "context": "...",
                    "page": 4,
                    "section": "..."
                },
                ...
            ]
        """
        logger.info("Extracting equations (placeholder)...")

        # Placeholder: Detect equation markers in text
        equations = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue

                # Look for equation references: "Eq. 1", "Equation (2)"
                eq_refs = re.finditer(r'(Eq(?:uation)?\.?\s*\(?(\d+)\)?)', text)
                for match in eq_refs:
                    equations.append({
                        "number": f"Eq {match.group(2)}",
                        "latex": "[LaTeX extraction requires pix2tex or mathpix]",
                        "context": text[max(0, match.start()-100):match.end()+100],
                        "page": page_num,
                        "section": "Unknown"
                    })

        logger.info(f"Found {len(equations)} equation references")
        return equations

    async def extract_figures_tables(self) -> List[Dict[str, Any]]:
        """Extract figures and tables (placeholder)."""
        logger.info("Extracting figures/tables (placeholder)...")

        figures = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Extract tables
                tables = page.extract_tables()
                for idx, table in enumerate(tables):
                    figures.append({
                        "type": "table",
                        "number": f"Table {page_num}.{idx+1}",
                        "content": table,
                        "page": page_num
                    })

        logger.info(f"Extracted {len(figures)} figures/tables")
        return figures


# ============================================================================
# STAGE 2: CONTENT CHUNKING
# ============================================================================

class ContentChunker:
    """Chunks paper content for embedding generation."""

    def __init__(self, max_tokens: int = 512, overlap: int = 50):
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    async def chunk_sections(self, sections: List[Dict]) -> List[Dict]:
        """
        Chunk sections into embedding-sized pieces.

        Returns:
            [
                {
                    "chunk_id": "...",
                    "text": "...",
                    "metadata": {...},
                    "token_count": 487
                },
                ...
            ]
        """
        logger.info("Chunking content...")

        chunks = []
        for section in sections:
            section_chunks = await self._chunk_section(section)
            chunks.extend(section_chunks)

        logger.info(f"Created {len(chunks)} chunks")
        return chunks

    async def _chunk_section(self, section: Dict) -> List[Dict]:
        """Chunk a single section."""
        text = section["content"]
        tokens = self.tokenizer.encode(text)

        chunks = []
        start = 0
        chunk_num = 0

        while start < len(tokens):
            end = min(start + self.max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.tokenizer.decode(chunk_tokens)

            chunks.append({
                "chunk_id": f"{self._sanitize_title(section['title'])}-{chunk_num:03d}",
                "text": chunk_text,
                "metadata": {
                    "section": section["title"],
                    "page_range": [section["page_start"], section["page_end"]],
                    "has_equations": self._contains_equations(chunk_text),
                    "citations": self._extract_citations_from_text(chunk_text)
                },
                "token_count": len(chunk_tokens)
            })

            chunk_num += 1
            start = end - self.overlap if end < len(tokens) else end

        return chunks

    def _sanitize_title(self, title: str) -> str:
        """Sanitize section title for chunk ID."""
        return re.sub(r'[^\w\s-]', '', title.lower()).replace(' ', '-')[:50]

    def _contains_equations(self, text: str) -> bool:
        """Check if text contains equations."""
        equation_markers = ["$$", "\\begin{equation}", "Eq ", "Equation "]
        return any(marker in text for marker in equation_markers)

    def _extract_citations_from_text(self, text: str) -> List[str]:
        """Extract citations from chunk text."""
        # Pattern: (Author, 2020) or [Author2020]
        citations = re.findall(r'\(([A-Z][a-z]+(?:\s+et\s+al\.)?,?\s+\d{4})\)', text)
        return [c.strip() for c in citations]


# ============================================================================
# STAGE 3: EMBEDDING GENERATION
# ============================================================================

class EmbeddingGenerator:
    """Generates vector embeddings for paper chunks."""

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model

    async def generate_embeddings(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for each chunk.

        Returns chunks with "embedding" field added.
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")

        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk["text"] for chunk in batch]

            # Generate embeddings via LiteLLM
            response = await aembedding(model=self.model, input=texts)

            # Attach embeddings
            for j, chunk in enumerate(batch):
                chunk["embedding"] = response.data[j]["embedding"]

        logger.info("Embeddings generated")
        return chunks

    async def generate_metadata_embedding(self, metadata: Dict) -> List[float]:
        """Generate embedding for paper metadata (title + abstract)."""
        combined_text = f"{metadata['title']}. {metadata['abstract']}"

        response = await aembedding(model=self.model, input=[combined_text])
        return response.data[0]["embedding"]


# ============================================================================
# STAGE 4: STORAGE
# ============================================================================

async def store_via_graphiti(
    metadata: Dict,
    sections: List[Dict],
    chunks: List[Dict],
    citation_key: str
) -> Dict:
    """Store via Graphiti temporal knowledge graph (development)."""
    from api.services.graphiti_service import get_graphiti_service

    logger.info("Storing via Graphiti...")

    service = await get_graphiti_service()
    group_id = f"paper-{citation_key.lower()}"

    # Ingest sections as episodes
    for section in sections:
        content = f"[{section['title']}] {section['content']}"
        await service.ingest_message(
            content=content,
            source_description=f"{metadata['title']} - {section['title']}",
            group_id=group_id,
            valid_at=datetime(metadata['year'], 1, 1)
        )

    logger.info(f"Stored in Graphiti group: {group_id}")
    return {
        "group_id": group_id,
        "sections_ingested": len(sections)
    }


async def store_via_n8n(
    metadata: Dict,
    chunks: List[Dict],
    equations: List[Dict],
    metadata_embedding: List[float]
) -> Dict:
    """Store via n8n webhooks (production)."""
    logger.info("Storing via n8n webhooks...")

    N8N_BASE = "https://72.61.78.89:5678"
    HMAC_SECRET = os.getenv("MEMEVOLVE_HMAC_SECRET")

    if not HMAC_SECRET:
        raise ValueError("MEMEVOLVE_HMAC_SECRET not set in environment")

    # 1. Create paper node
    paper_payload = {
        **metadata,
        "embedding": metadata_embedding
    }

    response = requests.post(
        f"{N8N_BASE}/webhook/papers/create",
        json=paper_payload,
        headers={"X-HMAC-Signature": generate_hmac(paper_payload, HMAC_SECRET)},
        verify=False  # Self-signed cert
    )
    response.raise_for_status()
    paper_id = response.json()["paper_id"]

    logger.info(f"Created paper node: {paper_id}")

    # 2. Add chunks (batched)
    for chunk in chunks:
        chunk_payload = {
            "paper_id": paper_id,
            **chunk
        }
        requests.post(
            f"{N8N_BASE}/webhook/papers/add-chunk",
            json=chunk_payload,
            headers={"X-HMAC-Signature": generate_hmac(chunk_payload, HMAC_SECRET)},
            verify=False
        )

    logger.info(f"Added {len(chunks)} chunks")

    # 3. Add equations
    for equation in equations:
        equation_payload = {
            "paper_id": paper_id,
            **equation
        }
        requests.post(
            f"{N8N_BASE}/webhook/papers/add-equation",
            json=equation_payload,
            headers={"X-HMAC-Signature": generate_hmac(equation_payload, HMAC_SECRET)},
            verify=False
        )

    logger.info(f"Added {len(equations)} equations")

    return {
        "paper_id": paper_id,
        "chunks_added": len(chunks),
        "equations_added": len(equations)
    }


def generate_hmac(payload: Dict, secret: str) -> str:
    """Generate HMAC-SHA256 signature for n8n webhook."""
    message = json.dumps(payload, sort_keys=True).encode()
    signature = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return signature


# ============================================================================
# UTILITIES
# ============================================================================

def generate_citation_key(metadata: Dict) -> str:
    """Generate citation key (e.g., 'nehrer2025')."""
    first_author = metadata['authors'][0].split(',')[0].lower() if metadata['authors'] else "unknown"
    year = metadata['year']
    return f"{first_author}{year}"


async def save_extraction(
    path: Path,
    metadata: Dict,
    sections: List[Dict],
    equations: List[Dict]
) -> None:
    """Save extraction to markdown file."""
    logger.info(f"Saving extraction to {path}...")

    with open(path, 'w') as f:
        f.write(f"# {metadata['title']}\n\n")
        f.write(f"**Authors**: {', '.join(metadata['authors'])}\n")
        f.write(f"**Year**: {metadata['year']}\n")
        f.write(f"**DOI**: {metadata['doi']}\n")
        f.write(f"**Journal**: {metadata.get('journal', 'Unknown')}\n\n")

        f.write(f"## Abstract\n\n{metadata['abstract']}\n\n")

        if metadata.get('keywords'):
            f.write(f"**Keywords**: {', '.join(metadata['keywords'])}\n\n")

        if equations:
            f.write("## Equations\n\n")
            for eq in equations[:20]:  # Limit to 20
                f.write(f"### {eq['number']} (p. {eq['page']})\n\n")
                f.write(f"```latex\n{eq['latex']}\n```\n\n")
                f.write(f"**Context**: {eq['context'][:200]}...\n\n")

        f.write("## Sections\n\n")
        for section in sections[:10]:  # Limit to 10
            f.write(f"### {section['title']} (pp. {section['page_start']}-{section['page_end']})\n\n")
            content_preview = section['content'][:500]
            f.write(f"{content_preview}...\n\n")


# ============================================================================
# MAIN PIPELINE
# ============================================================================

async def ingest_paper(
    pdf_path: Path,
    use_production: bool = False,
    citation_key: Optional[str] = None
) -> Dict:
    """
    Main ingestion pipeline.

    Args:
        pdf_path: Path to PDF file
        use_production: If True, use n8n webhooks; if False, use Graphiti
        citation_key: Optional citation key (e.g., "nehrer2025")

    Returns:
        Ingestion summary with status and metadata
    """
    logger.info(f"=== Starting Paper Ingestion ===")
    logger.info(f"PDF: {pdf_path}")
    logger.info(f"Backend: {'n8n (production)' if use_production else 'Graphiti (dev)'}")

    # Stage 1: PDF Processing
    logger.info("\n--- Stage 1: PDF Processing ---")
    processor = PDFProcessor(pdf_path)

    metadata = await processor.extract_metadata()
    sections = await processor.extract_sections()
    equations = await processor.extract_equations()
    figures = await processor.extract_figures_tables()

    # Stage 2: Content Chunking
    logger.info("\n--- Stage 2: Content Chunking ---")
    chunker = ContentChunker(max_tokens=512, overlap=50)
    chunks = await chunker.chunk_sections(sections)

    # Stage 3: Embedding Generation
    logger.info("\n--- Stage 3: Embedding Generation ---")
    embedder = EmbeddingGenerator(model="text-embedding-3-small")
    embedded_chunks = await embedder.generate_embeddings(chunks)
    metadata_embedding = await embedder.generate_metadata_embedding(metadata)

    # Stage 4: Storage
    logger.info("\n--- Stage 4: Storage ---")
    if use_production:
        result = await store_via_n8n(
            metadata,
            embedded_chunks,
            equations,
            metadata_embedding
        )
    else:
        key = citation_key or generate_citation_key(metadata)
        result = await store_via_graphiti(metadata, sections, embedded_chunks, key)

    # Save extraction
    extraction_path = pdf_path.parent.parent / "extractions" / f"{pdf_path.stem}-extraction.md"
    extraction_path.parent.mkdir(parents=True, exist_ok=True)
    await save_extraction(extraction_path, metadata, sections, equations)

    logger.info("\n=== Ingestion Complete ===")
    return {
        "status": "success",
        "backend": "n8n" if use_production else "graphiti",
        "metadata": metadata,
        "chunks": len(embedded_chunks),
        "equations": len(equations),
        "figures": len(figures),
        "extraction_file": str(extraction_path),
        **result
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest academic PDF into knowledge graph with RAG embeddings"
    )
    parser.add_argument(
        "pdf_path",
        type=Path,
        help="Path to PDF file"
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Use n8n webhooks (production) instead of Graphiti (dev)"
    )
    parser.add_argument(
        "--citation-key",
        type=str,
        help="Citation key (e.g., 'nehrer2025'). Auto-generated if not provided."
    )

    args = parser.parse_args()

    if not args.pdf_path.exists():
        logger.error(f"PDF not found: {args.pdf_path}")
        return 1

    try:
        result = asyncio.run(ingest_paper(
            pdf_path=args.pdf_path,
            use_production=args.production,
            citation_key=args.citation_key
        ))

        print("\n" + "="*60)
        print("INGESTION SUMMARY")
        print("="*60)
        print(f"Status: {result['status']}")
        print(f"Backend: {result['backend']}")
        print(f"Paper: {result['metadata']['title']}")
        print(f"Authors: {', '.join(result['metadata']['authors'][:3])}")
        print(f"Year: {result['metadata']['year']}")
        print(f"Chunks: {result['chunks']}")
        print(f"Equations: {result['equations']}")
        print(f"Extraction: {result['extraction_file']}")
        print("="*60)

        return 0

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
