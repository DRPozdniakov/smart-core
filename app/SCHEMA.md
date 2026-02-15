# Smart Core — Neo4j Schema & Data Structures

**Version:** 1.0
**Last Updated:** 2026-02-15
**Database:** smart-core (Neo4j 5.x)

---

## Table of Contents

1. [Overview](#overview)
2. [Node Types](#node-types)
3. [Relationship Types](#relationship-types)
4. [YAML Front Matter Specification](#yaml-front-matter-specification)
5. [MCP Tool Reference](#mcp-tool-reference)
6. [Indexes & Constraints](#indexes--constraints)
7. [Entity Naming Conventions](#entity-naming-conventions)
8. [Common Query Patterns](#common-query-patterns)

---

## Overview

Smart Core uses Neo4j as a knowledge graph to store business documentation with full traceability, entity extraction, and cross-document consistency management.

**Key Concepts:**
- **Documents** are markdown files with YAML front matter
- **Chunks** are document sections split by markdown headers, with semantic embeddings
- **Entities** are named business concepts extracted from documents
- **Tags** classify documents by topic
- **Commits** track changes git-style
- **MergeRequests** manage cross-document propagation

**Graph Model:**
```
Document 1:N Chunk (CONTAINS)
Chunk N:M Entity (HAS_ENTITY)
Document N:M Tag (HAS_TAG)
Document N:M Document (DEPENDS_ON, RESULTS_FROM)
Commit 1:N Change (INCLUDES)
MergeRequest N:M Document (TARGETS)
```

---

## Node Types

### 1. Document

Represents a markdown file in the project.

**Labels:** `Document`

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `doc_id` | String | Yes | Unique document ID | `"PRD-001"`, `"FM-001"` |
| `title` | String | Yes | Document title | `"Product Requirements Document"` |
| `path` | String | Yes (Unique) | Relative file path | `"docs_ver2\investor_package\PRD-001.md"` |
| `name` | String | Yes | Filename | `"PRD-001-Fers-Humanoid-Robot.md"` |
| `folder` | String | Yes | Parent directory | `"docs_ver2\investor_package"` |
| `version` | String | Yes | Semantic version | `"3.2"`, `"1.0"` |
| `status` | String | Yes | Document status | `"draft"`, `"active"`, `"archive"` |
| `domain` | String | Yes | Business domain | `"product"`, `"business"`, `"technical"`, `"finance"`, `"commercial"` |
| `phase` | String | Yes | Project phase | `"pre-seed"`, `"seed"`, `"round-a"`, `"round-b"` |
| `owner` | String | Yes | Document owner role | `"CTO"`, `"CFO"`, `"CEO"` |
| `deputies` | String[] | No | Deputy owners | `["CFO", "CEO"]` |
| `last_updated` | Date | Yes | Last edit date | `"2026-02-15"` |
| `tags_yaml` | String | Yes | Comma-separated tags | `"funding, seed, product"` |
| `chunk_count` | Integer | Yes | Number of chunks | `41` |
| `content_hash` | String | Yes | SHA256 hash (truncated) | `"9fdb4f2370bac2f5"` |
| `updated` | DateTime | Yes (Auto) | Last graph update | `2026-02-15T12:39:06.480Z` |
| `depends_on` | String[] | No | Upstream doc IDs | `["BRD-001", "FM-001"]` |
| `feeds_into` | String[] | No | Downstream doc IDs | `["ES-001", "PDT-001"]` |

**Indexes:**
- Primary: `path` (unique)
- Secondary: `doc_id`, `domain`, `phase`, `status`

**Example:**
```cypher
(:Document {
  doc_id: "PRD-001",
  title: "Fers Humanoid Robot - Product Requirements",
  path: "docs_ver2\\investor_package\\PRD-001-Fers-Humanoid-Robot.md",
  name: "PRD-001-Fers-Humanoid-Robot.md",
  folder: "docs_ver2\\investor_package",
  version: "3.2",
  status: "active",
  domain: "product",
  phase: "seed",
  owner: "CTO",
  deputies: ["CFO"],
  last_updated: "2026-02-08",
  tags_yaml: "product, technical, seed, phase-seed",
  chunk_count: 41,
  content_hash: "a3f2c9d8e1b4f7a6",
  updated: datetime("2026-02-15T12:39:06.480Z"),
  depends_on: ["BRD-001"],
  feeds_into: ["ES-001", "BP-001"]
})
```

---

### 2. Chunk

Represents a section of a document (split by markdown headers).

**Labels:** `Chunk`

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `id` | String | Yes (Unique) | Chunk ID (path::position) | `"docs_ver2\\PRD-001.md::15"` |
| `position` | Integer | Yes | Sequential position in doc | `15` |
| `section_header` | String | Yes | Markdown header text | `"3.1 Product Vision"` |
| `text` | String | Yes | Full chunk text | `"### 3.1 Product Vision\n\n..."` |
| `embedding` | Float[] | Yes | 384-dim semantic vector | `[0.0037, 0.0762, -0.0251, ...]` |

**Indexes:**
- Primary: `id` (unique)
- Vector: `embedding` (cosine similarity)

**Notes:**
- Embeddings generated using `sentence-transformers/all-MiniLM-L6-v2`
- Vector search uses cosine similarity with threshold > 0.7

**Example:**
```cypher
(:Chunk {
  id: "docs_ver2\\investor_package\\PRD-001.md::15",
  position: 15,
  section_header: "3.1 Product Vision",
  text: "### 3.1 Product Vision\n\nFers is an upper-body humanoid...",
  embedding: [0.003769, 0.076202, -0.025551, ...]  // 384 dimensions
})
```

---

### 3. Entity

Represents a named business concept extracted from documents.

**Labels:** `Entity`

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `name` | String | Yes (Unique) | Entity ID | `"Round-Seed"`, `"Prod-FersHumanoid"` |
| `type` | String | Yes | Entity category | `"FundingRound"`, `"Product"`, `"Metric"` |
| `value` | String | Yes | Current value | `"€1,000,000"`, `"Upper-body humanoid"` |
| `description` | String | No | Entity description | `"Seed funding round"` |

**Indexes:**
- Primary: `name` (unique)
- Secondary: `type`

**Entity Types:**

| Type | Example Names | Example Values |
|------|---------------|----------------|
| `FundingRound` | `Round-Seed`, `Round-A` | `"€1,000,000"`, `"€7-10M"` |
| `Product` | `Prod-FersHumanoid` | `"Upper-body humanoid robot"` |
| `Metric` | `Met-ARR`, `Met-CAC` | `"€2.1M by 2030"`, `"€15K"` |
| `Milestone` | `MS-Seed-MVP`, `MS-A-Production` | `"Q4 2026"`, `"Q3 2027"` |
| `Team` | `Team-CTO`, `Team-CFO` | `"30% equity"`, `"TBD equity"` |
| `Budget` | `Budget-Seed-Hardware` | `"€220,000, 22%"` |
| `Certification` | `Cert-CE`, `Cert-FoodGrade` | `"Q4 2028"`, `"IP67"` |

**Naming Convention:**
See [Entity Naming Conventions](#entity-naming-conventions) section.

**Example:**
```cypher
(:Entity {
  name: "Round-Seed",
  type: "FundingRound",
  value: "€1,000,000, 10 months, Q4 2026",
  description: "Seed funding round for prototype development"
})
```

---

### 4. Tag

Represents a classification label for documents.

**Labels:** `Tag`

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `name` | String | Yes (Unique) | Tag identifier (lowercase) | `"seed"`, `"funding"`, `"product"` |
| `description` | String | No | Tag description | `"Seed phase documents"` |
| `canonical_doc` | String | No | Authoritative doc for this tag | `"FM-001"` (for "funding") |

**Indexes:**
- Primary: `name` (unique)

**Common Tags:**
- **Phase:** `pre-seed`, `seed`, `round-a`, `round-b`
- **Domain:** `product`, `business`, `technical`, `finance`, `commercial`
- **Topic:** `funding`, `team`, `market`, `competitive`, `roadmap`
- **Status:** `confidential`, `draft`, `final`

**Example:**
```cypher
(:Tag {
  name: "seed",
  description: "Seed phase documents and planning",
  canonical_doc: "SP-001"
})
```

---

### 5. Commit

Git-style change record for audit trail.

**Labels:** `Commit`

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `commit_id` | String | Yes (Unique) | Commit ID (date-based) | `"c-2026-02-15-001"` |
| `date` | Date | Yes | Commit date | `"2026-02-15"` |
| `timestamp` | DateTime | Yes (Auto) | Exact timestamp | `2026-02-15T14:32:15.123Z` |
| `author` | String | Yes | Who made the change | `"CTO"`, `"CFO"`, `"Claude"` |
| `message` | String | Yes | Commit message | `"Update Seed round to €1.2M"` |
| `change_count` | Integer | Yes | Number of changes | `8` |

**Indexes:**
- Primary: `commit_id` (unique)
- Secondary: `author`, `date`

**Example:**
```cypher
(:Commit {
  commit_id: "c-2026-02-15-001",
  date: "2026-02-15",
  timestamp: datetime("2026-02-15T14:32:15.123Z"),
  author: "CTO",
  message: "Update Seed round to €1.2M across all investor docs",
  change_count: 8
})
```

---

### 6. Change

Individual text modification within a commit.

**Labels:** `Change`

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `change_id` | String | Yes (Unique) | Change ID | `"ch-2026-02-15-001-1"` |
| `doc_id` | String | Yes | Affected document | `"FM-001"` |
| `section` | String | Yes | Section name | `"5.2 Seed Phase Budget"` |
| `old_text` | String | Yes | Previous text | `"Seed Round: €1,000,000"` |
| `new_text` | String | Yes | New text | `"Seed Round: €1,200,000"` |

**Indexes:**
- Primary: `change_id` (unique)
- Secondary: `doc_id`

**Example:**
```cypher
(:Change {
  change_id: "ch-2026-02-15-001-1",
  doc_id: "FM-001",
  section: "5.2 Seed Phase Budget",
  old_text: "Seed Round: €1,000,000",
  new_text: "Seed Round: €1,200,000"
})
```

---

### 7. MergeRequest

Cross-document change propagation request.

**Labels:** `MergeRequest`

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `merge_id` | String | Yes (Unique) | Merge request ID | `"m-2026-02-15-001"` |
| `source_document` | String | Yes | Where change originated | `"FM-001"` |
| `affected_tag` | String | Yes | Entity/tag being changed | `"Round-Seed"` |
| `old_value` | String | Yes | Previous value | `"€1,000,000"` |
| `new_value` | String | Yes | New value | `"€1,200,000"` |
| `reason` | String | Yes | Why the change was made | `"Adjusted for market conditions"` |
| `status` | String | Yes | Request status | `"pending"`, `"approved"`, `"rejected"` |
| `created` | DateTime | Yes (Auto) | When created | `2026-02-15T14:32:15.123Z` |
| `approved_by` | String | No | Who approved | `"CTO"` |
| `approved_at` | DateTime | No | When approved | `2026-02-15T14:45:30.456Z` |

**Indexes:**
- Primary: `merge_id` (unique)
- Secondary: `status`, `source_document`

**Example:**
```cypher
(:MergeRequest {
  merge_id: "m-2026-02-15-001",
  source_document: "FM-001",
  affected_tag: "Round-Seed",
  old_value: "€1,000,000",
  new_value: "€1,200,000",
  reason: "Updated based on revised burn rate calculations",
  status: "pending",
  created: datetime("2026-02-15T14:32:15.123Z")
})
```

---

### 8. Phase

Project phase node for filtering.

**Labels:** `Phase`

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `name` | String | Yes (Unique) | Phase identifier | `"pre-seed"`, `"seed"`, `"round-a"`, `"round-b"` |

**Example:**
```cypher
(:Phase {name: "seed"})
```

---

### 9. Domain

Business domain node for filtering.

**Labels:** `Domain`

**Properties:**

| Property | Type | Required | Description | Example |
|----------|------|----------|-------------|---------|
| `name` | String | Yes (Unique) | Domain identifier | `"product"`, `"business"`, `"technical"`, `"finance"`, `"commercial"` |

**Example:**
```cypher
(:Domain {name: "product"})
```

---

## Relationship Types

### 1. CONTAINS

Document contains Chunks.

**Direction:** `(Document)-[:CONTAINS]->(Chunk)`
**Cardinality:** 1:N (one document, many chunks)

**Properties:** None

**Example:**
```cypher
(:Document {doc_id: "PRD-001"})-[:CONTAINS]->(:Chunk {position: 15})
```

---

### 2. BELONGS_TO

Chunk belongs to Document (inverse of CONTAINS).

**Direction:** `(Chunk)-[:BELONGS_TO]->(Document)`
**Cardinality:** N:1 (many chunks, one document)

**Properties:** None

**Example:**
```cypher
(:Chunk {id: "PRD-001::15"})-[:BELONGS_TO]->(:Document {doc_id: "PRD-001"})
```

---

### 3. HAS_ENTITY

Chunk/Document references an Entity.

**Direction:** `(Chunk|Document)-[:HAS_ENTITY]->(Entity)`
**Cardinality:** N:M (many chunks, many entities)

**Properties:**

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `context` | String | Surrounding text | `"The Seed round of €1M will fund..."` |

**Example:**
```cypher
(:Chunk {id: "FM-001::10"})-[:HAS_ENTITY {context: "Seed round of €1M"}]->(:Entity {name: "Round-Seed"})
```

---

### 4. HAS_TAG

Document has a Tag.

**Direction:** `(Document)-[:HAS_TAG]->(Tag)`
**Cardinality:** N:M (many documents, many tags)

**Properties:** None

**Example:**
```cypher
(:Document {doc_id: "FM-001"})-[:HAS_TAG]->(:Tag {name: "funding"})
```

---

### 5. DEPENDS_ON

Document depends on another document.

**Direction:** `(Document)-[:DEPENDS_ON]->(Document)`
**Cardinality:** N:M (many-to-many)

**Properties:** None

**Description:** Indicates logical dependency (e.g., Executive Summary depends on Financial Model).

**Example:**
```cypher
(:Document {doc_id: "ES-001"})-[:DEPENDS_ON]->(:Document {doc_id: "FM-001"})
```

---

### 6. RESULTS_FROM

Document results from another document (reverse dependency).

**Direction:** `(Document)-[:RESULTS_FROM]->(Document)`
**Cardinality:** N:M (many-to-many)

**Properties:** None

**Description:** Indicates downstream relationship (e.g., Pitch Deck results from Executive Summary).

**Example:**
```cypher
(:Document {doc_id: "PDT-001"})-[:RESULTS_FROM]->(:Document {doc_id: "ES-001"})
```

---

### 7. INCLUDES

Commit includes Changes.

**Direction:** `(Commit)-[:INCLUDES]->(Change)`
**Cardinality:** 1:N (one commit, many changes)

**Properties:** None

**Example:**
```cypher
(:Commit {commit_id: "c-2026-02-15-001"})-[:INCLUDES]->(:Change {change_id: "ch-2026-02-15-001-1"})
```

---

### 8. TARGETS

MergeRequest targets Documents.

**Direction:** `(MergeRequest)-[:TARGETS]->(Document)`
**Cardinality:** 1:N (one merge, many documents)

**Properties:** None

**Example:**
```cypher
(:MergeRequest {merge_id: "m-2026-02-15-001"})-[:TARGETS]->(:Document {doc_id: "ES-001"})
```

---

## YAML Front Matter Specification

All documents in `docs_ver2/` **MUST** include YAML front matter with these fields:

### Required Fields

```yaml
---
doc_id: "PRD-001"                           # Unique document ID (uppercase, hyphen-separated)
title: "Product Requirements Document"      # Human-readable title
version: "3.2"                              # Semantic version (major.minor)
last_updated: "2026-02-08"                  # Last edit date (YYYY-MM-DD)
status: "active"                            # draft | active | archive
domain: "product"                           # business | product | technical | finance | commercial
phase: "seed"                               # pre-seed | seed | round-a | round-b
owner: "CTO"                                # Primary document owner (role, not name)
---
```

### Optional Fields

```yaml
deputies: ["CFO", "CEO"]                    # Deputy owners (array of roles)
tags_yaml: ["product", "technical", "seed"] # Custom tags (array or comma-separated string)
depends_on: ["BRD-001", "FM-001"]          # Upstream document IDs
feeds_into: ["ES-001", "BP-001"]           # Downstream document IDs
confidential: true                          # Mark as confidential (default: false)
```

### Field Validation Rules

| Field | Type | Pattern | Example |
|-------|------|---------|---------|
| `doc_id` | String | `[A-Z]+-[0-9]{3}` | `PRD-001`, `FM-001` |
| `version` | String | `\d+\.\d+` | `1.0`, `3.2` |
| `last_updated` | Date | `YYYY-MM-DD` | `2026-02-15` |
| `status` | Enum | `draft\|active\|archive` | `active` |
| `domain` | Enum | See above | `product` |
| `phase` | Enum | See above | `seed` |
| `owner` | String | Role name | `CTO`, `CFO` |

### Example Front Matter

```yaml
---
doc_id: "PRD-001"
title: "Fers Humanoid Robot - Product Requirements"
version: "3.2"
last_updated: "2026-02-08"
status: "active"
domain: "product"
phase: "seed"
owner: "CTO"
deputies: ["CFO"]
tags_yaml: ["product", "technical", "seed", "phase-seed"]
depends_on: ["BRD-001"]
feeds_into: ["ES-001", "BP-001"]
---

# Product Requirements Document (PRD)

[Document content here...]
```

---

## MCP Tool Reference

Smart Core exposes these tools via the Model Context Protocol (MCP).

### Tool: `ping`

Check if Neo4j database is reachable.

**Parameters:** None

**Returns:**
```json
{
  "status": "ok",
  "database": "smart-core",
  "uri": "bolt://127.0.0.1:7687"
}
```

**Usage:**
```python
# ALWAYS call this first before any other MCP operations
result = mcp.ping()
if result["status"] != "ok":
    # Fall back to file-based operations
```

---

### Tool: `load_project`

Ingest/update markdown files into knowledge graph.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_path` | String | No | Auto-detect | Root project directory |
| `force_reload` | Boolean | No | `false` | Re-process all files even if unchanged |

**Returns:**
```json
{
  "documents_processed": 25,
  "documents": [
    {
      "path": "docs_ver2\\PRD-001.md",
      "status": "loaded",
      "chunks": 41,
      "sections": ["Executive Summary", "Product Overview", ...]
    }
  ],
  "relationships_created": 43
}
```

**Usage:**
```python
# Initial load
result = mcp.load_project()

# Force reload after major changes
result = mcp.load_project(force_reload=True)
```

**What It Does:**
1. Scans all `.md` files in `docs_ver2/`
2. Parses YAML front matter
3. Splits documents by markdown headers
4. Generates embeddings for each chunk
5. Creates Document, Chunk, Phase, Domain nodes
6. Creates CONTAINS, BELONGS_TO relationships

---

### Tool: `store_extraction`

Store extracted entities and tags for a document.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `document_path` | String | Yes | Relative path to document |
| `entities` | Array | Yes | List of entity objects |
| `tags` | Array | Yes | List of tag strings |

**Entity Object:**
```json
{
  "name": "Round-Seed",
  "type": "FundingRound",
  "value": "€1,000,000"
}
```

**Returns:**
```json
{
  "document": "docs_ver2\\investor_package\\FM-001.md",
  "entities_stored": 15,
  "tags_stored": 8
}
```

**Usage:**
```python
entities = [
    {"name": "Round-Seed", "type": "FundingRound", "value": "€1,000,000"},
    {"name": "Prod-FersHumanoid", "type": "Product", "value": "Upper-body humanoid"}
]
tags = ["funding", "seed", "product"]

result = mcp.store_extraction(
    document_path="docs_ver2/investor_package/FM-001.md",
    entities=entities,
    tags=tags
)
```

**What It Does:**
1. Creates Entity nodes (if not exist)
2. Creates Tag nodes (if not exist)
3. Creates HAS_ENTITY relationships
4. Creates HAS_TAG relationships

---

### Tool: `synchronize_project`

Detect drift between local files and knowledge graph.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_path` | String | No | Auto-detect | Root project directory |

**Returns:**
```json
{
  "summary": {
    "total_local": 25,
    "total_db": 25,
    "new": 0,
    "modified": 3,
    "deleted": 0,
    "unchanged": 22,
    "pending_merges": 2
  },
  "new_files": [],
  "modified_files": ["docs_ver2\\investor_package\\FM-001.md"],
  "deleted_files": [],
  "pending_merges": [
    {
      "merge_id": "m-2026-02-15-001",
      "affected_tag": "Round-Seed",
      "status": "pending"
    }
  ]
}
```

**Usage:**
```python
# Check sync status
result = mcp.synchronize_project()

if result["summary"]["modified"] > 0:
    # Re-load modified files
    mcp.load_project()
```

**What It Detects:**
- **New files:** Exist locally but not in graph
- **Modified files:** Hash mismatch between file and graph
- **Deleted files:** Exist in graph but not locally
- **Pending merges:** MergeRequests awaiting approval

---

### Tool: `knowledge_call`

Search knowledge graph using semantic similarity and/or graph traversal.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | String | Yes | — | Natural language query |
| `search_type` | Enum | No | `"hybrid"` | `"vector"` \| `"graph"` \| `"hybrid"` |
| `limit` | Integer | No | `10` | Max results (max: 100) |

**Search Types:**
- **vector:** Semantic search using embeddings (best for conceptual queries)
- **graph:** Traverse tags/entities (best for exact entity matches)
- **hybrid:** Both vector + graph (most comprehensive)

**Returns:**
```json
{
  "query": "Seed round funding",
  "search_type": "hybrid",
  "chunks": [
    {
      "doc": "docs_ver2\\investor_package\\FM-001.md",
      "section": "5.2 Seed Phase Budget",
      "text": "### 5.2 Seed Phase Budget...",
      "pos": 25,
      "score": 0.8551
    }
  ],
  "graph_results": {
    "tags": [
      {
        "tag": "seed",
        "documents": ["FM-001", "ES-001", "BP-001"]
      }
    ],
    "entities": [
      {
        "entity": "Round-Seed",
        "type": "FundingRound",
        "value": "€1,000,000",
        "documents": ["FM-001", "ES-001", "BP-001", "BRD-001"]
      }
    ]
  }
}
```

**Usage:**
```python
# Conceptual search
result = mcp.knowledge_call(
    query="What's the Seed round amount?",
    search_type="hybrid",
    limit=5
)

# Exact entity search
result = mcp.knowledge_call(
    query="Round-Seed",
    search_type="graph"
)
```

---

### Tool: `merge_report`

Create a change propagation request when an entity value changes.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_document` | String | Yes | Document where change originated |
| `affected_tag` | String | Yes | Entity/tag name being changed |
| `old_value` | String | Yes | Previous value |
| `new_value` | String | Yes | New value |
| `reason` | String | Yes | Why the change was made |

**Returns:**
```json
{
  "merge_id": "m-2026-02-15-001",
  "source_document": "FM-001",
  "affected_documents": [
    "ES-001",
    "BP-001",
    "BRD-001",
    "PDT-001"
  ],
  "status": "pending"
}
```

**Usage:**
```python
# After editing FM-001 and changing Seed round
result = mcp.merge_report(
    source_document="FM-001",
    affected_tag="Round-Seed",
    old_value="€1,000,000",
    new_value="€1,200,000",
    reason="Updated based on revised burn rate"
)

# Returns merge_id for approval
merge_id = result["merge_id"]
```

**What It Does:**
1. Creates MergeRequest node
2. Finds all documents with same entity
3. Creates TARGETS relationships
4. Returns list of affected documents
5. Waits for user approval

---

### Tool: `approve_merge`

Approve a pending merge request to propagate changes.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `merge_id` | String | Yes | Merge request ID from merge_report |

**Returns:**
```json
{
  "merge_id": "m-2026-02-15-001",
  "status": "approved",
  "approved_by": "CTO",
  "approved_at": "2026-02-15T14:45:30.456Z",
  "documents_to_update": [
    "ES-001",
    "BP-001",
    "BRD-001",
    "PDT-001"
  ]
}
```

**Usage:**
```python
# After user approves
result = mcp.approve_merge(merge_id="m-2026-02-15-001")

# Claude then updates all affected documents
for doc_id in result["documents_to_update"]:
    # Edit doc_id file to propagate change
    pass
```

**What It Does:**
1. Updates MergeRequest status to "approved"
2. Records approval metadata
3. Returns list of documents to update
4. Claude then performs actual file edits

---

### Tool: `commit_changes`

Record document changes in knowledge graph (git-style commit).

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `author` | String | Yes | Who made the change |
| `message` | String | Yes | Commit message |
| `changes` | Array | Yes | List of change objects |

**Change Object:**
```json
{
  "doc_id": "FM-001",
  "section": "5.2 Seed Phase Budget",
  "old_text": "Seed Round: €1,000,000",
  "new_text": "Seed Round: €1,200,000"
}
```

**Returns:**
```json
{
  "commit_id": "c-2026-02-15-001",
  "author": "CTO",
  "change_count": 8,
  "timestamp": "2026-02-15T14:32:15.123Z"
}
```

**Usage:**
```python
changes = [
    {
        "doc_id": "FM-001",
        "section": "5.2 Seed Phase Budget",
        "old_text": "Seed: €1,000,000",
        "new_text": "Seed: €1,200,000"
    },
    {
        "doc_id": "ES-001",
        "section": "Seed Round",
        "old_text": "€1M seed round",
        "new_text": "€1.2M seed round"
    }
]

result = mcp.commit_changes(
    author="CTO",
    message="Update Seed round to €1.2M across all investor docs",
    changes=changes
)
```

**What It Does:**
1. Creates Commit node
2. Creates Change nodes
3. Creates INCLUDES relationships
4. Records full audit trail

---

### Tool: `get_commit_history`

Query document change history.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `doc_id` | String | No | `null` | Filter by document ID |
| `author` | String | No | `null` | Filter by author |
| `limit` | Integer | No | `10` | Max commits to return |

**Returns:**
```json
{
  "commits": [
    {
      "commit_id": "c-2026-02-15-001",
      "date": "2026-02-15",
      "author": "CTO",
      "message": "Update Seed round to €1.2M",
      "change_count": 8,
      "changes": [
        {
          "section": "5.2 Seed Phase Budget",
          "doc_id": "FM-001",
          "old_text": "€1,000,000",
          "new_text": "€1,200,000"
        }
      ]
    }
  ]
}
```

**Usage:**
```python
# All recent commits
result = mcp.get_commit_history(limit=10)

# Commits for specific document
result = mcp.get_commit_history(doc_id="FM-001")

# Commits by specific author
result = mcp.get_commit_history(author="CTO", limit=5)
```

---

## Indexes & Constraints

### Unique Constraints

```cypher
CREATE CONSTRAINT document_path_unique IF NOT EXISTS
FOR (d:Document) REQUIRE d.path IS UNIQUE;

CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS
FOR (c:Chunk) REQUIRE c.id IS UNIQUE;

CREATE CONSTRAINT entity_name_unique IF NOT EXISTS
FOR (e:Entity) REQUIRE e.name IS UNIQUE;

CREATE CONSTRAINT tag_name_unique IF NOT EXISTS
FOR (t:Tag) REQUIRE t.name IS UNIQUE;

CREATE CONSTRAINT commit_id_unique IF NOT EXISTS
FOR (c:Commit) REQUIRE c.commit_id IS UNIQUE;

CREATE CONSTRAINT merge_id_unique IF NOT EXISTS
FOR (m:MergeRequest) REQUIRE m.merge_id IS UNIQUE;

CREATE CONSTRAINT phase_name_unique IF NOT EXISTS
FOR (p:Phase) REQUIRE p.name IS UNIQUE;

CREATE CONSTRAINT domain_name_unique IF NOT EXISTS
FOR (d:Domain) REQUIRE d.name IS UNIQUE;
```

### Indexes

```cypher
-- Document indexes
CREATE INDEX document_doc_id IF NOT EXISTS
FOR (d:Document) ON (d.doc_id);

CREATE INDEX document_domain IF NOT EXISTS
FOR (d:Document) ON (d.domain);

CREATE INDEX document_phase IF NOT EXISTS
FOR (d:Document) ON (d.phase);

CREATE INDEX document_status IF NOT EXISTS
FOR (d:Document) ON (d.status);

-- Entity indexes
CREATE INDEX entity_type IF NOT EXISTS
FOR (e:Entity) ON (e.type);

-- Commit indexes
CREATE INDEX commit_author IF NOT EXISTS
FOR (c:Commit) ON (c.author);

CREATE INDEX commit_date IF NOT EXISTS
FOR (c:Commit) ON (c.date);

-- MergeRequest indexes
CREATE INDEX merge_status IF NOT EXISTS
FOR (m:MergeRequest) ON (m.status);

CREATE INDEX merge_source IF NOT EXISTS
FOR (m:MergeRequest) ON (m.source_document);
```

### Vector Index (Embeddings)

```cypher
-- Vector similarity search on Chunk embeddings
CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 384,
    `vector.similarity_function`: 'cosine'
  }
};
```

---

## Entity Naming Conventions

All entities **MUST** follow standardized naming patterns for consistency across documents.

**Format:** `{Type}-{Name}`

**See:** [smart_core/app/Entity-Extraction-Guide.md](app/Entity-Extraction-Guide.md) for complete reference.

### Common Patterns

| Entity Type | Pattern | Examples |
|-------------|---------|----------|
| Funding Round | `Round-{Stage}` | `Round-Seed`, `Round-A`, `Round-B` |
| Product | `Prod-{Name}` | `Prod-FersHumanoid` |
| Certification | `Cert-{Type}` | `Cert-CE`, `Cert-FoodGrade` |
| Milestone | `MS-{Phase}-{Name}` | `MS-Seed-MVP`, `MS-A-Production` |
| Phase | `Phase-{Name}` | `Phase-Seed`, `Phase-RoundA` |
| Team Member | `Team-{Role}` | `Team-CTO`, `Team-CFO` |
| Budget Line | `Budget-{Phase}-{Category}` | `Budget-Seed-Hardware` |
| Metric | `Met-{Type}` | `Met-ARR`, `Met-CAC`, `Met-LTV` |

### Examples

✅ **CORRECT:**
```
Round-Seed: €1,000,000
MS-Seed-MVP: Q4 2026
Team-CTO: 30% equity
Budget-Seed-Hardware: €220,000
```

❌ **WRONG:**
```
Seed Round (inconsistent naming)
seed (lowercase, no prefix)
MVP Milestone (no prefix)
CTO (missing Team- prefix)
```

---

## Common Query Patterns

### Find All Documents by Tag

```cypher
MATCH (d:Document)-[:HAS_TAG]->(t:Tag {name: "seed"})
RETURN d.doc_id, d.title, d.path
ORDER BY d.last_updated DESC;
```

### Find All Occurrences of an Entity

```cypher
MATCH (e:Entity {name: "Round-Seed"})<-[:HAS_ENTITY]-(c:Chunk)-[:BELONGS_TO]->(d:Document)
RETURN d.doc_id, d.title, c.section_header, c.text
ORDER BY d.doc_id;
```

### Find Document Dependencies

```cypher
// Find all documents that depend on FM-001
MATCH (d:Document {doc_id: "FM-001"})<-[:DEPENDS_ON]-(downstream:Document)
RETURN downstream.doc_id, downstream.title;

// Find all documents that FM-001 depends on
MATCH (d:Document {doc_id: "FM-001"})-[:DEPENDS_ON]->(upstream:Document)
RETURN upstream.doc_id, upstream.title;
```

### Find Recent Changes to a Document

```cypher
MATCH (commit:Commit)-[:INCLUDES]->(change:Change {doc_id: "FM-001"})
RETURN commit.date, commit.author, commit.message,
       change.section, change.old_text, change.new_text
ORDER BY commit.date DESC
LIMIT 10;
```

### Find Pending Merge Requests

```cypher
MATCH (m:MergeRequest {status: "pending"})-[:TARGETS]->(d:Document)
RETURN m.merge_id, m.affected_tag, m.old_value, m.new_value,
       m.reason, collect(d.doc_id) as affected_docs
ORDER BY m.created DESC;
```

### Semantic Search (Vector Similarity)

```cypher
// Find chunks semantically similar to query
CALL db.index.vector.queryNodes('chunk_embedding', 10, $query_embedding)
YIELD node as chunk, score
MATCH (chunk)-[:BELONGS_TO]->(doc:Document)
WHERE score > 0.7
RETURN doc.doc_id, doc.title, chunk.section_header, chunk.text, score
ORDER BY score DESC;
```

### Find Cross-Document Entities (Consistency Check)

```cypher
// Find entities that appear in multiple documents
MATCH (e:Entity)<-[:HAS_ENTITY]-(c:Chunk)-[:BELONGS_TO]->(d:Document)
WITH e, collect(DISTINCT d.doc_id) as docs, count(DISTINCT d) as doc_count
WHERE doc_count > 1
RETURN e.name, e.type, e.value, docs, doc_count
ORDER BY doc_count DESC;
```

### Find Documents by Phase and Domain

```cypher
MATCH (d:Document)
WHERE d.phase = "seed" AND d.domain = "product"
RETURN d.doc_id, d.title, d.status
ORDER BY d.last_updated DESC;
```

---

## Schema Evolution

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-15 | Initial schema documentation |

### Planned Changes

- [ ] Add `User` node for multi-user collaboration
- [ ] Add `Session` node for tracking Claude sessions
- [ ] Add `AccessControl` relationships for RBAC
- [ ] Add `Notification` node for change alerts
- [ ] Add full-text search indexes
- [ ] Add temporal queries for time-travel

---

## References

- **Entity Extraction Guide:** [smart_core/app/Entity-Extraction-Guide.md](app/Entity-Extraction-Guide.md)
- **MCP Server Code:** [smart_core/app/smart-core-mcp/server.py](app/smart-core-mcp/server.py)
- **Feature Specification:** [smart_core/app/smart-core-mcp/mds/Feature-Specification.md](app/smart-core-mcp/mds/Feature-Specification.md)
- **README:** [smart_core/app/README.md](app/README.md)

---

*Smart Core Schema Documentation v1.0 | February 2026*
