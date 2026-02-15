# Universal Entity Extraction & Retrieval Guide

**Purpose:** Extract structured knowledge from any document collection for semantic + graph-based retrieval.
**Scope:** Legal contracts, technical documentation, business plans, research papers, manuals — any structured text.
**Output:** Neo4j knowledge graph with vector embeddings for hybrid search.

---

## Table of Contents

1. [Core Concepts](#1-core-concepts)
2. [Entity Extraction Workflow](#2-entity-extraction-workflow)
3. [Entity Naming Patterns](#3-entity-naming-patterns)
4. [Relationship Types](#4-relationship-types)
5. [Retrieval Strategies](#5-retrieval-strategies)
6. [Best Practices](#6-best-practices)
7. [Domain-Specific Patterns](#7-domain-specific-patterns)

---

## 1. Core Concepts

### What is Entity Extraction?

**Entity extraction** = identifying and structuring key concepts, values, and relationships from unstructured text.

**Example (Contract):**
```
Raw text: "The Contractor shall deliver the Software (version 2.0)
by March 31, 2027, for a fee of $50,000."

Extracted entities:
- Entity: Deliverable-Software-v2.0
- Entity: Deadline-2027-03-31
- Entity: Payment-50000-USD
- Entity: Role-Contractor

Relationships:
- (Role-Contractor)-[:MUST_DELIVER]->(Deliverable-Software-v2.0)
- (Deliverable-Software-v2.0)-[:HAS_DEADLINE]->(Deadline-2027-03-31)
- (Deliverable-Software-v2.0)-[:COSTS]->(Payment-50000-USD)
```

### Why Extract Entities?

1. **Cross-Document Consistency** — Find all mentions of `Deadline-2027-03-31` across 50 contracts
2. **Change Propagation** — Update `Payment-50000-USD` → `Payment-75000-USD` everywhere
3. **Dependency Tracking** — See what depends on `Deliverable-Software-v2.0` before changing it
4. **Semantic Search** — "What are the Q1 2027 deliverables?" → finds all deadline entities in Q1 2027
5. **Graph Queries** — "Show all payments over $25K that depend on software deliverables"

### Knowledge Graph Architecture

```
Document (MD file, PDF, DOCX)
    ├─ Chunks (semantic sections for vector search)
    ├─ Entities (structured concepts extracted from text)
    │   ├─ Properties (values, metadata)
    │   └─ Relationships (how entities connect)
    └─ Tags (categorization for filtering)
```

**Storage:**
- **Neo4j (graph)** — entities, relationships, document structure
- **Vector embeddings** — semantic similarity search on chunks
- **Hybrid search** — combine graph traversal + vector similarity

---

## 2. Entity Extraction Workflow

### Phase 1: Document Preparation

**Step 1: Identify Document Types**

Categorize your document collection:

| Document Type | Examples | Key Entities to Extract |
|---------------|----------|-------------------------|
| **Legal** | Contracts, NDAs, Terms | Parties, Obligations, Deadlines, Payments |
| **Technical** | Manuals, Specs, APIs | Components, Parameters, Versions, Dependencies |
| **Business** | Plans, Budgets, Roadmaps | Milestones, Budgets, Metrics, Teams |
| **Research** | Papers, Reports, Studies | Methods, Results, References, Hypotheses |
| **Operational** | SOPs, Checklists, Guides | Steps, Roles, Tools, Deliverables |

**Step 2: Define Entity Categories**

For your specific document collection, decide which categories matter:

**Universal categories (all domains):**
- **Identifiers** — document IDs, version numbers, reference codes
- **Temporal** — dates, deadlines, durations, phases
- **Agents** — people, roles, organizations, systems
- **Artifacts** — products, deliverables, documents, assets
- **Quantitative** — metrics, amounts, measurements, targets
- **Taxonomic** — categories, types, classifications

**Domain-specific categories:**
- Legal → Parties, Obligations, Jurisdictions, Clauses
- Technical → Components, Protocols, Specifications, APIs
- Business → Milestones, Budgets, KPIs, Markets

### Phase 2: Entity Naming

**Principle:** Structured IDs enable graph queries. Unstructured text doesn't.

#### Naming Pattern: `Type-Category-Instance`

```
Format: [TYPE]-[CATEGORY]-[INSTANCE]

Examples:
- Legal: Party-Client-Acme, Obligation-Deliver-Software, Deadline-2027-Q1
- Technical: Comp-Hardware-Sensor-01, API-REST-Payments, Spec-Voltage-5V
- Business: MS-Phase1-Launch, Budget-Marketing-2027, Metric-Revenue-Q4
```

**Rules:**

1. **Hierarchical left-to-right** (broad → specific)
2. **Dash-separated** (no spaces, no underscores)
3. **CamelCase for multi-word** (`Party-ClientName`, not `Party-client-name`)
4. **Unique per instance** (same entity = same ID everywhere)
5. **Minimal qualifiers** (add year/version only if multiple instances exist)

#### Temporal Anchoring

Add time reference **only when needed**:

```
✓ One instance:
  - Deadline-LaunchDate (only one launch)
  - Budget-2027 (tracking single year)

✓ Multiple instances:
  - Deadline-LaunchDate-v1, Deadline-LaunchDate-v2 (launch postponed)
  - Budget-2027-Q1, Budget-2027-Q2, Budget-2027-Q3 (quarterly budgets)
```

#### Properties vs IDs

**Keep IDs short. Store details in properties.**

```
❌ Bad: Obligation-Deliver-Software-v2.0-by-March-31-2027-for-50000-USD
✅ Good: Obligation-Deliver-Software
   Properties: {
     version: "2.0",
     deadline: "2027-03-31",
     amount: 50000,
     currency: "USD"
   }
```

### Phase 3: Extraction Process

**Step 1: High-Frequency Entities First**

Extract entities that appear in **3+ documents** first. These are your consistency anchors.

```
Document scan results:
- "March 31, 2027" appears in 8 documents → extract as Deadline-2027-03-31
- "Software v2.0" appears in 12 documents → extract as Deliverable-Software-v2.0
- "$50,000" appears in 3 documents → extract as Payment-50000-USD
```

**Step 2: Relationship Strength**

Track how many documents connect two entities. Strong relationships (4+ docs) indicate critical dependencies.

```
Deliverable-Software-v2.0 → Deadline-2027-03-31 (appears together in 8 docs)
  → Critical dependency, extract relationship

Feature-Analytics → Deliverable-Software-v2.0 (appears together in 1 doc)
  → Weak connection, lower priority
```

**Step 3: Cross-Reference Before Finalizing**

Check: "Does this entity appear under different names elsewhere?"

```
Common duplicates:
- "Software v2.0" = "Software version 2.0" = "v2 Software" → Pick ONE name
- "Q1 2027" = "Jan-Mar 2027" = "First quarter 2027" → Standardize to Deadline-2027-Q1
```

### Phase 4: Store Extraction

Use `store_extraction` MCP tool:

```python
# For each document, call:
store_extraction(
  document_path="path/to/document.md",
  entities=[
    {"name": "Deliverable-Software-v2.0", "type": "Deliverable", "value": "Software v2.0"},
    {"name": "Deadline-2027-03-31", "type": "Deadline", "value": "March 31, 2027"},
    {"name": "Payment-50000-USD", "type": "Payment", "value": "$50,000"}
  ],
  tags=["contract", "software", "Q1-2027"]
)
```

---

## 3. Entity Naming Patterns

### Universal Patterns (Any Domain)

#### Temporal Entities

| Pattern | Example | Use Case |
|---------|---------|----------|
| `Deadline-[YYYY-MM-DD]` | `Deadline-2027-03-31` | Specific dates |
| `Period-[YYYY]-[Q/H/M]` | `Period-2027-Q1` | Time periods |
| `Phase-[Name]` | `Phase-Development`, `Phase-Testing` | Project phases |
| `Duration-[N]-[Unit]` | `Duration-30-Days`, `Duration-6-Months` | Time spans |

#### Quantitative Entities

| Pattern | Example | Use Case |
|---------|---------|----------|
| `Amount-[Value]-[Unit]` | `Amount-50000-USD`, `Amount-100-Hours` | Monetary/numeric values |
| `Metric-[Name]` | `Metric-Accuracy`, `Metric-Throughput` | Measurements |
| `Target-[Metric]-[Value]` | `Target-Revenue-1M`, `Target-Uptime-99.9` | Goals/thresholds |
| `Range-[Min]-[Max]` | `Range-10-50-USD`, `Range-5-10-kg` | Value ranges |

#### Agent Entities

| Pattern | Example | Use Case |
|---------|---------|----------|
| `Role-[Title]` | `Role-Manager`, `Role-Auditor` | Positions |
| `Party-[Name]` | `Party-Acme`, `Party-Contractor` | Organizations/people |
| `Team-[Name]` | `Team-Engineering`, `Team-Legal` | Groups |
| `System-[Name]` | `System-PaymentAPI`, `System-CRM` | Software systems |

#### Artifact Entities

| Pattern | Example | Use Case |
|---------|---------|----------|
| `Doc-[Type]-[ID]` | `Doc-Contract-MSA-001`, `Doc-Report-Q4` | Documents |
| `Deliverable-[Name]` | `Deliverable-Software`, `Deliverable-Report` | Outputs |
| `Asset-[Type]-[Name]` | `Asset-IP-Patent-001`, `Asset-Physical-Server-01` | Resources |
| `Product-[Name]` | `Product-MainApp`, `Product-Widget` | Offerings |

#### Taxonomic Entities

| Pattern | Example | Use Case |
|---------|---------|----------|
| `Category-[Name]` | `Category-Hardware`, `Category-Legal` | Classifications |
| `Type-[Name]` | `Type-Contract-MSA`, `Type-Risk-Financial` | Subtypes |
| `Status-[State]` | `Status-Active`, `Status-Pending`, `Status-Closed` | States |
| `Priority-[Level]` | `Priority-Critical`, `Priority-High` | Ranking |

### Domain-Specific Patterns

#### Legal Documents

```
Party-[Name]              → Party-Acme, Party-Contractor
Obligation-[Action]       → Obligation-Deliver, Obligation-Pay
Clause-[Section]-[Type]   → Clause-5.2-Indemnity
Term-[Duration]           → Term-12-Months
Jurisdiction-[Location]   → Jurisdiction-Delaware, Jurisdiction-UK
Liability-[Type]-[Cap]    → Liability-Direct-1M-USD
```

#### Technical Documentation

```
Component-[System]-[Part] → Component-API-Auth, Component-DB-Cache
Protocol-[Name]           → Protocol-HTTPS, Protocol-MQTT
Version-[System]-[Number] → Version-API-v2.1
Parameter-[Name]          → Parameter-Timeout, Parameter-MaxRetries
Spec-[Property]-[Value]   → Spec-Voltage-5V, Spec-Port-8080
Error-[Code]              → Error-404, Error-Timeout
```

#### Business Plans

```
Milestone-[Phase]-[Name]  → Milestone-Phase1-Launch
Budget-[Period]           → Budget-2027-Q1
Revenue-[Period]          → Revenue-2027-Annual
Market-[Geo]-[Vertical]   → Market-EU-FinTech
Competitor-[Name]         → Competitor-CompanyX
Risk-[Category]-[ID]      → Risk-Financial-01
```

#### Research Papers

```
Method-[Name]             → Method-CRISPR, Method-RandomForest
Hypothesis-[ID]           → Hypothesis-H1, Hypothesis-H2
Result-[Metric]           → Result-Accuracy, Result-P-Value
Dataset-[Name]            → Dataset-ImageNet, Dataset-CocoAB
Reference-[Citation]      → Reference-Smith2023
```

---

## 4. Relationship Types

### Universal Relationships

#### Temporal Dependencies

```cypher
(Milestone-A)-[:PRECEDES]->(Milestone-B)
(Deliverable-X)-[:HAS_DEADLINE]->(Deadline-2027-Q1)
(Phase-Development)-[:DURATION]->(Duration-6-Months)
(Deadline-A)-[:BLOCKS]->(Milestone-B)  // B cannot start until A passes
```

#### Hierarchical Relationships

```cypher
(Document-Contract)-[:CONTAINS]->(Clause-5.2)
(System-API)-[:HAS_COMPONENT]->(Component-Auth)
(Product-Enterprise)-[:INCLUDES]->(Feature-Analytics)
(Phase-Development)-[:CONTAINS]->(Milestone-MVP)
```

#### Agent Relationships

```cypher
(Role-Manager)-[:RESPONSIBLE_FOR]->(Deliverable-Report)
(Party-Contractor)-[:MUST_DELIVER]->(Deliverable-Software)
(Team-Legal)-[:OWNS]->(Document-NDA)
(System-CRM)-[:INTEGRATES_WITH]->(System-PaymentAPI)
```

#### Value Relationships

```cypher
(Deliverable-Software)-[:COSTS]->(Amount-50000-USD)
(Metric-Revenue)-[:TARGET]->(Target-Revenue-1M)
(Budget-2027)-[:ALLOCATES]->(Amount-500K-USD)
(Risk-Financial)-[:HAS_PROBABILITY]->(Probability-20-Percent)
```

#### Dependency Relationships

```cypher
(Feature-Analytics)-[:DEPENDS_ON]->(Component-Database)
(Deliverable-Software)-[:REQUIRES]->(Approval-Legal)
(Milestone-Launch)-[:CONDITIONAL_ON]->(Milestone-Testing)
(Payment-Phase2)-[:TRIGGERED_BY]->(Deliverable-Phase1)
```

#### Reference Relationships

```cypher
(Document-A)-[:REFERENCES]->(Document-B)
(Document-New)-[:SUPERSEDES]->(Document-Old)
(Clause-5.2)-[:MODIFIES]->(Clause-3.1)
(Version-v2)-[:REPLACES]->(Version-v1)
```

---

## 5. Retrieval Strategies

### Hybrid Search (Recommended)

Combine **vector similarity** (semantic) + **graph traversal** (structured):

```python
# Query: "What are the Q1 2027 software deliverables?"

# Step 1: Vector search (semantic)
chunks = vector_search("Q1 2027 software deliverables")
# Returns: Relevant text chunks mentioning Q1, software, deliverables

# Step 2: Graph search (structured)
entities = graph_query("""
  MATCH (d:Entity {type: 'Deliverable'})
  WHERE d.name CONTAINS 'Software'
  MATCH (d)-[:HAS_DEADLINE]->(deadline:Entity)
  WHERE deadline.name CONTAINS '2027-Q1' OR deadline.value CONTAINS 'Q1 2027'
  RETURN d, deadline
""")

# Step 3: Merge results
# Entities from graph + Context from vector chunks
```

### Search Type Selection

| Query Type | Search Method | Example |
|------------|---------------|---------|
| **Exact entity lookup** | Graph only | "Show all payments over $50K" |
| **Semantic concept** | Vector only | "What are the quality requirements?" |
| **Structured + semantic** | Hybrid | "What Q1 deliverables depend on software approval?" |
| **Cross-document** | Graph + vector | "Find all contracts referencing Acme with March deadlines" |

### Query Patterns

#### 1. Find All Instances of Entity Type

```cypher
// Find all deadlines in Q1 2027
MATCH (d:Entity {type: 'Deadline'})
WHERE d.name CONTAINS '2027-Q1' OR d.value CONTAINS 'Q1 2027'
RETURN d.name, d.value, d.documents
```

#### 2. Trace Dependencies

```cypher
// What depends on Software v2.0?
MATCH (software:Entity {name: 'Deliverable-Software-v2.0'})
MATCH (software)-[r:HAS_DEADLINE|COSTS|REQUIRES*1..3]-(related)
RETURN software, r, related
```

#### 3. Cross-Document Consistency Check

```cypher
// Find all documents mentioning Payment-50000-USD
MATCH (payment:Entity {name: 'Payment-50000-USD'})
MATCH (doc:Document)-[:HAS_ENTITY]->(payment)
RETURN doc.path, payment.value
```

#### 4. Find Conflicts

```cypher
// Find entities with same name but different values
MATCH (e1:Entity), (e2:Entity)
WHERE e1.name = e2.name
  AND e1.value <> e2.value
  AND id(e1) < id(e2)
RETURN e1.name, e1.value, e1.documents, e2.value, e2.documents
```

#### 5. Time-Based Queries

```cypher
// All deliverables due before end of Q1 2027
MATCH (d:Entity {type: 'Deliverable'})
MATCH (d)-[:HAS_DEADLINE]->(deadline:Entity)
WHERE deadline.name <= 'Deadline-2027-03-31'
RETURN d.name, deadline.name, d.documents
```

---

## 6. Best Practices

### Extraction Efficiency

**1. Start with High-Value Entities**

Extract entities that appear in **3+ documents** first:

```
Frequency analysis:
- "Payment $50K" → 8 documents → HIGH PRIORITY
- "Server configuration" → 2 documents → MEDIUM PRIORITY
- "Contact email" → 1 document → LOW PRIORITY
```

**2. Extract More, Dedupe Later**

Better to over-extract and merge duplicates than miss critical entities.

**3. Use Relationship Strength**

Track how many docs connect two entities:

```
Software-v2.0 → Deadline-2027-Q1 (8 docs) → STRONG relationship
Feature-X → Software-v2.0 (1 doc) → WEAK relationship
```

Strong relationships (4+ docs) indicate critical dependencies.

### Performance vs Accuracy Trade-off

**User Control:** You decide between comprehensive extraction (slower, more accurate) vs minimal extraction (faster, less detail).

#### Extraction Modes

| Mode | Entity Count | Query Speed | Accuracy | Use Case |
|------|--------------|-------------|----------|----------|
| **Minimal** | 40-80 entities | 0.06s avg | 99% | Fast retrieval, core entities only |
| **Balanced** | 100-200 entities | 0.5-1s avg | 97% | Good balance for most projects |
| **Comprehensive** | 500+ entities | 2-3s avg | 96% | Maximum detail, rich context |

**Performance Benchmark (Fers Project):**

```
Baseline (100 entities):
- Query speed: 0.06s average
- Accuracy: 99%
- Completeness: 92%
- Graph queries: Instant (0.0s metadata filtering)

After enrichment (501 entities):
- Query speed: 2s average (33x slower)
- Accuracy: 96% (-3%)
- Completeness: 94% (+2%)
- Quality: 95% (+4%)
- Graph queries: Broken (fell back to vector search)
```

**Key Insight:** More entities = better answers (+4% quality) but slower queries if entity graph scales poorly.

#### When to Use Each Mode

**🟢 Minimal Mode (40-80 entities):**
- Fast retrieval critical (user-facing queries)
- Small document collections (<10 docs)
- Simple use cases (budget tracking, status updates)
- Frequent queries expected

**🟡 Balanced Mode (100-200 entities):**
- Mixed use cases (queries + change tracking)
- Medium collections (10-50 docs)
- Moderate complexity (business docs, contracts)
- **Recommended default**

**🔴 Comprehensive Mode (500+ entities):**
- Research and analysis primary use
- Large collections (50+ docs)
- Complex cross-document dependencies
- Infrequent but thorough queries
- Change propagation workflows critical

#### How to Control Extraction Depth

**1. Frequency Threshold**

```
Minimal:    Extract only freq ≥ 4 docs (core entities)
Balanced:   Extract freq ≥ 2 docs (standard)
Comprehensive: Extract freq ≥ 1 doc + unique value (everything)
```

**2. Relationship Threshold**

```
Minimal:    Extract only relationships ≥ 5 connections (hubs)
Balanced:   Extract relationships ≥ 3 connections (standard)
Comprehensive: Extract all relationships ≥ 1 connection (full graph)
```

**3. Entity Type Priority**

```
Minimal:    Only extract: Funding, Phases, Products, Critical Metrics
Balanced:   Add: Team, Specs, Milestones, Markets, Competitors
Comprehensive: Add: Use Cases, Tools, References, All Metrics
```

#### Optimization Strategies

**If queries are too slow (>3s average):**

1. ✅ Reduce entity count to Balanced mode (100-200)
2. ✅ Investigate entity graph search (may be broken)
3. ✅ Use vector-only search if graph queries timeout
4. ✅ Index optimization (ensure graph constraints/indexes exist)

**If answers lack detail:**

1. ✅ Increase to Comprehensive mode (500+)
2. ✅ Extract lower-frequency entities (freq ≥ 1)
3. ✅ Add more entity types (competitors, technologies, references)
4. ✅ Increase chunk retrieval limit (10 → 20-30)

**Recommended Approach:**

```
1. Start with Balanced mode (100-200 entities)
2. Measure query speed and answer quality
3. Adjust based on primary use case:
   - Queries frequent? → Reduce to Minimal
   - Analysis deep? → Increase to Comprehensive
4. Monitor performance over time
5. Re-optimize if collection grows significantly
```

#### Performance Targets by Mode

| Mode | Target Query Speed | Target Accuracy | Trade-off |
|------|-------------------|-----------------|-----------|
| Minimal | <0.1s | 95-99% | Speed over detail |
| Balanced | 0.5-1s | 96-98% | Balanced |
| Comprehensive | 2-5s | 96-100% | Detail over speed |

**Bottom Line:** Choose the extraction depth that matches your usage patterns. More entities = richer context but slower queries. Less entities = faster retrieval but may miss connections.

### Consistency Rules

**Rule 1: Same Entity = Same ID Everywhere**

```
❌ Wrong:
- Contract-A.md uses "Software-v2"
- Contract-B.md uses "Software-v2.0"
- SOW.md uses "SoftwareVersion2"

✅ Correct:
- All documents use "Deliverable-Software-v2.0"
```

**Rule 2: Canonical Values**

Designate one document as **source of truth** for each entity:

```
Entity: Payment-50000-USD
Canonical source: Contract-MSA-001.md
Referenced in: SOW-001.md, Invoice-001.md, Budget-2027.md

If value changes:
1. Update canonical source first
2. Run change propagation to all references
```

**Rule 3: Version Control**

When values change, track history:

```
Entity: Budget-2027-Marketing
v1: $100,000 (initial budget, set 2026-10-01)
v2: $150,000 (revised budget, set 2027-01-15)

Store as:
- Budget-2027-Marketing-v1 (archived)
- Budget-2027-Marketing (current, points to v2)
```

### Change Propagation

**Workflow:**

1. **Detect change** — `synchronize_project()` finds file changes
2. **Find impacted entities** — `knowledge_call("entity name")` finds all mentions
3. **Create merge request** — `merge_report(old_value, new_value)` identifies affected docs
4. **User approval** — Ask user to approve cross-document update
5. **Propagate changes** — `approve_merge(merge_id)` updates all affected documents
6. **Reload graph** — `load_project()` syncs Neo4j

**Example:**

```
Change detected: Budget-2027 changed from $100K → $150K

knowledge_call("Budget-2027") returns:
- Business-Plan.md (line 47)
- Financial-Model.md (line 102)
- Exec-Summary.md (line 23)

Create merge request → User approves → Update all 3 documents
```

---

## 7. Domain-Specific Patterns

### Legal Contracts

**Entity Categories:**
- Parties, Obligations, Deadlines, Payments, Liabilities, Jurisdictions, Terms

**Example Extraction:**

```
Contract text:
"The Contractor (Acme Corp) shall deliver the Software (v2.0) by March 31, 2027.
Upon acceptance, Client shall pay $50,000 within 30 days. Liability is capped at
$100,000. Jurisdiction: Delaware."

Entities:
- Party-Contractor-Acme
- Party-Client
- Deliverable-Software-v2.0
- Deadline-2027-03-31
- Payment-Acceptance-50K-USD
- Duration-Payment-30-Days
- Liability-Cap-100K-USD
- Jurisdiction-Delaware

Relationships:
(Party-Contractor-Acme)-[:MUST_DELIVER]->(Deliverable-Software-v2.0)
(Deliverable-Software-v2.0)-[:HAS_DEADLINE]->(Deadline-2027-03-31)
(Deliverable-Software-v2.0)-[:TRIGGERS]->(Payment-Acceptance-50K-USD)
(Payment-Acceptance-50K-USD)-[:DUE_WITHIN]->(Duration-Payment-30-Days)
```

### Technical Manuals

**Entity Categories:**
- Components, Specifications, Protocols, Versions, Parameters, Errors

**Example Extraction:**

```
Manual text:
"The API (v2.1) supports HTTPS protocol on port 8080. Timeout is 30 seconds.
Maximum payload: 10MB. Error 404 indicates resource not found."

Entities:
- Component-API
- Version-API-v2.1
- Protocol-HTTPS
- Spec-Port-8080
- Parameter-Timeout-30s
- Spec-MaxPayload-10MB
- Error-404

Relationships:
(Component-API)-[:HAS_VERSION]->(Version-API-v2.1)
(Component-API)-[:USES_PROTOCOL]->(Protocol-HTTPS)
(Component-API)-[:LISTENS_ON]->(Spec-Port-8080)
(Component-API)-[:HAS_PARAMETER]->(Parameter-Timeout-30s)
(Component-API)-[:RETURNS]->(Error-404)
```

### Business Plans

**Entity Categories:**
- Milestones, Budgets, Metrics, Markets, Competitors, Risks

**Example Extraction:**

```
Business plan text:
"Phase 1 budget: $500K. Target: Launch MVP by Q1 2027.
Market: EU FinTech ($5B). Competitor: CompanyX."

Entities:
- Phase-Phase1
- Budget-Phase1-500K-USD
- Milestone-Phase1-LaunchMVP
- Deadline-2027-Q1
- Market-EU-FinTech
- Metric-MarketSize-5B-USD
- Competitor-CompanyX

Relationships:
(Phase-Phase1)-[:HAS_BUDGET]->(Budget-Phase1-500K-USD)
(Phase-Phase1)-[:CONTAINS]->(Milestone-Phase1-LaunchMVP)
(Milestone-Phase1-LaunchMVP)-[:HAS_DEADLINE]->(Deadline-2027-Q1)
(Market-EU-FinTech)-[:SIZE]->(Metric-MarketSize-5B-USD)
```

---

## Appendix: Quick Reference

### Extraction Checklist

Before marking extraction complete:

- [ ] All high-frequency entities (3+ docs) extracted
- [ ] Entity IDs are unique and consistent across documents
- [ ] Relationships with 4+ document frequency captured
- [ ] Canonical sources designated for each entity
- [ ] Temporal entities include year/quarter when multiple instances exist
- [ ] Quantitative values stored as properties, not in IDs
- [ ] Tags applied for categorization and filtering
- [ ] Cross-references validated (no duplicate entity names)

### Common Mistakes

| Mistake | Fix |
|---------|-----|
| Different IDs for same entity | Standardize: Pick ONE name, use everywhere |
| Details in IDs (`Amount-50000-USD-from-Acme`) | Use properties: `Amount-50000-USD {from: "Acme"}` |
| Missing temporal anchors | Add year/quarter when multiple instances exist |
| Weak relationships extracted | Only extract relationships appearing in 2+ docs |
| No canonical source | Designate source of truth for each entity |
| Generic numbering (`Document-1`, `Document-2`) | Use typed IDs: `Doc-Contract-MSA-001` |

---

**Version:** 1.0
**Last Updated:** 2026-02-14
**Maintainer:** Smart Core
**License:** MIT
