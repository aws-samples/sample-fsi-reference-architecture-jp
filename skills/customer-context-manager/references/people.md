# Recording People

Rules for classifying and naming people, referenced from SKILL.md. Read this before
adding a person to a customer's `people.md` or to the shared people files.

Japanese version: [people_ja.md](people_ja.md)

## Classifying People

Before adding a person to a customer's `people.md`, check whether they already
exist in `people/internal.md` or `people/partners.md`. A name mentioned in a
customer meeting may belong to an internal team member or partner rather than a
customer contact. Steps:

1. Search `people/internal.md` for the name
2. Search `people/partners.md` for the name
3. If found, do not duplicate into the customer's `people.md` — update the
   existing entry if new information was learned
4. If not found in either, add to the customer's `people.md` as a customer contact

Search by surname and by reading, not only by the exact string you were given: the same
person may be recorded there as a full name while the conversation used a surname, or
written in the other script.

When uncertain about a person's affiliation (customer vs internal vs partner),
use conversation context clues (e.g., "our team", "our side", job titles like
"technical consultant", "account manager") to classify. If still ambiguous, ask the user.

## Recording Person Names

A surname alone is not enough. `A-san (IT Strategy)` cannot be matched against an email
sender, an attendee list, or a CRM contact record, and it forces the next task to ask the
user again for something that was already established once. Record a person once,
completely, so no later task has to re-ask.

Every people table — a customer's `people.md`, `people/internal.md`,
`people/partners.md` — records at least:

| Field | Rule |
|-------|------|
| Name | The full name as its owner writes it, in the original script. Family *and* given name. |
| Reading | How it is pronounced: kana for Japanese names; for Latin-script names only when a Japanese reading is actually in use. |
| Source | Where the name came from (see [Source Tracking](#source-tracking)). |

Script rules — record the name the way its owner writes it:

- **Japanese names**: keep the kanji/kana as written (`山田 太郎`) and record the reading
  (`やまだ たろう`). Readings are not derivable from kanji — `新谷`, `丁野`, and given
  names like `一` each have several valid readings, and picking the most common one is a
  guess that will eventually be repeated out loud in front of the customer
- **Latin-script names**: keep the Latin spelling exactly as the person writes it —
  capitalization, hyphens, apostrophes, accents, and given/family order included
  (`Anne-Marie O'Brien`, `José Álvarez`, `LEE Min-ho`). Do not transliterate into katakana
  as the primary record; add katakana to Reading only if that form is actually used in the
  engagement
- **Someone who uses both forms** (`山田 太郎` / `Taro Yamada`): put the primary form in
  Name and the other in Notes, so either spelling resolves on search
- **Keep honorifics and titles out of the name itself.** `様`, `さん`, `-san`, `Mr.`, `Dr.`
  are forms of address; `部長` and `CTO` are roles. Neither belongs in the Name column, nor in
  a labeled field that identifies a person (`Primary contacts:`, `SA Assignment:`). Those
  carry the recorded name so it can be matched against an email, an attendee list, or a CRM
  record — `山田 太郎`, not `山田様` or `山田部長`.
- **In prose, write people the way you would normally write them.** A Notes cell, a
  `- What happened:` line, a free-text bullet, an annotation on an org chart — these are
  sentences, so use the form of address the language and the relationship call for
  (`乙野様`, `甲山さん`). Stripping honorifics out of Japanese prose reads wrong, and for a
  customer it reads rude. In a language that has no honorifics, use the name on its own. The
  registry is what makes this safe: because `people.md` holds the full name and reading, a
  sentence can say `乙野様` without losing the ability to resolve who that is.
- **A role written beside a name in prose is a claim, and it goes stale silently.** Prefer
  the honorific to the title — `甲野様`, not `甲野CTO` — because the role belongs in that
  person's people-table row, which is the one place that gets corrected when they move.
  Prose that says `甲野CTO` keeps asserting the title years after the reorganization.
- **Anyone named anywhere must have a row in a people table.** If a person is worth
  mentioning in `notes.md`, an event, or an org chart, they are worth a row in `people.md`
  (or `people/internal.md` / `people/partners.md`) carrying their reading and source. A name
  that appears only in prose has no reading and no provenance, which is how surname-only
  records got created in the first place — and it is what makes a bare `乙野様` in a sentence
  unresolvable.

Fill gaps rather than freezing them, using the markers defined in
[Markers for Incomplete Information](#markers-for-incomplete-information):

- **Never invent a given name or a reading.** A missing one is `{unknown}`; a value you
  derived is `{inferred}`, with `inferred` as its Source
- When only the surname is known, write it `山田 {unknown}`. The marker is a visible,
  searchable statement that the record is unfinished, unlike a bare `山田`, which reads as
  complete
- Complete it from evidence at the next opportunity: an email signature, a meeting invite
  attendee list, a business card, an org chart, a document byline, or a CRM contact
  record. Prefer a written source over what was heard
- When the task at hand needs a name that is incomplete, ask the user for it once and save
  the answer with its reading. Do not quietly proceed with a surname, and do not ask again
  in a later task
- Do not block a save on completeness: save the partial record with `{unknown}` and its
  Source, then fill it in

The same applies outside tables. In `organization.md` charts, `history.md` events, and
prose notes, use the full name on first mention (`山田 太郎 CTO`); a short form afterwards
in the same file is fine once the full name is recorded in `people.md`.

## Distinguishing People with Similar Names

Two people sharing a surname within one customer is common, and a surname-only record is
precisely what makes them indistinguishable. Full name plus reading usually resolves it
on its own. When it does not:

- Add department or contextual information to the entry
- If they cannot be distinguished at the time of recording, save what is known and note
  the ambiguity explicitly (`山田 {unknown} (department {unknown} — may be distinct from
  山田 太郎 in Sales)`)
- Update the entry once later information clarifies it. Merge two rows only after
  confirming they are the same person — two similar rows are safer than a wrong merge

Do not block on perfect identification — partial information, marked as partial, is
better than none.
