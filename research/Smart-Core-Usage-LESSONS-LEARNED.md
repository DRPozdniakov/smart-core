# Lessons Learned — Fers Project

*Real cases where Smart Core's knowledge graph would have prevented or detected issues. Each entry is a documented incident showing why entity-level tracking and change propagation matter.*

---

## Case 1: Stale Artifacts After Vision Changes (2026-02-07)

### The Problem

After the CTO made significant strategic shifts (pricing model change from per-robot tiers to flat enterprise subscription, Seed phase refocus to PoC-only, team structure decisions), Claude updated the primary documents but **old values survived in secondary documents** that weren't part of the immediate edit pass.

These artifacts were invisible during normal work because:
- No single person reads all 14 documents end-to-end after every change
- Claude's context window only holds a few files at once — stale data in unloaded files goes undetected
- The artifacts looked correct in isolation (proper formatting, reasonable numbers) — only cross-document comparison exposed them

### Artifacts Found (Audit of 2026-02-07)

| Stale Artifact | Where | Old Value | Correct Value | How Long It Survived |
|----------------|-------|-----------|---------------|---------------------|
| Platform pricing model | TAM-SAM-SOM-Analysis.md | €8-25K/robot/year | €120K/enterprise/year | Multiple sessions |
| Global food robotics market | TAM-SAM-SOM-Analysis.md | $3.8B (math error) | $2.76B | Since document creation |
| Europe market year | Business Plan, Exec Summary | $780M labeled as 2025 | $780M is 2024; 2025 = $940M | Multiple sessions |
| Payback period | TAM-SAM-SOM-Analysis.md | "4-month payback" | "<3 to ~21 months" | Multiple sessions |
| Job types list | Pitch-Deck-Tracker.md | Loading, Garnishing, Quality check | Flipping/turning, Stacking, Cleaning | Since tracker creation |
| Seed timing | Pitch-Deck-Tracker.md | Q3 2026 | Q4 2026 | Since tracker creation |
| Seed valuation | BRD-001.md | "TBD" | €4M pre / €5M post | Weeks after decision was made |
| ROI figure | Financial-Model-Fers.md | 300%+ (robot lifetime) | 230%+ (5-year standard) | Multiple sessions |
| Team size | Seed-Phase-Plan.md | 6 people | 7-8 people | Multiple sessions |
| Round A budget split | Round-A-Plan.md | 6 categories, team 25-30 | 5 categories (matching Roadmap), team 20+ | Since document creation |

**Total: 10 categories of stale data across 8 files.** All invisible without a full cross-document audit.

### Why This Happens Without Smart Core

1. **Claude edits file-by-file.** When a vision change hits, Claude updates the file the user is discussing. It does NOT automatically scan all 14 documents for downstream references.
2. **CLAUDE.md is updated but docs lag.** The project memory reflects the latest decisions, but secondary docs (TAM-SAM-SOM, Pitch Deck Tracker, BRD) still carry old data.
3. **No entity-level tracking.** Without the graph, "platform subscription price" is just text scattered across files. There's no system that knows which files contain that value.
4. **Audits are expensive.** The full audit above required reading 14 files (~15,000 lines), cross-referencing ~30 data points, and took significant time. This is not sustainable after every change.

### How Smart Core Solves This

**With Smart Core active**, the workflow after a pricing model change would be:

```
1. User says: "Change subscription to €120K/enterprise/year"
2. Claude calls: knowledge_call("platform subscription price")
3. Graph returns: ALL documents containing that entity + current values
4. Claude edits ALL affected files in one pass
5. Claude calls: merge_report() for each changed entity
6. Graph tracks: which docs are now stale vs updated
7. Next session: synchronize_project() flags any remaining drift
```

**Key difference:** Step 3 is impossible without the graph. Claude would need to read every file to find references — and in practice, it doesn't. It fixes the file in front of it and moves on. The graph makes the invisible visible.

### Takeaway

> **Smart Core's primary value is not search — it's change propagation.** The graph knows which documents share entities. When a value changes, it can enumerate every document that needs updating. Without it, stale artifacts accumulate silently until an expensive manual audit catches them.

---

## Case 2: Conflicting Entity Values Across Documents (2026-02-07)

### The Problem

The second audit pass revealed that **the same entity had different values in different documents**, and neither Claude nor the user noticed across multiple sessions. These weren't stale leftovers from a decision change — they were contradictions that existed from creation and were never caught.

### Contradictions Found

| Entity | Document A | Value A | Document B | Value B | Correct |
|--------|-----------|---------|-----------|---------|---------|
| Global food robotics 2025 | TAM-SAM-SOM-Analysis.md | $3.8B | Executive-Summary-Angels.md | $2.76B | $2.76B (math error in TAM-SAM-SOM) |
| Customer ROI | Financial-Model-Fers.md | 300%+ (robot lifetime) | Business-Plan-Fers.md | 230%+ (5-year) | 230%+ (standardized 5-year basis) |
| Payback period | TAM-SAM-SOM-Analysis.md | "4-month payback" | Executive-Summary-Angels.md | "<3 to ~21 months" | "<3 to ~21 months" (scale-dependent) |
| Round A team size | Round-A-Plan.md | 25-30 people | Full_Roadmap.md | 20+ people | 20+ people (Roadmap is source of truth) |
| Round A budget categories | Round-A-Plan.md | 6 categories | Full_Roadmap.md | 5 categories | 5 categories (aligned to Roadmap) |

### Why This Is Different From Case 1

Case 1 was about **old values surviving after a decision change**. This case is about **the same concept being written with different numbers from the start**, because each document was authored in a different session without cross-referencing the others.

The $3.8B figure in TAM-SAM-SOM was a math error (didn't match the 20.6% CAGR and $14.93B endpoint). It sat in the document for weeks because no system compared it against the $2.76B in Executive Summary.

### How Smart Core Solves This

With the graph, entities like `TAM-FoodRobotics` would have a **single stored value**. When Claude writes "$3.8B" in TAM-SAM-SOM but `knowledge_call("TAM-FoodRobotics")` returns "$2.76B" from Executive Summary, the contradiction is **immediately visible** — before the document is even saved.

```
1. Claude writes TAM-SAM-SOM, calculates $3.8B
2. Claude calls: store_extraction(entities=[{name: "TAM-FoodRobotics", value: "$3.8B"}])
3. Graph detects: TAM-FoodRobotics already stored as $2.76B (from ES-001)
4. Graph flags: CONFLICT — two documents claim different values
5. Claude resolves: recalculates, finds math error, fixes to $2.76B
6. Contradiction never reaches the user
```

**Without the graph:** Both values coexist invisibly. Only a manual audit comparing every number across every document catches it.

### Takeaway

> **Smart Core prevents contradictions at write time, not audit time.** When the graph stores entity values, any new document that introduces a different value for the same entity triggers an immediate conflict check. The cost of catching a contradiction at creation is near zero; the cost of catching it months later during investor due diligence could be the deal.

---

## Case 3: Entity Name Inconsistency (2026-01-28)

### The Problem

Early docs used inconsistent names for the same concept: "Seed Round" vs "Round-Seed" vs "seed funding" vs "Seed phase." The graph couldn't link these as the same entity across documents because the identifiers didn't match.

This meant `knowledge_call("Round-Seed")` would miss documents that used "Seed Round" — defeating the entire purpose of cross-document tracking.

### How It Was Found

During the first `load_project` ingestion, entity extraction produced duplicate nodes for the same real-world concept. Manual inspection revealed 4+ naming variants for funding rounds alone.

### Fix

Created `Entity-Extraction-Guide.md` with strict naming conventions. Same entity = same ID everywhere. Examples:
- `Round-Seed` (not "Seed Round", "seed funding", "Seed phase")
- `Prod-FersHumanoid` (not "Fers robot", "the robot", "F1")
- `TAM-FoodRobotics` (not "global market", "food robotics TAM")

### Why This Matters for Smart Core

Without consistent entity IDs, the graph degrades to a keyword search engine. The power of Smart Core is that `knowledge_call("Round-Seed")` returns **every document** that references the Seed round — but only if every document uses `Round-Seed` as the entity name. One document using "Seed funding" instead means that document is invisible to propagation queries.

**This is a graph-specific problem.** Plain text search can fuzzy-match synonyms. A knowledge graph cannot — entity identity must be exact, or relationships break.

### Takeaway

> **Define entity naming BEFORE writing docs. Retrofitting is 10x harder.** A knowledge graph is only as good as its entity consistency. The Entity-Extraction-Guide is not documentation — it's infrastructure.

---

## Case 4: Expensive Manual Audits Replace What Graph Queries Do Instantly (2026-02-07)

### The Problem

To prepare the investor package for external review, the team needed to verify cross-document consistency. Without Smart Core, this required:

1. Reading all 14 documents (~15,000 lines)
2. Extracting ~30 key data points manually (pricing, team sizes, timelines, market figures, ROI numbers, budget splits)
3. Building a cross-reference matrix in working memory
4. Comparing every data point across every document
5. Two full audit passes to catch everything (first pass found 12 issues, second found 16 more)

**Total effort:** Multiple hours of Claude context, 14 file reads, 2 subagent deployments, dozens of grep searches. The user had to explicitly request the audit — it would never have happened automatically.

### What Was Found

28 issues across two passes. Categories:
- 10 stale values from vision changes (Case 1)
- 5 entity value contradictions (Case 2)
- 9 confidential name leaks
- 4 formatting/structural issues

### How Smart Core Replaces This

Every query below would return results **instantly** from the graph, replacing hours of manual cross-referencing:

| Manual Audit Step | Smart Core Equivalent | Time |
|---|---|---|
| "Find all docs mentioning platform price" | `knowledge_call("Rev-Platform")` → returns all docs + stored values | <1 sec |
| "Check if TAM is consistent" | `knowledge_call("TAM-FoodRobotics")` → shows value per document | <1 sec |
| "Find all docs with Seed timeline" | `knowledge_call("Round-Seed")` → all documents + dates | <1 sec |
| "Check team size consistency" | `knowledge_call("team size seed")` → all references | <1 sec |
| "Detect any drift since last sync" | `synchronize_project()` → full drift report | <5 sec |
| "Find changed entities needing propagation" | `merge_report()` pending queue | <1 sec |

**The audit that took two full passes would be a single `synchronize_project()` call.** Every entity mismatch, every stale value, every document out of sync — reported in one response.

### Why This Matters

Audits are reactive and expensive. They happen only when someone explicitly requests them. Between audits, stale data accumulates silently. Smart Core makes consistency checking **continuous and automatic** — every session starts with `synchronize_project()`, and every edit triggers `knowledge_call()` to check propagation.

The difference is not speed — it's that **graph-based consistency checking actually happens**, while manual audits only happen when someone remembers to ask.

### Takeaway

> **The most dangerous bugs are the ones nobody checks for.** Smart Core turns cross-document consistency from a manual audit (that someone must remember to request) into an automatic check (that runs every session). The 28 issues found in this audit survived for weeks precisely because nobody asked until now.

---

*Last updated: 2026-02-07*
