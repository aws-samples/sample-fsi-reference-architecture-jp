# Example Store

A complete, filled-in customer context store. This is the only reference for file
structure and content — it replaces the separate empty-template and sample documents,
which said the same things twice.

Read it two ways:

- **As the template.** Every file shows the sections and table columns a real file must
  have. `<!-- -->` comments state what belongs in each section
- **As the quality bar.** The content shows the expected density. Aim for this, not for an
  empty skeleton with three bullets

Everything here is fictional — names, companies, systems, and figures. Copy the structure;
never copy the content into a real store.

**Names here are placeholders, not realistic names.** They follow the 十干 convention used
in Japanese legal drafting (甲野・乙野・丙野…), with the second character marking which side
a person is on: 野 for the customer, 山 for your own organization, 川 for partners and
advisors. Latin-script names use `John Doe`. A published example must not use names that
could be mistaken for real individuals, so keep this convention when extending the store —
and never carry a name over from a real store.

**System names carry the same convention.** They use an `ANY-` prefix (`ANY-EB`,
`ANY-SEISAN`), and external services and industry infrastructure are written as generic
terms rather than by name. Nothing here is a name a reader would have to check. The example
does not need real names to demonstrate structure, and a name that might belong to a product
that exists is not worth the doubt it creates. A real store records internal names and
product names as they are used.

**Read the example as intentionally incomplete.** `notes.md` has no `Competitive Landscape`
section: it is one of the never-disclosed sections, so it is not demonstrated here. A real
store carries it. An omission in this example carries a reason — it is not a gap to fill.

**Premise:** This store is owned by a regional bank's corporate banking division
(relationship managers). The "customer" is a business corporation — not an individual, and
not a technology vendor. The Revenue section records the bank's own transaction data
(loan balance, deposits, fee income), which is internal and not disclosed externally.

```
example-store/
├── index.md                          # Master index: slug → display name + aliases + group
├── customers/
│   └── any-manufacturing/            # One directory per customer, named by slug
│       ├── profile.md
│       ├── people.md
│       ├── organization.md
│       ├── systems.md
│       ├── history.md
│       ├── terms.md
│       └── notes.md
└── people/
    ├── internal.md                   # Internal team members, shared across customers
    └── partners.md                   # Partner companies, cross-customer level
```

Beyond structure, these files demonstrate the rules that are easy to get wrong:

- **Full names with readings**, in the script their owner uses — including a same-surname
  pair separated by given name, an incomplete record, a derived reading, and a Latin-script
  name kept as written
- **A source on every row and every notable fact**, linked by URL wherever an address
  exists, and honestly marked where none does
- **The incompleteness markers in use** — `{unknown}`, `{inferred}`, `{unconfirmed}`,
  `{unsourced}`, `{no-url}` — and the difference between `-` (nothing to record) and
  `{unknown}` (something is missing)
- **法人関係情報 (insider information) handling** — a dedicated section in notes.md
  separating non-public material facts from ordinary notes, with firewall rules in comments

