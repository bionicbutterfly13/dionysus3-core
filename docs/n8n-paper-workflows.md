# n8n Workflows for Paper Ingestion

**Purpose**: Neo4j storage endpoints for academic paper RAG pipeline

**Date**: 2026-01-03

---

## Overview

These n8n workflows provide production-grade Neo4j storage for academic papers with vector embeddings. Each workflow validates HMAC signatures and executes Cypher queries against the production Neo4j instance.

**Base URL**: `https://72.61.78.89:5678/webhook/papers/`

---

## Workflow 1: Create Paper Node

**Endpoint**: `/webhook/papers/create`

**Method**: POST

**Purpose**: Create a new paper node with metadata and embedding

### Request Payload

```json
{
  "doi": "10.3390/e27010062",
  "title": "Introducing ActiveInference.jl: A Julia Library...",
  "authors": ["Nehrer, S. W.", "Laursen, J. E.", "Heins, C.", ...],
  "abstract": "The emergence of cognition requires...",
  "year": 2025,
  "journal": "Entropy",
  "keywords": ["active inference", "POMDP", "Julia"],
  "pdf_path": "/docs/papers/pdfs/nehrer-2025.pdf",
  "embedding": [0.123, -0.456, ...]  // 1536-dim vector
}
```

### Response

```json
{
  "status": "success",
  "paper_id": "4:12345678-1234-5678-1234-567812345678",
  "created_at": "2026-01-03T12:00:00Z"
}
```

### n8n Workflow Configuration

**Nodes**:

1. **Webhook Trigger**
   - Method: POST
   - Path: `/papers/create`
   - Response Mode: Wait for Response

2. **Function: Validate HMAC**
   ```javascript
   const crypto = require('crypto');
   const secret = $env.MEMEVOLVE_HMAC_SECRET;
   const signature = $input.headers['x-hmac-signature'];
   const payload = JSON.stringify($input.body);

   const expectedSignature = crypto
     .createHmac('sha256', secret)
     .update(payload)
     .digest('hex');

   if (signature !== expectedSignature) {
     throw new Error('Invalid HMAC signature');
   }

   return $input.all();
   ```

3. **Neo4j: Create Paper**
   - Query:
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
       embedding: $embedding,
       created_at: datetime()
     })
     RETURN elementId(p) as paper_id
     ```
   - Parameters:
     ```json
     {
       "doi": "={{ $json.doi }}",
       "title": "={{ $json.title }}",
       "authors": "={{ $json.authors }}",
       "abstract": "={{ $json.abstract }}",
       "year": "={{ $json.year }}",
       "journal": "={{ $json.journal }}",
       "keywords": "={{ $json.keywords }}",
       "pdf_path": "={{ $json.pdf_path }}",
       "embedding": "={{ $json.embedding }}"
     }
     ```

4. **Respond to Webhook**
   ```json
   {
     "status": "success",
     "paper_id": "={{ $json.paper_id }}",
     "created_at": "={{ $now }}"
   }
   ```

---

## Workflow 2: Add Chunk with Embedding

**Endpoint**: `/webhook/papers/add-chunk`

**Method**: POST

**Purpose**: Add content chunk with vector embedding to paper

### Request Payload

```json
{
  "paper_id": "4:12345678-1234-5678-1234-567812345678",
  "chunk_id": "introduction-001",
  "text": "Active inference is a process of proactively refining...",
  "embedding": [0.234, -0.567, ...],  // 1536-dim
  "metadata": {
    "section": "Introduction",
    "page_range": [1, 3],
    "has_equations": false,
    "citations": ["Friston2010"],
    "token_count": 487
  }
}
```

### Response

```json
{
  "status": "success",
  "chunk_id": "introduction-001"
}
```

### n8n Workflow Configuration

**Nodes**:

1. **Webhook Trigger**
   - Method: POST
   - Path: `/papers/add-chunk`

2. **Function: Validate HMAC** (same as Workflow 1)

3. **Neo4j: Create Chunk + Relationship**
   - Query:
     ```cypher
     MATCH (p:Paper)
     WHERE elementId(p) = $paper_id
     CREATE (c:Chunk {
       chunk_id: $chunk_id,
       text: $text,
       embedding: $embedding,
       section: $section,
       page_range: $page_range,
       has_equations: $has_equations,
       citations: $citations,
       token_count: $token_count,
       created_at: datetime()
     })
     CREATE (p)-[:HAS_CHUNK]->(c)
     RETURN c.chunk_id as chunk_id
     ```
   - Parameters:
     ```json
     {
       "paper_id": "={{ $json.paper_id }}",
       "chunk_id": "={{ $json.chunk_id }}",
       "text": "={{ $json.text }}",
       "embedding": "={{ $json.embedding }}",
       "section": "={{ $json.metadata.section }}",
       "page_range": "={{ $json.metadata.page_range }}",
       "has_equations": "={{ $json.metadata.has_equations }}",
       "citations": "={{ $json.metadata.citations }}",
       "token_count": "={{ $json.metadata.token_count }}"
     }
     ```

4. **Respond to Webhook**
   ```json
   {
     "status": "success",
     "chunk_id": "={{ $json.chunk_id }}"
   }
   ```

---

## Workflow 3: Add Equation

**Endpoint**: `/webhook/papers/add-equation`

**Method**: POST

**Purpose**: Add extracted equation to paper

### Request Payload

```json
{
  "paper_id": "4:12345678-1234-5678-1234-567812345678",
  "number": "Eq 5",
  "latex": "F = D_{KL}[q(s) || p(o,s)]",
  "context": "The variational free energy is defined as...",
  "page": 4,
  "section": "Theoretical Background",
  "concept": "VFE"  // Optional - for cross-referencing
}
```

### Response

```json
{
  "status": "success",
  "equation_id": "5:87654321-4321-8765-4321-876543218765"
}
```

### n8n Workflow Configuration

**Nodes**:

1. **Webhook Trigger**
   - Method: POST
   - Path: `/papers/add-equation`

2. **Function: Validate HMAC**

3. **Neo4j: Create Equation + Relationship**
   - Query:
     ```cypher
     MATCH (p:Paper)
     WHERE elementId(p) = $paper_id
     CREATE (e:Equation {
       number: $number,
       latex: $latex,
       context: $context,
       page: $page,
       section: $section,
       concept: $concept,
       created_at: datetime()
     })
     CREATE (p)-[:DEFINES]->(e)
     RETURN elementId(e) as equation_id
     ```
   - Parameters:
     ```json
     {
       "paper_id": "={{ $json.paper_id }}",
       "number": "={{ $json.number }}",
       "latex": "={{ $json.latex }}",
       "context": "={{ $json.context }}",
       "page": "={{ $json.page }}",
       "section": "={{ $json.section }}",
       "concept": "={{ $json.concept }}"
     }
     ```

4. **Respond to Webhook**

---

## Workflow 4: Vector Similarity Search

**Endpoint**: `/webhook/papers/search-similar`

**Method**: POST

**Purpose**: RAG retrieval via vector similarity search

### Request Payload

```json
{
  "query_embedding": [0.345, -0.678, ...],  // 1536-dim
  "top_k": 5,
  "filters": {
    "year": 2025,
    "author": "Nehrer"  // Optional
  }
}
```

### Response

```json
{
  "results": [
    {
      "chunk_id": "theoretical-background-005",
      "text": "The Expected Free Energy (EFE) decomposes...",
      "similarity": 0.92,
      "metadata": {
        "paper": "Introducing ActiveInference.jl (2025)",
        "authors": ["Nehrer, S. W.", ...],
        "year": 2025,
        "section": "Theoretical Background",
        "page_range": [3, 4]
      }
    },
    ...
  ],
  "query_time_ms": 45
}
```

### n8n Workflow Configuration

**Nodes**:

1. **Webhook Trigger**
   - Method: POST
   - Path: `/papers/search-similar`

2. **Function: Validate HMAC**

3. **Neo4j: Vector Similarity Search**
   - Query:
     ```cypher
     CALL db.index.vector.queryNodes('chunk_embeddings', $top_k, $query_embedding)
     YIELD node, score
     MATCH (p:Paper)-[:HAS_CHUNK]->(node)
     WHERE ($year IS NULL OR p.year = $year)
       AND ($author IS NULL OR ANY(a IN p.authors WHERE a CONTAINS $author))
     RETURN {
       chunk_id: node.chunk_id,
       text: node.text,
       similarity: score,
       metadata: {
         paper: p.title + ' (' + toString(p.year) + ')',
         authors: p.authors,
         year: p.year,
         section: node.section,
         page_range: node.page_range
       }
     } as result
     ORDER BY score DESC
     LIMIT $top_k
     ```
   - Parameters:
     ```json
     {
       "query_embedding": "={{ $json.query_embedding }}",
       "top_k": "={{ $json.top_k }}",
       "year": "={{ $json.filters.year || null }}",
       "author": "={{ $json.filters.author || null }}"
     }
     ```

4. **Function: Format Results**
   ```javascript
   const startTime = Date.now();

   const results = $input.all().map(item => item.json.result);

   return {
     json: {
       results: results,
       query_time_ms: Date.now() - startTime
     }
   };
   ```

5. **Respond to Webhook**

---

## Workflow 5: Find Equations by Concept

**Endpoint**: `/webhook/papers/find-equation`

**Method**: POST

**Purpose**: Find all equations implementing a concept (e.g., VFE, EFE)

### Request Payload

```json
{
  "concept": "VFE",
  "paper_filter": "Nehrer"  // Optional
}
```

### Response

```json
{
  "equations": [
    {
      "equation": "F = D_{KL}[q(s) || p(o,s)]",
      "number": "Eq 5",
      "paper": "Introducing ActiveInference.jl (2025)",
      "context": "The variational free energy is defined as...",
      "page": 4
    },
    {
      "equation": "F_i = D_KL[q(μ_i) || p(μ_i | ...)]",
      "number": "Eq 3",
      "paper": "Thoughtseeds Framework (2025)",
      "context": "NP Free Energy Minimization...",
      "page": 8
    }
  ]
}
```

### n8n Workflow Configuration

**Nodes**:

1. **Webhook Trigger**

2. **Function: Validate HMAC**

3. **Neo4j: Find Equations by Concept**
   - Query:
     ```cypher
     MATCH (e:Equation)<-[:DEFINES]-(p:Paper)
     WHERE e.concept = $concept
       AND ($paper_filter IS NULL
            OR p.title CONTAINS $paper_filter
            OR ANY(a IN p.authors WHERE a CONTAINS $paper_filter))
     RETURN {
       equation: e.latex,
       number: e.number,
       paper: p.title + ' (' + toString(p.year) + ')',
       context: e.context,
       page: e.page
     } as result
     ORDER BY p.year DESC
     ```

4. **Function: Format Response**
   ```javascript
   return {
     json: {
       equations: $input.all().map(item => item.json.result)
     }
   };
   ```

5. **Respond to Webhook**

---

## Workflow 6: Cross-Reference Concept

**Endpoint**: `/webhook/papers/cross-reference`

**Method**: POST

**Purpose**: Find how different papers implement the same concept

### Request Payload

```json
{
  "concept": "Expected Free Energy"
}
```

### Response

```json
{
  "concept": "Expected Free Energy",
  "implementations": [
    {
      "paper": "Introducing ActiveInference.jl (2025)",
      "equations": [
        {
          "number": "Eq 17",
          "latex": "G(π, τ) = E_{q(o_{τ}|π)}[log q(s_{τ}|o_{τ}, π)]",
          "context": "Policy evaluation...",
          "page": 6
        }
      ]
    },
    {
      "paper": "Thoughtseeds Framework (2025)",
      "equations": [
        {
          "number": "Eq 24",
          "latex": "EFE = Epistemic + Pragmatic",
          "context": "Affordances...",
          "page": 15
        }
      ]
    }
  ]
}
```

### n8n Workflow Configuration

**Nodes**:

1. **Webhook Trigger**

2. **Function: Validate HMAC**

3. **Neo4j: Cross-Reference Query**
   - Query:
     ```cypher
     MATCH (e:Equation)<-[:DEFINES]-(p:Paper)
     WHERE e.concept = $concept
     RETURN {
       paper: p.title + ' (' + toString(p.year) + ')',
       equations: collect({
         number: e.number,
         latex: e.latex,
         context: e.context,
         page: e.page
       })
     } as implementation
     ORDER BY p.year DESC
     ```

4. **Function: Format Response**
   ```javascript
   return {
     json: {
       concept: $('Webhook').item.json.body.concept,
       implementations: $input.all().map(item => item.json.implementation)
     }
   };
   ```

5. **Respond to Webhook**

---

## Workflow 7: Get Paper by DOI

**Endpoint**: `/webhook/papers/get-paper`

**Method**: GET

**Purpose**: Retrieve full paper metadata by DOI

### Request

```
GET /webhook/papers/get-paper?doi=10.3390/e27010062
```

### Response

```json
{
  "paper": {
    "doi": "10.3390/e27010062",
    "title": "Introducing ActiveInference.jl...",
    "authors": [...],
    "year": 2025,
    "abstract": "...",
    "journal": "Entropy",
    "keywords": [...],
    "chunk_count": 45,
    "equation_count": 20
  }
}
```

### n8n Workflow Configuration

**Nodes**:

1. **Webhook Trigger** (GET)

2. **Neo4j: Get Paper + Stats**
   - Query:
     ```cypher
     MATCH (p:Paper {doi: $doi})
     OPTIONAL MATCH (p)-[:HAS_CHUNK]->(c:Chunk)
     OPTIONAL MATCH (p)-[:DEFINES]->(e:Equation)
     RETURN p {
       .*,
       chunk_count: count(DISTINCT c),
       equation_count: count(DISTINCT e)
     } as paper
     ```

3. **Respond to Webhook**

---

## Neo4j Setup Requirements

### Vector Index Creation

Run these queries in Neo4j before deploying workflows:

```cypher
// Create vector index for chunk embeddings
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

// Create index on DOI for fast lookup
CREATE INDEX paper_doi IF NOT EXISTS
FOR (p:Paper)
ON (p.doi);

// Create index on concept for equation searches
CREATE INDEX equation_concept IF NOT EXISTS
FOR (e:Equation)
ON (e.concept);
```

### Constraints

```cypher
// Ensure unique DOI
CREATE CONSTRAINT paper_doi_unique IF NOT EXISTS
FOR (p:Paper) REQUIRE p.doi IS UNIQUE;

// Ensure unique chunk IDs
CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE;
```

---

## Testing Workflows

### Test Workflow 1: Create Paper

```bash
curl -X POST https://72.61.78.89:5678/webhook/papers/create \
  -H "Content-Type: application/json" \
  -H "X-HMAC-Signature: [generated-signature]" \
  -d '{
    "doi": "10.1234/test",
    "title": "Test Paper",
    "authors": ["Test Author"],
    "abstract": "Test abstract",
    "year": 2025,
    "journal": "Test Journal",
    "keywords": ["test"],
    "pdf_path": "/test.pdf",
    "embedding": [0.1, 0.2, ...]
  }'
```

### Test Workflow 4: Vector Search

```bash
# First generate embedding for query
QUERY_EMBEDDING=$(python -c "
import asyncio
from litellm import aembedding

async def get_embedding():
    response = await aembedding(
        model='text-embedding-3-small',
        input=['What is active inference?']
    )
    print(response.data[0]['embedding'])

asyncio.run(get_embedding())
")

# Then search
curl -X POST https://72.61.78.89:5678/webhook/papers/search-similar \
  -H "Content-Type: application/json" \
  -d "{
    \"query_embedding\": $QUERY_EMBEDDING,
    \"top_k\": 5,
    \"filters\": {}
  }"
```

---

## Error Handling

All workflows should include error handling nodes:

**Function: Handle Errors**
```javascript
if ($input.all().length === 0) {
  return {
    json: {
      status: "error",
      message: "No results found",
      code: 404
    }
  };
}

if ($input.all()[0].error) {
  return {
    json: {
      status: "error",
      message: $input.all()[0].error,
      code: 500
    }
  };
}

return $input.all();
```

---

## Monitoring & Logging

Add logging nodes to track:
- Request count per endpoint
- Average query time
- Error rates
- Vector search performance

**Function: Log Metrics**
```javascript
const metrics = {
  endpoint: $('Webhook').item.node.name,
  timestamp: new Date().toISOString(),
  duration_ms: Date.now() - $vars.startTime,
  status: "success",
  result_count: $input.all().length
};

// Send to monitoring system (e.g., Prometheus, Grafana)
console.log(JSON.stringify(metrics));

return $input.all();
```

---

## Deployment Checklist

- [ ] Neo4j vector indexes created
- [ ] HMAC secret configured in n8n environment
- [ ] All 7 workflows imported and activated
- [ ] Test each endpoint with sample data
- [ ] Verify HMAC signature validation
- [ ] Monitor query performance
- [ ] Set up error alerting

---

**Author**: Mani Saint-Victor, MD
**Date**: 2026-01-03
**Related**: `/docs/pdf-ingestion-pipeline.md`, `/scripts/ingest_paper.py`
