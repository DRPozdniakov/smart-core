# Smart Core Repository Contents

**Created:** February 2026
**Purpose:** Standalone Smart Core knowledge graph platform for reuse in other projects

---

## Directory Structure

```
smart-core-repo/
├── README.md                              # Main documentation (start here)
├── LICENSE                                # MIT License
├── REPOSITORY-CONTENTS.md                 # This file
├── QUICK-REFERENCE.md                     # Quick command reference
├── .gitignore                             # Git ignore rules
│
├── architecture.html                      # Visual architecture diagram
├── Smart-Core-Validation-Summary.html     # Validation results visualization
│
├── app/
│   ├── README.md                          # App-level documentation (legacy)
│   ├── SCHEMA.md                          # Complete schema reference
│   ├── Entity-Extraction-Guide.md         # Entity naming conventions & extraction guide
│   └── smart-core-mcp/
│       ├── server.py                      # MCP server (main entry point)
│       ├── __init__.py                    # Python package init
│       ├── requirements.txt               # Python dependencies
│       ├── config.json.template           # Configuration template
│       └── mds/
│           └── Feature-Specification.md   # Original design specification
│
├── research/
│   ├── Cypher_Cheatsheet.md               # Neo4j Cypher query reference
│   ├── Smart-Core-Performance-Comparison-Feb-2026.md
│   ├── Smart-Core-Performance-Experiment.md
│   ├── Smart-Core-Performance-Results.md
│   ├── Smart-Core-Performance-Results-Extra-Entites.md
│   ├── Smart-Core-Usage-LESSONS-LEARNED.md
│   └── Smart-Core-Validation-Summary.md
│
├── examples/
│   ├── README.md                          # Configuration examples guide
│   └── mcp.json.example                   # Claude Code MCP configuration example
│
└── .claude/
    └── rules/
        ├── README.md                      # Rules documentation
        ├── smart-core-workflow.md         # MCP workflow rules (CRITICAL)
        ├── entity-naming.md               # Entity naming rules (CRITICAL)
        └── entity-extraction.md           # Entity extraction patterns (IMPORTANT)
```

---

## Key Files

### Documentation (Start Here)

| File | Purpose |
|------|---------|
| **[README.md](README.md)** | Main documentation - installation, usage, workflows |
| **[QUICK-REFERENCE.md](QUICK-REFERENCE.md)** | Quick command reference |
| **[app/SCHEMA.md](app/SCHEMA.md)** | Complete schema - nodes, relationships, MCP tools |
| **[app/Entity-Extraction-Guide.md](app/Entity-Extraction-Guide.md)** | Entity naming conventions and extraction guide |

### Core Implementation

| File | Purpose |
|------|---------|
| **[app/smart-core-mcp/server.py](app/smart-core-mcp/server.py)** | MCP server implementation (45KB, 1,200+ lines) |
| **[app/smart-core-mcp/requirements.txt](app/smart-core-mcp/requirements.txt)** | Python dependencies |
| **[app/smart-core-mcp/config.json.template](app/smart-core-mcp/config.json.template)** | Configuration template |

### Configuration Examples

| File | Purpose |
|------|---------|
| **[examples/mcp.json.example](examples/mcp.json.example)** | Claude Code MCP server configuration |
| **[examples/README.md](examples/README.md)** | Setup guide for configuration files |

### Claude Code Rules

| File | Purpose | Priority |
|------|---------|----------|
| **[.claude/rules/smart-core-workflow.md](.claude/rules/smart-core-workflow.md)** | MCP workflow rules | 🔴 CRITICAL |
| **[.claude/rules/entity-naming.md](.claude/rules/entity-naming.md)** | Entity naming conventions | 🔴 CRITICAL |
| **[.claude/rules/entity-extraction.md](.claude/rules/entity-extraction.md)** | Entity extraction patterns | 🟡 IMPORTANT |

### Research & Validation

| File | Purpose |
|------|---------|
| **[research/Smart-Core-Performance-Comparison-Feb-2026.md](research/Smart-Core-Performance-Comparison-Feb-2026.md)** | Baseline vs 501 entities performance comparison |
| **[research/Smart-Core-Performance-Results.md](research/Smart-Core-Performance-Results.md)** | Initial performance benchmarks |
| **[research/Smart-Core-Validation-Summary.md](research/Smart-Core-Validation-Summary.md)** | Validation experiments and results |
| **[research/Smart-Core-Usage-LESSONS-LEARNED.md](research/Smart-Core-Usage-LESSONS-LEARNED.md)** | Design decisions and lessons |
| **[research/Cypher_Cheatsheet.md](research/Cypher_Cheatsheet.md)** | Neo4j Cypher query reference |

---

## What's Included

### ✅ Generic Smart Core Components

**All files in this repository are generic and reusable:**
- MCP server implementation
- Neo4j knowledge graph schema
- Entity extraction framework
- Performance benchmarking methodology
- Configuration templates
- Claude Code rules
- Documentation

### ❌ Fers-Specific Files (Excluded)

**Not included (kept in original Fers project):**
- Fers business documents (investor package, PRD, BRD, etc.)
- Fers-specific entities and relationships
- Fers-specific experiments (Robot-Price-Change-Experiment.md)
- Fers project-specific rules (document-consistency.md, file-placement.md)

---

## Dependencies

### Required

- **Neo4j Desktop 5.x** - Knowledge graph database
- **Python 3.10-3.12** - MCP server runtime
- **NVIDIA GPU with CUDA** - Embedding generation (GPU-only)
- **Claude Code** - VS Code extension or CLI

### Python Packages

See [app/smart-core-mcp/requirements.txt](app/smart-core-mcp/requirements.txt):
- `neo4j>=5.0` - Database driver
- `sentence-transformers>=2.2.0` - Embeddings (requires GPU)
- `torch>=2.0.0` - Deep learning framework
- `fastmcp>=0.1.0` - MCP server framework

---

## Setup Instructions

**See [README.md](README.md) Quick Start section for complete setup guide.**

**Quick setup:**
1. Install Neo4j Desktop, create database "smart-core"
2. Install Python dependencies: `pip install -r app/smart-core-mcp/requirements.txt`
3. Configure `app/smart-core-mcp/config.json` (from template)
4. Configure `.mcp.json` in your project (from examples/mcp.json.example)
5. Test: `ping` in Claude Code

---

## Usage Patterns

### For New Projects

1. **Copy repository** to your project location
2. **Create config** from template with your project's docs path
3. **Load documents** using `load_project`
4. **Extract entities** using entity extraction guide
5. **Query graph** using `knowledge_call`

### For Fers-Style Multi-Document Projects

1. **Follow Fers patterns** for YAML front matter in documents
2. **Use entity naming conventions** from Entity-Extraction-Guide.md
3. **Apply Claude rules** from `.claude/rules/` to your project
4. **Track changes** using `commit_changes` for audit trail
5. **Propagate updates** using `merge_report` → `approve_merge` workflow

---

## Performance Characteristics

**Based on real-world testing (Fers project, 25 documents, ~1,200 chunks):**

| Operation | Time | Notes |
|-----------|------|-------|
| `load_project` (25 docs) | 45-60s | Includes GPU embedding generation |
| `knowledge_call` (first) | 8-12s | Loads model into GPU (one-time) |
| `knowledge_call` (subsequent) | 1-2s | Model cached in memory |
| `synchronize_project` | 1-2s | File hash comparison |
| `merge_report` | 500ms | Graph query |
| `commit_changes` | 200ms | Node creation |

**See [research/Smart-Core-Performance-Comparison-Feb-2026.md](research/Smart-Core-Performance-Comparison-Feb-2026.md) for detailed benchmarks.**

---

## Known Limitations

1. **GPU required** - Embeddings require NVIDIA GPU with CUDA (CPU mode too slow)
2. **Single project** - No multi-tenant support yet
3. **Path normalization** - Manual fix needed for deleted files (see README troubleshooting)
4. **First call slow** - Model loads on first `knowledge_call` (~10s, unavoidable)

---

## Version History

**Alpha 1.0 (February 2026)**
- Initial extraction from Fers project
- Complete MCP server with 8 tools
- Entity extraction framework
- Performance benchmarks
- Documentation and examples

---

## License

MIT License - See [LICENSE](LICENSE)

---

## Support & Contributing

**Questions?**
- See [README.md](README.md) troubleshooting section
- Review [research/Smart-Core-Usage-LESSONS-LEARNED.md](research/Smart-Core-Usage-LESSONS-LEARNED.md)

**Future Plans:**
- Multi-user coordination
- Web dashboard
- CPU-only mode (pre-computed embeddings)
- Role-based access control

---

**Smart Core** - Knowledge Graph Platform for Business Documentation
**Version:** Alpha 1.0 | **Created:** February 2026 | **License:** MIT
