# Entity Naming Convention Rules

## Rule: Follow Entity-Extraction-Guide Patterns

**All entities MUST follow patterns in `smart_core/Entity-Extraction-Guide.md`.**

Same entity = same ID across all documents.

---

## Common Entity Patterns

| Entity Type | Pattern | Examples |
|-------------|---------|----------|
| Funding Round | `Round-{Stage}` | `Round-Seed`, `Round-A`, `Round-B` |
| Product | `Prod-{Name}` | `Prod-FersHumanoid` |
| Certification | `Cert-{Type}` | `Cert-CE`, `Cert-FoodGrade` |
| Milestone | `MS-{Phase}-{Name}` | `MS-Seed-MVP`, `MS-A-Production` |
| Phase | `Phase-{Name}` | `Phase-Seed`, `Phase-RoundA` |
| Team Member | `Team-{Role}` | `Team-CTO`, `Team-CFO` |
| Deliverable | `Del-{Phase}-{Name}` | `Del-Seed-Prototype` |
| Metric | `Met-{Type}` | `Met-ARR`, `Met-CAC` |

---

## Examples

✅ **CORRECT:**
```
Entity: Round-Seed
Value: €1,000,000

Entity: MS-Seed-MVP
Value: Q4 2026

Entity: Team-CTO
Value: 30% equity
```

❌ **WRONG:**
```
Entity: Seed Round (inconsistent naming)
Entity: seed (lowercase)
Entity: MVP Milestone (no prefix)
```

---

## Why This Matters

- **Graph queries depend on exact entity IDs**
- **Cross-document consistency requires identical naming**
- **Merge reports only work if entity names match**

**If unsure about entity naming, check `smart_core/Entity-Extraction-Guide.md` first.**
