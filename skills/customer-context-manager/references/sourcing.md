# Sourcing and Incompleteness Markers

Provenance and gap-marking rules referenced from SKILL.md. Read this before writing
a Source field or recording a value you are not sure of.

Japanese version: [sourcing_ja.md](sourcing_ja.md)

## Markers for Incomplete Information

Incompleteness is recorded with one of four fixed markers, written in braces. They exist so
a gap survives being read months later, quoted into another file, or mixed into surrounding
prose — a bare `?` does not: it is one character, it collides with ordinary punctuation, and
it is effectively unsearchable.

There are two independent axes. **Value** markers say something is missing or made up.
**Trust** markers say the fact may not hold. A row can carry one of each.

| Marker | Axis | Means | Example |
|--------|------|-------|---------|
| `{unknown}` | value | The value is not known. The field is a real gap to be filled. | `己野 {unknown}` |
| `{inferred}` | value | A value the agent derived. Nobody actually stated it. | `ていの しろう {inferred}` |
| `{unconfirmed}` | trust | The source is identified, but the fact is not corroborated. | `meeting 2026-02-10 {unconfirmed}` |
| `{unsourced}` | trust | Provenance cannot be determined. Goes in the Source field. | `{unsourced} recorded 2026-05-12` |
| `-` | — | Not applicable, deliberately empty. **Not** a gap. | Reading of `Anne-Marie O'Brien` |

A fifth marker, `{no-url}`, marks a source that is identified but has no shareable address;
it is defined in [Source Tracking](#source-tracking).

**Braces, not square brackets.** `[unknown]` would be a valid Markdown *link label*: with a
`[unknown]: url` definition anywhere in the same file — inside a list or a block quote is
enough — every occurrence in that file silently becomes a link. Label matching is
case-insensitive and collapses internal whitespace, so `[Unknown]` and `[ unknown ]` would
collide too. Braces carry no inline meaning in CommonMark, so no definition can capture
them. The division is worth remembering: **square brackets belong to Markdown** (links,
footnotes like `[^1]`); **braces belong to these markers**.

Rules that keep the markers meaningful:

- **Write the marker literally, in ASCII, in braces, in every language.** Files may be
  Japanese; the markers are not translated. One search finds every gap across a
  mixed-language store:
  ```
  grep -rn '{unknown}\|{inferred}\|{unconfirmed}\|{unsourced}\|{no-url}' <data-directory>
  ```
- **Never escape the braces.** They need no escaping, and an escaped form renders
  identically while being a different string, so it silently drops out of the search above
- **Never substitute a shorter or looser form.** Not `?`, not `不明`, not `TBD`, not `n/a`,
  and never an empty cell. An empty cell is indistinguishable from an oversight
- **`{unknown}` occupies the field**, so the gap is visible in the same place the real
  value will go. `己野 {unknown}` reads as unfinished; a bare `己野` reads as done
- **Distinguish `-` from `{unknown}`.** `-` means there is nothing to record and nobody
  should look; `{unknown}` means someone should
- **Where a marker goes says what it applies to.** A value marker sits in the field it
  describes. A trust marker goes in the `Source` field (or after the footnote source) by
  default, which is what makes the trust level of a whole row readable in one column. Put
  `{unconfirmed}` next to a value instead only when one field in an otherwise solid row is
  the doubtful part
- **Do not stack redundant markers.** `{unsourced}` already implies uncorroborated, so do
  not add `{unconfirmed}` to it. Use the one that says the most
- **A marker travels with the value.** When a marked value is quoted elsewhere — another
  file, another skill, a summary — the marker comes with it
- **Markers never reach a deliverable.** They are internal bookkeeping. If a proposal,
  report, or message needs a value that carries one, resolve it first or ask the user.
  Never silently drop the marker and print the value as fact

## Source Tracking

Every fact carries where it came from. Without provenance a stored line cannot be
verified, corrected, or weighted, and a guess written down six months ago becomes
indistinguishable from something the customer stated directly.

**What needs a source.** Anything that came from outside your own head: a person, a system,
a term, an org structure, an event, a proposal, a figure, a constraint, a preference. Not
only financial numbers.

**What does not.** A field that is bookkeeping rather than a claim about the world needs no
source, and forcing one produces noise:

- Identifiers and state you maintain yourself: `Status`, `Last synced`, the slug, the
  `Group` assignment, `Date Added`
- A value that is definitionally the file it lives in (the display name at the top of a
  customer's own file)
- Section headings, template comments, and your own migration notes

**Block-level sources.** An event entry under `## Key Events`, or a `### YYYY-MM-DD:` change
record, is one fact told in several lines. One `- Source:` line at the end of the block
covers the whole block; the individual `- What happened:` / `- Significance:` lines do not
each need their own. Add a per-line footnote only when one line inside the block came from
somewhere else.

If a section is not in the standard template — a customer-specific design section, a
diagram, an ad-hoc analysis — it is still content, and its facts still carry sources. Custom
sections are the easiest place for provenance to quietly go missing.

- **In tables**: a `Source` column, filled on every row. The one exception is `index.md`,
  which is a resolution registry rather than a set of facts and is kept lightweight because
  it is loaded on every task — alias provenance belongs on the `Common aliases` line in
  that customer's `profile.md`.
Sources are recorded once per file and referenced by a key, so a source that supports twenty
facts is written out once instead of twenty times — and a table cell, which cannot hold a
nested list, carries a short reference instead of a long string.

**Reference sites** carry `[[KEY](#KEY)]` at the end of the line the fact occupies — a
bracketed citation, so it reads as a marker rather than as part of the sentence. A table cell
puts a bare `[KEY](#KEY)` in the `Source` column, where the column heading already says what
it is:

```markdown
| Name | Reading | Department | Source | Notes |
|------|---------|-----------|--------|-------|
| 乙野 次郎 | おつの じろう | 財務部 | [AP20260512](#AP20260512) | 銀行取引の窓口 |

- 総合振込の承認は経理課長 → 財務部長の2段階 [[AP20260512](#AP20260512)]
- 基幹システム更新に伴い設備資金の需要が生じ得る [[M20260804](#M20260804)] {unconfirmed}
```

The outer brackets need no escaping. An inline link inside them cannot nest, so the brackets
stay literal and render as `[AP20260512]` — and they remain literal even if a stray
`[AP20260512]: url` reference definition is present, because an inline link takes precedence
over a shortcut reference.

Three placements, and the position says what the reference covers:

| Placement | Covers |
|-----------|--------|
| End of a list item | that fact |
| `Source` column of a table row | that row |
| `- Source:` field inside an event block, alongside `- What happened:` | the whole block |
| `Source:` paragraph next to non-list content (a diagram, a paragraph) | that content |

Do not put the reference on a nested `- Source:` line under a fact — the key is short enough
to sit on the fact's own line, and one line per fact reads better and is simpler to parse.

**Definitions** live in a `## Sources` section at the end of the file, one per line, each
carrying an anchor so the reference is a working in-page link:

```markdown
## Sources

- <a id="AP20260512"></a>**AP20260512** — doc:account-plan 2026-05-12 {no-url}
- <a id="M20260804"></a>**M20260804** — meeting 2026-08-04（設備投資計画のヒアリング）
```

**Key format is `<KIND><YYYYMMDD>`** — derived from the source, never invented, so the same
source always produces the same key and two facts from one source cannot drift apart. Use
`<KIND><YYYYMM>` or `<KIND><YYYY>` when only the month or year is known, and `<KIND>000000`
when the source carries no
date at all (which is itself a gap worth filling). If two genuinely different sources collide
on one key, append `b`, `c`, … in a stable order.

| KIND | Source kind | KIND | Source kind |
|------|-------------|------|-------------|
| `M` | meeting with the customer | `AP` | account plan |
| `IS` | internal sync / account team | `AR` | activity report |
| `U` | told by the user (operator) | `D` | other document |
| `SIG` | email header or signature | `L` | other linked record |
| `DIR` | people directory | `AC` | CRM account record |
| `SL` | chat message | `OP` | CRM opportunity |
| `INF` | derived by the agent | `ACT` / `TA` | CRM activity / task |
| `ORG` | org chart | `UNS` | `{unsourced}` |

Where the markers go:

- `{no-url}` describes the source itself, so it lives in the **definition**
- `{unconfirmed}` and `{inferred}` describe *this* fact's reliability, so they stay at the
  **reference site** — otherwise a row-level doubt would be lost
- Scope notes (`（このセクション全体）`) stay at the reference site too

Placement of the reference tells you what it covers: a `Source:` paragraph under a heading
covers the section; a `- Source:` list item nested under a fact covers that fact; a
`- Source:` sibling inside an event block covers the block.

**Do not use Markdown footnotes (`[^1]`).** Footnotes are not part of CommonMark. GitHub
renders them, but many viewers — including VS Code's built-in Markdown preview — do not, and
they degrade badly rather than visibly failing: the `[^1]` stays as literal text and every
definition collapses into one run-on paragraph. The key scheme above is a portable
replacement: `[KEY](#KEY)` renders as a real link in every parser, and the definition list
renders one source per line.

**Validate after editing.** The key scheme trades verbosity for a class of mechanical errors
— undefined keys, orphaned definitions, duplicates — so they must be checked rather than
trusted:

```
python3 <skill>/scripts/validate-store.py <data-directory>
```

It also checks table column counts, empty `Source` cells, honorifics left in a `Name` column,
old-style bracket markers, fact lines with no source, and footnote usage. Run it after a
batch update, and after any hand edit of a `## Sources` section.

These are the forms in use. The leading label names the *kind* of source, and a new kind
follows the same shape — a kind plus a date, or a link — never a file path:

| Form | Means |
|------|-------|
| `meeting 2026-03-19` | Stated by the customer in a meeting on that date |
| `user 2026-03-19` | Told to the agent by the user (the operator) |
| `email signature 2026-02-14` | Read off an email header or signature |
| `internal directory 2026-05-01` | Your own organization's people directory |
| `[<title> 2026-03-19](https://…)` | A document, message, or record — **linked** |
| `doc:<title> 2026-03-19 {no-url}` | A document with no shareable address (see below) |
| `inferred 2026-03-19` | Derived by the agent; nobody actually said it |
| `{unsourced} recorded 2026-03-19` | Provenance could not be determined |

A [companion skill](#companion-skills) may define further kinds for the systems it reaches;
they extend this table rather than replacing it.

### Prefer a URL Over a Name

A source is only useful if someone else can reach it. Record the address, not the container
it happened to arrive in.

- **Link the source whenever an address exists.** A document library entry, a wiki page, a
  message permalink, a CRM record, an issue, a published page — any of these is worth more
  than a bare title, because it survives being read by another person on another machine
- **Never record a local filesystem path.** `~/Downloads/plan_final_v3.xlsx` is useless to
  anyone else and useless to you once the file moves. It is not a source
- Prefer the stable address over the transient one: the page or record that holds the file
  over a one-time download link; a message permalink over "the file in that chat"
- Match reachability to the audience: an internal wiki URL is a fine source for an internal
  store, and a link the intended reader cannot open is not a source

### When a Document Has No URL

Two situations produce a source with no address: a file handed over as a file, and content
pasted straight into the conversation. Work down this order — do not skip to the bottom.

1. **Resolve the address.** Use whatever document-search, messaging, or CRM skills are
   available to locate the document's canonical location, then link that
2. **Ask the user.** One question — "does this have a URL or a permanent location?" — is
   cheaper than a source nobody can follow later. Ask once, and save the answer
3. **Record it honestly with `{no-url}`**, keeping the document's own title and date:
   `doc:FY26 Cloud Migration Plan 2026-05-12 {no-url}`

For content pasted into the conversation there is no document to find, so the handover
itself is the only traceable link. Record both:
`doc:<title as stated> {no-url} via user 2026-08-20`. The `via user <date>` is what makes
it recoverable — the user can identify what they handed over that day.

- **Never invent a URL.** A plausible-looking link is worse than `{no-url}`, for the same
  reason an invented meeting date is worse than `{unsourced}`
- Keep the dates distinct: the document's own date is the date of the fact; the handover
  date is only when it reached you. If the document carries no date, record the handover
  date and label it (`recorded 2026-08-20`)
- `{no-url}` is not `{unsourced}`. `{no-url}` means *we know what this is and cannot
  address it*; `{unsourced}` means *we do not know what this is*. A `{no-url}` source still
  supports a fact — resolve its address at the next opportunity

Dates and confidence are recorded separately from source:

- Record the date the fact refers to, not the date you wrote it down. When only the
  recording date is known, label it as such (`recorded 2026-05-12`)
- Mark unverified verbal information `{unconfirmed}` until it is corroborated. A
  `Source` entry records where a claim came from; it does not make the claim verified
- A fact learned from an external document is attributed to that document, not asserted
  as verified

**Provenance is not laundered.** When copying a fact from one file to another, or out of
a document into the store, carry its original Source with it. Never record the file you
copied from as the source — that erases the only trail back to the origin and promotes
hearsay into apparent fact.

### Facts With Unknown Provenance

Some facts arrive with no traceable origin: the store already contained them, a document
repeats them without attribution, or nobody remembers who said it. Keep them — but keep
them marked.

- Record `{unsourced}` in the Source field together with the date you recorded it. Never
  close the gap with a plausible-looking source. An invented `meeting 2026-03-19` is worse
  than `{unsourced}`, because it looks verified
- Treat an unsourced fact as a hypothesis: use it to orient your own thinking and to
  form a question to ask. Do not state it as fact in customer-facing output, do not rest a
  recommendation on it alone, and do not hand it to another skill without the marker
- Verify it at the next opportunity — ask the user, or confirm with the customer — then
  replace the marker with the real source. `{unsourced}` and `{unconfirmed}` entries are
  the first candidates in the periodic review (see [Retention and Pruning](#retention-and-pruning))
- When it contradicts a sourced fact, the sourced fact wins. Keep the conflict visible in
  Notes rather than silently deleting one side
- Entries written before source tracking was in place are `{unsourced} pre-existing`.
  When you touch such an entry, add that marker rather than guessing where it came from
