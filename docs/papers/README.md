# Academic Papers - Knowledge Base

**Purpose**: Store, extract, and cross-reference academic papers for Thoughtseeds implementation.

## Directory Structure

```
papers/
├── pdfs/                          # Original PDF files
│   ├── kavi-2025-thoughtseeds.pdf
│   ├── nehrer-2025-activeinference-jl.pdf
│   └── friston-spm-dem.pdf
├── extractions/                   # Extracted technical content
│   ├── kavi-2025-models.md
│   ├── nehrer-2025-technical.md
│   └── friston-spm-equations.md
└── README.md                      # This file
```

## Papers Index

### 1. Thoughtseeds Framework (Kavi et al., 2025)
- **Citation**: Kavi, P. C., Zamora-López, G., & Friedman, D. A. (2025). From Neuronal Packets to Thoughtseeds: A Hierarchical Model of Embodied Cognition in the Global Workspace.
- **Status**: ✅ Models extracted
- **Key Equations**: 1-17 (NP, SE, KD, TS, VFE, EFE, GFE)
- **Extraction**: `/docs/thoughtseeds-paper-models-extraction.md`
- **Neo4j**: Pending ingestion

### 2. ActiveInference.jl (Nehrer et al., 2025)
- **Citation**: Nehrer, S. W., Laursen, J. E., Heins, C., Friston, K., Mathys, C., & Waade, P. T. (2025). Introducing ActiveInference.jl: A Julia Library for Simulation and Parameter Estimation with Active Inference Models. *Entropy*, 27(1), 62. https://doi.org/10.3390/e27010062
- **Status**: 🔄 Extraction in progress (Agent a374ad1)
- **Key Equations**: 1-20 (POMDP, VFE, EFE, CAVI, Dirichlet learning)
- **Extraction**: `/docs/papers/activeinference-jl-technical-reference.md` (pending)
- **Neo4j**: Schema design in progress (Agent a473e8d)

### 3. SPM DEM Framework (Friston et al.)
- **Citation**: Pending
- **Status**: ⏳ Awaiting PDF
- **Key Content**: Dynamic Expectation Maximization, Hierarchical Dynamic Models
- **Extraction**: Pending

## RAG Ingestion Pipeline

**Design Status**: 🔄 In progress (Agent a84a3e7)

**Workflow**:
1. Place PDF in `/docs/papers/pdfs/{citation-key}.pdf`
2. Run: `python scripts/ingest_paper.py {citation-key}.pdf`
3. Automated extraction → Neo4j → Vector embeddings
4. Query via: `scripts/query_papers.py "POMDP free energy"`

**Documentation**: `/docs/pdf-ingestion-pipeline.md` (pending)

## Cross-Reference Map

### Thoughtseeds ↔ ActiveInference.jl

| Thoughtseeds Concept | Equation | ActiveInference.jl | Equation |
|----------------------|----------|-------------------|----------|
| NP Free Energy | Eq 3 | VFE (CAVI) | Eq 5-16 |
| TS Free Energy | Eq 11 | EFE (Policy) | Eq 17-18 |
| Knowledge Domain | Eq 5-7 | POMDP A, B matrices | Eq 1 |
| Active Pool Selection | Eq 12-13 | Policy softmax (γ) | Section 2.3 |
| Parameter Learning | Conceptual | Dirichlet updates | Eq 19-20 |
| Agent-Level GFE | Eq 17.1 | VFE + E[EFE] | Implicit |

**Full mapping**: See `/docs/papers/cross-reference-thoughtseeds-activeinference.md` (pending agent completion)

## Neo4j Knowledge Graph

**Schema**: See `/docs/neo4j-paper-schema.md` (pending)

**Sample Queries**:

```cypher
// Find all equations implementing VFE
MATCH (p:Paper)-[:DEFINES]->(eq:Equation)
WHERE eq.concept = "VFE"
RETURN p.title, eq.number, eq.latex

// Find implementation mappings
MATCH (eq1:Equation {paper: "Kavi2025"})-[:MAPS_TO]->(eq2:Equation {paper: "Nehrer2025"})
RETURN eq1.number, eq2.number, eq1.concept

// Find all papers by Friston
MATCH (a:Author {name: "Karl Friston"})<-[:AUTHORED_BY]-(p:Paper)
RETURN p.title, p.year
```

## Usage Instructions

### For Researchers
1. **Add new paper**: Place PDF in `pdfs/`, run ingestion script
2. **Query concepts**: Use Neo4j queries or RAG search
3. **Cross-reference**: Check extraction files for equation mappings

### For Developers
1. **Find implementation**: Check cross-reference map
2. **Get equation details**: Read extraction markdown files
3. **Verify correctness**: Compare against original PDFs

## Traceability

All extracted content includes:
- **Source**: Paper citation + section number
- **Equation number**: Original equation number from paper
- **Page number**: PDF page reference
- **LaTeX**: Original mathematical notation
- **Variables**: Complete symbol definitions

**Example**:
```markdown
### VFE Definition (Nehrer et al., 2025, Eq 5, p. 4)

$$F \triangleq D_{KL}[q(s) \| p(o,s)] = \sum_s q(s) \ln \frac{q(s)}{p(o,s)}$$

**Variables**:
- F: Variational Free Energy
- q(s): Approximate posterior over states
- p(o,s): Joint likelihood
```

---

**Maintained by**: Dionysus3-core team
**Last updated**: 2026-01-03
**Contact**: See CLAUDE.md for project guidelines
