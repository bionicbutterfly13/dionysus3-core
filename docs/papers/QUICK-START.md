# PDF Ingestion Pipeline - Quick Start Guide

**Purpose**: Fast reference for ingesting and querying academic papers

---

## Installation

```bash
# Install dependencies
pip install pdfplumber PyMuPDF tiktoken litellm

# Optional: LaTeX equation extraction
pip install pix2tex
```

---

## Usage Examples

### 1. Ingest Paper (Development)

```bash
# Basic ingestion (uses Graphiti)
python scripts/ingest_paper.py docs/papers/pdfs/nehrer-2025.pdf

# With custom citation key
python scripts/ingest_paper.py docs/papers/pdfs/kavi-2025.pdf --citation-key kavi2025
```

### 2. Ingest Paper (Production)

```bash
# Production ingestion (uses n8n webhooks)
python scripts/ingest_paper.py docs/papers/pdfs/nehrer-2025.pdf --production

# Requires: MEMEVOLVE_HMAC_SECRET environment variable
```

### 3. Query Papers

```bash
# Semantic search
python scripts/query_papers.py "What is the POMDP formulation in active inference?"

# Search with filters
python scripts/query_papers.py "Expected Free Energy" --year 2025 --author Nehrer

# Find equations
python scripts/query_papers.py --concept VFE --mode equation

# Cross-reference concept
python scripts/query_papers.py --concept "Variational Free Energy" --mode cross-reference
```

---

## Example Workflow: ActiveInference.jl Paper

```bash
# 1. Download PDF (if not already available)
# wget https://www.mdpi.com/1099-4300/27/1/62/pdf -O docs/papers/pdfs/nehrer-2025.pdf

# 2. Ingest paper
python scripts/ingest_paper.py docs/papers/pdfs/nehrer-2025.pdf --citation-key nehrer2025

# Output:
# === Starting Paper Ingestion ===
# PDF: docs/papers/pdfs/nehrer-2025.pdf
# Backend: Graphiti (dev)
#
# --- Stage 1: PDF Processing ---
# Extracting metadata...
# Metadata extracted: Introducing ActiveInference.jl (2025)
# Extracting sections...
# Extracted 8 sections
# Extracting equations (placeholder)...
# Found 20 equation references
#
# --- Stage 2: Content Chunking ---
# Chunking content...
# Created 45 chunks
#
# --- Stage 3: Embedding Generation ---
# Generating embeddings for 45 chunks...
# Embeddings generated
#
# --- Stage 4: Storage ---
# Storing via Graphiti...
# Stored in Graphiti group: paper-nehrer2025
#
# === Ingestion Complete ===

# 3. Query for POMDP equations
python scripts/query_papers.py "What is the POMDP formulation?" --top-k 3

# Output:
# ================================================================================
# SEARCH RESULTS
# ================================================================================
#
# [1] Similarity: 0.892
# Section: Theoretical Background
# Paper: Introducing ActiveInference.jl (2025)
# Pages: [3, 4]
#
# A POMDP is defined by the tuple (S, A, O, T, R, Ω) where S is the state space,
# A is the action space, O is the observation space, T is the state transition
# function, R is the reward function, and Ω is the observation function...
# --------------------------------------------------------------------------------

# 4. Find VFE equations across all papers
python scripts/query_papers.py --concept VFE --mode cross-reference

# Output:
# ================================================================================
# CROSS-REFERENCE RESULTS
# ================================================================================
#
# Paper: Introducing ActiveInference.jl (2025)
# Concept: VFE
#   Eq 5: F = D_{KL}[q(s) || p(o,s)]
#   Context: The variational free energy is defined as the KL divergence...
# --------------------------------------------------------------------------------
#
# Paper: Thoughtseeds Framework (2025)
# Concept: VFE
#   Eq 3: F_i = D_KL[q(μ_i) || p(μ_i | s_i, a_i, θ_i, K_i, S_i)]
#   Context: NP Free Energy Minimization - neuronal packets minimize VFE...
# --------------------------------------------------------------------------------
```

---

## Pipeline Stages

### Stage 1: PDF Processing
- **Input**: PDF file
- **Output**: Metadata, sections, equations, figures
- **Time**: ~30 seconds for typical paper

### Stage 2: Content Chunking
- **Input**: Extracted sections
- **Output**: 512-token chunks with overlap
- **Time**: ~5 seconds

### Stage 3: Embedding Generation
- **Input**: Text chunks
- **Output**: 1536-dim embeddings via OpenAI
- **Time**: ~15 seconds for 50 chunks

### Stage 4: Storage
- **Input**: Embeddings + metadata
- **Output**: Neo4j nodes + relationships
- **Time**: ~10 seconds (Graphiti) or ~30 seconds (n8n)

**Total**: ~60 seconds per paper (development mode)

---

## Troubleshooting

### Issue: HMAC signature error (production mode)

```bash
# Check environment variable
echo $MEMEVOLVE_HMAC_SECRET

# If not set:
export MEMEVOLVE_HMAC_SECRET="your-secret-here"
```

### Issue: Embedding generation fails

```bash
# Check OpenAI API key
echo $OPENAI_API_KEY

# If not set:
export OPENAI_API_KEY="sk-..."
```

### Issue: PDF extraction incomplete

```bash
# Install additional dependencies
pip install pdf2image poppler-utils

# For equation extraction:
pip install pix2tex torch torchvision
```

### Issue: Neo4j connection error (n8n mode)

```bash
# Test n8n webhook
curl https://72.61.78.89:5678/webhook/papers/health

# Check n8n workflows are active in UI
```

---

## File Locations

### Ingested Papers

```
docs/papers/
├── pdfs/                          # Original PDFs
│   ├── nehrer-2025.pdf
│   ├── kavi-2025.pdf
│   └── friston-spm-dem.pdf
├── extractions/                   # Auto-generated markdown
│   ├── nehrer-2025-extraction.md
│   ├── kavi-2025-extraction.md
│   └── friston-spm-dem-extraction.md
└── README.md
```

### Scripts

```
scripts/
├── ingest_paper.py               # Main ingestion script
├── query_papers.py               # RAG query interface
└── [helper modules]              # pdf_processor.py, etc.
```

### Documentation

```
docs/
├── pdf-ingestion-pipeline.md     # Complete architecture
├── n8n-paper-workflows.md        # n8n webhook specs
└── papers/
    ├── README.md                  # Papers index
    └── QUICK-START.md             # This file
```

---

## Advanced Usage

### Batch Ingestion

```bash
# Ingest multiple papers
for pdf in docs/papers/pdfs/*.pdf; do
    python scripts/ingest_paper.py "$pdf"
done
```

### Custom Chunking

```python
# In ingest_paper.py, modify:
chunker = ContentChunker(
    max_tokens=256,  # Smaller chunks
    overlap=100      # More overlap
)
```

### Save Query Results

```bash
# Save to JSON
python scripts/query_papers.py "active inference POMDP" --output results.json
```

---

## Integration with Existing Code

### Use Graphiti Service Directly

```python
from api.services.graphiti_service import get_graphiti_service

service = await get_graphiti_service()

# Search papers
results = await service.search(
    query="thoughtseed neuronal packet",
    group_ids=["paper-kavi2025"],
    limit=10
)
```

### Use in Agent Tools

```python
from smolagents import Tool

class PaperSearchTool(Tool):
    name = "search_papers"
    description = "Search academic papers for concepts"
    inputs = {"query": {"type": "string", "description": "Search query"}}
    output_type = "string"

    async def forward(self, query: str) -> str:
        from scripts.query_papers import PaperRAG

        rag = PaperRAG(use_production=False)
        results = await rag.search(query, top_k=3)

        return "\n\n".join([
            f"[{i+1}] {r['metadata']['paper']}\n{r['text'][:200]}..."
            for i, r in enumerate(results)
        ])
```

---

## Next Steps

1. **Ingest your first paper**: Start with ActiveInference.jl or Thoughtseeds
2. **Query the knowledge base**: Test semantic search and equation lookup
3. **Deploy to production**: Set up n8n workflows for high-value papers
4. **Extend pipeline**: Add equation OCR, figure extraction, citation network analysis

---

**Documentation**: `/docs/pdf-ingestion-pipeline.md`
**Scripts**: `/scripts/ingest_paper.py`, `/scripts/query_papers.py`
**n8n Workflows**: `/docs/n8n-paper-workflows.md`

**Author**: Mani Saint-Victor, MD
**Date**: 2026-01-03
