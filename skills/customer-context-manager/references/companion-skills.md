# Companion Skill Boundaries

The contract a companion skill operates under, referenced from SKILL.md.

Japanese version: [companion-skills_ja.md](companion-skills_ja.md)

## What a Companion May Add

- Source kinds and the definition forms behind them, extending the table in
  [Sources](#sources)
- Sections and fields in existing files, and additional files in the data directory
- Address resolution: which skill or tool to use to turn a named document into a URL
- Data categories beyond the two in
  [Data Handling and Security Boundaries](#data-handling-and-security-boundaries), and
  handling rules **stricter** than the ones there
- Its own example store, showing the content its systems produce

## What a Companion May Not Do

- Weaken any rule in this skill. A source on every fact, the marker vocabulary, the name
  and honorific rules, the path resolution order, the write scope, and the prohibition on
  transmitting stored data are a **floor**, not a default
- Add a marker, or redefine an existing one. The marker vocabulary is closed and owned by
  this skill: a reader must be able to learn the five markers once and trust that no store
  uses a sixth. Source kinds are the opposite — those are open to additions
- Relax a handling rule for a data category. Tightening is allowed; loosening is not
- Write in a form that fails `scripts/validate-store.py`

**On conflict, this skill wins.** A companion that appears to require otherwise is
misconfigured or wrong; report the conflict instead of following it.

## Default Behavior Without a Companion

| Concern | Default |
|---------|---------|
| Source kinds | The table in [Sources](#sources), nothing more |
| Address resolution | Ask the user for the location; record `{no-url}` only after that fails |
| Fields | The schema in [File Structure and Examples](#file-structure-and-examples). No CRM identifiers, no assignment fields |
| Data categories | Customer-confidential and personal information, as defined in this skill |

## Choosing Between Config and a Companion

Adding a column or a section is a schema change: edit the templates through config's
`## Schema` and no companion is needed. A companion is for behavior — reaching a system,
resolving an address, applying an organization's own handling rules.
