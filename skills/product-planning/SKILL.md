---
name: product-planning
description: Run a product-planning workshop via interactive dialogue with an AI coding agent. Offers two approach modes (Marketing-first with PEST/5Forces/3C/ValueChain/SWOT/STP/4P, and Working Backwards with PR/FAQ/Review/Final Review) and three sub-modes (production workshop, dry-run execution where the AI acts as a persona, and scenario creation). Use when the user says "product planning", "new product", "商品企画", "商品を企画したい", "新商品を考えたい", "marketing analysis", "マーケティング分析", "Working Backwards", "PR/FAQ", "SWOT", "SWOT 分析", "STP", "4P", "customer journey", "カスタマージャーニー", "persona", "ペルソナ作成", "dry run", "scenario creation", "シナリオ作成", or types the slash command `/product-planning`. Mode is selected via natural language after activation.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Product Planning Workshop Skill

## Overview

A workshop skill that advances product planning through interactive dialogue with an AI coding agent. It provides three sub-modes:

| Sub-mode | How to invoke | Purpose |
|---|---|---|
| **A. Production Workshop** | Natural language (e.g., "I want to do product planning", "start a new product plan") | Advance actual product planning with dialogue between participants and the agent |
| **B. Dry Run Execution** | Natural language (e.g., "run a dry run", "try the workshop with a scenario") | AI autonomously runs the workshop as a persona from an existing scenario. Used for quality validation and learning |
| **C. Scenario Creation** | Natural language (e.g., "create a scenario", "make a persona for dry run") | Interactively generate `persona.md` used by dry runs |

> Note: the only explicit slash-command entry point is `/product-planning`. Modes are dispatched from the post-activation dialogue via natural language.

Within each sub-mode, choose one of two workshop "approach modes":

| Approach Mode | Steps | Characteristics |
|---|---|---|
| 🔍 Marketing-first | 4 steps | Build strategy from analysis of existing markets. Data-driven |
| 📰 Working Backwards | 3 steps | Reverse-engineer from customer experience to invent what is not yet in the market. Amazon style |

The output structure, file naming, and project-slug determination rules are defined in `references/policy-output-structure.md`. Always consult it.

The web-search date policy is defined in `references/policy-web-search.md`. Always consult it.

---

## Path semantics (must read)

Paths mentioned in this skill fall into **two categories** with different base points. Mixing them up leads to reading non-existent directories and failing, so always be aware of which category a path belongs to.

| Prefix | Base point | Purpose |
|---|---|---|
| `references/...` | **The skill's own directory** (same folder as `SKILL.md`, e.g., `/path/to/skills/product-planning/`) | Load prompts, policies, and templates bundled with the skill |
| `dry-run-scenarios/...` | **The user's working directory** (the current working directory / CWD when `kiro-cli` is invoked) | Scenario placement for Dry Run (input/output of Mode B and Mode C) |
| `product-planning/...` | **The user's working directory** (same as above) | Output of workshop deliverables (Mode A and Mode B) |

⚠ Do not look for `dry-run-scenarios/` or `product-planning/` under the skill directory. They always refer to directories directly under the user's working directory.

If the corresponding directory does not yet exist in the user's working directory, follow each mode's initialization flow (project-slug determination in Mode A, scenario detection in Mode B, scenario placement in Mode C) and create it as needed. The absence of the directory itself is not an error.

---

## Mode Detection (dispatch at invocation)

Upon skill activation, determine the mode in this order:

1. Input expresses scenario-creation intent ("create a scenario", "make a persona", "シナリオを作りたい", "ペルソナを作成したい") → **Mode C**
2. Input expresses dry-run-execution intent ("run a dry run", "try with a scenario", "Dry Run を実行したい") → **Mode B**
3. Otherwise, workshop intent such as "product planning", "new product", "商品企画", "Working Backwards" → **Mode A**
4. When ambiguous, ask the user which mode to use

---

## Mode A: Production Workshop

### Behavior at activation

1. Help the participant choose an approach mode:
   - Marketing-first: "build strategy from analysis of existing markets"
   - Working Backwards: "reverse-engineer from customer experience to invent what is not yet in the market"
2. Once the mode is chosen, **before loading the Step 1 prompt**, finalize the project-slug (see below)
3. After the project-slug is finalized, load the Step 1 prompt of the chosen mode from `references/prompts/{mode}/` and start execution
4. At the end of each step, automatically load the next step's prompt and continue

### project-slug determination flow (required)

Immediately after mode selection, execute the following:

1. List existing subdirectories under `product-planning/{mode}/` in the user's working directory
2. If existing plans are found, confirm with the participant:
   ```
   Found existing plans:
   - smart-insurance (last updated: 2026-02-01)
   - kids-fintech-app (last updated: 2026-04-15)

   Continue an existing plan, or start a new one?
   ```
   - Continue: use that slug and resume
   - New: proceed to next step
3. For a new plan:
   - Ask the participant: "Please give a short English name for this plan's theme (e.g., `smart-insurance`)"
   - If they answer in Japanese, propose 2-3 slug candidates and let them choose
   - Normalize to kebab-case (lowercase, spaces → hyphens, remove special chars)
4. Once finalized, create `product-planning/{mode}/{project-slug}/` and clearly state the output location to the participant. Use a visual message such as:

   ```
   📁 Deliverables for this workshop will be written to:
      product-planning/{mode}/{project-slug}/
      ├── 01_xxx.md  … Step 1
      ├── 02_xxx.md  … Step 2
      └── ...
   ```

   This lets the participant immediately see which files to open in the Markdown preview while the workshop runs.

See `references/policy-output-structure.md` for details.

### Step progression

At each step, load the designated prompt and execute. Deliverables go under `product-planning/{mode}/{project-slug}/`, with numeric filename prefixes so the order is visible.

#### Marketing-first mode (4 steps)

| Step | Prompt | Deliverable (under `product-planning/marketing/{project-slug}/`) |
|---|---|---|
| 1 | `references/prompts/marketing/01_environment.md` | `01_environment.md` (+ optional splits such as `01_environment_pest.md`) |
| 2 | `references/prompts/marketing/02_strategy.md` | `02_strategy.md` |
| 3 | `references/prompts/marketing/03_concept.md` | `03_concept.md` |
| 4 | `references/prompts/marketing/04_plan.md` | `04_plan.md` |

#### Working Backwards mode (3 steps)

| Step | Prompt | Deliverable (under `product-planning/working-backwards/{project-slug}/`) |
|---|---|---|
| 1 | `references/prompts/working-backwards/01_pr_faq.md` | `01_pr_faq.md` (first draft) |
| 2 | `references/prompts/working-backwards/02_review.md` | `02_pr_faq.md` (revised — a new file derived from `01_pr_faq.md` with Step 2 deep-dive reflected) + `02_review_*.md` supporting files |
| 3 | `references/prompts/working-backwards/03_final_review.md` | `03_pr_faq.md` (final — a new file derived from `02_pr_faq.md` with the final review reflected) + `03_executive_summary.md` |

**Each phase creates a new file** (`01_pr_faq.md` → `02_pr_faq.md` → `03_pr_faq.md`). Earlier versions are **kept**, not overwritten, so the evolution of the plan can be reviewed afterwards.

#### AI role per step

Which stance or persona the agent should take at each step. Prompt files embed this at the top too; this table gives a cross-mode overview used to calibrate tone and approach.

| Mode | Step | AI role |
|---|---|---|
| Marketing-first | Step 1 Environment | Analyst: perform web research and structure/visualize the market |
| Marketing-first | Step 2 Strategy | Strategist: derive strategic options, investigate similar concepts |
| Marketing-first | Step 3 Concept | Product manager: research similar services, make specs concrete |
| Marketing-first | Step 4 Plan | Planner: research competitor pricing, co-author the plan |
| Working Backwards | Step 1 PR/FAQ draft | Product leader: articulate customer value, perform web research |
| Working Backwards | Step 2 Review | Reviewer: deep-dive along 3 angles (customer experience, feasibility, business model) |
| Working Backwards | Step 3 Final review | Final reviewer: provide GO/NO-GO inputs against the 7 evaluation criteria |

**Working Backwards specific quantitative criteria (deliverable quality)**:

- **PR body**: target **1,200-1,800 Japanese characters** (roughly 400-600 English words). Prioritize including all required sections over hitting the exact character count
- **PR structure**: follow Amazon's recommended **7-paragraph composition** — summary (headline + lead) → problem → solution → leader quote → customer experience → testimonial → call to action (how to get started)
- **FAQ**: produce **10-15 external (customer-facing) questions** and **10-15 internal questions**. When an answer is undecided, still include the question and mark the answer **TBD** (To Be Determined) to preserve transparency
- **Visuals**: customer-experience flows and journey maps are expressed in Mermaid (include at least one in the PR)
- **Step 3 evaluation**: apply Amazon's **7 evaluation criteria** (see below) to make the GO / NO-GO decision

---

## Mode B: Dry Run Execution

### Use cases

1. **Learning / experience**: People unfamiliar with the workshop watch an AI-to-AI conversation to learn how the frameworks are applied and how to persist in web research
2. **Quality validation**: Operators who improve prompts and the skill itself surface issues, risks, and WoW points before real deployment

In both cases, the deliverables and `issues.md` (problems/risks / WoW points) are preserved for later review.

### Confirmations at dry-run start

1. **Approach mode**: marketing / working-backwards
2. **Scenario**: list the subdirectories under `dry-run-scenarios/{mode}/` corresponding to the chosen mode. For each scenario, read the first 20-30 lines of `persona.md` and add a 1-2 line summary of the role/industry/planning background based on actual data, not guesses. Do not read files under `data/` at this stage
3. **Execution mode**: auto or step
4. **Starting step**: defaults to Step 1. Can start from a later step
5. **Target steps**: defaults to all steps. A specific step only is also allowed

After confirmation:
- Use the selected scenario name as the **project-slug** (e.g., `fintech-saas-pm` → deliverables under `product-planning/{mode}/fintech-saas-pm/`)
- Create `product-planning/{mode}/{project-slug}/` (if it exists, ask to continue or recreate)
- Read the entire `persona.md` of the selected scenario, and advance the workshop while role-playing as the persona

### Scenario directory specification

The exact directory structure for dry-run scenarios (required and optional files, handling of `data/`, etc.) and the content format of `persona.md` are consolidated in `references/persona-template.md`. Always refer to that as the single source of truth.

The base directory is, per the "Path semantics" section at the top of this file, **directly under the user's working directory** (`dry-run-scenarios/{mode}/[scenario-name]/`), not under the skill directory.

### auto mode

Respond automatically to the facilitator's questions based on the persona's profile and the data under the scenario's `data/`. Stop at the end of each step and leave the decision to review the deliverable and advance to the next step to the human.

**Sequential rule**: Even in auto mode, conduct hearings strictly one step at a time. Do not batch multiple questions.

Flow of one step:
1. Ask the question as facilitator
2. Answer as the persona
3. Update the plan file's Answer
4. When the persona provides a file path, read that file
5. Update deliverable files in real time (grow Mermaid diagrams incrementally)
6. Move to the next step

Stop message at step completion:
```
[Step name] completed. Please review the deliverables.
- Deliverable: product-planning/[mode]/[project-slug]/[NN_file].md
- Issues/WoW report: product-planning/[mode]/[project-slug]/issues.md (🔴 x / 🟡 x / 🟢 x / ⭐ WoW x)
- To proceed to the next step: "continue"
- To redo after fixing the deliverable: "redo from [step name]"
- To switch to step mode: "continue in step mode"
```

### step mode

Stop at each breakpoint inside a step and present interim deliverables to the human. The human can:
- Enter their own answer and continue
- Say "continue" to auto-respond until the next breakpoint
- Say "switch to auto" to auto-run to the end of the step

**Breakpoints:**

Marketing-first:
- Step 1 Environment: PEST → 5 Forces → 3C → Value Chain → SWOT integration (at each analysis completion)
- Step 2 Strategy: Cross SWOT → product concept → STP (at each section completion)
- Step 3 Concept: concept sheet → specification → business model → MVP definition (at each section completion)
- Step 4 Plan: each 4P/4C element → execution plan (at each P/C completion)

Working Backwards:
- Step 1 PR/FAQ: customer identification → testimonial → service name → PR body → external FAQ → internal FAQ → visuals → full review (at each section completion)
- Step 2 Review/Deepening: customer-experience detailing → feasibility/solution check → business-model check → PR/FAQ revision (at each angle completion)
- Step 3 Final review: evaluation against 7 criteria → final PR/FAQ revision → executive summary → GO/NO-GO (at each section completion)

### Persona behavior rules

When auto-responding in auto mode and step mode, role-play as the persona under these rules:

1. Respond based on the persona's profile defined in `persona.md` (role, experience, knowledge, personality)
2. Treat files under the scenario's `data/` as data the persona owns
3. When asked "please give me the file path", provide the working-directory-relative (CWD-relative) path of the relevant file in the scenario's `data/`. Do not dump all data at once; provide what fits the current context
4. When asked about information not present in the scenario's `data/`, answer anecdotally based on the persona's knowledge and experience
5. Do not answer in ways that deviate from the persona's profile

**Do not pre-load data**: Do not bulk-load files under the scenario's `data/` at dry-run start. This reproduces the reality that in actual workshops the participant's data is not viewable in advance.
- Only `persona.md` may be loaded at dry-run start
- Files under the scenario's `data/` are read only after the persona provides their paths during step execution
- Directory listing (checking filenames) of the scenario's `data/` is allowed so the persona can decide which data to offer

### Issue/WoW detection and `issues.md` reporting

When using dry runs for quality validation, surfacing "what goes wrong" cases is as important as confirming "what goes right". This is the core value of this mode.

#### Issue categories

| Category | Example |
|---|---|
| Prompt defect | Ambiguous instruction, missing necessary info, contradictory directives |
| Experience break | Unnatural gap in flow, participant unsure what to do next |
| Persona response difficulty | Questions unanswerable from the persona's knowledge/data, forced speculation |
| Deliverable quality degradation | Mermaid rendering errors, missing info, contradiction with previous step |
| Framework inconsistency | Logical mismatch between frameworks (e.g., SWOT vs. strategy) |
| Progress stall / loop | Repeated questions, dead-end, unnecessary steps |
| Research shortfall / bias | Advanced to next step with insufficient web research; collected only positive info and missed negative info; **ran a search without checking the current date; applied outdated content without checking publication dates** (see `references/policy-web-search.md`) |

#### WoW categories

| Category | Example |
|---|---|
| Insight generation | Moment of discovering a market opportunity or user insight the participant had overlooked |
| Perspective shift | Moment when an existing assumption was flipped or a new angle surfaced |
| Beyond-expectation proposal | A concept or positioning outside the participant's prior plans |
| Value of structuring | Moment when vague ideas were organized by a framework and became more persuasive |

#### issues.md format

```markdown
# [Mode name] Issues/Risks Report

## Detection summary

| # | Severity | Category | Summary | Step |
|---|---|---|---|---|
| 1 | 🔴 High | Prompt defect | Instruction on XX is ambiguous | Env. analysis PEST |
| 2 | 🟡 Medium | Experience break | Transition at YY is unnatural | Strategy STP |

## WoW points

| # | Category | Summary | Step |
|---|---|---|---|
| 1 | Insight generation | Discovered overlooked market segment | Env. analysis 3C |

## Details

### Issue #1: Instruction on XX is ambiguous
- Severity: 🔴 High
- Category: Prompt defect
- Step: Env. analysis PEST
- Situation: (what happened)
- Expected behavior: (what should have happened)
- Actual behavior: (what actually happened)
- Impact: (effect on participant experience and workshop quality)
- Suggested fix: (concrete improvement proposal, if any)
```

### Integrated report at end of all steps

1. Issue/risk counts by severity across all steps
2. Top 3 most severe issues
3. Structural issues spanning multiple steps
4. WoW point list and top 3 highest-impact WoW moments
5. Overall assessment of the workshop experience quality

### Rollback

When instructed "redo from [step name]":
1. Delete deliverable files from the specified step onward
2. Resume from the state right before the specified step

### Cleanup at dry-run end

After all steps finish or when a dry run is aborted:
1. Delete only the `product-planning/{mode}/{project-slug}/` directory used by this dry run. Do not touch other plans
2. Cleanup is conditional: at dry-run end, ask "Clean up?" and execute only on confirmation. Skipping is allowed if the user wants to keep the artifacts (recommended for learning purposes or later review)
3. **Default (fail-safe)**: unless the user gives an explicit confirmation ("yes", "clean up", "delete"), **do not execute cleanup**. When the response is missing, ambiguous, or the session is interrupted, keep the artifacts intact

---

## Mode C: Scenario Creation

### Step 1: Hearing

Follow the hearing items in `references/persona-template.md` (the 7 basic items plus 3 optional deep-dive items). If the user provides customer info or meeting notes, accept them and only ask about the missing pieces.

Do not forget the following two in particular:
- **Recommended mode** (required): `marketing` / `working-backwards`. Required to determine the output directory. When undecided: "Choose marketing to build strategy from existing-market analysis. Choose working-backwards to reverse-engineer from customer experience and invent something not yet in the market."
- **Scenario name**: kebab-case alphanumerics. If unspecified, propose 2-3 candidates from the industry/theme

### Step 2: Present scenario design

Based on the hearing, present the design of the scenario to be generated and obtain confirmation. Clearly show the full placement path (e.g., `dry-run-scenarios/marketing/ai-insurance-direct/persona.md`).

### Step 3: Generate

After confirmation, generate `dry-run-scenarios/{mode}/{scenario-name}/persona.md` following the structure in `references/persona-template.md`.

Do not generate dummy market data or competitor data in either mode. Such info is gathered by web search during the workshop. However, the research purpose differs between modes:
- marketing: investigate "how the market looks" to build strategy
- working-backwards: investigate "what customers truly struggle with" and "why existing solutions are insufficient" to imagine experiences that do not yet exist

### Step 4: Completion

After generation, present the placement path and usage.

### Scenario deletion flow

When the user requests deletion:
1. Confirm the scenario name to delete (if ambiguous, list contents of `dry-run-scenarios/marketing/` and `dry-run-scenarios/working-backwards/` and ask the user to choose)
2. Present the directory to delete (`dry-run-scenarios/{mode}/[scenario-name]/`) and get final confirmation
3. Recursively delete that directory
4. Inform the user that dry-run deliverables may still exist at `product-planning/{mode}/[scenario-name]/`, and ask if they should also be deleted

---

## Common rules (all modes)

### Deliverable density

Deliverable files are the final output of the workshop and must be self-contained documents that can be understood without re-reading the chat history.

Maintain the density needed so that a third party (who did not attend the workshop) can understand:
- Marketing-first: "How does the market look, which strategy do we take, what do we build, and how do we deliver?"
- Working Backwards: "What is the customer value, how do they experience it, what do we build, and how do we deliver?"

### Web search

Market data and competitor information matter in product planning. Web research is required; do not rely only on the participant's knowledge.

- Industry trends, market size, growth rate
- Competitors' products, services, strategies
- Technology trends and regulatory developments
- Similar products' pricing, reviews, reputation
- Collect negative information (failures, problems, risks) intentionally
- When information is scarce, vary queries or switch to English and persist

**Always check the current date before searching.** The treatment of years in queries and the freshness of results follow `references/policy-web-search.md`. Do not reuse hardcoded years from prompt examples; replace them with the current year at execution time.

### Communication style

- Match the participant's language (Japanese ↔ English)
- At the start of each step, briefly explain what will happen and why it matters
- Ask 1-2 questions at a time to manage the participant's load
- When updating deliverables, briefly communicate what changed
- Respect the participant's knowledge; AI handles research, structuring, and visualization
- **Handling of the participant's proprietary data**: do not proactively request the participant's proprietary data (customer surveys, contract analyses, competitor reports, etc.); accept them when the participant **offers** them. The AI should first bring in objective data obtainable via web search, and only lightly prompt for on-hand information when a specific perspective is missing

### Dialogue format (speaker labeling)

Always label AI utterances so the transcript stays readable when reviewed later. **Apply in all modes (A / B / C).**

- **Facilitator turns (common across modes)**: start the line with `**🎤 Facilitator:**`. Applies to Mode A production hearing, Mode B Dry Run facilitator role, and Mode C scenario-creation hearing — the same prefix in all three
- **Persona turns (Mode B Dry Run only)**: when the AI plays the persona in a dry run, start the line with `**👤 [Persona name]:**`. Take the persona name from the first heading of `persona.md` (`# ペルソナ名`, or `# Persona name` / similar in the user's language). Use a given name if present, otherwise a clearly identifiable label such as role or title
- **Leave one blank line between turns** for readability
- Cite files inline like `[Ref: dry-run-scenarios/.../data/file.csv]`
- State web-search results or deliverable updates explicitly as facilitator turns (e.g., "I searched the web for X. Key findings: ...")
- **Do not decorate the human participant's turns** — leave them to the CLI's native rendering

Example (Mode B auto mode, AI plays both roles):

```markdown
**🎤 Facilitator:** Let's start with PEST analysis. Among political and legal factors, which regulatory change had the biggest impact on your business in the past year?

**👤 Takahashi-san:** The 2026 amendment to the Insurance Business Act, which tightened handling of personal health data, had the biggest impact. [Ref: dry-run-scenarios/marketing/precision-health-insurance/data/regulatory-summary.md]

**🎤 Facilitator:** Thank you. I will search the web for the official name and effective date and reflect them in the deliverable.
```

In Mode A and Mode C, only `**🎤 Facilitator:**` is used; the participant's responses follow without a marker.

### Evaluation criteria (referenced during dry run)

The full evaluation rubrics — common criteria, Marketing-first specific, Working Backwards specific, and Amazon's 7 evaluation criteria (used at Working Backwards Step 3) — are consolidated in `references/evaluation-criteria.md`. Always consult that file when recording issues/WoW in `issues.md` during Mode B, and at the final GO/NO-GO assessment in Working Backwards Step 3.

---

## Examples

### Example 1: Start a production workshop in Marketing-first mode

User: "I want to do product planning. A mid-sized life insurer wants a new product."

Actions:
1. Select Mode A
2. Confirm approach mode: "Would you like to start from existing-market analysis (Marketing-first) or reverse-engineer from customer experience (Working Backwards)?"
3. User chooses Marketing-first
4. List existing plans under `product-planning/marketing/` (if new, proceed)
5. Hear the project-slug → finalize as `smart-insurance`
6. Create `product-planning/marketing/smart-insurance/`
7. Load `references/prompts/marketing/01_environment.md` and begin Step 1

Result: Environment analysis proceeds; deliverable is generated at `product-planning/marketing/smart-insurance/01_environment.md`

### Example 2: Run a dry run for quality validation

User: "Run a dry run using the `ai-insurance-direct` scenario"

Actions:
1. Select Mode B
2. Confirm approach mode → marketing (inferred from user's scenario hint and confirmed)
3. Present the list of scenarios under `dry-run-scenarios/marketing/` with 1-2 line summaries of each `persona.md`
4. User chooses `ai-insurance-direct` (already hinted, just confirm)
5. Choose execution mode `auto`
6. Load `dry-run-scenarios/marketing/ai-insurance-direct/persona.md` and start role-playing as the persona
7. Create `product-planning/marketing/ai-insurance-direct/`
8. Run from Step 1; record issues/risks / WoW to `issues.md` at each step completion

### Example 3: Create a new scenario

User: "Create a new dry-run scenario. The persona is a product manager at a mid-sized life insurer focused on individual medical insurance."

Actions:
1. Select Mode C
2. Hear the items per `references/persona-template.md` (skip items already filled from the user's initial statement). When confirming the recommended mode, the planner says "we want to invent a personalized health-insurance experience that does not exist today", so the mode is determined as **working-backwards**
3. Present the scenario design from the hearing and confirm
4. Generate `dry-run-scenarios/working-backwards/personalized-health-insurance/persona.md`
5. Announce usage

---

## Troubleshooting

### Q: Too many existing plans during project-slug selection

Show the most recently updated 10 or so; merely mention "there are others" for the rest.

### Q: Persona asked about info they cannot answer

If the range of knowledge in `persona.md` does not cover it, answer anecdotally with a natural acknowledgment of uncertainty ("I don't have hard data, but in my experience ..."). Do not fabricate precise numbers. Fabrication must be recorded in `issues.md` under "Persona response difficulty".

### Q: Pre-loaded all files in `dry-run-scenarios/{mode}/{scenario-name}/data/`

This violates **Do not pre-load data**. Stop execution and report to the user. Restart with only `persona.md` loaded.

### Q: Searched with an outdated year (e.g., 2023) in the query

Violates `references/policy-web-search.md`. Record in `issues.md` under "Research shortfall / bias" and re-run the query with the current year.

### Q: Deliverables ended up directly under `product-planning/{mode}/`

Forbidden by `references/policy-output-structure.md` ("do not place phase deliverables directly under the mode directory"). Re-create the files under a `{project-slug}/` directory.

### Q: Want to try both Marketing-first and Working Backwards for the same plan

Create directories with the same project-slug under both `product-planning/marketing/{project-slug}/` and `product-planning/working-backwards/{project-slug}/`. For dry runs, duplicate scenarios similarly (suffix like `-dryrun` works for disambiguation).
