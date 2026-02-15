# Smart Core

**Knowledge Graph Platform for Business Documentation with Claude Code Integration**

Smart Core is a Neo4j-powered knowledge graph that gives Claude Code persistent memory, cross-document consistency, and git-style change tracking for business documentation. Built specifically for startups managing complex investor packages where every number must align across 20+ documents.

---

## Why Smart Core?

**The Problem:** You're managing a startup investor package with a Business Plan, Financial Model, Executive Summary, PRD, BRD, Pitch Deck, and 15 other documents. When you change the Seed round from €1M to €1.2M in the Financial Model, you need to update it in **8 other documents**. Miss one, and your pitch falls apart.

**Traditional Approach:**
- ❌ Manual search & replace (error-prone, miss edge cases)
- ❌ Global find/replace (changes wrong instances)
- ❌ Version control (doesn't track semantic relationships)
- ❌ Multiple Claude sessions (each starts from scratch, no shared memory)

**Smart Core Approach:**
- ✅ **Knowledge graph** tracks every entity across all documents
- ✅ **One change** → automatic detection of all 8 affected documents
- ✅ **Approval workflow** → you control what propagates
- ✅ **Git-style audit trail** → who changed what, when, and why
- ✅ **Multi-user collaboration** → CTO, CFO, CEO work on same graph simultaneously
- ✅ **Semantic search** → Claude finds relevant context without exact keywords

---

## Quick Start (5 Minutes)

### Prerequisites

- **Neo4j Desktop** installed ([download](https://neo4j.com/download/))
- **Python 3.10+** with pip
- **NVIDIA GPU with CUDA** (required for embeddings)
- **Claude Code** (VS Code extension or CLI)

### 1. Setup Neo4j Database

```bash
# In Neo4j Desktop:
# 1. Create new database named "smart-core"
# 2. Set password (e.g., "65433456")
# 3. Start the database
# 4. Verify it's running at bolt://127.0.0.1:7687
```

### 2. Install Dependencies

```bash
cd smart_core/app/smart-core-mcp
pip install -r requirements.txt
```

**Key dependencies:**
- `neo4j>=5.0` - Database driver
- `sentence-transformers>=2.2.0` - Embeddings (requires GPU)
- `torch>=2.0.0` - Deep learning framework
- `fastmcp>=0.1.0` - MCP server framework

### 3. Configure MCP Server

Edit `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "smart-core": {
      "type": "stdio",
      "command": "python",
      "args": ["C:\\path\\to\\Fers\\smart_core\\app\\smart-core-mcp\\server.py"],
      "env": {
        "DB_URI": "bolt://127.0.0.1:7687",
        "DB_USER": "neo4j",
        "DB_PASSWORD": "65433456",
        "DB_NAME": "smart-core"
      }
    }
  }
}
```

### 4. Configure Document Path

Edit `smart_core/app/smart-core-mcp/config.json` to point to your documents folder:

```json
{
  "database": {
    "uri": "bolt://127.0.0.1:7687",
    "user": "neo4j",
    "password": "65433456",
    "name": "smart-core"
  },
  "embedding": {
    "model": "all-MiniLM-L6-v2",
    "dimensions": 384
  },
  "processing": {
    "chunk_max_tokens": 512,
    "project_docs_path": "../docs_ver2"
  }
}
```

**Important - Path is relative from server.py location:**
- `server.py` is at: `smart_core/app/smart-core-mcp/server.py`
- To reach `docs_ver2/` in project root, use: `"../docs_ver2"`
- The `../` goes up 3 levels: `smart-core-mcp/` → `app/` → `smart_core/` → project root

**Common path configurations:**

| Your Folder Structure | Path Value |
|----------------------|------------|
| `project/smart_core/app/smart-core-mcp/server.py`<br>`project/docs_ver2/` | `"../docs_ver2"` (default) |
| `project/smart_core/app/smart-core-mcp/server.py`<br>`project/documentation/` | `"../documentation"` |
| Absolute path (not recommended) | `"C:\\path\\to\\docs_ver2"` |

**Verify configuration:**
```bash
# From smart_core/app/smart-core-mcp/, this should list your docs:
ls ../docs_ver2
```

### 5. Test Connection

In Claude Code:

```
User: "Ping Neo4j"

Claude uses: mcp__smart-core__ping
Result: {"status": "ok", "database": "smart-core"}
```

### 6. Load Your Documents

```
User: "Load all documents from docs_ver2/"

Claude uses: mcp__smart-core__load_project
Result: 25 documents processed, 1,247 chunks created
```

**That's it!** Your knowledge graph is now populated and ready.

---

## Core Workflows

### Workflow 1: Search Across Documents

**Task:** "What's our current Seed round amount?"

**Traditional:** Open 8 files, search for "seed", read each context, hope you found them all.

**Smart Core:**
```
User: "What's our current Seed round amount?"

Claude:
  1. Calls mcp__smart-core__knowledge_call(query="Seed round funding")
  2. Returns: "Round-Seed: €1,000,000" found in 8 documents
  3. Shows all locations with context
```

**Result:** 1 query, all occurrences, guaranteed complete.

---

### Workflow 2: Update Values Across Documents

**Task:** Change Seed round from €1M to €1.2M everywhere.

**Traditional:** Find/replace in 8 files manually, pray you didn't break anything.

**Smart Core:**
```
User: "Change Seed round to €1.2M"

Claude:
  1. Calls knowledge_call("Round-Seed") → finds 8 documents
  2. Edits first file (e.g., Financial Model)
  3. Calls merge_report(
       source_document="FM-001",
       affected_tag="Round-Seed",
       old_value="€1,000,000",
       new_value="€1,200,000"
     )
  4. Returns: "8 documents affected: ES-001, BP-001, BRD-001..."
  5. Asks: "Approve propagation to 8 documents?"

User: "Yes, approve"

Claude:
  6. Calls approve_merge(merge_id="m-2026-02-15-001")
  7. Updates all 8 files
  8. Calls commit_changes(author="CTO", message="Update Seed to €1.2M")
  9. Calls load_project() to re-sync graph
```

**Result:** One change, 8 files updated, full audit trail, zero errors.

---

### Workflow 3: Cross-Document Consistency Check

**Task:** "Are all our Seed round references consistent?"

**Smart Core:**
```
User: "Check if Seed round is consistent across all docs"

Claude:
  1. Calls knowledge_call("Round-Seed", search_type="graph")
  2. Groups by value:
     - "€1,000,000" → 7 documents
     - "€1.2M" → 1 document (inconsistent!)
  3. Flags inconsistency
  4. Asks: "Update the 1 outlier to match the 7?"
```

**Result:** Automatic inconsistency detection you'd never find manually.

---

### Workflow 4: Change History Audit

**Task:** "Who changed the Seed round last month?"

**Smart Core:**
```
User: "Show Seed round change history"

Claude:
  1. Calls get_commit_history(limit=20)
  2. Filters for commits affecting "Round-Seed"
  3. Shows:
     - 2026-02-15, CTO: "€1M → €1.2M" (8 files)
     - 2026-02-08, CFO: "€800K → €1M" (8 files)
     - 2026-02-01, CEO: "€1.5M → €800K" (realigned budget)
```

**Result:** Full git-style audit trail for every business decision.

---

## MCP Tools Reference

Smart Core exposes 8 MCP tools to Claude Code:

| Tool | Purpose | When to Use |
|------|---------|-------------|
| [`ping`](#tool-ping) | Check Neo4j connection | **Always first** - before any other operation |
| [`load_project`](#tool-load_project) | Ingest/update documents | After creating/editing files |
| [`knowledge_call`](#tool-knowledge_call) | Search graph (semantic + graph) | Before answering questions, before editing |
| [`synchronize_project`](#tool-synchronize_project) | Detect file drift | Check if files changed outside Claude |
| [`store_extraction`](#tool-store_extraction) | Add entities/tags | After load_project for richer metadata |
| [`merge_report`](#tool-merge_report) | Propose cross-doc changes | After editing a canonical document |
| [`approve_merge`](#tool-approve_merge) | Approve propagation | After user reviews merge request |
| [`commit_changes`](#tool-commit_changes) | Record changes (audit trail) | After editing documents |
| [`get_commit_history`](#tool-get_commit_history) | Query change history | Review past changes |

**Quick Reference:** See [SCHEMA.md - MCP Tool Reference](SCHEMA.md#mcp-tool-reference) for detailed parameters and examples.

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code Sessions                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ CTO      │  │ CFO      │  │ CEO      │  │ Advisor  │    │
│  │ Session  │  │ Session  │  │ Session  │  │ Session  │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             │ MCP Protocol
                    ┌────────▼────────┐
                    │   Smart Core    │
                    │   MCP Server    │
                    │   (Python)      │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐         ┌─────▼─────┐        ┌────▼────┐
   │ Vector  │         │   Graph   │        │ Change  │
   │ Search  │         │ Traversal │        │ Tracking│
   │ (384d)  │         │ (Cypher)  │        │ (Audit) │
   └────┬────┘         └─────┬─────┘        └────┬────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │     Neo4j       │
                    │  (smart-core)   │
                    │                 │
                    │ 9 Node Types    │
                    │ 8 Relationships │
                    │ Vector Index    │
                    └─────────────────┘
```

### Data Flow

1. **Document Ingestion:**
   ```
   docs_ver2/*.md → load_project → Parse YAML → Split by headers
   → Generate embeddings (GPU) → Store in Neo4j
   ```

2. **Semantic Search:**
   ```
   Query → Embedding (GPU) → Vector search (cosine) + Graph traversal
   → Ranked results → Return to Claude
   ```

3. **Change Propagation:**
   ```
   Edit file → merge_report → Find all entity occurrences (graph)
   → Create MergeRequest → User approval → approve_merge
   → Claude edits all files → commit_changes → Audit trail
   ```

---

## Knowledge Graph Schema

### Node Types (9)

| Node | Purpose | Count | Example |
|------|---------|-------|---------|
| **Document** | Markdown file | 25 | `{doc_id: "FM-001", title: "Financial Model"}` |
| **Chunk** | Document section | ~1,200 | `{section: "5.2 Seed Budget", embedding: [0.003, ...]}` |
| **Entity** | Business concept | 0-200 | `{name: "Round-Seed", value: "€1M"}` |
| **Tag** | Classification | 0-100 | `{name: "funding", canonical_doc: "FM-001"}` |
| **Commit** | Change record | 0+ | `{author: "CTO", message: "Update Seed to €1.2M"}` |
| **Change** | Text modification | 0+ | `{doc_id: "FM-001", old: "€1M", new: "€1.2M"}` |
| **MergeRequest** | Pending update | 0+ | `{status: "pending", affected_docs: [8]}` |
| **Phase** | Project phase | 4 | `{name: "seed"}` |
| **Domain** | Business area | 5 | `{name: "product"}` |

### Relationship Types (8)

| Relationship | From → To | Meaning |
|--------------|-----------|---------|
| `CONTAINS` | Document → Chunk | Document contains sections |
| `BELONGS_TO` | Chunk → Document | Chunk belongs to document |
| `HAS_ENTITY` | Chunk → Entity | Chunk references entity |
| `HAS_TAG` | Document → Tag | Document has tag |
| `DEPENDS_ON` | Document → Document | Logical dependency |
| `RESULTS_FROM` | Document → Document | Downstream relationship |
| `INCLUDES` | Commit → Change | Commit includes changes |
| `TARGETS` | MergeRequest → Document | Merge targets documents |

**Detailed Schema:** See [SCHEMA.md](SCHEMA.md) for complete property specs, indexes, and query patterns.

---

## Performance Characteristics

### Benchmarks (February 2026)

Based on real-world usage with Fers project (25 documents, ~1,200 chunks):

| Operation | Cold Start | Warm | Notes |
|-----------|------------|------|-------|
| **ping** | <100ms | <50ms | Health check |
| **load_project** (25 docs) | 45-60s | 30-45s | Includes embedding generation |
| **knowledge_call** (hybrid) | 8-12s | 1-2s | First call loads model (~10s) |
| **knowledge_call** (graph only) | 200-500ms | 200-500ms | No embedding needed |
| **synchronize_project** | 1-2s | 1-2s | File hash comparison |
| **merge_report** | 500ms | 500ms | Graph query |
| **commit_changes** | 200ms | 200ms | Node creation |

**Hardware:** NVIDIA RTX 3060, 16GB RAM, SSD
**Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)

### Optimization Tips

1. **First `knowledge_call` is slow (8-12s)** - model loads into GPU memory
   - Subsequent calls are fast (1-2s)
   - This is normal and only happens once per session

2. **`load_project` takes time** - it's doing a lot:
   - Reading 25 files
   - Parsing YAML + markdown
   - Generating 1,200 embeddings (GPU)
   - Creating ~1,500 nodes + relationships
   - **45s for 25 docs is good performance**

3. **Use `graph` search when possible:**
   - `search_type="graph"` skips embeddings (200ms vs 1-2s)
   - Use for exact entity lookups: `"Round-Seed"`, `"Team-CTO"`
   - Use `hybrid` for natural language: `"What's our seed funding?"`

4. **`force_reload=False` (default) is smart:**
   - Only re-processes changed files
   - Uses content hash to detect changes
   - Saves 30-40s on unchanged projects

**Performance Details:** See [research/Smart-Core-Performance-Comparison-Feb-2026.md](research/Smart-Core-Performance-Comparison-Feb-2026.md)

---

## Document Requirements

Smart Core works with **markdown files** that follow this structure:

### Required YAML Front Matter

```yaml
---
doc_id: "FM-001"                    # Unique ID (uppercase, e.g., "PRD-001")
title: "Financial Model"            # Human-readable title
version: "3.2"                      # Semantic version
last_updated: "2026-02-15"          # Date (YYYY-MM-DD)
status: "active"                    # draft | active | archive
domain: "finance"                   # business | product | technical | finance | commercial
phase: "seed"                       # pre-seed | seed | round-a | round-b
owner: "CFO"                        # Role (not person name)
---

# Document Title

[Content here...]
```

### Optional Front Matter

```yaml
deputies: ["CTO", "CEO"]            # Deputy owners
tags_yaml: ["funding", "seed"]      # Custom tags
depends_on: ["BRD-001"]            # Upstream docs
feeds_into: ["ES-001", "PDT-001"]  # Downstream docs
confidential: true                  # Mark as confidential
```

### Markdown Structure

Smart Core splits documents **by headers** into chunks:

```markdown
# Main Title            → Chunk 0 (preamble)

## Section 1            → Chunk 1
Content here...

### 1.1 Subsection      → Chunk 2
More content...

## Section 2            → Chunk 3
Content here...
```

Each chunk gets:
- 384-dimensional semantic embedding
- Section header as metadata
- Position number (for ordering)

**Best practices:**
- Use descriptive headers (not just "Overview" - use "Financial Overview")
- Keep sections focused (easier to find via search)
- Update `last_updated` when editing

**Full Spec:** See [SCHEMA.md - YAML Front Matter](SCHEMA.md#yaml-front-matter-specification)

---

## Entity Naming Conventions

Entities must follow standardized patterns for cross-document consistency:

### Pattern: `{Type}-{Name}`

| Type | Pattern | Examples |
|------|---------|----------|
| **Funding** | `Round-{Stage}` | `Round-Seed`, `Round-A`, `Round-B` |
| **Product** | `Prod-{Name}` | `Prod-FersHumanoid` |
| **Milestone** | `MS-{Phase}-{Name}` | `MS-Seed-MVP`, `MS-A-Production` |
| **Team** | `Team-{Role}` | `Team-CTO`, `Team-CFO` |
| **Budget** | `Budget-{Phase}-{Category}` | `Budget-Seed-Hardware` |
| **Metric** | `Met-{Type}` | `Met-ARR`, `Met-CAC`, `Met-LTV` |
| **Phase** | `Phase-{Name}` | `Phase-Seed`, `Phase-RoundA` |

### Why It Matters

**Same entity = same name** across all documents.

❌ **WRONG:** Different names for the same thing
```
Financial Model: "Seed Round: €1M"
Business Plan: "Seed Funding: €1,000,000"
Executive Summary: "seed round €1M"
```

✅ **CORRECT:** Standardized entity name
```
All docs: "Round-Seed: €1,000,000"
Entity name: "Round-Seed"
```

**Now Claude can:**
- Find all 8 occurrences with one query
- Detect inconsistencies automatically
- Propagate changes correctly

**Complete Guide:** See [app/Entity-Extraction-Guide.md](app/Entity-Extraction-Guide.md)

---

## Common Issues & Troubleshooting

### Issue: `ping` returns connection error

**Symptoms:**
```
{"status": "error", "message": "Connection refused"}
```

**Solutions:**
1. Check Neo4j Desktop - is database running?
2. Verify connection details in `.mcp.json`:
   - URI: `bolt://127.0.0.1:7687`
   - Password matches Neo4j database
   - Database name: `smart-core`
3. Test connection manually:
   ```bash
   python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=('neo4j', 'yourpassword')); driver.verify_connectivity(); print('OK')"
   ```

---

### Issue: `load_project` fails with "docs directory not found"

**Symptoms:**
```
load_project → Error: Docs directory not found
```

**Root Cause:** Incorrect `project_docs_path` in `config.json`.

**Solutions:**
1. **Check path is relative from server.py location:**
   ```bash
   # If server.py is at: smart_core/app/smart-core-mcp/server.py
   # And docs are at: docs_ver2/
   # Path should be: "../docs_ver2"
   ```

2. **Verify with ls command:**
   ```bash
   cd smart_core/app/smart-core-mcp
   ls ../docs_ver2  # Should list your documents
   ```

3. **Common mistakes:**
   - ❌ `"docs_ver2"` (missing ../)
   - ❌ `"../../../docs_ver2"` (too many levels)
   - ❌ Absolute path with wrong drive letter
   - ✅ `"../docs_ver2"` (correct for default structure)

4. **After fixing config.json, restart MCP server:**
   - In Claude Code: Reload window or restart VS Code
   - MCP server caches configuration on startup

---

### Issue: First `knowledge_call` takes 10+ seconds

**Symptoms:**
```
knowledge_call("seed funding") → 12 seconds
knowledge_call("team equity") → 1.5 seconds (fast!)
```

**Explanation:** This is **normal and expected**.
- First call loads embedding model into GPU (~10s)
- Model stays in memory for subsequent calls (1-2s)
- Only happens once per MCP server session

**Not an issue - working as designed.**

---

### Issue: `load_project` shows 46 "deleted" files

**Symptoms:**
```
synchronize_project → 46 deleted files, but files exist!
```

**Root Cause:** Path normalization bug in MCP server.
- Graph stores: `docs_ver2\file.md`
- MCP scans: `..\docs_ver2\file.md`
- String comparison fails → false "deleted" alert

**Solution (done February 2026):**
1. Wipe graph: `MATCH (n) DETACH DELETE n`
2. Re-ingest: `load_project(force_reload=True)`
3. Paths now consistent

**Future fix:** Update `synchronize_project` to normalize paths before comparison.

---

### Issue: Out of memory during `load_project`

**Symptoms:**
```
CUDA out of memory error during embedding generation
```

**Solutions:**
1. **Free GPU memory:**
   ```bash
   # Close other GPU apps (games, ML training, etc.)
   nvidia-smi  # Check GPU usage
   ```

2. **Reduce batch size** (edit `server.py`):
   ```python
   # Default: 32 chunks per batch
   BATCH_SIZE = 16  # or 8 for low-memory GPUs
   ```

3. **Use smaller model** (edit `server.py`):
   ```python
   # Default: all-MiniLM-L6-v2 (384d, ~200MB)
   # Alternative: all-MiniLM-L12-v2 (384d, ~120MB) - slightly less accurate
   MODEL_NAME = "sentence-transformers/all-MiniLM-L12-v2"
   ```

---

### Issue: Entities not found in `knowledge_call`

**Symptoms:**
```
knowledge_call("Round-Seed") → 0 results
But Round-Seed exists in documents!
```

**Root Cause:** Entity nodes not created yet.

**Solution:**
```
1. load_project() → Creates Document + Chunk nodes
2. store_extraction() → Creates Entity + Tag nodes ← YOU ARE HERE
```

**`load_project` does NOT create Entity nodes** - only Document/Chunk.

To populate entities:
```
User: "Extract entities from all documents"

Claude:
  For each document:
    1. Read document
    2. Extract entities (Round-Seed, Team-CTO, etc.)
    3. Call store_extraction(document_path, entities, tags)
```

**Or use graph search only:**
```
knowledge_call("Seed round funding", search_type="graph")
→ Searches tags/metadata instead of entities
```

---

## File Structure

```
smart_core/
├── README.md                           # This file
├── SCHEMA.md                           # Complete schema reference
├── LICENSE                             # License
├── architecture.html                   # Visual architecture diagram
├── app/
│   ├── README.md                       # Old README (deprecated)
│   ├── Entity-Extraction-Guide.md      # Entity naming conventions
│   └── smart-core-mcp/
│       ├── server.py                   # MCP server (main entry point)
│       ├── requirements.txt            # Python dependencies
│       ├── config.json                 # Server config (optional)
│       └── mds/
│           └── Feature-Specification.md # Original design spec
├── research/
│   ├── Smart-Core-Performance-Comparison-Feb-2026.md
│   ├── Smart-Core-Validation-Summary.md
│   ├── Smart-Core-Performance-Experiment.md
│   ├── Robot-Price-Change-Experiment.md
│   ├── LESSONS-LEARNED.md
│   └── Cypher_Cheatsheet.md
└── [other research files]
```

**Key Files:**
- **[README.md](README.md)** ← You are here - Start here
- **[SCHEMA.md](SCHEMA.md)** - Complete schema, all node types, relationships, MCP tools
- **[app/Entity-Extraction-Guide.md](app/Entity-Extraction-Guide.md)** - Entity naming rules
- **[app/smart-core-mcp/server.py](app/smart-core-mcp/server.py)** - MCP server implementation

---

## Use Cases

### 1. Startup Investor Package Management

**Scenario:** Preparing for Seed round with 15+ interconnected documents.

**Smart Core Benefits:**
- **Cross-document consistency:** Change Seed amount once, propagate to 8 docs automatically
- **Audit trail:** Track every decision, review what changed before investor meetings
- **Multi-user collaboration:** CTO writes PRD, CFO updates financials, CEO drafts pitch - all in sync
- **Semantic search:** "What's our customer acquisition cost?" → finds CAC mentions across all docs

**Real Example (Fers):**
- 25 documents (PRD, BRD, Business Plan, Financial Model, Pitch Deck, phase plans...)
- 200+ entities (funding rounds, metrics, milestones, team, budget lines)
- 1,200+ chunks with semantic embeddings
- Full consistency maintained through 3 funding phases

---

### 2. Multi-User Business Documentation

**Scenario:** CTO, CFO, and CEO working simultaneously on fundraising materials.

**Traditional Approach:**
- Email drafts back and forth
- Merge conflicts in Google Docs
- "What's the latest version?" confusion
- Numbers get out of sync

**Smart Core Approach:**
- All three use separate Claude Code sessions
- All sessions connect to same Neo4j graph
- CTO updates product specs → CFO sees in financial model
- CFO changes budget → CEO sees in executive summary
- Automatic conflict detection if both edit same entity

**Status:** ⚠️ Multi-user currently requires manual coordination
**Roadmap:** Auto-sync and conflict resolution (Q2 2026)

---

### 3. Consulting Deliverables

**Scenario:** Team of consultants producing 10-document client deliverable.

**Smart Core Benefits:**
- Tag documents by workstream, phase, client
- Track who wrote what (attribution)
- Ensure recommendations align across documents
- Generate final export package with guaranteed consistency

---

## System Requirements

### Required

| Component | Requirement | Why |
|-----------|-------------|-----|
| **Neo4j Desktop** | 5.x (Community or Enterprise) | Knowledge graph database |
| **Python** | 3.10 - 3.12 | MCP server runtime |
| **NVIDIA GPU** | CUDA 11.x or 12.x | Embedding generation (GPU-only) |
| **RAM** | 8GB+ | Model + database overhead |
| **Storage** | 2GB+ free | Database + model cache |

### GPU Requirement Explained

**Why GPU-only?**
- Embedding model (`sentence-transformers/all-MiniLM-L6-v2`) requires CUDA
- CPU mode: 60s per document (unusably slow)
- GPU mode: 2s per document (45s for 25 docs)

**What if I don't have GPU?**
- Option 1: Use cloud GPU (AWS g4dn.xlarge ~$0.50/hr)
- Option 2: Use `search_type="graph"` only (no embeddings, no GPU needed)
- Option 3: Use pre-computed embeddings (TODO: not implemented yet)

**Verified GPUs:**
- ✅ NVIDIA RTX 3060 (12GB VRAM) - recommended
- ✅ NVIDIA GTX 1660 Ti (6GB VRAM) - works
- ❌ AMD GPUs - not supported (no CUDA)
- ❌ CPU-only - too slow (not practical)

---

## Development Status

**Current Version:** Alpha 1.0 (February 2026)

**Production Ready For:**
- ✅ Single-user knowledge graph
- ✅ Cross-document consistency tracking
- ✅ Semantic + graph search
- ✅ Git-style change history
- ✅ Merge request workflow

**Not Ready For:**
- ⚠️ Multi-user with auto-sync (requires manual coordination)
- ⚠️ Role-based access control (all users see all data)
- ⚠️ Real-time notifications (no push alerts)
- ⚠️ Web UI (command-line only via Claude Code)

**Known Limitations:**
1. **Path normalization bug** in `synchronize_project` (fixed manually, needs code fix)
2. **No auto-cleanup** of deleted files from graph (manual Cypher query needed)
3. **First `knowledge_call` slow** (10s model load - unavoidable with current architecture)
4. **Single project only** (no multi-tenant support yet)

---

## Roadmap

### Q1 2026 (Done)

- [x] Core knowledge graph schema
- [x] MCP server with 8 tools
- [x] Document ingestion (YAML + markdown)
- [x] Semantic search (vector embeddings)
- [x] Entity extraction framework
- [x] Merge request workflow
- [x] Change history (git-style commits)
- [x] Performance optimization (45s for 25 docs)
- [x] Production deployment (Fers project)

### Q2 2026 (Planned)

- [ ] **Multi-user coordination** - Real-time sync between Claude sessions
- [ ] **Path normalization fix** - Auto-cleanup of deleted files
- [ ] **Web dashboard** - View graph without Claude Code
- [ ] **Pre-computed embeddings** - Support CPU-only mode
- [ ] **Entity auto-extraction** - AI-powered entity detection

### Q3 2026 (Future)

- [ ] **Role-based access control** - Owner/deputy/contractor/advisor/investor tiers
- [ ] **Multi-project support** - Manage multiple companies in one graph
- [ ] **Real-time notifications** - Push alerts on changes
- [ ] **API gateway** - REST API for external integrations
- [ ] **Export tools** - Generate PDFs, presentations, data rooms

### Long-Term Vision

- **Business CI/CD platform** - Like GitHub for business docs
- **Plugin architecture** - Custom instruments (issue tracker, roadmap generator, etc.)
- **Enterprise features** - SSO, audit logs, compliance
- **SaaS offering** - Hosted Smart Core for teams

---

## Contributing

Smart Core is **open source** under the MIT License.

**Interested in contributing?**
- Review [research/Smart-Core-Usage-LESSONS-LEARNED.md](research/Smart-Core-Usage-LESSONS-LEARNED.md) for design rationale
- Check [app/SCHEMA.md](app/SCHEMA.md) for data model
- Read performance experiments in `research/`

**How to contribute:**
- Open a GitHub issue for bugs or feature requests
- Submit pull requests for improvements
- Share your use cases and experiences

---

## License

**MIT License** - See [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Smart Core Contributors

---

## Resources

### Documentation

- **[SCHEMA.md](SCHEMA.md)** - Complete schema reference (node types, relationships, MCP tools)
- **[app/Entity-Extraction-Guide.md](app/Entity-Extraction-Guide.md)** - Entity naming conventions
- **[app/smart-core-mcp/mds/Feature-Specification.md](app/smart-core-mcp/mds/Feature-Specification.md)** - Original design spec

### Research & Validation

- **[research/Smart-Core-Performance-Comparison-Feb-2026.md](research/Smart-Core-Performance-Comparison-Feb-2026.md)** - Performance benchmarks
- **[research/Smart-Core-Validation-Summary.md](research/Smart-Core-Validation-Summary.md)** - Validation results
- **[research/Smart-Core-Usage-LESSONS-LEARNED.md](research/Smart-Core-Usage-LESSONS-LEARNED.md)** - Design decisions and lessons learned

### External Resources

- **Neo4j Documentation:** https://neo4j.com/docs/
- **MCP Specification:** https://github.com/anthropics/mcp
- **Sentence Transformers:** https://www.sbert.net/
- **Claude Code:** https://claude.ai/code

---

## Support

**Questions? Issues?**

1. Check [Troubleshooting](#common-issues--troubleshooting) section
2. Review [research/LESSONS-LEARNED.md](research/LESSONS-LEARNED.md)
3. Search existing GitHub issues (when open-sourced)
4. Ask in Fers team chat

**Performance concerns?**
- See [Performance Characteristics](#performance-characteristics)
- Review [research/Smart-Core-Performance-Comparison-Feb-2026.md](research/Smart-Core-Performance-Comparison-Feb-2026.md)

---

**Smart Core** - Knowledge graph platform for business documentation
**Version:** Alpha 1.0 | **Last Updated:** February 2026 | **License:** Proprietary (internal)
