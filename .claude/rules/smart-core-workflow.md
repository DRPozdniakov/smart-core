# Smart Core MCP Workflow Rules

## Rule 1: Always Ping Neo4j First

**BEFORE ANY MCP CALL:** Call `mcp__smart-core__ping` to check Neo4j status.

```
✅ CORRECT:
1. Call ping → returns {"status": "ok"}
2. Proceed with knowledge_call, load_project, etc.

❌ WRONG:
1. Directly call knowledge_call without ping
   → Will hang indefinitely if Neo4j is down
```

**Only need to ping once per session.** If it returned "ok" earlier, proceed without re-ping.

---

## Rule 2: Knowledge Call Before Editing

**BEFORE editing any document in docs_ver2/:**

1. Run `mcp__smart-core__knowledge_call` to find which entities/tags the document contains
2. Check DEPENDS_ON / RESULTS_FROM relationships to identify downstream docs

**🔴 NEVER do single-file fixes for entity/value changes.**

ANY change to a value (amount, valuation, timeline, spec) MUST be traced across ALL documents using `knowledge_call` BEFORE editing.

```
✅ CORRECT:
1. User: "Change Seed round to €1.2M"
2. Run knowledge_call("Seed round funding") → finds 8 documents
3. Edit all 8 documents in one pass
4. Update changelog.md
5. Run load_project

❌ WRONG:
1. User: "Change Seed round to €1.2M"
2. Edit only the file user mentioned
3. Skip knowledge_call
   → Other documents now have inconsistent data
```

---

## Rule 3: After Editing Documents

**MANDATORY sequence after editing any document in docs_ver2/:**

1. **Run `knowledge_call`** to find ALL documents containing the changed entity/value
2. **Edit ALL affected files** in one pass (not just the file the user mentioned)
3. **Update `docs_ver2/changelog.md`** — log every change with:
   - Date
   - File path
   - Old value → New value
   - Reason for change
4. Run `load_project` to re-ingest changed documents
5. Run `store_extraction` with updated entities
6. If entity VALUE changed, run `merge_report` for each affected entity
7. Update downstream documents flagged by merge_report

**The changelog update is MANDATORY and must happen IMMEDIATELY after edits, before any MCP calls.**

---

## Rule 4: Merge Approval Required

**Claude MUST get user approval for cross-document propagation.**

When entity values change across documents:

1. Run `synchronize_project` to detect changes
2. For each change, run `merge_report` to create a pending merge
3. **Ask user for approval using `AskUserQuestion`:**
   - Format: `"Entity: old_value → new_value. Approve?"`
   - Options: Approve / Reject
4. Only after user approves, run `approve_merge` for approved merge_id
5. Run `load_project` to sync graph

**NEVER auto-approve merges.** User controls all cross-document propagation.

Example approval question:
```
Question: "Equity: CTO 35%→30%, CFO/CEO→TBD. Approve?"
Options: [Approve] [Reject]
```

---

## Rule 5: Before Answering Questions

**Before answering questions about the project:**

1. **Ping Neo4j first** — if down, read files directly
2. If up: Use `knowledge_call` (hybrid search) instead of reading multiple files
3. Cross-reference graph entities for consistency
4. If two docs disagree on same entity → flag it to user

---

## Rule 6: Session Start Workflow

**At session start (when working on docs_ver2/):**

1. Call `mcp__smart-core__ping` to check Neo4j
2. If up: Run `knowledge_call` with relevant query to load context
3. If down: Read files directly, skip graph operations

---

## Common Mistakes to Avoid

❌ Calling MCP tools without pinging first
❌ Editing one file without checking cross-document impacts
❌ Skipping changelog updates
❌ Auto-approving merge requests
❌ Using file reads when knowledge_call would be better
❌ Forgetting to run load_project after edits
