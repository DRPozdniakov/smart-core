# Claude Code Rules for Smart Core

This directory contains enforceable rules that Claude Code applies when working with Smart Core.

**Why rules?** These rules ensure consistent workflows when using Smart Core's MCP tools, entity extraction, and knowledge graph operations.

---

## Available Rules

| Rule File | Purpose | Priority |
|-----------|---------|----------|
| [`smart-core-workflow.md`](smart-core-workflow.md) | MCP/Neo4j workflow (ping first, knowledge_call before edits, merge approval) | 🔴 CRITICAL |
| [`entity-naming.md`](entity-naming.md) | Entity naming conventions | 🔴 CRITICAL |
| [`entity-extraction.md`](entity-extraction.md) | Entity extraction patterns and thresholds | 🟡 IMPORTANT |

---

## How Rules Work

**Claude Code automatically loads all `.md` files in `.claude/rules/` and enforces them during work.**

Rules override default behavior — they are MANDATORY unless explicitly overridden by user instructions.

---

## Rule Priority Levels

| Level | Meaning | Example |
|-------|---------|---------|
| 🔴 CRITICAL | MUST follow — violations break the system | Ping Neo4j before MCP calls |
| 🟡 IMPORTANT | SHOULD follow — violations create inconsistency | Entity naming patterns |
| 🟢 GUIDELINE | Preferred patterns — violations are acceptable if justified | Performance trade-offs |

---

## Adding Project-Specific Rules

When using Smart Core in your project, you can add project-specific rules:

1. Create `.claude/rules/` in your project root
2. Add Smart Core rules:
   - Copy `smart-core-workflow.md`
   - Copy `entity-naming.md`
   - Copy `entity-extraction.md`
3. Add your project-specific rules:
   - Document consistency rules
   - File placement rules
   - Custom naming conventions

**Example project structure:**
```
your-project/
├── .claude/
│   └── rules/
│       ├── smart-core-workflow.md      (copied from Smart Core)
│       ├── entity-naming.md            (copied from Smart Core)
│       ├── entity-extraction.md        (copied from Smart Core)
│       ├── document-consistency.md     (your project-specific rule)
│       └── file-placement.md           (your project-specific rule)
├── docs/
└── smart_core/
```

---

## Testing Rules

**To verify a rule is working:**
1. Ask Claude to perform an action that should trigger the rule
2. Check if Claude follows the rule without being reminded
3. Check if Claude warns when the rule might be violated

**Example test:**
```
User: "Update the Seed round to €1.2M"

Expected behavior (from smart-core-workflow.md):
1. Claude calls ping first
2. Claude calls knowledge_call to find all occurrences
3. Claude lists all affected documents
4. Claude asks for approval before propagating
```

---

**Smart Core Rules** | Part of Smart Core Knowledge Graph Platform
