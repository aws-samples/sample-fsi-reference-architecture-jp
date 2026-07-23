---
name: customer-context-manager
description: >-
  Automatically manage customer-specific context that LLMs cannot know on their own —
  abbreviations, internal system names, org structures, key contacts, deal history,
  and relationship notes. Stores context as human-readable Markdown files organized
  per customer, following XDG Base Directory Specification. The agent reads context
  automatically when a customer is mentioned in conversation, and updates it when new
  information surfaces — no explicit command needed. Use this skill whenever the user
  mentions a customer name, discusses a sales meeting, references a deal or opportunity,
  asks about a contact person, or works on any customer-related task. Also use when
  the user wants to register, update, search, or review customer information.
  Trigger keywords: "customer context", "顧客コンテキスト", "お客様情報",
  "顧客情報", "取引先", "account", "customer", "お客様", "略称登録",
  "組織図", "キーパーソン", "商談メモ", "関係者", "コンテキスト更新",
  "context update", "who is", "誰", "どの会社".
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Customer Context Manager

Automatically manage customer-specific context that LLMs cannot know on their own.
The agent reads relevant context when a customer appears in conversation and updates
it when new information is discovered — without requiring explicit user commands.

## Why This Skill Exists

LLMs lack customer-specific knowledge that humans accumulate through meetings,
emails, and internal discussions:

- **Abbreviations and aliases**: Customers often have internal shorthand that only insiders know
- **System and project names**: Internal system names like "Any Core Banking" are never public
- **Organizational structure**: Who reports to whom, who makes decisions, who holds budget
- **Relationship history**: Past proposals, outcomes, sensitivities, preferences
- **Communication preferences**: Preferred channels, response patterns, meeting styles

Without this context, AI agents produce generic outputs or make incorrect assumptions.

## Data Storage

Configuration follows the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/latest/).
Context data is stored in a user-configurable directory.

- **Context data**: `~/Documents/customer-context/` (default, configurable in config)
- **Configuration**: `$XDG_CONFIG_HOME/customer-context-manager/` (default: `~/.config/customer-context-manager/`)

### Directory Structure

```
~/Documents/customer-context/
├── customers/
│   ├── <customer-slug>/
│   │   ├── profile.md          # Company overview, aliases, industry
│   │   ├── people.md           # Contacts at this customer (and partners)
│   │   ├── organization.md     # Org structure, decision-making flow, change history
│   │   ├── systems.md          # Known systems, tech stack, constraints
│   │   ├── history.md          # Key turning points (not CRM-duplicating activity logs)
│   │   ├── terms.md            # Customer-specific terminology / glossary
│   │   └── notes.md            # Free-form notes, communication preferences
│   └── ...
├── people/
│   ├── internal.md             # Internal team members (shared across customers)
│   └── partners.md            # Partner companies (cross-customer level info)
└── index.md                    # Master index: customer slug → display name + aliases + group
```

### Configuration

```
$XDG_CONFIG_HOME/customer-context-manager/
└── config.md                   # User preferences and schema customization
```

## First-Time Setup

When invoked for the first time (no `config.md` exists):

1. Resolve XDG paths (respect environment variables, fall back to defaults)
2. Create the directory structure
3. Create `config.md` with defaults:
   ```markdown
   # Customer Context Manager Configuration

   ## Data Directory
   - data_directory: ~/Documents/customer-context

   ## Preferences
   - auto_update: true          # Automatically update context from conversations
   - auto_read: true            # Automatically load context when customer is mentioned
   - confirm_updates: false     # Ask before writing updates (set true for cautious mode)
   - language: ja               # Primary language for context files
   - git_enabled: true          # Track changes with git (auto-commit on updates)

   ## Schema
   Use default templates. Customize by editing template files in this directory.
   ```
4. Create `index.md`, `people/internal.md`, and `people/partners.md` with empty templates
5. Inform the user that setup is complete

## Core Behaviors

### Automatic Context Reading

When a customer name, alias, or abbreviation appears in conversation:

1. Search `index.md` for matching entries (fuzzy match on aliases)
2. Load the relevant customer directory files
3. Use loaded context silently to inform responses — do not dump raw context unless asked

If the customer is not found in the index, note this internally. If the conversation
reveals enough information to create an entry, do so automatically.

### Automatic Context Updates

When new customer information surfaces in conversation (meetings, user statements,
documents being processed):

1. Identify new facts: names, roles, system names, decisions, preferences
2. Determine which file(s) to update
3. Write the update immediately (or ask first if `confirm_updates: true`)
4. Briefly acknowledge what was saved (one line, not verbose)

Updates are append-friendly — add new information without removing existing content.
Include dates on all entries for freshness tracking.

### What to Save

When in doubt, save it. Storage cost is negligible and information that seems
unimportant now may become relevant later. General guidelines:

- **Always save**: Person names + roles/departments, system names, terminology,
  organizational changes, key decisions, relationship dynamics
- **Save with date**: Proposals and their outcomes, technical constraints discovered,
  competitive intelligence, communication preferences
- **Let CRM handle**: Detailed activity logs, meeting-by-meeting notes, opportunity
  stage changes. If a CRM integration skill is available, query it on demand rather
  than duplicating data here

The user can mark specific entries as important with `[!important]` inline. This
has no automated effect but serves as a visual signal when reading context.

### Source Tracking

Record where information came from so it can be verified later. Format:

- **In tables**: Add a `Source` column. Use plain text for local/verbal sources
  (e.g., `account-plan 2026-05-12`, `meeting 2026-03-19`). Use Markdown links
  when a URL is available (e.g., `[activity 2026-01-28](https://crm.example.com/...)`).
- **In prose sections**: Use Markdown footnotes for important facts:
  ```markdown
  - Contract value: $10M/3 years[^1]

  [^1]: account-plan 2026-05-12
  [^2]: [activity 2026-03-19](https://crm.example.com/task/xxx)
  ```

Do not add source annotations to every line — only to facts that may need
verification later (financial figures, key decisions, dates, quotes).
Local file paths are not useful as sources and should be omitted.

### Classifying People

Before adding a person to a customer's `people.md`, check whether they already
exist in `people/internal.md` or `people/partners.md`. A name mentioned in a
customer meeting may belong to an internal team member or partner rather than a
customer contact. Steps:

1. Search `people/internal.md` for the name
2. Search `people/partners.md` for the name
3. If found, do not duplicate into the customer's `people.md` — update the
   existing entry if new information was learned
4. If not found in either, add to the customer's `people.md` as a customer contact

When uncertain about a person's affiliation (customer vs internal vs partner),
use conversation context clues (e.g., "our team", "our side", job titles like
"technical consultant", "account manager") to classify. If still ambiguous, ask the user.

### Handling Ambiguous Names

People with the same surname may exist within a single customer. When recording
a person:

- Include department or contextual information to distinguish them when possible
- If disambiguation is not possible at the time of recording, save what is known
  and note the ambiguity (e.g., "Tanaka-san (department unknown, possibly different from Tanaka-san in Sales)")
- When later information clarifies the distinction, update the entry

Do not block on perfect identification — partial information is better than none.

### Renaming and Merging Customers

Customer identity changes over time: companies rename, merge, split off, or get
absorbed. **Keep the slug and display name aligned with the current correct name** —
do not freeze an outdated slug. A rename is not a single file edit; it is one
operation that automatically carries the following follow-up updates so nothing is
left pointing at the old name:

When a customer is **renamed** (slug `<old>` → `<new>`):

1. **Move the directory** `customers/<old>/` → `customers/<new>/` (use `git mv` so
   history is preserved when git is enabled).
2. **Update `index.md`**: set the new Slug and Display Name, and **add the old
   name and old slug to Aliases** so the customer is still findable by its former
   name.
3. **Record the change in `profile.md`**: note the rename/merger/spin-off and the
   date under Basic Information or Notes (what it was, what it became, why).
4. **Fix inbound references**: search the data directory for the old slug/old name
   and update every place that points to it — e.g. `people/partners.md` Customers
   column, group parent/child references in other customers' files, and (if the
   internal companion is active) `internal-config.md` account groupings.
5. **Commit** with an intent-revealing message (e.g.
   `rename any-bank → any-bank-renamed: company renamed 2026-04-01`).

When two customers **merge** (2 → 1):

- Choose the surviving slug = the new/correct company name.
- Merge the disappearing customer's file contents into the survivor (history,
  people, systems — do not lose accumulated context).
- Collect the disappearing slug, display name, and former aliases into the
  survivor's Aliases.
- Record the merger and date in `profile.md`, then remove the old directory and
  index row (via `git mv`/commit so history remains).

For a **spin-off/split** (1 → 2), create the new customer entry, copy the relevant
shared context, and cross-reference both in their Aliases/profile so the lineage is
traceable.

The guiding principle: the slug and display name always reflect the *correct
current* name, and Aliases + profile.md preserve the *history* so old names still
resolve.

### Manual Commands

Users can also give explicit instructions:

| Command | Action |
|---------|--------|
| `<customer>の情報を見せて` / `show context for <customer>` | Display all context for a customer |
| `<customer>を登録して` / `register <customer>` | Create a new customer entry interactively |
| `<info>を保存して` / `save <info>` | Explicitly save specific information |
| `顧客一覧` / `list customers` | Show all registered customers |
| `<customer>の<category>を更新` / `update <category> for <customer>` | Edit a specific context file |
| `検索: <term>` / `search <term>` | Search across all customer contexts |

## File Templates

For a complete example showing the expected density and quality of context files,
see [references/sample-context.md](references/sample-context.md). The templates
below show the minimum structure — aim for the richness demonstrated in the sample.

### index.md

```markdown
# Customer Index

| Slug | Display Name | Aliases | Industry | Group | Status |
|------|-------------|---------|----------|-------|--------|
| any-bank | Any Bank | AB | Banking | Any Group | Active |
| any-securities | Any Securities | AS | Securities | Any Group | Active |
| any-insurance | Any Insurance | AI | Insurance | - | Active |
```

The Group column captures corporate group relationships (parent company, keiretsu,
holding company affiliations). Use `-` for standalone customers.

**Aliases is the name-resolution entry point.** Put *every* name a human (or an
internal tool) might use to refer to this customer here, so the customer can be
found no matter which name appears in conversation:

- Abbreviations / informal shorthand (e.g., `AB`)
- Formal legal name and the short form (e.g., with/without `株式会社` / `Inc.`)
- Japanese and English names
- **Former names** kept after a rename (so the customer is still findable by old name)
- Group/brand names the customer is known by
- Registered name in an internal CRM if it differs from reality (the internal
  companion skill writes this back here)

If you ever fail to resolve a name that turns out to be a known customer, add that
name to Aliases so the next lookup succeeds.

### customers/<slug>/profile.md

```markdown
# <Display Name>

## Basic Information
- Formal name: 
- Common aliases: 
- Industry: 
- Size: 
- Headquarters: 
- Website: 

## Relationship Summary
- First engagement: 
- Current status: 
- Primary contact: 

## Revenue
<!-- Sales-side financial information: contracts, deal size, spend -->

## Strategic Context
<!-- Customer's business priorities and how they relate to your engagement -->

## Notes
```

### customers/<slug>/people.md

```markdown
# People — <Display Name>

## Customer Contacts

| Name | Department | Title | Role in Decisions | Email | Notes |
|------|-----------|-------|-------------------|-------|-------|

## Partner Contacts

Partners assigned to specific projects with this customer.

| Name | Company | Role | Project/Context | Email | Notes |
|------|---------|------|-----------------|-------|-------|
```

### customers/<slug>/organization.md

```markdown
# Organization — <Display Name>

## Current Structure
<!-- Describe org hierarchy relevant to your engagement -->

## Decision-Making Flow
<!-- Who approves what: technical decisions, budget, contracts -->

## Key Departments

## Change History
<!-- Track reorganizations. Newest first. -->

### YYYY-MM-DD: <Change Description>
- Old: <previous structure>
- New: <new structure>
- Impact: <how this affects engagement>
```

### customers/<slug>/systems.md

```markdown
# Systems & Technology — <Display Name>

## Known Systems

| System Name | Category | Technology | Notes |
|-------------|----------|-----------|-------|

## Technical Constraints
<!-- Regulatory requirements, security policies, network restrictions -->

## Technology Preferences
```

### customers/<slug>/history.md

```markdown
# History — <Display Name>

Record key turning points only — not routine meeting logs. For detailed activity
history, query the CRM if available.

## Key Events

### YYYY-MM-DD: <Event Title>
- What happened: 
- Significance: 
- Impact on relationship: 

## Past Proposals

| Date | Topic | Outcome | Reason |
|------|-------|---------|--------|
```

### customers/<slug>/terms.md

```markdown
# Terminology — <Display Name>

## Glossary

| Term | Meaning | Context | Date Added |
|------|---------|---------|------------|
```

### customers/<slug>/notes.md

```markdown
# Notes — <Display Name>

## Communication Preferences
- Preferred channel: 
- Response patterns: 
- Meeting preferences: 

## Competitive Landscape
<!-- Other vendors, competing solutions -->

## Sensitivities
<!-- Topics to handle carefully, past negative experiences -->

## Free Notes
```

### people/internal.md

```markdown
# Internal Team Members

Members listed here may be relevant across multiple customer engagements.

| Name | Role | Expertise | Notes |
|------|------|-----------|-------|
```

### people/partners.md

```markdown
# Partner Companies

Cross-customer partner information. For project-specific assignments,
see each customer's people.md.

| Company | Relationship | Domains | Key Contacts | Customers |
|---------|-------------|---------|--------------|-----------|
```

## Context Reading Priority

When loading context for a conversation, prioritize based on the task:

1. **Always load**: `index.md` (lightweight, needed for name resolution)
2. **When customer is mentioned**: `profile.md`, `terms.md` (identity and vocabulary)
   - If the customer belongs to a group (per index.md), also load the parent
     company's `terms.md` for group-wide terminology
3. **When discussing people**: `people.md`, `people/internal.md`
4. **When discussing architecture/technology**: `systems.md`
5. **When planning engagement**: `history.md`, `organization.md`, `notes.md`
6. **When writing reports or proposals**: All files for that customer

## Slug Generation

Customer slugs are generated from the display name:
- Lowercase
- Replace spaces and special characters with hyphens
- Remove consecutive hyphens
- For Japanese names, use romanized form (e.g., `any-bank`)
- Keep slugs short but recognizable

## Search

When searching across customers:
- Search all Markdown files under `customers/` and `people/`
- Return matches with file path and surrounding context
- Support both exact and fuzzy matching for Japanese text

## Integration with Other Skills

This skill provides context that other skills can consume. When another skill is
processing customer-related work (reports, proposals, meeting notes), this skill's
context should be loaded automatically to provide accurate names, terminology, and
background.

The skill does not depend on any specific CRM or external tool. It operates purely
on local Markdown files. Extensions for CRM integration should be implemented as
separate companion skills.

## File Write Scope

This skill writes to:
- `$XDG_CONFIG_HOME/customer-context-manager/` (configuration)
- The data directory specified in config (default: `~/Documents/customer-context/`)

It never modifies its own SKILL.md or files outside these locations.

## Git Version Control

When `git_enabled: true` (default), the data directory is managed as a git repository:

### Setup
- On first-time setup, run `git init` in the data directory if not already a repo
- Create a `.gitignore` if needed (empty by default — track everything)

### Auto-Commit
- After every context update (file create or modify), stage the changed files
  and commit with a descriptive message
- Commit message format: `update <customer-slug>/<file>: <brief description>`
- Examples:
  - `update any-bank/people: add Tanaka-san (Digital Banking)`
  - `update any-bank/terms: add CORE-Next terminology`
  - `update index: register new customer Any Insurance`
- Batch multiple changes in a single conversation into one commit when practical

### Benefits
- Full history of context changes with timestamps
- Ability to diff and revert incorrect updates
- Optional push to a private remote for backup

### Disabling
Set `git_enabled: false` in config.md to disable. No git operations will be performed.
