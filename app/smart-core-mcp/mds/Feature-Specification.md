# Smart Core - Feature Specification

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Status** | Draft |
| **Last Updated** | January 2026 |

---

## Product Overview

Smart Core is a context engineering platform that gives AI agents persistent memory, institutional knowledge, and role-based access controls.

```
┌─────────────────────────────────────────────────────────────────┐
│                         SMART CORE                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Neo4j     │  │    MCP      │  │   RBAC      │             │
│  │  Knowledge  │◄─┤   Server    │◄─┤   Layer     │             │
│  │   Graph     │  │             │  │             │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         ▲                ▲                ▲                     │
│         │                │                │                     │
│  ┌──────┴────────────────┴────────────────┴──────┐             │
│  │              Integration Layer                 │             │
│  │  • Meeting Reports (Plaud.ai, Otter.ai)       │             │
│  │  • Document Imports                            │             │
│  │  • Change Detection                            │             │
│  └────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature 1: Knowledge Graph Storage

### Description
Store all company documents in Neo4j with full tracing, tagging, and entity extraction for early context recovery and rapid deployment.

### Capabilities

| Capability | Description |
|------------|-------------|
| **Document Storage** | Store documents as nodes with metadata |
| **Entity Extraction** | Auto-extract people, companies, dates, amounts |
| **Tag System** | Classify documents by topic (Equity, Timeline, etc.) |
| **Relationship Mapping** | Link related documents, entities, decisions |
| **Change Tracing** | Full history of modifications with timestamps |
| **Canonical Sources** | Mark authoritative source per topic |

### Data Model

```
Node Types:
├── Document
│   ├── path: string (unique)
│   ├── name: string
│   ├── folder: string
│   ├── tags: string[]
│   ├── created: datetime
│   ├── updated: datetime
│   └── content_hash: string
│
├── Tag
│   ├── name: string (unique)
│   ├── description: string
│   └── canonical: string (path to canonical doc)
│
├── Entity
│   ├── type: Person | Company | Amount | Date
│   ├── value: string
│   └── normalized: string
│
└── ChangeLog
    ├── tag: string
    ├── old_value: string
    ├── new_value: string
    ├── source: string
    └── timestamp: datetime

Relationships:
├── (Document)-[:HAS_TAG]->(Tag)
├── (Document)-[:MENTIONS]->(Entity)
├── (Document)-[:REFERENCES]->(Document)
├── (Tag)-[:CHANGED_IN]->(ChangeLog)
└── (Entity)-[:APPEARS_IN]->(Document)
```

### Use Cases

1. **Context Recovery**: Agent starts session → queries graph → gets relevant context
2. **Impact Analysis**: Change spec → find all affected documents
3. **Entity Lookup**: "What do we know about Company X?"
4. **Decision Audit**: "Why did we choose this approach?"

---

## Feature 2: MCP Server Interface

### Description
Model Context Protocol server that gives Claude Code agents direct read/write access to the Neo4j knowledge graph.

### Capabilities

| Capability | Description |
|------------|-------------|
| **Read Context** | Query documents by tag, entity, or relationship |
| **Write Context** | Store new documents, update existing |
| **Notify Changes** | Log changes, trigger propagation |
| **Search** | Full-text and semantic search across graph |
| **Export** | Generate context summaries for agent prompts |

### MCP Tools Exposed

```typescript
// Read Operations
smart_core_get_documents_by_tag(tag: string): Document[]
smart_core_get_tags_for_document(path: string): Tag[]
smart_core_get_canonical(tag: string): Document
smart_core_search(query: string): Document[]
smart_core_get_entity(type: string, value: string): Entity
smart_core_get_stale_documents(): Document[]

// Write Operations
smart_core_store_document(path: string, content: string, tags: string[]): void
smart_core_notify_change(tag: string, old: string, new: string, source: string): AffectedDocs
smart_core_mark_synced(path: string): void
smart_core_add_entity(doc: string, type: string, value: string): void

// Context Operations
smart_core_get_context_for_task(task: string): ContextBundle
smart_core_export_summary(tags: string[]): string
```

### Configuration

```json
{
  "mcpServers": {
    "smart-core": {
      "command": "python",
      "args": ["-m", "smart_core.mcp_server"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "***",
        "NEO4J_DATABASE": "smart-core"
      }
    }
  }
}
```

---

## Feature 3: Meeting Reports Integration

### Description
Automatically import meeting transcripts and reports from services like Plaud.ai, detect changes, and merge updates into the company context.

### Supported Sources

| Service | Import Method | Notes |
|---------|---------------|-------|
| **Plaud.ai** | API / File upload | AI meeting notes |
| **Otter.ai** | API / File upload | Transcription service |
| **Fireflies.ai** | API | Meeting transcription |
| **Manual upload** | File upload | Any transcript format |

### Processing Pipeline

```
1. IMPORT
   └── Receive meeting report (JSON/MD/TXT)

2. PARSE
   ├── Extract participants
   ├── Extract action items
   ├── Extract decisions
   └── Extract key information

3. DETECT CHANGES
   ├── Compare against existing context
   ├── Identify new information
   ├── Identify contradictions
   └── Identify updates to existing facts

4. MERGE
   ├── Create new entities if needed
   ├── Update existing documents (flag as stale)
   ├── Log changes with source attribution
   └── Notify affected documents

5. REPORT
   └── Generate change summary for review
```

### Change Detection Output

```markdown
## Meeting Import Summary
**Source**: Product Review Meeting - 2026-01-15
**Service**: Plaud.ai

### New Information
- Decision: Robot payload changed from 2kg to 3kg per arm
- Action: CTO to update specifications by Jan 20

### Context Updates Required
| Tag | Old Value | New Value | Affected Docs |
|-----|-----------|-----------|---------------|
| Robot_Specs | 2kg payload | 3kg payload | 8 documents |

### Flagged for Review
- Contradiction: Meeting says "Q2 launch" but Timeline shows "Q3"
```

### Integration Example

```python
from smart_core import MeetingImporter

importer = MeetingImporter(smart_core_client)

# Import from Plaud.ai
result = importer.import_from_plaud(
    api_key="...",
    meeting_id="meeting_123"
)

# Or upload file directly
result = importer.import_file(
    path="meeting_notes.md",
    source="Product Review 2026-01-15"
)

print(result.changes)        # List of detected changes
print(result.affected_docs)  # Documents needing update
print(result.new_entities)   # New entities created
```

---

## Feature 4: Role-Based Access Control (RBAC)

### Description
Hierarchical access control ensuring users and agents only see data appropriate to their role. Steering committee sees all processes; managers see their branches; engineers see their projects.

### Role Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                         STEERING                                 │
│  • Full company data access                                     │
│  • All running processes visible                                │
│  • Can see all branches and projects                            │
│  • Audit logs and decision history                              │
├─────────────────────────────────────────────────────────────────┤
│                         MANAGER                                  │
│  • Branch/department scope                                      │
│  • Team's projects and documents                                │
│  • Cross-project view within branch                             │
│  • Cannot see other branches                                    │
├─────────────────────────────────────────────────────────────────┤
│                         ENGINEER                                 │
│  • Project scope only                                           │
│  • Assigned project documents                                   │
│  • Cannot see other projects                                    │
│  • Read-only on shared resources                                │
└─────────────────────────────────────────────────────────────────┘
```

### Access Scopes

| Role | Documents | Entities | Processes | Audit Logs |
|------|-----------|----------|-----------|------------|
| **Steering** | All | All | All | Full |
| **Manager** | Branch | Branch | Branch | Branch |
| **Engineer** | Project | Project | Own only | None |

### Implementation

```python
# API Key structure
{
    "key": "sc_live_xxx",
    "role": "manager",
    "scope": {
        "branches": ["engineering", "product"],
        "projects": null  # null = all within branches
    },
    "permissions": {
        "read": true,
        "write": true,
        "admin": false
    }
}

# Usage in queries
client = SmartCore(api_key="sc_live_xxx")

# Automatically filtered to allowed scope
docs = client.get_documents_by_tag("Robot_Specs")
# Returns only docs within engineering/product branches
```

### Scope Definitions

```yaml
# Company structure
company:
  branches:
    - name: engineering
      projects:
        - fers-robot
        - smart-core
        - simulation
    - name: product
      projects:
        - prd-development
        - customer-research
    - name: operations
      projects:
        - legal
        - finance
        - hr
    - name: commercial
      projects:
        - sales
        - marketing
        - partnerships
```

### Agent Access Patterns

| Scenario | Role | Scope |
|----------|------|-------|
| CEO briefing agent | Steering | All data |
| Engineering standup agent | Manager | Engineering branch |
| Code review agent | Engineer | Specific project |
| Customer meeting prep agent | Manager | Commercial + Product |

---

## Feature Summary

| # | Feature | Status | Priority |
|---|---------|--------|----------|
| 1 | Knowledge Graph Storage | ✅ Built (basic) | P0 |
| 2 | MCP Server Interface | 🔄 Design ready | P0 |
| 3 | Meeting Reports Integration | 📋 Specified | P1 |
| 4 | Role-Based Access Control | 📋 Specified | P1 |

### Development Roadmap

| Phase | Features | Timeline |
|-------|----------|----------|
| **MVP** | Graph storage + MCP server | Month 1-2 |
| **V1.0** | + Meeting integration | Month 3-4 |
| **V1.5** | + RBAC | Month 5-6 |
| **V2.0** | + Enterprise features | Month 7+ |

---

## Technical Requirements

### Infrastructure

| Component | Technology | Notes |
|-----------|------------|-------|
| Database | Neo4j 5.x | Community or Enterprise |
| MCP Server | Python 3.11+ | FastAPI / asyncio |
| Auth | API Keys + JWT | Role embedded in token |
| Hosting | Self-hosted / Cloud | AWS, GCP, or local |

### Dependencies

```
neo4j>=5.0
fastapi>=0.100
pydantic>=2.0
httpx>=0.24
python-jose>=3.3  # JWT
```

---

*Smart Core Feature Specification v1.0 | January 2026*
