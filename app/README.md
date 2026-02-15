# Smart Core

**⚠️ This README is deprecated. See [../README.md](../README.md) for current documentation.**

---

## Quick Links

- **📘 [Main README](../README.md)** - Complete documentation, quick start, workflows
- **📊 [SCHEMA.md](../SCHEMA.md)** - Database schema, node types, MCP tools
- **⚡ [QUICK-REFERENCE.md](../QUICK-REFERENCE.md)** - One-page cheat sheet
- **🏷️ [Entity-Extraction-Guide.md](Entity-Extraction-Guide.md)** - Entity naming conventions
- **📈 [Performance Benchmarks](../research/Smart-Core-Performance-Comparison-Feb-2026.md)** - Speed tests

---

## What is Smart Core?

**Knowledge graph platform for business documentation with Claude Code integration.**

Smart Core gives Claude:
- ✅ Persistent memory across sessions (Neo4j knowledge graph)
- ✅ Cross-document consistency tracking (find all occurrences)
- ✅ Git-style change history (who changed what, when, why)
- ✅ Semantic search (vector embeddings + graph traversal)
- ✅ Multi-user collaboration (shared knowledge base)

**Use case:** Managing startup investor packages where 1 change (e.g., Seed round €1M → €1.2M) must propagate to 8+ documents automatically.

---

## Quick Start

1. **Install Neo4j Desktop** and create database `smart-core`
2. **Configure `.mcp.json`** with Neo4j credentials
3. **Test connection:** `mcp__smart-core__ping()`
4. **Load documents:** `mcp__smart-core__load_project()`
5. **Search:** `mcp__smart-core__knowledge_call("seed funding")`

**Full instructions:** [../README.md - Quick Start](../README.md#quick-start-5-minutes)

---

## MCP Server

**Entry point:** [smart-core-mcp/server.py](smart-core-mcp/server.py)

**Tools exposed:**
- `ping` - Check Neo4j connection
- `load_project` - Ingest documents
- `knowledge_call` - Search graph
- `synchronize_project` - Detect drift
- `store_extraction` - Add entities/tags
- `merge_report` - Propose cross-doc changes
- `approve_merge` - Approve propagation
- `commit_changes` - Record audit trail
- `get_commit_history` - Query changes

**API Reference:** [../SCHEMA.md - MCP Tool Reference](../SCHEMA.md#mcp-tool-reference)

---

**For complete documentation, see [../README.md](../README.md)**
