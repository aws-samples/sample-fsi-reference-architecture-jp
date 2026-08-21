# Context File Templates

Minimum structure for each context file managed by `customer-context-manager`.
For a filled-in example showing the expected density and quality, see
[sample-context.md](sample-context.md).

Japanese version: [templates_ja.md](templates_ja.md)

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
<!-- Sales-side financial information: contracts, deal size, spend. Never disclosed outside your own organization -->

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
<!-- Other vendors, competing solutions. Never disclosed outside your own organization -->

## Sensitivities
<!-- Topics to handle carefully, past negative experiences. Never disclosed outside your own organization -->

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
