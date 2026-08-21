# Renaming, Merging, and Splitting Customers

Step-by-step procedures referenced from SKILL.md. Read this before performing any of
them, and only after the guardrails in SKILL.md (plan, confirmation, clean git state,
identity verification) have been satisfied.

Japanese version: [renaming-merging_ja.md](renaming-merging_ja.md)

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
