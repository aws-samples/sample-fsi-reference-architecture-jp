# Sample Customer Context: Any Bank

This is a reference example showing the expected density and quality of customer
context. Use this as a guide when creating or updating context files.

---

## index.md (relevant row)

```markdown
| any-bank | Any Bank, Ltd. | AB, エニー銀行 | Banking | Any Financial Group | Active |
```

---

## customers/any-bank/profile.md

```markdown
# Any Bank, Ltd.

## Basic Information
- Formal name: 株式会社エニー銀行
- Common aliases: AB, エニー銀行, Any Bank
- Industry: Banking (Internet bank, retail-focused)
- Size: ~2,000 employees, 5M accounts
- Headquarters: Tokyo, Minato-ku
- Website: https://www.anybank.example.co.jp/

## Relationship Summary
- First engagement: 2023-04
- Current status: Active — multiple concurrent projects
- Primary contacts: Yamada CTO, Suzuki-bucho (IT Strategy)
- Key partners: GlobalSI Corp (infrastructure), DataTech Inc (analytics)

## Revenue
- Annual contract value: $2.4M
- Contract term: 3 years (renewal 2027-03)
- YoY growth: +25%
- Deal size trend: expanding (started at $800K)

## Strategic Context
- Pursuing "Digital Bank 2030" strategy: full digitization of retail banking
- Board-level mandate to reduce IT cost by 30% through cloud migration
- Competing with neobanks on mobile UX — speed of feature delivery is critical
- Regulatory pressure from FSA on operational resilience (FISC compliance)

## Notes
- CEO personally championed cloud adoption after visiting our technology center
- Annual planning cycle: budget decisions in November for April start
```

---

## customers/any-bank/people.md

```markdown
# People — Any Bank, Ltd.

## Customer Contacts

| Name | Department | Title | Role in Decisions | Notes |
|------|-----------|-------|-------------------|-------|
| Yamada様 | IT Strategy | CTO | Final technical authority | Monthly executive meeting. Strong advocate for cloud. Former engineer background |
| Suzuki様 | IT Strategy | 部長 | Budget holder for cloud projects | Day-to-day decision maker. Pragmatic, data-driven. Prefers written proposals |
| Tanaka様 | Digital Banking | 課長 | Mobile app architecture | Key technical contact. Responsive on Slack. Interested in serverless |
| Tanaka様 (別) | Infrastructure | 課長 | On-prem operations | Different person from Digital Banking Tanaka. Cautious about migration pace |
| Sato様 | Compliance | 部長 | Regulatory sign-off | Must approve any architecture touching customer data. 2-week review cycle |
| Ito様 | Contact Center | マネージャー | CC platform selection | Evaluating 3 vendors. Decision expected by Q2 |

## Partner Contacts

| Name | Company | Role | Project/Context | Notes |
|------|---------|------|-----------------|-------|
| Kim様 | GlobalSI Corp | Project Manager | Core banking migration | On-site 3 days/week. Good relationship, shares info proactively |
| Lee様 | DataTech Inc | Lead Architect | DWH modernization | Remote. Technical depth in Spark/Iceberg |
```

---

## customers/any-bank/organization.md

```markdown
# Organization — Any Bank, Ltd.

## Current Structure

```
CEO 佐々木様
├── CTO Yamada様 (IT Strategy本部)
│   ├── Suzuki部長 (クラウド推進部)
│   │   ├── Tanaka課長 (Digital Banking)
│   │   └── Watanabe課長 (API Platform)
│   ├── Tanaka課長 (Infrastructure) ← 別のTanaka
│   └── Nakamura部長 (Security & Compliance)
│       └── Sato部長 (Compliance)
├── CDO Ogawa様 (Data & AI本部)
│   └── Kimura課長 (Data Science)
└── COO Morita様 (Operations本部)
    └── Ito マネージャー (Contact Center)
```

## Decision-Making Flow
- Technical architecture: Yamada CTO approves (Suzuki部長 recommends)
- Budget < $500K: Suzuki部長 can approve alone
- Budget > $500K: Yamada CTO + CFO joint approval
- Customer data touching: Sato部長 must sign off (allow 2 weeks)
- Vendor selection: Procurement department involved above $1M

## Key Departments
- クラウド推進部: Main counterpart. 15 engineers. Owns cloud strategy
- Infrastructure: Legacy ops team. 40 people. Gradually shrinking
- Data & AI本部: New org (created 2024-04). Growing fast. Reports to CDO

## Change History

### 2024-04: Data & AI本部 created
- Old: Data Science was under IT Strategy
- New: Standalone division under new CDO Ogawa様
- Impact: AI projects now have separate budget and faster approval

### 2023-10: Cloud推進部 split from Infrastructure
- Old: Cloud team was a sub-group within Infrastructure
- New: Independent department under CTO with own budget
- Impact: Cloud decisions no longer blocked by legacy ops concerns
```

---

## customers/any-bank/systems.md

```markdown
# Systems & Technology — Any Bank, Ltd.

## Known Systems

| System Name | Category | Technology | Notes |
|-------------|----------|-----------|-------|
| CORE-Next | Core Banking | Java on Linux (on-prem) | Migration to cloud planned FY27. 20M transactions/day |
| MobileApp | Customer-facing | React Native + API Gateway | 3M MAU. Deployed on cloud already |
| DWH | Analytics | Teradata → migrating to Snowflake | $2M annual Teradata license. Migration in progress |
| CC-Platform | Contact Center | Legacy Avaya | RFP in progress. Decision Q2. We are one of 3 vendors |
| EAGLE | Internal workflow | .NET on Windows Server | Name is internal codename. Document management system |
| Fraud-AI | ML Platform | Python + SageMaker | In production since 2024-06. 99.2% accuracy |

## Technical Constraints
- FISC compliance required for all customer-data systems
- No data outside Japan (Tokyo + Osaka regions only)
- Change freeze: December and March (fiscal year end)
- Security review required for any new SaaS adoption (6-week process)
- Network: Direct Connect 10Gbps x2 (redundant) to Tokyo region

## Technology Preferences
- Containers preferred over VMs for new workloads
- PostgreSQL preferred over proprietary databases
- GitLab for CI/CD (enterprise license)
- Datadog for observability (recently adopted)
- Conservative on bleeding-edge: prefer GA services with 6+ months track record
```

---

## customers/any-bank/terms.md

```markdown
# Terminology — Any Bank, Ltd.

## Glossary

| Term | Meaning | Context | Source | Date Added |
|------|---------|---------|--------|------------|
| CORE-Next | 次期勘定系システムのプロジェクト名 | FY27移行予定 | meeting 2024-11-15 | 2024-11 |
| EAGLE | 社内ワークフローシステム | 文書管理。.NET製 | meeting 2024-08-22 | 2024-08 |
| Digital Bank 2030 | 中期経営計画の名称 | リテール完全デジタル化 | [IR資料](https://example.com/ir) | 2024-04 |
| クラウド推進部 | 2023-10に新設された部署 | 旧Infrastructure部から分離 | meeting 2023-10-05 | 2023-10 |
| AB-Connect | 社内Slackワークスペース名 | 連絡はここが最速 | meeting 2024-01 | 2024-01 |
| 月次定例 | CTO Yamada様との月次ミーティング | 毎月第2火曜 14:00 | - | 2023-04 |
| FreezeWindow | 12月・3月の変更凍結期間 | リリース不可 | meeting 2024-03 | 2024-03 |
```

---

## customers/any-bank/history.md

```markdown
# History — Any Bank, Ltd.

Key turning points only. For activity details, query CRM.

## Key Events

### 2024-11: CORE-Next migration decision
- What happened: Board approved cloud migration of core banking (CORE-Next)
- Significance: Largest deal opportunity. Multi-year engagement confirmed
- Impact on relationship: Elevated from tactical to strategic partner

### 2024-06: Fraud-AI production launch
- What happened: ML-based fraud detection went live
- Significance: First ML workload in production. Built trust in cloud for critical systems
- Impact on relationship: Data & AI team became strong internal advocate

### 2024-02: Contact Center RFP issued
- What happened: Customer issued RFP for CC platform replacement
- Significance: $500K ARR opportunity. Competing against 2 other vendors
- Impact on relationship: Need to demonstrate differentiation quickly

### 2023-04: Initial engagement
- What happened: Introductory meeting via partner referral (GlobalSI Corp)
- Significance: Started with small analytics workload ($200K)
- Impact on relationship: Proved reliability, led to expansion

## Past Proposals

| Date | Topic | Outcome | Reason |
|------|-------|---------|--------|
| 2024-09 | Multi-account governance framework | Accepted | Aligned with their security audit findings |
| 2024-05 | Mainframe assessment | Deferred | Budget not available until FY26. Revisit in Nov |
| 2024-01 | Data lake on S3 + Glue | Accepted | Cost savings vs Teradata convinced CFO |
| 2023-08 | Full lift-and-shift proposal | Rejected | Too aggressive timeline. Customer wanted phased approach |
```

---

## customers/any-bank/notes.md

```markdown
# Notes — Any Bank, Ltd.

## Communication Preferences
- Preferred channel: Slack (AB-Connect workspace) for day-to-day
- Email for formal proposals and approvals
- Yamada CTO prefers 30-min focused meetings over 1-hour broad ones
- Suzuki部長 likes to see cost comparisons in spreadsheet format
- Avoid scheduling meetings on Monday mornings (all-hands)

## Competitive Landscape
- Oracle: Legacy DB vendor. Trying to push OCI but no traction
- Google Cloud: BigQuery evaluated for DWH but lost to Snowflake+S3
- Microsoft: M365 for office tools. Azure AD for identity. No compute workloads
- Genesys: Competing for CC platform (strong incumbent relationship)

## Sensitivities
- 2023-09 incident: Our service had a 45-min outage affecting their mobile app.
  Yamada CTO was understanding but Tanaka (Infra) still references it.
  Always acknowledge reliability improvements when presenting to Infra team.
- Avoid pushing migration speed — they were burned by a rushed project with
  another vendor in 2022. Phased approach language works better.
- Compliance team (Sato部長) is risk-averse. Lead with security benefits, not cost.

## Free Notes
- Annual golf event with CTO in September — good relationship-building opportunity
- Customer presented at our user conference in 2024 (Fraud-AI case study)
- They are hiring aggressively for cloud engineers — may need training support
```
