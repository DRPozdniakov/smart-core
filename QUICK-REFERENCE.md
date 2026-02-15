# Smart Core — Quick Reference Card

**One-page cheat sheet for common operations**

---

## MCP Tools (8)

| Tool | Command | Purpose |
|------|---------|---------|
| **ping** | `mcp__smart-core__ping()` | Check Neo4j connection (ALWAYS FIRST) |
| **load_project** | `mcp__smart-core__load_project(force_reload=False)` | Ingest/update documents |
| **knowledge_call** | `mcp__smart-core__knowledge_call(query, search_type="hybrid", limit=10)` | Search graph |
| **synchronize** | `mcp__smart-core__synchronize_project()` | Check file drift |
| **store_extraction** | `mcp__smart-core__store_extraction(doc_path, entities, tags)` | Add metadata |
| **merge_report** | `mcp__smart-core__merge_report(source, tag, old, new, reason)` | Propose changes |
| **approve_merge** | `mcp__smart-core__approve_merge(merge_id)` | Approve propagation |
| **commit_changes** | `mcp__smart-core__commit_changes(author, message, changes)` | Record audit trail |
| **get_history** | `mcp__smart-core__get_commit_history(doc_id=None, author=None, limit=10)` | Query changes |

---

## Common Workflows

### 1. Initial Setup
```
1. ping() → verify Neo4j connection
2. load_project() → ingest all documents (45s for 25 docs)
3. knowledge_call("test query") → verify search works (first call: 10s)
```

### 2. Search for Information
```
# Semantic search (natural language)
knowledge_call("What's our Seed round?", search_type="hybrid")

# Exact entity search (faster)
knowledge_call("Round-Seed", search_type="graph")

# Vector only (conceptual)
knowledge_call("customer acquisition strategy", search_type="vector")
```

### 3. Update Cross-Document Value
```
1. knowledge_call("Round-Seed") → find all occurrences
2. Edit first file (canonical source)
3. merge_report(source="FM-001", tag="Round-Seed", old="€1M", new="€1.2M", reason="...")
4. Ask user: "Approve propagation to 8 docs?"
5. approve_merge(merge_id="m-2026-02-15-001")
6. Edit all 8 files
7. commit_changes(author="CTO", message="Update Seed to €1.2M", changes=[...])
8. load_project() → re-sync graph
```

### 4. Check Consistency
```
1. knowledge_call("Round-Seed", search_type="graph")
2. Group results by value
3. If multiple values found → flag inconsistency
4. Ask user which value is correct
5. Use merge_report workflow to fix
```

### 5. Review Change History
```
# All recent changes
get_commit_history(limit=10)

# Changes to specific document
get_commit_history(doc_id="FM-001")

# Changes by specific person
get_commit_history(author="CTO", limit=5)
```

---

## Search Types

| Type | Speed | Use When | Example |
|------|-------|----------|---------|
| **hybrid** | 1-2s | Natural language questions | `"What's our seed funding?"` |
| **graph** | 200ms | Exact entity lookups | `"Round-Seed"`, `"Team-CTO"` |
| **vector** | 1-2s | Conceptual/semantic search | `"customer acquisition cost"` |

**Tip:** Use `graph` when you know the exact entity name (10x faster).

---

## Entity Naming Patterns

| Type | Pattern | Example |
|------|---------|---------|
| Funding | `Round-{Stage}` | `Round-Seed`, `Round-A` |
| Product | `Prod-{Name}` | `Prod-FersHumanoid` |
| Milestone | `MS-{Phase}-{Name}` | `MS-Seed-MVP` |
| Team | `Team-{Role}` | `Team-CTO`, `Team-CFO` |
| Budget | `Budget-{Phase}-{Category}` | `Budget-Seed-Hardware` |
| Metric | `Met-{Type}` | `Met-ARR`, `Met-CAC` |
| Phase | `Phase-{Name}` | `Phase-Seed` |

**Rule:** Same entity = same name across ALL documents.

---

## YAML Front Matter (Required)

```yaml
---
doc_id: "FM-001"                    # Unique ID (e.g., "PRD-001")
title: "Financial Model"            # Human-readable title
version: "3.2"                      # Semantic version
last_updated: "2026-02-15"          # Date (YYYY-MM-DD)
status: "active"                    # draft | active | archive
domain: "finance"                   # business|product|technical|finance|commercial
phase: "seed"                       # pre-seed|seed|round-a|round-b
owner: "CFO"                        # Role (not name)
---
```

**Optional:** `deputies`, `tags_yaml`, `depends_on`, `feeds_into`, `confidential`

---

## Node Types (9)

| Node | What | Count |
|------|------|-------|
| **Document** | Markdown file | 25 |
| **Chunk** | Document section (by header) | ~1,200 |
| **Entity** | Business concept (e.g., Round-Seed) | 0-200 |
| **Tag** | Classification label | 0-100 |
| **Commit** | Change record | 0+ |
| **Change** | Text modification | 0+ |
| **MergeRequest** | Pending propagation | 0+ |
| **Phase** | Project phase | 4 |
| **Domain** | Business area | 5 |

---

## Relationship Types (8)

| Relationship | From → To | Meaning |
|--------------|-----------|---------|
| `CONTAINS` | Document → Chunk | Doc contains sections |
| `BELONGS_TO` | Chunk → Document | Section belongs to doc |
| `HAS_ENTITY` | Chunk → Entity | Section references entity |
| `HAS_TAG` | Document → Tag | Doc has tag |
| `DEPENDS_ON` | Document → Document | Logical dependency |
| `RESULTS_FROM` | Document → Document | Downstream relationship |
| `INCLUDES` | Commit → Change | Commit includes changes |
| `TARGETS` | MergeRequest → Document | Merge targets docs |

---

## Performance (Feb 2026)

| Operation | Time | Notes |
|-----------|------|-------|
| ping | <100ms | Health check |
| load_project (25 docs) | 45-60s | Includes embeddings |
| knowledge_call (first) | 8-12s | Loads model into GPU |
| knowledge_call (warm) | 1-2s | Model already loaded |
| knowledge_call (graph) | 200ms | No embeddings |
| synchronize_project | 1-2s | File hash check |
| merge_report | 500ms | Graph query |
| commit_changes | 200ms | Node creation |

**Hardware:** RTX 3060, 16GB RAM, SSD

---

## Useful Cypher Queries

### Find all documents with tag
```cypher
MATCH (d:Document)-[:HAS_TAG]->(t:Tag {name: "seed"})
RETURN d.doc_id, d.title
ORDER BY d.last_updated DESC;
```

### Find all entity occurrences
```cypher
MATCH (e:Entity {name: "Round-Seed"})<-[:HAS_ENTITY]-(c:Chunk)-[:BELONGS_TO]->(d:Document)
RETURN d.doc_id, c.section_header, c.text
ORDER BY d.doc_id;
```

### Find cross-document entities
```cypher
MATCH (e:Entity)<-[:HAS_ENTITY]-(c:Chunk)-[:BELONGS_TO]->(d:Document)
WITH e, collect(DISTINCT d.doc_id) as docs, count(DISTINCT d) as doc_count
WHERE doc_count > 1
RETURN e.name, e.value, docs, doc_count
ORDER BY doc_count DESC;
```

### Find recent changes
```cypher
MATCH (commit:Commit)-[:INCLUDES]->(change:Change)
RETURN commit.date, commit.author, commit.message,
       change.doc_id, change.section, change.old_text, change.new_text
ORDER BY commit.date DESC
LIMIT 10;
```

### Delete everything (fresh start)
```cypher
MATCH (n) DETACH DELETE n;
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **ping fails** | Check Neo4j running, verify password in `.mcp.json` |
| **First knowledge_call slow (10s)** | Normal - loads embedding model into GPU (once) |
| **load_project slow (60s)** | Normal - generating 1,200 embeddings on GPU |
| **"46 deleted files" but exist** | Path normalization bug - wipe graph + reload |
| **Out of GPU memory** | Close other GPU apps, reduce batch size |
| **Entities not found** | Run `store_extraction` after `load_project` |

---

## Configuration (.mcp.json)

```json
{
  "mcpServers": {
    "smart-core": {
      "type": "stdio",
      "command": "python",
      "args": ["C:\\path\\to\\smart_core\\app\\smart-core-mcp\\server.py"],
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

---

## Quick Links

- **[README.md](README.md)** - Full documentation
- **[SCHEMA.md](SCHEMA.md)** - Complete schema reference
- **[app/Entity-Extraction-Guide.md](app/Entity-Extraction-Guide.md)** - Entity naming rules
- **[research/Smart-Core-Performance-Comparison-Feb-2026.md](research/Smart-Core-Performance-Comparison-Feb-2026.md)** - Benchmarks

---

**Smart Core Quick Reference** | Version 1.0 | February 2026
