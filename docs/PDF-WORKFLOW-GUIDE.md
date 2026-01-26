# PDF Paper Ingestion - Quick Start Guide

**For**: Dr. Mani Saint-Victor
**Purpose**: Streamlined workflow for adding academic papers to Dionysus knowledge base

---

## 🎯 **Simple Workflow (Recommended)**

### **Step 1: Upload PDFs**

Place PDF files in: `/docs/papers/pdfs/`

**Naming convention**: `{first-author-year-keyword}.pdf`

Examples:
- `kavi-2025-thoughtseeds.pdf`
- `nehrer-2025-activeinference.pdf`
- `friston-2020-spm-dem.pdf`

### **Step 2: Tell Claude**

Just say:
```
"Process these PDFs: [list filenames]"
```

Claude will automatically:
1. ✅ Extract equations, concepts, code patterns
2. ✅ Create markdown documentation in `/docs/papers/extractions/`
3. ✅ Build Neo4j knowledge graph nodes
4. ✅ Generate cross-reference mappings
5. ✅ Create Quartz documentation

### **Step 3: Query Knowledge**

Ask questions like:
- "How does ActiveInference.jl implement VFE calculation?"
- "Map SPM DEM equations to Thoughtseeds framework"
- "Find all papers mentioning Markov blankets"

---

## 📂 **File Organization (Auto-Created)**

```
docs/papers/
├── pdfs/                              # 📄 Original PDFs (you upload here)
│   ├── kavi-2025-thoughtseeds.pdf
│   ├── nehrer-2025-activeinference.pdf
│   └── friston-2020-spm-dem.pdf
│
├── extractions/                       # 📝 Auto-generated technical docs
│   ├── kavi-2025-models.md           # All equations + models
│   ├── nehrer-2025-technical.md      # API + algorithms
│   └── friston-2020-equations.md     # SPM DEM framework
│
└── cross-references/                  # 🔗 Mapping documents
    ├── thoughtseeds-to-activeinference.md
    ├── activeinference-to-spm-dem.md
    └── master-equation-index.md
```

---

## 🔍 **What Gets Extracted Automatically**

### From Each Paper:

1. **Metadata**
   - Authors, year, DOI, abstract
   - Citation key for references

2. **Mathematical Content**
   - All equations (LaTeX format preserved)
   - Variable definitions
   - Equation cross-references

3. **Conceptual Content**
   - Key concepts (VFE, EFE, POMDP, etc.)
   - Definitions
   - Relationships between concepts

4. **Implementation Details**
   - Algorithm pseudocode
   - Code patterns
   - API signatures

5. **Cross-References**
   - Links to related papers
   - Equation mappings
   - Concept mappings

---

## 🗄️ **Neo4j Knowledge Graph (Auto-Populated)**

**Nodes Created**:
```cypher
(Paper {title, year, doi, citation_key})
(Equation {number, latex, description})
(Concept {name, definition, domain})
(Author {name, affiliation})
(Implementation {language, library, function})
```

**Relationships**:
```cypher
(Paper)-[:DEFINES]->(Equation)
(Paper)-[:INTRODUCES]->(Concept)
(Equation)-[:MAPS_TO]->(Equation)  // Cross-paper
(Concept)-[:IMPLEMENTS]->(Implementation)
```

**Query Examples**:
```cypher
// Find how VFE is calculated across papers
MATCH (p:Paper)-[:DEFINES]->(eq:Equation {concept: "VFE"})
RETURN p.title, eq.number, eq.latex

// Find implementation in Julia
MATCH (eq:Equation)-[:IMPLEMENTS]->(impl:Implementation {language: "Julia"})
RETURN eq.concept, impl.function, impl.library
```

---

## 💡 **Usage Examples**

### Example 1: Adding ActiveInference.jl Paper

**You**:
```
Here's the ActiveInference.jl PDF: [upload to /docs/papers/pdfs/]
Process this and map it to Thoughtseeds equations.
```

**Claude (spawns agents)**:
1. Agent 1: Extract all 20 equations from paper
2. Agent 2: Map to Thoughtseeds Eq 1-17
3. Agent 3: Create Neo4j nodes
4. Agent 4: Build Quartz docs

**Output** (auto-created):
- `/docs/papers/extractions/nehrer-2025-technical.md`
- `/docs/papers/cross-references/thoughtseeds-to-activeinference.md`
- Neo4j nodes + relationships
- `/docs/garden/content/papers/activeinference-jl.md`

### Example 2: Querying Across Papers

**You**:
```
"How is EFE calculated in ActiveInference.jl vs SPM DEM?"
```

**Claude (uses Neo4j + RAG)**:
```cypher
MATCH (p1:Paper {citation_key: "Nehrer2025"})-[:DEFINES]->(eq1:Equation {concept: "EFE"}),
      (p2:Paper {citation_key: "Friston2020"})-[:DEFINES]->(eq2:Equation {concept: "EFE"})
RETURN eq1.latex, eq2.latex, eq1.description, eq2.description
```

Returns side-by-side comparison with LaTeX equations.

---

## 🎨 **Quartz Integration**

Each paper automatically gets a Quartz page:

**Location**: `/docs/garden/content/papers/{citation-key}.md`

**Structure**:
```markdown
# [Paper Title]

## Quick Reference
- **Authors**: [list]
- **Year**: [year]
- **DOI**: [doi]
- **Domain**: Active Inference, Computational Neuroscience

## Key Equations

### Equation 5: VFE Definition
$$F \triangleq D_{KL}[q(s) \| p(o,s)]$$
- **Variables**: ...
- **Used in**: NP free energy (Thoughtseeds Eq 3)
- **Implementation**: `ActiveInference.jl::infer_states!`

## Concepts
- [[VFE]] - Variational Free Energy
- [[POMDP]] - Partially Observable Markov Decision Process
- [[CAVI]] - Coordinate Ascent Variational Inference

## Cross-References
- Maps to [[Thoughtseeds Framework]] Eq 3, 11
- Implements [[SPM DEM]] variational Laplace
- Uses [[pymdp]] Python library patterns

## Code Examples
[Extracted from paper Section 3.1...]
```

---

## ⚡ **Fast Track: Just for You**

**Your workflow**:
1. Drop PDFs in `/docs/papers/pdfs/`
2. Say: "Process new papers"
3. Ask: "How do I implement X using Y paper?"

**Claude handles**:
- Spawning parallel agents
- Extracting + documenting
- Building knowledge graph
- Creating cross-references
- Updating Quartz docs

**You get**:
- Full traceability
- Equation mappings
- Implementation guidance
- RAG-powered Q&A

---

## 🚀 **Ready to Use**

**Current Status**:
- ✅ Directory structure created
- ✅ README.md with paper index
- 🔄 3 agents processing ActiveInference.jl now
- ⏳ Awaiting SPM DEM PDF

**Next**: Just upload PDFs and tell me to process them!

---

**Questions?** Just ask Claude in natural language:
- "Show me all VFE equations across papers"
- "How does Julia implement free energy minimization?"
- "Map Thoughtseeds Eq 11 to executable code"
