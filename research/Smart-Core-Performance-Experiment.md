# Smart Core Performance Experiment

**Objective:** Compare Smart Core (Neo4j knowledge graph) vs. Pure Claude Code (file tools) for documentation queries.

**Date:** 2026-02-12

---

## Experiment Design

### Performance Criteria

| Metric | Measurement Method | Why It Matters |
|--------|-------------------|----------------|
| **Tokens Burned** | Sum of input + output tokens across all API calls | Direct cost impact |
| **Tool Calls** | Count of tool invocations | Efficiency indicator |
| **Time Required** | Wall clock time (manual timing) | User experience |
| **Accuracy** | Factual correctness (0-100%) | Core value - is information correct? |
| **Completeness/Fulfillment** | How fully the question was answered (0-100%) | Did it address all parts? |
| **Quality** | Structure, clarity, usefulness (0-100%) | How good is the answer? |
| **Context Efficiency** | Did it need to re-read files? | Smart Core advantage |

### Scoring System

Each answer receives 3 independent scores (0-100% each), then averaged for overall score.

#### 1. Accuracy Score (Factual Correctness)
**"Is the information correct?"**

- **100%**: All facts correct, no errors
- **75%**: Mostly correct, 1-2 minor errors (e.g., wrong section number but right content)
- **50%**: Several errors or outdated information
- **25%**: Major factual errors, significant misinformation
- **0%**: Completely wrong or hallucinated

#### 2. Completeness/Fulfillment Score
**"Did it answer the whole question?"**

- **100%**: Fully addressed all parts of question, nothing missing
- **75%**: Answered main question, minor gaps (e.g., missed 1 document out of 7)
- **50%**: Partial answer, significant omissions (e.g., found 3 of 7 documents)
- **25%**: Barely addressed question, mostly incomplete
- **0%**: Did not answer the question asked

#### 3. Quality Score (Structure & Usefulness)
**"How useful and well-presented is the answer?"**

- **100%**: Clear structure, sources cited, actionable, easy to verify
  - Example: "Found in Business Plan Section 6.2, Financial Model Tab 3, Executive Summary Page 2"
- **75%**: Good structure, mostly useful, some sources missing
  - Example: "Found in Business Plan and Financial Model" (but no specific locations)
- **50%**: Acceptable but unclear, hard to verify, vague references
  - Example: "This is mentioned in several documents"
- **25%**: Poor structure, confusing, not actionable
  - Example: Wall of text with no organization
- **0%**: Unusable answer, no structure, cannot act on it

#### Overall Score Calculation
```
Overall Score = (Accuracy + Completeness + Quality) / 3
```

**Winner Determination:**
- Overall score difference >10% = Clear winner
- Overall score difference 5-10% = Slight advantage
- Overall score difference <5% = Tie

---

## Test Questions

### Q1: Roadmap Status Aggregation
**Question:** "Tell current status on Roadmap."

**Expected Answer:**
- Pre-Seed: In progress (M1-M8 detailed plan exists)
- Seed: Planning phase (checklist exists, needs monthly burn plan)
- Round A: High-level only (needs detailed breakdown)
- Current phase: Pre-Seed
- Documents: Full_Roadmap.md, Roadmap_Docs.md, ROADMAP_PHASES.html
- Status indicators per phase (Priority 0, 1, 2, 3)

**What This Tests:**
- Smart Core: Query documents with Phase tags, aggregate status metadata
- Pure Claude: Must read multiple roadmap files, synthesize manually
- **Advantage: Smart Core** (structured phase metadata + graph relationships)

---

### Q2: Technical BOM Pricing
**Question:** "What is the BOM prices of the Robot?"

**Expected Answer:**
- Target selling price: €55,000
- BOM/production cost details may be in:
  - PRD-001 (if specified)
  - Business Plan (unit economics section)
  - Financial Model (COGS breakdown)
- Hardware margin: ~40% (from China manufacturing)
- Note: Detailed BOM may not exist yet (prototype phase)

**What This Tests:**
- Smart Core: Entity search for pricing/BOM across technical + financial docs
- Pure Claude: Grep for "BOM", "cost", "price" then contextualize
- **Advantage: Uncertain** (depends if BOM is documented vs. implicit)

---

### Q3: Role-Based Task Identification
**Question:** "What are the next jobs for CFO?"

**Expected Answer:**
- Check documents tagged with owner: CFO or deputies: CFO
- Look in TODO.md, LESSONS-LEARNED.md, Roadmap_Docs.md
- CFO responsibilities from Business Plan / CLAUDE.md
- Phase-specific CFO tasks (financial modeling, fundraising prep)

**What This Tests:**
- Smart Core: Query by owner/deputy metadata field
- Pure Claude: Text search for "CFO" across docs, infer tasks
- **Advantage: Smart Core** (structured owner metadata)

---

### Q4: Financial Aggregation & Calculation
**Question:** "Calculate all expenses required by Round A?"

**Expected Answer:**
- Round A target: €7-10M
- Expense breakdown from Round-A-Plan.md (if exists)
- Timeline: 24 months (estimate)
- Categories: Hardware development, team scaling, certifications, facilities
- May need to aggregate from:
  - Round-A-Plan.md
  - Financial Model
  - Full_Roadmap.md (Round A milestones)

**What This Tests:**
- Smart Core: Query Phase: Round A docs, aggregate expense entities
- Pure Claude: Read multiple financial docs, calculate manually
- **Advantage: Smart Core** (entity aggregation + phase filtering)

---

### Q5: Holistic Project Assessment
**Question:** "Assess readiness of the project from 0-100 for Investors."

**Expected Answer:**
- Multi-dimensional assessment:
  - Market research: 80% (TAM/SAM/SOM, competitive analysis complete)
  - Product definition: 75% (PRD/BRD exist, hardware details TBD)
  - Financial model: 70% (models exist, need validation)
  - Team: 60% (CTO+CFO confirmed, other roles TBD)
  - Go-to-market: 65% (customer personas exist, no pilot commitments yet)
  - Legal/IP: 40% (not incorporated, no patent filings)
- Overall: 65-70% (strong foundation, execution gaps)
- Source: Cross-document analysis of completion status

**What This Tests:**
- Smart Core: Aggregate status across all domains, analyze gaps
- Pure Claude: Read multiple docs, synthesize holistic view
- **Advantage: Pure Claude?** (requires judgment/reasoning, not just data retrieval)

---

### Scoring Examples

**Example 1: High Quality Answer (Quality Score: 100%)**
```
The Seed round pre-money valuation is €4,000,000 across all documents:

✓ Business Plan (Section 5.2, Page 12): €4M pre-money
✓ Financial Model (Tab: "Funding Rounds", Cell B4): €4M
✓ Executive Summary (Page 2, Funding section): €4M pre-money
✓ CLAUDE.md (Company Overview table): €4M
✓ Seed-Phase-Plan.md (Header): €4M pre-money

No inconsistencies found. All documents align.
```
**Why 100%:** Clear structure, specific citations, easy to verify, actionable.

---

**Example 2: Medium Quality Answer (Quality Score: 50%)**
```
The Seed round valuation is €4 million. This is mentioned in several documents
including the business plan, financial model, and executive summary.
```
**Why 50%:** Correct info but vague, no specific locations, hard to verify, not as useful.

---

**Example 3: Low Quality Answer (Quality Score: 25%)**
```
I found information about the Seed round. The valuation appears to be around
€4M based on what I saw in the documentation. There are various documents
that discuss this.
```
**Why 25%:** Uncertain language ("appears", "around"), no sources, not actionable.

---

**Example 4: High Completeness (Completeness Score: 100%)**
*Question: "If we change robot price to €60K, which docs need updates?"*
```
7 documents require updates:
1. PRD-001-Fers-Humanoid-Robot.md (Section 2.1: Technical Specs)
2. Business-Plan-Fers.md (Section 6.2: Unit Economics)
3. Financial-Model-Fers.md (Revenue calculations)
4. Executive-Summary-Angels.md (Product description)
5. Customer-Personas.md (ROI calculations for all 3 segments)
6. Competitive-Analysis.md (Price positioning table)
7. CLAUDE.md (Product specs table)
```
**Why 100%:** Found all 7 documents, nothing missed.

---

**Example 5: Low Completeness (Completeness Score: 50%)**
*Same question*
```
The robot price is mentioned in the PRD, Business Plan, and Financial Model.
You should update these documents.
```
**Why 50%:** Found only 3 of 7 documents (43% coverage), significant gaps.

---

## Experiment Protocol

### Setup Phase
1. **Smart Core Test:**
   - Ensure Neo4j is running (`ping` MCP tool)
   - Verify documents loaded (`synchronize_project`)
   - Start with fresh conversation context

2. **Pure Claude Test:**
   - Start with fresh conversation context
   - Only allow: Read, Grep, Glob, Bash (no MCP tools)
   - Same starting instructions

### Execution Phase
1. Ask question verbatim (copy-paste)
2. Record start time
3. Let Claude answer naturally (don't guide or interrupt)
4. Record end time
5. Copy full response for evaluation

### Evaluation Phase
**For each answer, score independently on 3 dimensions:**

1. **Accuracy (Factual Correctness):**
   - Check facts against ground truth in actual documents
   - Mark each fact as: ✓ Correct, ✗ Incorrect, ? Cannot verify
   - Calculate: % correct facts
   - Deduct for hallucinations or outdated info

2. **Completeness (Fulfillment):**
   - List all parts of the question
   - Check if each part was addressed: ✓ Yes, ⚠ Partial, ✗ No
   - Calculate: % of question parts answered
   - Example: If question has 3 parts and only 2 answered → 67%

3. **Quality (Structure & Usefulness):**
   - Can user act on this answer without re-asking?
   - Are sources/locations cited specifically?
   - Is structure clear (bullets, tables, organized)?
   - Is it concise or overly verbose?
   - Use rubric: 100% (excellent) → 0% (unusable)

**Scoring Tips:**
- Be objective: compare against expected answer template
- Don't let token count bias quality score (concise can be high quality)
- If unsure between two scores, pick the lower one (avoid grade inflation)
- Document reasoning for scores in "Notes" field

### Data Collection Template

```markdown
## Question [N]: [Title]

### Smart Core Approach
- **Tokens (Input/Output):** [from API logs]
- **Tool Calls:** [list tools used]
- **Time:** [seconds]
- **Accuracy Score:** [0-100%] - Factual correctness
- **Completeness Score:** [0-100%] - Question fully answered?
- **Quality Score:** [0-100%] - Structure, clarity, usefulness
- **Overall Score:** [(Accuracy + Completeness + Quality) / 3]
- **Notes:** [observations, what worked well, what didn't]

### Pure Claude Approach
- **Tokens (Input/Output):** [from API logs]
- **Tool Calls:** [list tools used]
- **Time:** [seconds]
- **Accuracy Score:** [0-100%] - Factual correctness
- **Completeness Score:** [0-100%] - Question fully answered?
- **Quality Score:** [0-100%] - Structure, clarity, usefulness
- **Overall Score:** [(Accuracy + Completeness + Quality) / 3]
- **Notes:** [observations, what worked well, what didn't]

### Winner: [Smart Core / Pure Claude / Tie]
**Reason:** [why - consider all dimensions]
**Key Difference:** [what made the winner better?]
```

---

## Results Template

### Summary Table

| Question | Smart Core Tokens | Pure Claude Tokens | Token Savings | Smart Core Time (s) | Pure Claude Time (s) | Time Savings | Smart Core Overall | Pure Claude Overall | Winner |
|----------|------------------|-------------------|--------------|-------------------|-------------------|-------------|------------------|-------------------|--------|
| Q1 | | | | | | | | | |
| Q2 | | | | | | | | | |
| Q3 | | | | | | | | | |
| Q4 | | | | | | | | | |
| Q5 | | | | | | | | | |
| **Total** | | | | | | | | | |
| **Avg** | | | | | | | | | |

### Detailed Scoring Breakdown

| Question | Approach | Accuracy | Completeness | Quality | Overall | Tool Calls |
|----------|----------|----------|--------------|---------|---------|-----------|
| Q1 | Smart Core | | | | | |
| Q1 | Pure Claude | | | | | |
| Q2 | Smart Core | | | | | |
| Q2 | Pure Claude | | | | | |
| Q3 | Smart Core | | | | | |
| Q3 | Pure Claude | | | | | |
| Q4 | Smart Core | | | | | |
| Q4 | Pure Claude | | | | | |
| Q5 | Smart Core | | | | | |
| Q5 | Pure Claude | | | | | |

### Aggregate Statistics

```
Smart Core Wins: [N/5]
Pure Claude Wins: [N/5]
Ties: [N/5]

Average Token Reduction (Smart Core): [%]
Average Time Reduction (Smart Core): [%]
Average Quality Improvement (Smart Core): [%]

Best Use Case for Smart Core: [Q#]
Best Use Case for Pure Claude: [Q#]
```

---

## Analysis Framework

### When Smart Core Wins
- Cross-document entity tracking
- Semantic search (embeddings)
- Dependency traversal (graph relationships)
- Structured metadata queries (tags, phase, domain)

### When Pure Claude Wins
- Single-document queries
- Git history analysis (if not in graph)
- Simple text search (one-off grep)
- Low overhead for trivial questions

### Cost-Benefit Analysis
```
Smart Core Setup Cost: [Neo4j infra + MCP server + ingestion time]
Smart Core Query Cost: [avg tokens per query]
Pure Claude Query Cost: [avg tokens per query]

Breakeven Point: [N queries where Smart Core pays off]
```

---

## Hypotheses to Test

**H1:** Smart Core uses 40-60% fewer tokens for multi-document aggregation (Q1, Q4)
**H2:** Smart Core has higher completeness for structured metadata queries (Q1, Q3)
**H3:** Pure Claude performs better on reasoning/judgment tasks (Q5)
**H4:** Smart Core reduces tool calls by 50%+ for entity searches (Q2, Q4)
**H5:** Quality scores are similar when both find correct info, but Smart Core finds it faster

**Question-Specific Predictions:**
- Q1 (Roadmap status): **Smart Core wins** - phase metadata aggregation
- Q2 (BOM pricing): **Tie or slight Smart Core advantage** - depends if BOM documented
- Q3 (CFO tasks): **Smart Core wins** - owner/deputy metadata filtering
- Q4 (Round A expenses): **Smart Core wins** - financial entity aggregation
- Q5 (Investor readiness): **Pure Claude wins or tie** - requires holistic reasoning, not just data retrieval

---

## Next Steps

1. [ ] Run experiment for all 5 questions (both approaches)
2. [ ] Collect token/time/accuracy data
3. [ ] Analyze results vs. hypotheses
4. [ ] Document findings in `smart_core/Smart-Core-Performance-Results.md`
5. [ ] Update `SMART-CORE-GUIDE.md` with recommended use cases
6. [ ] Consider adding more complex questions if results are unclear

---

## Notes

- **Token counting:** Use VSCode extension API logs or Claude.ai conversation export
- **Time measurement:** Manual stopwatch (wall clock)
- **Accuracy scoring:** Manual review by CTO/CFO against ground truth
- **Control variables:** Same model (Sonnet 4.5), same instructions, same starting context

---

**Status:** 🔴 Experiment designed, ready to execute
