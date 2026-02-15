# Entity Extraction Rules for Smart Core

## Rule 1: Extract Entities After load_project

**MANDATORY workflow:**

```
1. load_project() → Creates Document + Chunk nodes
2. Read each document to identify entities
3. store_extraction(document_path, entities, tags) → Creates Entity nodes
4. Repeat for all documents
```

**⚠️ `load_project` does NOT create Entity nodes** - you must call `store_extraction` separately.

---

## Rule 2: Follow Standardized Naming Patterns

**Format:** `{Type}-{Name}`

### Common Patterns (Fers Project)

| Entity Type | Pattern | Examples | Type Value |
|-------------|---------|----------|------------|
| **Funding** | `Round-{Stage}` | `Round-Seed`, `Round-A`, `Round-B` | `"FundingRound"` |
| **Product** | `Prod-{Name}` | `Prod-FersHumanoid` | `"Product"` |
| **Milestone** | `MS-{Phase}-{Name}` | `MS-Seed-MVP`, `MS-A-Production` | `"Milestone"` |
| **Team** | `Team-{Role}` | `Team-CTO`, `Team-CFO` | `"Team"` |
| **Budget** | `Budget-{Phase}-{Category}` | `Budget-Seed-Hardware` | `"Budget"` |
| **Metric** | `Met-{Type}` | `Met-ARR`, `Met-CAC`, `Met-LTV` | `"Metric"` |
| **Phase** | `Phase-{Name}` | `Phase-Seed`, `Phase-RoundA` | `"Phase"` |
| **Certification** | `Cert-{Type}` | `Cert-CE`, `Cert-FoodGrade` | `"Certification"` |

### Entity Structure

```python
{
  "name": "Round-Seed",           # Unique ID (follows pattern)
  "type": "FundingRound",         # Category
  "value": "€1,000,000, 10 months, Q4 2026"  # Current value with context
}
```

---

## Rule 3: Same Entity = Same Name Everywhere

**Critical for cross-document consistency:**

❌ **WRONG:** Different names for the same thing
```python
# Financial Model
{"name": "SeedRound", "type": "Funding", "value": "€1M"}

# Business Plan
{"name": "Seed-Funding", "type": "Round", "value": "€1,000,000"}

# Executive Summary
{"name": "seed", "type": "funding_round", "value": "1M EUR"}
```

✅ **CORRECT:** Standardized name across all documents
```python
# All documents use the same entity name
{"name": "Round-Seed", "type": "FundingRound", "value": "€1,000,000"}
```

**Why:** `knowledge_call("Round-Seed")` finds all 8 occurrences. Inconsistent naming = missed documents.

---

## Rule 4: Extract High-Value Entities Only

**Extract entities that:**
- ✅ Appear in 2+ documents (cross-document importance)
- ✅ Have specific, concrete values (e.g., "€1M", "Q4 2026", "30% equity")
- ✅ Are referenced by other documents (dependencies)
- ✅ Change over time (need tracking)

**DO NOT extract:**
- ❌ Generic concepts (e.g., "technology", "market", "strategy")
- ❌ One-off mentions with no value (e.g., "innovation" mentioned once)
- ❌ Descriptive text that's not a distinct entity
- ❌ Section headers (already captured as Chunk metadata)

### Examples

✅ **Good entities:**
```python
{"name": "Round-Seed", "type": "FundingRound", "value": "€1,000,000"}
# → Appears in 8 docs, has concrete value, changes over time

{"name": "MS-Seed-MVP", "type": "Milestone", "value": "Q4 2026"}
# → Appears in 5 docs, has deadline, tracked for progress

{"name": "Team-CTO", "type": "Team", "value": "30% equity"}
# → Appears in 6 docs, has equity value, may change
```

❌ **Bad entities:**
```python
{"name": "Market", "type": "Concept", "value": ""}
# → Too generic, no value, not useful for search

{"name": "Introduction", "type": "Section", "value": ""}
# → Section header, already in Chunk metadata

{"name": "Technology-AI", "type": "Technology", "value": ""}
# → Too vague, not actionable
```

---

## Rule 5: Include Context in Values

**Values should be self-explanatory:**

❌ **Bad:** Value lacks context
```python
{"name": "Round-Seed", "type": "FundingRound", "value": "€1M"}
# → What's the timeline? Pre/post money? Equity?
```

✅ **Good:** Value includes relevant context
```python
{"name": "Round-Seed", "type": "FundingRound", "value": "€1,000,000, 10 months, Q4 2026"}
# → Amount, duration, timing - complete picture

{"name": "Budget-Seed-Hardware", "type": "Budget", "value": "€220,000, 22%"}
# → Amount and percentage of total budget
```

---

## Rule 6: Extract Per-Document, Not Per-Chunk

**Call `store_extraction` once per document** with all entities found in that document.

❌ **WRONG:** Call store_extraction for every chunk
```python
# Too many calls, creates duplicate relationships
for chunk in chunks:
    entities = extract_from_chunk(chunk)
    store_extraction(doc_path, entities, tags)  # 41 calls for 41 chunks!
```

✅ **CORRECT:** One call per document with all entities
```python
# Read entire document
doc_text = read_file(doc_path)

# Extract all entities from the document
all_entities = []
for chunk in chunks:
    entities = extract_from_chunk(chunk)
    all_entities.extend(entities)

# Deduplicate and store once
unique_entities = deduplicate(all_entities)
store_extraction(doc_path, unique_entities, tags)  # 1 call per document
```

---

## Rule 7: Use Tags for Document Classification

**Tags** classify documents, **Entities** are concepts within documents.

### Tags (Document-level)

```python
tags = [
    "funding",        # Topic
    "seed",          # Phase
    "product",       # Domain
    "confidential"   # Access level
]
```

**Use tags for:**
- Document categorization (funding, product, technical)
- Phase filtering (pre-seed, seed, round-a)
- Domain grouping (business, technical, financial)
- Access control (confidential, public, internal)

### Entities (Content-level)

```python
entities = [
    {"name": "Round-Seed", "type": "FundingRound", "value": "€1M"},
    {"name": "Team-CTO", "type": "Team", "value": "30% equity"}
]
```

**Use entities for:**
- Cross-document tracking (find all mentions of Round-Seed)
- Value consistency (ensure €1M is same everywhere)
- Dependency analysis (what depends on Team-CTO equity?)
- Change propagation (update Round-Seed everywhere)

---

## Rule 8: Verify Before Storing

**Before calling `store_extraction`, verify:**

1. **Entity names follow patterns** (check Rule 2)
2. **No duplicates** in the entity list
3. **Values are meaningful** (not empty, not "TBD")
4. **Types are consistent** (use same type strings across docs)
5. **Document exists in graph** (load_project was called first)

```python
# Good verification
def verify_entities(entities):
    # Check for duplicates
    names = [e["name"] for e in entities]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate entity names found")

    # Check for empty values
    for e in entities:
        if not e.get("value", "").strip():
            print(f"Warning: Entity {e['name']} has empty value")

    # Check naming pattern
    for e in entities:
        if "-" not in e["name"]:
            print(f"Warning: Entity {e['name']} doesn't follow pattern")

    return True
```

---

## Rule 9: Extraction Workflow Example

**Complete workflow for Fers investor package:**

```python
# Step 1: Load all documents (creates Document + Chunk nodes)
load_project()

# Step 2: Extract entities from each document
documents = [
    "docs_ver2/investor_package/Financial-Model-Fers.md",
    "docs_ver2/investor_package/Executive-Summary-Angels.md",
    "docs_ver2/investor_package/Business-Plan-Fers.md",
    # ... all 25 documents
]

for doc_path in documents:
    # Read document
    doc_text = read_file(doc_path)

    # Extract entities (follows patterns from Rule 2)
    entities = [
        {"name": "Round-Seed", "type": "FundingRound", "value": "€1,000,000, 10 months"},
        {"name": "Budget-Seed-Hardware", "type": "Budget", "value": "€220,000, 22%"},
        {"name": "MS-Seed-MVP", "type": "Milestone", "value": "Q4 2026"},
        # ... other entities
    ]

    # Extract tags
    tags = ["funding", "seed", "finance", "investor-package"]

    # Verify (Rule 8)
    verify_entities(entities)

    # Store once per document (Rule 6)
    store_extraction(doc_path, entities, tags)

# Step 3: Verify extraction worked
knowledge_call("Round-Seed", search_type="graph")
# Should return: 8 documents with Round-Seed entity
```

---

## Rule 10: Common Mistakes to Avoid

| Mistake | Why It's Bad | Correct Approach |
|---------|--------------|------------------|
| **Inconsistent naming** | `Round-Seed` in FM-001, `Seed-Round` in ES-001 → Can't find both | Use exact same name across all docs |
| **Too many generic entities** | `Technology`, `Market`, `Strategy` → No value | Only extract specific, concrete entities |
| **Empty values** | `{"name": "Team-CTO", "value": ""}` → Useless | Include actual values: "30% equity" |
| **Calling store_extraction per chunk** | 41 calls instead of 1 → Slow, duplicates | One call per document |
| **Not deduplicating** | Same entity extracted 5 times from different sections | Deduplicate before storing |
| **Wrong type names** | `"Funding"` vs `"FundingRound"` → Inconsistent | Use same type string everywhere |
| **No verification** | Store invalid entities → Graph pollution | Verify before calling store_extraction |

---

## Quick Reference

**✅ DO:**
- Extract entities after load_project
- Use standardized naming patterns (Round-{Stage}, Team-{Role})
- Same entity name across all documents
- Include context in values ("€1M, 10 months, Q4 2026")
- One store_extraction call per document
- Verify entities before storing

**❌ DON'T:**
- Extract generic concepts without values
- Use inconsistent naming across documents
- Store empty or "TBD" values
- Call store_extraction per chunk
- Skip verification

---

**Full Guide:** [smart_core/app/Entity-Extraction-Guide.md](../../smart_core/app/Entity-Extraction-Guide.md)

**Entity Patterns Reference:** [smart_core/SCHEMA.md - Entity Naming](../../smart_core/SCHEMA.md#entity-naming-conventions)
