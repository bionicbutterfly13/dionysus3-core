# PDF Ingestion Pipeline for Academic Papers

**Status**: Design Document
**Date**: 2026-01-03
**Purpose**: RAG-enabled knowledge extraction from academic papers with Neo4j knowledge graph integration

---

## Executive Summary

This pipeline transforms academic PDFs into a queryable knowledge graph with vector embeddings for RAG retrieval. It follows Dionysus3-core's dual-tier architecture:

- **Development/Testing**: Graphiti temporal knowledge graph (concepts, relationships)
- **Production/High-Value**: n8n webhooks → Neo4j (paper nodes, citations, metadata)

---

## Architecture Overview

```
┌─────────────┐
│  PDF File   │
│  (.pdf)     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  STAGE 1: PDF Processing                        │
│  - Text extraction (pdfplumber)                 │
│  - Metadata extraction (DOI, authors, abstract) │
│  - Equation extraction (LaTeX-OCR)              │
│  - Figure/table extraction                      │
└──────┬──────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  STAGE 2: Content Chunking                      │
│  - Section-based splitting                      │
│  - Semantic chunking (512 tokens)               │
│  - Equation preservation                        │
│  - Citation tracking                            │
└──────┬──────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│  STAGE 3: Embedding Generation                  │
│  - LiteLLM text-embedding-3-small               │
│  - Per-chunk embeddings (1536-dim)              │
│  - Metadata embedding (title+abstract)          │
└──────┬──────────────────────────────────────────┘
       │
       ├──────────────────┬──────────────────────┐
       │                  │                      │
       ▼                  ▼                      ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│ Graphiti     │  │ n8n Webhooks │  │ Local Cache      │
│ (Temporal KG)│  │ (Production) │  │ (embeddings.pkl) │
└──────────────┘  └──────────────┘  └──────────────────┘
       │                  │
       │                  │
       ▼                  ▼
┌──────────────┐  ┌──────────────┐
│ Neo4j        │  │ Neo4j        │
│ (Dev Graph)  │  │ (Prod Graph) │
└──────────────┘  └──────────────┘
       │                  │
       └────────┬─────────┘
                │
                ▼
        ┌───────────────┐
        │ Vector Index  │
        │ (Similarity)  │
        └───────────────┘
                │
                ▼
        ┌───────────────┐
        │  RAG Query    │
        │  Interface    │
        └───────────────┘
```

---

## Stage 1: PDF Processing

### Tools Selection

| Tool | Purpose | Justification |
|------|---------|---------------|
| **pdfplumber** | Text extraction | Better table/layout handling than PyPDF2 |
| **PyMuPDF (fitz)** | Metadata extraction | Fast DOI/citation parsing |
| **pix2tex** | Equation extraction | LaTeX-OCR for mathematical notation |
| **pdf2image** | Figure extraction | Convert pages to images for equation OCR |

### Implementation Pattern

```python
# scripts/ingest_paper.py - STAGE 1

import pdfplumber
import fitz  # PyMuPDF
from pix2tex.cli import LatexOCR
from pathlib import Path

class PDFProcessor:
    """Extracts content and metadata from academic PDFs."""

    def __init__(self, pdf_path: Path):
        self.pdf_path = pdf_path
        self.metadata = {}
        self.sections = []
        self.equations = []
        self.figures = []

    async def extract_metadata(self) -> dict:
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
                "citations": ["Friston2010", "Kavi2025", ...],
                "keywords": ["active inference", "POMDP", ...]
            }
        """
        doc = fitz.open(self.pdf_path)

        # Extract from PDF metadata fields
        raw_metadata = doc.metadata

        # Parse first page for structured metadata
        first_page = doc[0].get_text()

        # DOI extraction (regex pattern)
        doi_match = re.search(r'10\.\d{4,}/[\w\.\-]+', first_page)
        doi = doi_match.group(0) if doi_match else None

        # Author extraction (heuristic: before abstract)
        # Title extraction (first bold/large text)
        # Abstract extraction (section marker)

        return {
            "doi": doi,
            "title": self._extract_title(first_page),
            "authors": self._extract_authors(first_page),
            "abstract": self._extract_abstract(first_page),
            "year": self._extract_year(raw_metadata, first_page),
            "journal": raw_metadata.get("subject", None),
            "citations": self._extract_citations(doc),
            "keywords": self._extract_keywords(first_page)
        }

    async def extract_sections(self) -> list[dict]:
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
        with pdfplumber.open(self.pdf_path) as pdf:
            sections = []
            current_section = None

            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()

                # Detect section headers (heuristic: all caps, numbered, etc.)
                for line in text.split('\n'):
                    if self._is_section_header(line):
                        if current_section:
                            sections.append(current_section)
                        current_section = {
                            "title": line.strip(),
                            "level": self._detect_level(line),
                            "content": "",
                            "page_start": page_num,
                            "page_end": page_num
                        }
                    elif current_section:
                        current_section["content"] += line + "\n"
                        current_section["page_end"] = page_num

            if current_section:
                sections.append(current_section)

            return sections

    async def extract_equations(self) -> list[dict]:
        """
        Extract LaTeX equations using OCR.

        Returns:
            [
                {
                    "number": "Eq 1",
                    "latex": "F = D_{KL}[q(s) || p(o,s)]",
                    "context": "...surrounding text...",
                    "page": 4,
                    "section": "Variational Free Energy"
                },
                ...
            ]
        """
        # Use pix2tex LatexOCR on equation regions
        # 1. Detect equation blocks (whitespace, centered, numbered)
        # 2. Extract bounding box
        # 3. OCR to LaTeX
        # 4. Validate LaTeX syntax

        ocr = LatexOCR()
        equations = []

        # Implementation: Detect equation regions and OCR
        # Pseudocode - actual implementation would use pdf2image + bbox detection

        return equations

    async def extract_figures_tables(self) -> list[dict]:
        """
        Extract figures and tables with captions.

        Returns:
            [
                {
                    "type": "figure",
                    "number": "Figure 1",
                    "caption": "...",
                    "image_path": "extractions/fig1.png",
                    "page": 5
                },
                ...
            ]
        """
        with pdfplumber.open(self.pdf_path) as pdf:
            figures = []

            for page_num, page in enumerate(pdf.pages, 1):
                # Extract tables
                tables = page.extract_tables()
                for table in tables:
                    figures.append({
                        "type": "table",
                        "content": table,
                        "page": page_num
                    })

                # Extract images (would need additional bbox detection)

            return figures
```

---

## Stage 2: Content Chunking

### Chunking Strategy

**Semantic Chunking** (preferred for academic papers):
- Split by section boundaries (preserve logical structure)
- Maximum 512 tokens per chunk (for embedding models)
- Overlap 50 tokens (preserve context across chunks)
- Keep equations intact (don't split mid-equation)

**Metadata Preservation**:
- Each chunk carries: section, page, equation numbers, citations

```python
# scripts/ingest_paper.py - STAGE 2

from typing import List
import tiktoken

class ContentChunker:
    """Chunks paper content for embedding generation."""

    def __init__(self, max_tokens: int = 512, overlap: int = 50):
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    async def chunk_sections(self, sections: list[dict]) -> list[dict]:
        """
        Chunk sections into embedding-sized pieces.

        Returns:
            [
                {
                    "chunk_id": "kavi2025-intro-001",
                    "text": "...",
                    "metadata": {
                        "section": "Introduction",
                        "page_range": [1, 3],
                        "has_equations": False,
                        "citations": ["Friston2010"]
                    },
                    "token_count": 487
                },
                ...
            ]
        """
        chunks = []

        for section in sections:
            section_text = section["content"]
            tokens = self.tokenizer.encode(section_text)

            # Split into max_tokens chunks with overlap
            start = 0
            chunk_num = 0

            while start < len(tokens):
                end = min(start + self.max_tokens, len(tokens))
                chunk_tokens = tokens[start:end]
                chunk_text = self.tokenizer.decode(chunk_tokens)

                chunks.append({
                    "chunk_id": f"{section['title'].lower().replace(' ', '-')}-{chunk_num:03d}",
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

    def _contains_equations(self, text: str) -> bool:
        """Check if text contains LaTeX or equation markers."""
        equation_markers = ["$$", "\\begin{equation}", "Eq ", "Equation "]
        return any(marker in text for marker in equation_markers)

    def _extract_citations_from_text(self, text: str) -> list[str]:
        """Extract citation keys from text."""
        # Regex for common citation patterns: (Author, Year) or [Author2020]
        import re
        citations = re.findall(r'\(([A-Z][a-z]+(?:\s+et\s+al\.)?,?\s+\d{4})\)', text)
        return citations
```

---

## Stage 3: Embedding Generation

### Embedding Strategy

**Model**: OpenAI `text-embedding-3-small` (1536 dimensions)
- Fast, cost-effective
- Good for academic text
- Supported by LiteLLM

**Alternatives**:
- `text-embedding-3-large` (3072 dim) - higher quality, slower
- `sentence-transformers/all-MiniLM-L6-v2` (384 dim) - local, fast

```python
# scripts/ingest_paper.py - STAGE 3

from litellm import aembedding
import numpy as np
from typing import List

class EmbeddingGenerator:
    """Generates vector embeddings for paper chunks."""

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model

    async def generate_embeddings(self, chunks: list[dict]) -> list[dict]:
        """
        Generate embeddings for each chunk.

        Returns:
            [
                {
                    "chunk_id": "...",
                    "text": "...",
                    "embedding": [0.123, -0.456, ...],  # 1536-dim vector
                    "metadata": {...}
                },
                ...
            ]
        """
        # Batch process for efficiency (max 100 chunks per batch)
        batch_size = 100
        embedded_chunks = []

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk["text"] for chunk in batch]

            # Generate embeddings via LiteLLM
            response = await aembedding(
                model=self.model,
                input=texts
            )

            # Attach embeddings to chunks
            for j, chunk in enumerate(batch):
                chunk["embedding"] = response.data[j]["embedding"]
                embedded_chunks.append(chunk)

        return embedded_chunks

    async def generate_metadata_embedding(self, metadata: dict) -> np.ndarray:
        """
        Generate single embedding for paper metadata (title + abstract).
        Used for high-level paper similarity search.
        """
        combined_text = f"{metadata['title']}. {metadata['abstract']}"

        response = await aembedding(
            model=self.model,
            input=[combined_text]
        )

        return np.array(response.data[0]["embedding"])
```

---

## Stage 4: Neo4j Storage

### Dual-Tier Storage Strategy

#### Tier 1: Graphiti (Development/Testing)

**Use Case**: Temporal knowledge graph for concept exploration, relationship discovery

```python
# scripts/ingest_paper.py - Graphiti path

from api.services.graphiti_service import get_graphiti_service
from datetime import datetime

async def ingest_via_graphiti(
    metadata: dict,
    sections: list[dict],
    chunks: list[dict]
) -> dict:
    """
    Ingest paper via Graphiti temporal knowledge graph.

    Best for:
    - Development/testing
    - Concept extraction
    - Temporal relationships
    """
    service = await get_graphiti_service()

    citation_key = f"{metadata['authors'][0].split(',')[0]}{metadata['year']}"
    group_id = f"paper-{citation_key.lower()}"

    # 1. Ingest sections as episodes
    for section in sections:
        content = f"[{section['title']}] {section['content']}"
        await service.ingest_message(
            content=content,
            source_description=f"{metadata['title']} - {section['title']}",
            group_id=group_id,
            valid_at=datetime(metadata['year'], 1, 1)
        )

    # 2. Extract and ingest relationships
    # Graphiti will automatically extract entities and relationships

    # 3. Store embeddings (if Graphiti supports vector storage)
    # Note: Current Graphiti may not have native vector storage
    # May need separate vector index

    return {
        "status": "success",
        "group_id": group_id,
        "sections_ingested": len(sections)
    }
```

#### Tier 2: n8n Webhooks (Production)

**Use Case**: High-value papers, production RAG, persistent storage

**Required n8n Webhooks**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/webhook/papers/create` | POST | Create paper node with metadata |
| `/webhook/papers/add-chunk` | POST | Add content chunk with embedding |
| `/webhook/papers/add-citation` | POST | Create citation relationship |
| `/webhook/papers/search-similar` | POST | Vector similarity search |
| `/webhook/papers/get-paper` | GET | Retrieve paper by DOI |

**Webhook Payload Examples**:

```python
# scripts/ingest_paper.py - n8n path

import requests
import os

N8N_BASE = "https://72.61.78.89:5678"
HMAC_SECRET = os.getenv("MEMEVOLVE_HMAC_SECRET")

async def ingest_via_n8n(
    metadata: dict,
    chunks: list[dict],
    equations: list[dict]
) -> dict:
    """
    Ingest paper via n8n webhooks to production Neo4j.

    Best for:
    - Production RAG
    - High-value papers
    - Citation network analysis
    """

    # 1. Create paper node
    paper_payload = {
        "doi": metadata["doi"],
        "title": metadata["title"],
        "authors": metadata["authors"],
        "abstract": metadata["abstract"],
        "year": metadata["year"],
        "journal": metadata["journal"],
        "keywords": metadata["keywords"],
        "pdf_path": str(self.pdf_path)
    }

    response = requests.post(
        f"{N8N_BASE}/webhook/papers/create",
        json=paper_payload,
        headers={"X-HMAC-Signature": generate_hmac(paper_payload, HMAC_SECRET)}
    )
    paper_id = response.json()["paper_id"]

    # 2. Add chunks with embeddings
    for chunk in chunks:
        chunk_payload = {
            "paper_id": paper_id,
            "chunk_id": chunk["chunk_id"],
            "text": chunk["text"],
            "embedding": chunk["embedding"],
            "metadata": chunk["metadata"]
        }

        requests.post(
            f"{N8N_BASE}/webhook/papers/add-chunk",
            json=chunk_payload,
            headers={"X-HMAC-Signature": generate_hmac(chunk_payload, HMAC_SECRET)}
        )

    # 3. Add citations
    for citation in metadata["citations"]:
        citation_payload = {
            "source_paper_id": paper_id,
            "cited_work": citation
        }

        requests.post(
            f"{N8N_BASE}/webhook/papers/add-citation",
            json=citation_payload,
            headers={"X-HMAC-Signature": generate_hmac(citation_payload, HMAC_SECRET)}
        )

    # 4. Add equations
    for equation in equations:
        equation_payload = {
            "paper_id": paper_id,
            "number": equation["number"],
            "latex": equation["latex"],
            "context": equation["context"],
            "page": equation["page"]
        }

        requests.post(
            f"{N8N_BASE}/webhook/papers/add-equation",
            json=equation_payload,
            headers={"X-HMAC-Signature": generate_hmac(equation_payload, HMAC_SECRET)}
        )

    return {
        "status": "success",
        "paper_id": paper_id,
        "chunks_added": len(chunks),
        "equations_added": len(equations)
    }

def generate_hmac(payload: dict, secret: str) -> str:
    """Generate HMAC-SHA256 signature for n8n webhook."""
    import hmac
    import hashlib
    import json

    message = json.dumps(payload, sort_keys=True).encode()
    signature = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return signature
```

---

## Stage 5: Cypher Queries (Neo4j Schema)

### Graph Schema

```cypher
// Node types
(:Paper {
    doi: String,
    title: String,
    authors: [String],
    abstract: String,
    year: Integer,
    journal: String,
    keywords: [String],
    pdf_path: String,
    embedding: [Float]  // 1536-dim for metadata
})

(:Chunk {
    chunk_id: String,
    text: String,
    embedding: [Float],  // 1536-dim vector
    section: String,
    page_range: [Integer],
    has_equations: Boolean,
    token_count: Integer
})

(:Equation {
    number: String,
    latex: String,
    context: String,
    page: Integer,
    concept: String  // e.g., "VFE", "EFE", "GFE"
})

(:Author {
    name: String,
    affiliations: [String]
})

(:Concept {
    name: String,
    description: String
})

// Relationships
(:Paper)-[:HAS_CHUNK]->(:Chunk)
(:Paper)-[:DEFINES]->(:Equation)
(:Paper)-[:AUTHORED_BY]->(:Author)
(:Paper)-[:CITES]->(:Paper)
(:Paper)-[:DISCUSSES]->(:Concept)
(:Equation)-[:IMPLEMENTS]->(:Concept)
(:Equation)-[:MAPS_TO]->(:Equation)  // Cross-paper equivalence
```

### Vector Index Creation

```cypher
// Create vector index for chunk embeddings (Neo4j 5.11+)
CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
FOR (c:Chunk)
ON c.embedding
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1536,
        `vector.similarity_function`: 'cosine'
    }
};

// Create vector index for paper metadata embeddings
CREATE VECTOR INDEX paper_embeddings IF NOT EXISTS
FOR (p:Paper)
ON p.embedding
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1536,
        `vector.similarity_function`: 'cosine'
    }
};

// Create text index for full-text search
CREATE TEXT INDEX paper_fulltext IF NOT EXISTS
FOR (p:Paper)
ON (p.title, p.abstract);
```

### Storage Queries

```cypher
// 1. Create paper node
CREATE (p:Paper {
    doi: $doi,
    title: $title,
    authors: $authors,
    abstract: $abstract,
    year: $year,
    journal: $journal,
    keywords: $keywords,
    pdf_path: $pdf_path,
    embedding: $metadata_embedding
})
RETURN id(p) as paper_id;

// 2. Add chunk with embedding
MATCH (p:Paper {doi: $doi})
CREATE (c:Chunk {
    chunk_id: $chunk_id,
    text: $text,
    embedding: $embedding,
    section: $section,
    page_range: $page_range,
    has_equations: $has_equations,
    token_count: $token_count
})
CREATE (p)-[:HAS_CHUNK]->(c);

// 3. Add equation
MATCH (p:Paper {doi: $doi})
CREATE (e:Equation {
    number: $number,
    latex: $latex,
    context: $context,
    page: $page,
    concept: $concept
})
CREATE (p)-[:DEFINES]->(e);

// 4. Add citation
MATCH (source:Paper {doi: $source_doi})
MATCH (target:Paper {doi: $target_doi})
CREATE (source)-[:CITES]->(target);
```

---

## Stage 6: RAG Retrieval

### Query Interface

```python
# scripts/query_papers.py

from typing import List, Dict
import numpy as np
from litellm import aembedding
import requests

class PaperRAG:
    """RAG interface for academic paper knowledge base."""

    def __init__(self, use_n8n: bool = True):
        self.use_n8n = use_n8n
        self.n8n_base = "https://72.61.78.89:5678"

    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict = None
    ) -> List[Dict]:
        """
        Semantic search across paper chunks.

        Args:
            query: Natural language query
            top_k: Number of results to return
            filters: Optional filters (year, author, journal)

        Returns:
            [
                {
                    "chunk_id": "...",
                    "text": "...",
                    "similarity": 0.87,
                    "metadata": {
                        "paper": "...",
                        "section": "...",
                        "page": 5
                    }
                },
                ...
            ]
        """
        # 1. Generate query embedding
        query_embedding = await self._embed_query(query)

        # 2. Vector similarity search
        if self.use_n8n:
            results = await self._search_via_n8n(query_embedding, top_k, filters)
        else:
            results = await self._search_via_graphiti(query, top_k)

        return results

    async def _embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for query."""
        response = await aembedding(
            model="text-embedding-3-small",
            input=[query]
        )
        return np.array(response.data[0]["embedding"])

    async def _search_via_n8n(
        self,
        query_embedding: np.ndarray,
        top_k: int,
        filters: dict
    ) -> List[Dict]:
        """Search via n8n webhook (production)."""
        payload = {
            "query_embedding": query_embedding.tolist(),
            "top_k": top_k,
            "filters": filters or {}
        }

        response = requests.post(
            f"{self.n8n_base}/webhook/papers/search-similar",
            json=payload
        )

        return response.json()["results"]

    async def find_equation(
        self,
        concept: str,
        paper_filter: str = None
    ) -> List[Dict]:
        """
        Find equations implementing a concept.

        Args:
            concept: Concept name (e.g., "VFE", "EFE")
            paper_filter: Optional paper title/author filter

        Returns:
            [
                {
                    "equation": "F = D_{KL}[q(s) || p(o,s)]",
                    "number": "Eq 5",
                    "paper": "Nehrer et al. (2025)",
                    "context": "...",
                    "page": 4
                },
                ...
            ]
        """
        if self.use_n8n:
            payload = {
                "concept": concept,
                "paper_filter": paper_filter
            }

            response = requests.post(
                f"{self.n8n_base}/webhook/papers/find-equation",
                json=payload
            )

            return response.json()["equations"]

    async def find_cross_references(
        self,
        concept: str
    ) -> List[Dict]:
        """
        Find how different papers implement the same concept.

        Returns:
            [
                {
                    "concept": "VFE",
                    "implementations": [
                        {
                            "paper": "Kavi et al. (2025)",
                            "equation": "Eq 3",
                            "latex": "F_i = D_KL[...]"
                        },
                        {
                            "paper": "Nehrer et al. (2025)",
                            "equation": "Eq 5",
                            "latex": "F = D_{KL}[...]"
                        }
                    ]
                },
                ...
            ]
        """
        # Query for equations with same concept across papers
        # Uses Cypher: MATCH (eq:Equation {concept: $concept})-[:DEFINED_BY]->(p:Paper)
        pass
```

### n8n Webhook Implementation (Cypher Queries)

**Webhook**: `/webhook/papers/search-similar`

```javascript
// n8n workflow node: Execute Cypher Query

const queryEmbedding = $json.query_embedding;
const topK = $json.top_k || 5;
const filters = $json.filters || {};

// Neo4j vector similarity search
const cypherQuery = `
CALL db.index.vector.queryNodes('chunk_embeddings', $topK, $queryEmbedding)
YIELD node, score
MATCH (p:Paper)-[:HAS_CHUNK]->(node)
WHERE ($year IS NULL OR p.year = $year)
  AND ($author IS NULL OR $author IN p.authors)
RETURN {
    chunk_id: node.chunk_id,
    text: node.text,
    similarity: score,
    metadata: {
        paper: p.title,
        authors: p.authors,
        year: p.year,
        section: node.section,
        page_range: node.page_range
    }
} as result
ORDER BY score DESC
LIMIT $topK
`;

return {
    query: cypherQuery,
    parameters: {
        queryEmbedding: queryEmbedding,
        topK: topK,
        year: filters.year || null,
        author: filters.author || null
    }
};
```

**Webhook**: `/webhook/papers/find-equation`

```javascript
// n8n workflow node: Find equations by concept

const cypherQuery = `
MATCH (e:Equation {concept: $concept})<-[:DEFINES]-(p:Paper)
WHERE ($paperFilter IS NULL OR p.title CONTAINS $paperFilter OR ANY(author IN p.authors WHERE author CONTAINS $paperFilter))
RETURN {
    equation: e.latex,
    number: e.number,
    paper: p.title + ' (' + toString(p.year) + ')',
    context: e.context,
    page: e.page
} as result
ORDER BY p.year DESC
`;

return {
    query: cypherQuery,
    parameters: {
        concept: $json.concept,
        paperFilter: $json.paper_filter || null
    }
};
```

---

## Integration with Existing Services

### 1. LLM Service Integration

```python
# api/services/llm_service.py - Add embedding function

async def generate_embeddings(
    texts: List[str],
    model: str = "text-embedding-3-small"
) -> List[np.ndarray]:
    """
    Generate embeddings via LiteLLM.

    Integrates with existing LLM service infrastructure.
    """
    from litellm import aembedding

    response = await aembedding(
        model=model,
        input=texts
    )

    return [np.array(data["embedding"]) for data in response.data]
```

### 2. Graphiti Service Integration

```python
# Extend existing Graphiti service for paper ingestion

from api.services.graphiti_service import GraphitiService

class PaperGraphitiService(GraphitiService):
    """Extended Graphiti service for paper knowledge graph."""

    async def ingest_paper_section(
        self,
        section: dict,
        paper_metadata: dict,
        group_id: str
    ) -> dict:
        """
        Ingest paper section via Graphiti.
        Reuses existing ingest_message pattern.
        """
        content = f"[{section['title']}] {section['content']}"

        return await self.ingest_message(
            content=content,
            source_description=f"{paper_metadata['title']} - {section['title']}",
            group_id=group_id,
            valid_at=datetime(paper_metadata['year'], 1, 1)
        )
```

### 3. Remote Sync Integration

```python
# api/services/remote_sync.py - Add paper sync utilities

async def sync_paper_to_neo4j(
    pdf_path: Path,
    use_n8n: bool = True
) -> dict:
    """
    Orchestrates paper ingestion and syncs to Neo4j.

    Integrates with existing remote_sync patterns.
    """
    processor = PDFProcessor(pdf_path)

    # Extract
    metadata = await processor.extract_metadata()
    sections = await processor.extract_sections()
    equations = await processor.extract_equations()

    # Chunk
    chunker = ContentChunker()
    chunks = await chunker.chunk_sections(sections)

    # Embed
    embedder = EmbeddingGenerator()
    embedded_chunks = await embedder.generate_embeddings(chunks)

    # Store
    if use_n8n:
        result = await ingest_via_n8n(metadata, embedded_chunks, equations)
    else:
        result = await ingest_via_graphiti(metadata, sections, embedded_chunks)

    return result
```

---

## Complete Script Template

```python
#!/usr/bin/env python3
"""
scripts/ingest_paper.py

Ingest academic PDF into Neo4j knowledge graph with RAG embeddings.

Usage:
    python scripts/ingest_paper.py docs/papers/pdfs/nehrer-2025.pdf --production
    python scripts/ingest_paper.py docs/papers/pdfs/kavi-2025.pdf --dev
"""

import asyncio
import logging
from pathlib import Path
import argparse
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import stages
from pdf_processor import PDFProcessor
from content_chunker import ContentChunker
from embedding_generator import EmbeddingGenerator

# Import storage backends
from api.services.graphiti_service import get_graphiti_service
import requests
import os


async def ingest_paper(
    pdf_path: Path,
    use_production: bool = False,
    citation_key: Optional[str] = None
) -> dict:
    """
    Main ingestion pipeline.

    Args:
        pdf_path: Path to PDF file
        use_production: If True, use n8n webhooks; if False, use Graphiti
        citation_key: Optional citation key (e.g., "nehrer2025")

    Returns:
        Ingestion summary with status and metadata
    """
    logger.info(f"Starting ingestion: {pdf_path}")
    logger.info(f"Storage backend: {'n8n (production)' if use_production else 'Graphiti (dev)'}")

    # Stage 1: PDF Processing
    logger.info("Stage 1: Extracting PDF content...")
    processor = PDFProcessor(pdf_path)

    metadata = await processor.extract_metadata()
    sections = await processor.extract_sections()
    equations = await processor.extract_equations()
    figures = await processor.extract_figures_tables()

    logger.info(f"Extracted: {len(sections)} sections, {len(equations)} equations")

    # Stage 2: Content Chunking
    logger.info("Stage 2: Chunking content...")
    chunker = ContentChunker(max_tokens=512, overlap=50)

    chunks = await chunker.chunk_sections(sections)
    logger.info(f"Created {len(chunks)} chunks")

    # Stage 3: Embedding Generation
    logger.info("Stage 3: Generating embeddings...")
    embedder = EmbeddingGenerator(model="text-embedding-3-small")

    embedded_chunks = await embedder.generate_embeddings(chunks)
    metadata_embedding = await embedder.generate_metadata_embedding(metadata)

    logger.info(f"Generated embeddings for {len(embedded_chunks)} chunks")

    # Stage 4: Storage
    if use_production:
        logger.info("Stage 4: Storing via n8n webhooks (production)...")
        result = await _store_via_n8n(
            metadata,
            embedded_chunks,
            equations,
            metadata_embedding
        )
    else:
        logger.info("Stage 4: Storing via Graphiti (development)...")
        result = await _store_via_graphiti(
            metadata,
            sections,
            embedded_chunks,
            citation_key or _generate_citation_key(metadata)
        )

    # Save extraction to markdown
    extraction_path = pdf_path.parent.parent / "extractions" / f"{pdf_path.stem}-extraction.md"
    await _save_extraction(extraction_path, metadata, sections, equations)
    logger.info(f"Saved extraction to: {extraction_path}")

    logger.info("Ingestion complete!")
    return {
        "status": "success",
        "backend": "n8n" if use_production else "graphiti",
        "metadata": metadata,
        "chunks": len(embedded_chunks),
        "equations": len(equations),
        "extraction_file": str(extraction_path),
        **result
    }


async def _store_via_n8n(
    metadata: dict,
    chunks: list[dict],
    equations: list[dict],
    metadata_embedding: list[float]
) -> dict:
    """Store via n8n webhooks (production)."""
    N8N_BASE = "https://72.61.78.89:5678"
    HMAC_SECRET = os.getenv("MEMEVOLVE_HMAC_SECRET")

    # 1. Create paper node
    paper_payload = {
        **metadata,
        "embedding": metadata_embedding
    }

    response = requests.post(
        f"{N8N_BASE}/webhook/papers/create",
        json=paper_payload,
        headers={"X-HMAC-Signature": _generate_hmac(paper_payload, HMAC_SECRET)}
    )
    paper_id = response.json()["paper_id"]

    # 2. Add chunks
    for chunk in chunks:
        chunk_payload = {
            "paper_id": paper_id,
            **chunk
        }
        requests.post(
            f"{N8N_BASE}/webhook/papers/add-chunk",
            json=chunk_payload,
            headers={"X-HMAC-Signature": _generate_hmac(chunk_payload, HMAC_SECRET)}
        )

    # 3. Add equations
    for equation in equations:
        equation_payload = {
            "paper_id": paper_id,
            **equation
        }
        requests.post(
            f"{N8N_BASE}/webhook/papers/add-equation",
            json=equation_payload,
            headers={"X-HMAC-Signature": _generate_hmac(equation_payload, HMAC_SECRET)}
        )

    return {
        "paper_id": paper_id,
        "chunks_added": len(chunks),
        "equations_added": len(equations)
    }


async def _store_via_graphiti(
    metadata: dict,
    sections: list[dict],
    chunks: list[dict],
    citation_key: str
) -> dict:
    """Store via Graphiti temporal knowledge graph (development)."""
    from datetime import datetime

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

    # Note: Graphiti doesn't natively support vector embeddings yet
    # Store embeddings separately or extend Graphiti service

    return {
        "group_id": group_id,
        "sections_ingested": len(sections)
    }


def _generate_citation_key(metadata: dict) -> str:
    """Generate citation key (e.g., 'nehrer2025')."""
    first_author = metadata['authors'][0].split(',')[0].lower()
    year = metadata['year']
    return f"{first_author}{year}"


def _generate_hmac(payload: dict, secret: str) -> str:
    """Generate HMAC-SHA256 signature."""
    import hmac
    import hashlib
    import json

    message = json.dumps(payload, sort_keys=True).encode()
    signature = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    return signature


async def _save_extraction(
    path: Path,
    metadata: dict,
    sections: list[dict],
    equations: list[dict]
) -> None:
    """Save extraction to markdown file."""
    with open(path, 'w') as f:
        f.write(f"# {metadata['title']}\n\n")
        f.write(f"**Authors**: {', '.join(metadata['authors'])}\n")
        f.write(f"**Year**: {metadata['year']}\n")
        f.write(f"**DOI**: {metadata['doi']}\n\n")
        f.write(f"## Abstract\n\n{metadata['abstract']}\n\n")

        f.write("## Equations\n\n")
        for eq in equations:
            f.write(f"### {eq['number']} (p. {eq['page']})\n\n")
            f.write(f"```latex\n{eq['latex']}\n```\n\n")
            f.write(f"**Context**: {eq['context']}\n\n")

        f.write("## Sections\n\n")
        for section in sections:
            f.write(f"### {section['title']} (pp. {section['page_start']}-{section['page_end']})\n\n")
            f.write(f"{section['content'][:500]}...\n\n")


def main():
    parser = argparse.ArgumentParser(description="Ingest academic PDF into knowledge graph")
    parser.add_argument("pdf_path", type=Path, help="Path to PDF file")
    parser.add_argument("--production", action="store_true", help="Use n8n webhooks (production)")
    parser.add_argument("--citation-key", type=str, help="Citation key (e.g., 'nehrer2025')")

    args = parser.parse_args()

    if not args.pdf_path.exists():
        logger.error(f"PDF not found: {args.pdf_path}")
        return

    result = asyncio.run(ingest_paper(
        pdf_path=args.pdf_path,
        use_production=args.production,
        citation_key=args.citation_key
    ))

    print("\n=== Ingestion Summary ===")
    print(f"Status: {result['status']}")
    print(f"Backend: {result['backend']}")
    print(f"Paper: {result['metadata']['title']}")
    print(f"Chunks: {result['chunks']}")
    print(f"Equations: {result['equations']}")
    print(f"Extraction: {result['extraction_file']}")


if __name__ == "__main__":
    main()
```

---

## Example Workflows

### Workflow 1: ActiveInference.jl Paper

```bash
# 1. Download PDF
wget https://www.mdpi.com/1099-4300/27/1/62/pdf -O docs/papers/pdfs/nehrer-2025-activeinference.pdf

# 2. Ingest (development mode)
python scripts/ingest_paper.py docs/papers/pdfs/nehrer-2025-activeinference.pdf --citation-key nehrer2025

# 3. Query for POMDP equations
python scripts/query_papers.py "What is the POMDP formulation in ActiveInference.jl?"

# Output:
# [
#   {
#     "text": "A POMDP is defined by the tuple (S, A, O, T, R, Ω) where...",
#     "similarity": 0.89,
#     "metadata": {
#       "paper": "Introducing ActiveInference.jl (2025)",
#       "section": "Theoretical Background",
#       "page": 3
#     }
#   }
# ]
```

### Workflow 2: Cross-Reference VFE Across Papers

```bash
# 1. Ingest multiple papers
python scripts/ingest_paper.py docs/papers/pdfs/kavi-2025-thoughtseeds.pdf --citation-key kavi2025
python scripts/ingest_paper.py docs/papers/pdfs/nehrer-2025-activeinference.pdf --citation-key nehrer2025
python scripts/ingest_paper.py docs/papers/pdfs/friston-spm-dem.pdf --citation-key friston2020

# 2. Query for VFE implementations
python scripts/query_papers.py --concept VFE --mode cross-reference

# Output:
# Cross-Reference: Variational Free Energy (VFE)
#
# Kavi et al. (2025) - Thoughtseeds
#   Eq 3: F_i = D_KL[q(μ_i) || p(μ_i | s_i, a_i, θ_i, K_i, S_i)] - E_q[log p(...)]
#   Context: "NP Free Energy Minimization"
#
# Nehrer et al. (2025) - ActiveInference.jl
#   Eq 5: F = D_{KL}[q(s) || p(o,s)]
#   Context: "CAVI updates for state inference"
#
# Friston et al. (2020) - SPM DEM
#   Eq 12: F(q) = E_q[log q(ψ) - log p(y, ψ)]
#   Context: "Dynamic Expectation Maximization"
```

### Workflow 3: Production RAG with n8n

```bash
# 1. Ingest to production (creates n8n webhook calls)
python scripts/ingest_paper.py docs/papers/pdfs/nehrer-2025-activeinference.pdf --production --citation-key nehrer2025

# 2. Query production endpoint
curl -X POST https://72.61.78.89:5678/webhook/papers/search-similar \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the EFE decomposition?",
    "top_k": 3,
    "filters": {"year": 2025}
  }'

# Response:
# {
#   "results": [
#     {
#       "chunk_id": "theoretical-background-005",
#       "text": "The Expected Free Energy (EFE) decomposes into epistemic and pragmatic components...",
#       "similarity": 0.92,
#       "metadata": {...}
#     }
#   ]
# }
```

---

## Required n8n Workflows

### Workflow 1: Create Paper

**Endpoint**: `/webhook/papers/create`

**Nodes**:
1. Webhook (POST)
2. HMAC Verification
3. Execute Cypher: Create Paper Node
4. Return paper_id

**Cypher**:
```cypher
CREATE (p:Paper {
    doi: $doi,
    title: $title,
    authors: $authors,
    abstract: $abstract,
    year: $year,
    journal: $journal,
    keywords: $keywords,
    pdf_path: $pdf_path,
    embedding: $embedding
})
RETURN id(p) as paper_id
```

### Workflow 2: Add Chunk

**Endpoint**: `/webhook/papers/add-chunk`

**Nodes**:
1. Webhook (POST)
2. HMAC Verification
3. Execute Cypher: Create Chunk + Relationship
4. Return success

**Cypher**:
```cypher
MATCH (p:Paper) WHERE id(p) = $paper_id
CREATE (c:Chunk {
    chunk_id: $chunk_id,
    text: $text,
    embedding: $embedding,
    section: $section,
    page_range: $page_range,
    has_equations: $has_equations,
    token_count: $token_count
})
CREATE (p)-[:HAS_CHUNK]->(c)
```

### Workflow 3: Search Similar

**Endpoint**: `/webhook/papers/search-similar`

**Nodes**:
1. Webhook (POST)
2. Execute Cypher: Vector Similarity Search
3. Format Results
4. Return JSON

**Cypher**: (see Stage 6 example above)

---

## Performance Considerations

### Embedding Generation

- **Batch size**: 100 chunks per API call (OpenAI limit: 2048 per request)
- **Rate limiting**: Respect OpenAI rate limits (500 RPM for tier 1)
- **Caching**: Store embeddings locally to avoid re-computation

### Vector Search

- **Index type**: HNSW (Hierarchical Navigable Small World) for Neo4j 5.11+
- **Similarity function**: Cosine similarity (standard for text embeddings)
- **Top-k optimization**: Use approximate nearest neighbor search for speed

### Storage Optimization

- **Chunk size**: 512 tokens balances context vs granularity
- **Overlap**: 50 tokens prevents context loss at chunk boundaries
- **Compression**: Store embeddings as float32 (not float64) to save space

---

## Dependencies

Add to `requirements.txt`:

```txt
# PDF Processing
pdfplumber>=0.10.0
PyMuPDF>=1.23.0
pdf2image>=1.16.0

# Equation Extraction
pix2tex>=0.1.2  # LaTeX-OCR

# Embeddings (already in project)
litellm>=1.30.0

# Text Processing
tiktoken>=0.5.0

# Existing dependencies
graphiti-core>=0.3.0
requests>=2.31.0
numpy>=1.24.0
```

---

## Testing

### Unit Tests

```python
# tests/unit/test_pdf_ingestion.py

import pytest
from pathlib import Path
from scripts.pdf_processor import PDFProcessor
from scripts.content_chunker import ContentChunker

@pytest.mark.asyncio
async def test_metadata_extraction():
    """Test PDF metadata extraction."""
    pdf_path = Path("docs/papers/pdfs/nehrer-2025-activeinference.pdf")
    processor = PDFProcessor(pdf_path)

    metadata = await processor.extract_metadata()

    assert metadata["doi"] == "10.3390/e27010062"
    assert "Nehrer" in metadata["authors"][0]
    assert metadata["year"] == 2025

@pytest.mark.asyncio
async def test_chunking():
    """Test content chunking."""
    sections = [
        {
            "title": "Introduction",
            "content": "Test content " * 200,  # ~400 words
            "page_start": 1,
            "page_end": 2
        }
    ]

    chunker = ContentChunker(max_tokens=512, overlap=50)
    chunks = await chunker.chunk_sections(sections)

    assert len(chunks) > 0
    assert all(chunk["token_count"] <= 512 for chunk in chunks)
```

### Integration Tests

```python
# tests/integration/test_paper_ingestion_flow.py

import pytest
from pathlib import Path
from scripts.ingest_paper import ingest_paper

@pytest.mark.asyncio
async def test_full_ingestion_graphiti():
    """Test full ingestion pipeline (Graphiti)."""
    pdf_path = Path("docs/papers/pdfs/test-paper.pdf")

    result = await ingest_paper(
        pdf_path=pdf_path,
        use_production=False,
        citation_key="test2025"
    )

    assert result["status"] == "success"
    assert result["backend"] == "graphiti"
    assert result["chunks"] > 0
```

---

## Monitoring & Logging

### Ingestion Metrics

Track in Prometheus/Grafana:
- Papers ingested per day
- Average chunks per paper
- Embedding generation time
- Storage latency (Graphiti vs n8n)
- Vector search performance

### Error Handling

```python
# Add to script template

import sentry_sdk

try:
    result = await ingest_paper(pdf_path)
except PDFExtractionError as e:
    logger.error(f"PDF extraction failed: {e}")
    sentry_sdk.capture_exception(e)
except EmbeddingGenerationError as e:
    logger.error(f"Embedding generation failed: {e}")
    sentry_sdk.capture_exception(e)
except StorageError as e:
    logger.error(f"Storage failed: {e}")
    sentry_sdk.capture_exception(e)
```

---

## Future Enhancements

### Phase 2 Features

1. **Multi-modal embeddings**: Support for figures/diagrams (CLIP embeddings)
2. **Citation network analysis**: PageRank for important papers
3. **Concept drift tracking**: Temporal evolution of concepts across papers
4. **Cross-lingual support**: Translate non-English papers
5. **Equation solver integration**: SymPy for equation manipulation

### Phase 3 Features

1. **Automated literature review**: Generate summaries across multiple papers
2. **Hypothesis generation**: Identify research gaps
3. **Experimental design suggestions**: Based on methodology analysis
4. **Reproducibility scoring**: Assess paper reproducibility

---

## Conclusion

This pipeline provides a comprehensive solution for ingesting academic papers into a RAG-enabled knowledge graph. Key features:

- **Dual-tier storage**: Graphiti for development, n8n for production
- **Vector embeddings**: Enable semantic search across paper content
- **Structured extraction**: Preserve equations, citations, metadata
- **Flexible querying**: Support both similarity search and graph traversal
- **Integration**: Seamless integration with existing Dionysus services

**Next Steps**:
1. Implement PDF processing modules (`pdf_processor.py`, `content_chunker.py`, `embedding_generator.py`)
2. Create n8n workflows for production storage
3. Test with ActiveInference.jl and SPM DEM papers
4. Deploy to VPS and benchmark performance

---

**Author**: Mani Saint-Victor, MD
**Date**: 2026-01-03
**Repository**: dionysus3-core
**Related**: `docs/thoughtseeds-paper-models-extraction.md`, `scripts/ingest_thoughtseeds_paper.py`
