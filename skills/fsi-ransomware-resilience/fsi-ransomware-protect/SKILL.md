---
name: fsi-ransomware-protect
description: >-
  Provides architecture design and evaluation support for ransomware-resilient backup environments on AWS, for financial services industry organizations. Use when: (1) designing a backup architecture from scratch, or (2) evaluating an existing backup environment (AWS Backup, native per-service backups, third-party products) for resilience gaps. Covers multi-account role separation, AWS Backup with Logically air-gapped vault, Vault Lock, Multi-party approval, Malware Scan, cross-account/cross-Region copy, immutable backup design, encryption/key management, IAM/SCP policy design, log collection/protection, backup monitoring/auditing, and on-premises integration. Activate on mentions of ransomware-resilient backup design, immutable backups, air-gapped vaults, or AWS Backup architecture. Do NOT use for detection, response, recovery, or unclear phase -- use fsi-ransomware-overview first. Target users: FSI backup design/evaluation practitioners, incl. security/infra and risk/compliance staff.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Ransomware Resilience for Financial Institutions: Protect

## Overview

This skill supports the architecture design and existing-environment evaluation of ransomware-resilient backup environments that financial services industry organizations build on AWS. What this skill provides:

- Design support for an account-separation strategy based on a multi-account structure
- Design of a backup architecture centered on AWS Backup
- Design of backup-data immutability (Vault Lock / Object Lock) and encryption
- Policy design (preventive controls via IAM / KMS / Vault Access Policy / SCP)
- Malware scanning strategy (AWS Backup malware protection, third-party product workarounds, ECR container protection)
- Design of log collection and protection in preparation for forensic response
- Design of monitoring and audit reporting for backup operations
- Selection of means to protect on-premises backups on AWS (AWS Backup Gateway / DataSync / Storage Gateway / S3 API)

The scope this skill covers:

- Focuses on the "Protect" phase of ransomware resilience
- The Detect, Respond/Isolate, and Recover phases are handled by separate skills
- Pre-incident prevention (network perimeter defense, EDR, etc.) is out of scope (the focus is on post-intrusion resilience)

The detailed guides and report-generation templates for this skill are stored in the `references/` folder and the `report-templates/` folder located in the same hierarchy as this skill file. When a workflow's processing step instructs you to "refer to references/XX" or "refer to report-templates/XX", locate the relevant file using the following procedure and read it before composing your response.

1. Try `.kiro/skills/fsi-ransomware-protect/{references,report-templates}/` under the workspace
2. If not found, try the user-level `~/.kiro/skills/fsi-ransomware-protect/{references,report-templates}/`
3. If found in neither, ask the user for this skill's deployment path

Even if loading a reference or template fails, do not compose a response based on general knowledge alone; always inform the user of the situation before deciding how to proceed.

This skill is designed to ensure the accuracy of its answers by referring to official AWS documentation. For use, we recommend setting up the AWS Documentation MCP server in advance (see the README.md included with this skill for setup instructions).

## Reference Foundations

This skill is built on the following authoritative sources, complemented by the design considerations required in the context of financial institutions. Links are kept, in principle, at the service-top or major-category level; deeper references to individual features are made as needed within the body text and the references/ folder.

### AWS official guidance (comprehensive best practices)

- AWS Blueprint for Ransomware Defense
- AWS Well-Architected Framework — Financial Services Industry Lens
- AWS Well-Architected Framework — Reliability / Security Pillar

### Service-specific official documentation

- AWS Backup
- Amazon S3
- AWS Key Management Service (KMS)
- AWS Organizations
- Amazon GuardDuty
- AWS Backup Gateway / AWS DataSync / AWS Storage Gateway
- AWS CloudTrail / AWS Config

### Reference resources

- AWS re:Invent 2025 - Building resilience against ransomware using AWS Backup (STG412)

## Common Tasks

### 0. Classify the Request

From the user's question, tentatively select a workflow based on the following correspondence.

| User intent | Workflow |
|---|---|
| Wants to understand the overall picture of backup/data protection as ransomware resilience in an AWS environment / wants to consult on where to start / wants to newly assemble an overall ransomware-resilient architecture design | A |
| Wants to evaluate the sufficiency of an existing backup/data-protection environment in an AWS environment as ransomware resilience, identify gaps, and improve | B |
| Wants to know the overall picture of ransomware-resilience best practices at an overview level / wants to explore interactively for learning purposes (no concrete design work or evaluation right now) | C |
| Wants pinpoint, in-depth consultation on a specific topic of backup/data protection in an AWS environment (or an on-premises environment involving AWS integration) (account separation, Vault Lock, encryption, malware scanning, log collection, SCP, monitoring/audit, etc.) | D |
| Wants to take and protect on-premises backups on AWS / wants to unify on-premises and AWS backups | E |

However, since in many cases the workflow cannot be uniquely determined from the user's question alone, always confirm interactively with the user "which direction to proceed in" before moving to the appropriate workflow. Specifically, present a confirmation message such as the following. This confirmation message MUST always begin with a statement that this skill covers only Protect among the five areas (see PR-C13).

> This skill covers "Protect" among the five areas of ransomware countermeasures (Protect, Detect, Respond, Recover, Organization), supporting the design and evaluation of backup and data protection. If you have questions about other areas, please request the corresponding skill.
>
> Before I answer your question, let me confirm which direction to proceed in.
>
> **[Produces a design/evaluation report]**
> - A. Build a ransomware-resilient architecture design on AWS from scratch (including when some controls are already in place)
> - B. Evaluate the sufficiency of an existing AWS backup environment as ransomware resilience (evaluation/improvement of an existing environment)
>
> **[Interactive guidance, no report]**
> - C. First understand the overall picture of best practices at an overview level (explore interactively and, as needed, guide to workflow A / B / D / E)
> - D. Learn about a specific topic in a pinpoint manner (LAG vault, Vault Lock, encryption, log collection, etc.)
> - E. Integrate on-premises environment backups into AWS
>
> Which direction does your case mainly fall under? Please also let me know if multiple apply.

Based on the user's reply, proceed to the appropriate workflow.

### 1. Common Hearing Items

Shared across Workflows A and B. The required/recommended/optional assignment differs per workflow.

| # | Hearing item |
|---|---|
| PR-H1 | Types of resources to protect (EC2, RDS, Aurora, S3, EFS, ECR, Fargate, etc.) |
| PR-H2 | Whether to consider ransomware resilience for the on-premises environment together with the AWS-side controls. If so, the presence and scale of a VMware environment |
| PR-H3 | Backup requirements (per business-impact level, what backup frequency/cadence/retention period is required for backup acquisition. The tendency of acquisition intervals according to the tolerance for data loss. If there is a regulatory long-term retention obligation, include that retention period as well. It need not be a uniform value; a per-system tendency is fine) |
| PR-H4 | Regulatory/compliance-driven protection requirements (requirements for tamper-proofing / WORM of backups, in-country data residency requirements, preservation of audit trails, etc. The retention period itself is handled by PR-H3) |
| PR-H5 | Existing multi-account structure / organizational structure (whether Organizations / Control Tower is used, the account-separation policy (per business system / per team / per environment, etc.), the scale of the number of accounts) |
| PR-H6 | Presence of existing security products (EDR/AV) and the policy on continuing to use them |
| PR-H7 | Priority of backup acquisition targets (the difference in business impact) |
| PR-H8 | Presence of an existing log-collection platform (SIEM, Security Lake, etc.) |

The Regions are fixed on the premise of Tokyo + Osaka.

### 2. Workflow A: Overall Design of a Ransomware-Resilient Architecture

#### Activation conditions

Handles questions such as "I want to assemble the overall picture of ransomware resilience from scratch," "I want to consider it comprehensively," or "the narrowing-down is weak, but I want to consult on the direction of controls." This also applies when some controls are already partially in place. However, select Workflow A when the goal is to newly assemble an overall design from a ransomware-resilience perspective, rather than an evaluation premised on an existing environment (if the goal is evaluation/improvement of an existing environment, select Workflow B).

#### Goal

Upon completion of Workflow A, the user has obtained:

1. A multi-account structure proposal tailored to the customer's situation (how many accounts, separated into what roles)
2. The AWS services to adopt and the role of each (AWS Backup, Vault Lock, KMS, SCP, CloudTrail, GuardDuty, etc.)
3. The rationale for each design element (why use Vault Lock, why separate accounts, etc.)
4. The design's priorities and a phased approach (what to start with first, what can be deferred)
5. A design-proposal report (an HTML / Markdown report consolidating the design policy, account structure, each design element, and the phased roadmap) and a roadmap-detail report
6. Pointers to references and other workflows for deeper exploration

#### Hearing items

Select the following from the common hearing items:

- Required: PR-H1, PR-H3, PR-H5
- Recommended: PR-H4, PR-H6
- Optional: PR-H7, PR-H8

Note: Workflow A focuses on designing controls on AWS, and on-premises integration is separated into Workflow E; therefore PR-H2, which asks whether to consider on-premises, is not included in Workflow A's hearing items. If on-premises is mentioned, inform the user of the existence of Workflow E (Step 1 / Step 7).

#### Processing steps

1. **Initial hearing**: Confirm the required items (PR-H1, PR-H3, PR-H5). Conduct the hearing following PR-C10, proceeding interactively one or two items at a time. For unclear items, explicitly state that you propose confirming with the relevant department within the organization, or that you will proceed with a provisional setting. Also, at the outset, convey that this workflow focuses on the design of a ransomware-resilient architecture on AWS, and inform the user that if they wish to integrate on-premises (VMware, etc.) backups into AWS, this can be handled in Workflow E (here, do not interactively confirm whether to expand into Workflow E; merely inform them of its existence). If, in response to this notice, the user also mentions an on-premises environment, record that and use it for the Workflow E referral in Step 7.
2. **Presentation of the design frame (preview)**: After presenting a summary of the hearing results, preview as a list the overall picture of the design to be presented (broad design policy → account structure → core components → peripheral functions → phased roadmap), and convey that "from here, the design proposal will be presented all at once." From this preview onward, Steps 3–4 are presented in one continuous pass without requesting user confirmation for each individual design area.
3. **Design proposal (executed continuously in one pass)**: Present the following design areas in sequence and continuously, without inserting user confirmation for each area. In each area, load the corresponding reference and present a summary and pointers.
   - **Broad design policy**: Based on the hearing results, present the broad outline of the recommended approach.
   - **Account structure**: Propose the number of accounts and role separation according to the customer's situation. The decision on adopting a LAG vault is as follows (details in references/01-multi-account-architecture.md):
     - If PR-H1 does not include RDS → propose a LAG vault as an advanced configuration
     - If PR-H1 includes only RDS → propose a basic configuration (regular Vault + Vault Lock)
     - If PR-H1 includes a mix of RDS and other resources → also present, as an option, a hybrid configuration (RDS in a regular Vault, other resources split-protected in a LAG vault)
   - **Core components**: Propose backup plan design (acquisition frequency, target selection, retention period, lifecycle, references/03-backup-plan-design.md), immutability (Vault Lock / Object Lock, references/02-immutability.md), encryption and KMS key management (references/04-encryption-strategy.md), cross-account/cross-Region copy (references/01), and policy design (IAM / KMS / Vault Access / SCP, references/06-policy-and-access-control.md).
   - **Peripheral functions**: Propose malware scanning (if PR-H6 indicates a third-party product is present, propose using it in combination, references/05-malware-protection.md), log collection and protection (references/07-log-collection-and-protection.md), monitoring and audit reporting for backup operations (references/08-monitoring-and-audit.md), and ECR protection (only if PR-H1 includes containers, references/05).
4. **Presentation of design priorities and a phased roadmap**: Following the PR-C12 phase-judgment axes (risk-reduction effect, ease of response / impact on the existing environment, dependencies), present a short-/mid-/long-term roadmap. As a basic way of thinking, position controls that have little impact on the existing environment and offer quick effect (adding preventive controls, strengthening protection of existing log-storage S3, etc.) as short term; controls that complete within an individual account unit (backup plan development within an individual account, applying Vault Lock, checking encryption, etc.) as mid term; and organization-wide account-structure changes, development of centralized-management foundations, and advanced measures (creating Backup / isolation / recovery accounts, organization-wide Backup Policy, cross-account/cross-Region copy, centralized monitoring/audit, organization-wide rollout of malware scanning, migration to LAG vault, etc.) as long term. Do not present specific numeric durations (PR-NA2). From the Step 2 preview through this step, execute in one continuous pass and proceed continuously up to the generation of the design-proposal report (Step 5).
5. **Automatic generation of the design-proposal report (MUST)**: After completing the roadmap presentation, automatically generate the design-proposal report in both HTML and Markdown formats without inserting user confirmation. Generation must fully comply with the specification in `report-templates/template-spec.md` and the style and structure of `report-templates/design-proposal-template.html`. The output destinations are `fsi-ransomware-protect/report/workflow-a-{YYYYMMDD}-{NN}/html/design-proposal.html` and `fsi-ransomware-protect/report/workflow-a-{YYYYMMDD}-{NN}/md/design-proposal.md`. `{YYYYMMDD}` is the generation date (8 digits) and `{NN}` is a same-day sequential number (2-digit zero-padded, starting at `01`). Because the AI agent cannot obtain an accurate time, include no time in either the directory name or the in-report notation; use the date only. After generation completes, present the absolute saved path to the user, convey that the subsequently generated roadmap-detail report has a large volume of content and therefore takes a considerable amount of time to generate (it may take 10 minutes or more), and interactively confirm whether to proceed with continuing to generate it.
6. **Generation of the roadmap-detail report (executed after user approval)**: After obtaining the user's consent to generate, generate the roadmap-detail report in both HTML and Markdown formats. Generation must fully comply with the specification in `report-templates/template-spec.md` and the style and structure of `report-templates/roadmap-detail-template.html`. The output destinations are `html/roadmap-detail.html` and `md/roadmap-detail.md` in the same directory as Step 5. Do not record specific durations (numeric values in weeks/months) for each roadmap item; present them only by the short-/mid-/long-term phase classification. After generation completes, present the absolute saved path to the user.
7. **Offer to expand into detail and provide pointers to related references and other workflows**: After report generation completes, interactively confirm with the user, "I have included the details of each design area in the report, but it is also possible to dive deeper through interactive discussion." If desired, expand the detail one area at a time, confirming with the user at the end of each area whether to continue. The end point of the detail expansion is the level of description in the corresponding reference (up to architecture design decisions, rationale, and considerations in the financial-institution context). If not desired, briefly point to related references and other workflows, then end the workflow. In addition, if the user mentioned on-premises backup integration in Step 1, again inform them that on-premises integration can be handled in Workflow E.

#### Workflow A-specific Constraints

- **PR-MA1**: You MUST confirm the required hearing items (PR-H1, PR-H3, PR-H5) before assembling the design proposal.
- **PR-MA2**: You MUST, after completing the hearing (Step 1), execute Step 2 (the design-frame preview) through Step 5 (design-proposal report generation) in one continuous pass. You must not request individual user confirmation and interrupt processing at each break of the design areas in Step 3 (the broad policy, account structure, core components, peripheral functions) or the roadmap presentation in Step 4. PR-C10 and PR-C11 (interactive progression of the hearing, stopping at the overview level) apply only to the hearing (Step 1), not to the design-proposal phase (Steps 2–5).
- **PR-MA3**: You MUST, after completing Step 4 (the roadmap presentation), automatically generate the design-proposal report (Step 5) in both HTML and Markdown formats. Generation must fully comply with the specification in `report-templates/template-spec.md` and the style and structure of `report-templates/design-proposal-template.html`. You must not make independent judgments regarding format, granularity, color scheme, or fonts. After generation completes, present the saved path to the user.
- **PR-MA4**: You MUST, after completing the design-proposal report generation and before generating the roadmap-detail report (Step 6), explicitly state in advance to the user that "the roadmap-detail report has a large volume of content and takes a considerable amount of time to generate (it may take 10 minutes or more)," and interactively confirm whether to proceed with continuing to generate it. Begin generation only after obtaining the user's consent. When generating, fully comply with the style and structure of `report-templates/roadmap-detail-template.html`.
- **PR-MA5**: You MUST always place the design-proposal report and the roadmap-detail report under the same `workflow-a-{YYYYMMDD}-{NN}/` directory. When generating only the roadmap-detail report after the fact, interactively confirm with the user the existing directory in which the corresponding design-proposal report is stored, and add it to that directory.
- **PR-NA1**: You MUST NOT arbitrarily guess information the user has not provided and incorporate it as a settled matter into the design proposal or the report. Treat unobtained items as explicitly "unconfirmed" in the report and handle them as follow-ups that prompt confirmation.
- **PR-NA2**: You MUST NOT present specific durations ("1–2 months," "6–12 months," etc.) for each roadmap item. Because durations are greatly influenced by the customer's organizational structure, budget, existing operations, etc., present them only by the short-/mid-/long-term phase classification.
- **PR-NA3**: You MUST NOT propose Control Tower / Security Lake as a mandatory requirement. However, presenting them as optional efficiency-enhancing elements is permitted.
- **PR-NA4**: You MUST NOT delve into the detailed design of on-premises backup integration (selecting VMware backup means, designing the on-premises → AWS ingestion, etc.) within this workflow. On-premises integration is the scope of Workflow E; within this workflow, focus on the design of controls on AWS, and merely inform the user of the existence of Workflow E in Step 1 and Step 7.
- **PR-NA5**: You MUST NOT, when generating the report, add original sections not in the template, change the template's section order or column composition, or change the color scheme, fonts, or gradients. Only the data portions (customer information, design-proposal content, roadmap content) are swapped in from the template.

### 3. Workflow B: Sufficiency Evaluation of an Existing Environment

#### Activation conditions

Handles questions such as "I want to evaluate the sufficiency of my existing environment's ransomware resilience," "I want to compare against best practices," "I want to identify gaps," or "I want to improve my existing environment."

#### Goal

Upon completion of Workflow B, the user has obtained:

1. The evaluation result for each evaluation item (OK / NG / partially addressed / unconfirmed) and the rationale for the judgment
2. An organized account of the missing items (what is missing and why it is a problem)
3. The direction and priority of improvements (which gap to address first, including a risk evaluation)
4. Concrete improvement design proposals for the missing items (at the architecture level, with the same level of detail as Workflow A)
5. A phased implementation roadmap
6. Pointers to references for deeper exploration

#### Hearing items

##### Layer 1: Common hearing items

- Required: PR-H1, PR-H2, PR-H5
- Recommended: PR-H4, PR-H6
- Optional: PR-H7, PR-H8

##### Layer 2: Workflow B-specific current-state hearing items

| Importance | Item | Content |
|---|---|---|
| Required | PR-HB1 | Current backup-acquisition status (target resources, acquisition frequency, retention period, storage location) |
| Required | PR-HB2 | Current account structure / presence of account separation |
| Required | PR-HB3 | Current application status of Vault Lock / S3 Object Lock |
| Required | PR-HB4 | Presence and method of current cross-account/cross-Region copy |
| Required | PR-HB5 | Current malware-scanning status (AWS native / third-party / none) |
| Required | PR-HB6 | Current log-collection/protection status (CloudTrail / Config / VPC Flow Logs, etc.) |
| Required | PR-HB7 | Presence of current SCP / preventive controls |
| Required | PR-HB8 | Current encryption settings (KMS key management, CMK / managed key, etc.) |
| Required | PR-HB9 | Current monitoring status of backup operations (whether cross-account monitoring, Audit Manager reports, etc. are used) |

#### Processing steps

1. **Initial hearing of the framework**: Confirm PR-H1, PR-H2, PR-H5. Conduct the hearing following PR-C10, proceeding interactively one or two items at a time. For unclear items, explicitly state that you propose confirming with the relevant department within the organization, or that you will proceed with a provisional setting. If PR-H2 confirms that consideration of on-premises-side controls is also desired, interactively confirm with the user the possibility of expanding into Workflow E.
2. **Presentation of the evaluation frame**: Present the evaluation perspectives as a list, and convey to the user that "we will first confirm the current state, then enter the evaluation."
3. **Detailed current-state hearing (PR-HB1–PR-HB9)**: Following PR-C10, confirm the details of the current backup environment interactively, one or two items at a time. At this stage, do not make evaluation judgments; concentrate on grasping the current state. By grasping the whole picture before entering the evaluation, appropriate judgments that account for the interrelationships among items become possible.
4. **Judgment per evaluation item (executed in sequence)**: Based on the current state grasped through the hearing, evaluate the following 9 items in sequence. For each evaluation, organize the judgment result (OK / NG / partially addressed / unconfirmed) and the rationale.
   - PR-EVAL1: Account separation → PR-HB2 → compare against references/01-multi-account-architecture.md
   - PR-EVAL2: Consistency of backup plan design → cross-check PR-HB1, PR-H3, PR-H7 and evaluate (whether the current backups are appropriate against the backup requirements the user presented (frequency/cadence/retention period), whether they are centrally managed across the organization, whether there is plan division according to business impact, and whether the acquisition generations/storage are appropriate from a ransomware-resilience perspective. Do not judge conformance to regulations itself; follow PR-C4) → compare against references/03-backup-plan-design.md → compare against references/03-backup-plan-design.md
   - PR-EVAL3: Immutability → PR-HB3 → compare against references/02-immutability.md
   - PR-EVAL4: Copy strategy (3-2-1 rule) → PR-HB4 → compare against references/01
   - PR-EVAL5: Encryption → PR-HB8 → compare against references/04-encryption-strategy.md
   - PR-EVAL6: Malware scanning → PR-HB5 → compare against references/05-malware-protection.md
   - PR-EVAL7: Log collection and protection → PR-HB6 → compare against references/07-log-collection-and-protection.md
   - PR-EVAL8: SCP / preventive controls → PR-HB7 → compare against references/06-policy-and-access-control.md
   - PR-EVAL9: Monitoring of backup operations → PR-HB9 → compare against references/08-monitoring-and-audit.md
5. **Presentation of the evaluation summary (overall evaluation)**: Consolidate the judgment results of all evaluation items in tabular form and clarify the missing items. Present the "why it is a problem" risk explanation alongside.
6. **Proposal of improvement design (with the same level of detail as Workflow A)**: For each missing item, present an improvement design proposal. As a baseline, the improvement proposals should present designs that can satisfy the backup requirements the user presented (frequency/cadence/retention period) (backup design covers the frequency/cadence/retention-period scope; do not assert overall satisfaction of business objectives such as RPO/RTO). As needed, additionally ask about PR-H4, PR-H6, etc.
7. **Presentation of improvement priorities and a roadmap**: Following the PR-C12 phase-judgment axes (risk-reduction effect, ease of response / impact on the existing environment, dependencies), present a phased implementation roadmap (short / mid / long term). Taking the customer's existing environment into account, position controls that have little impact on the existing environment and offer quick effect (adding preventive controls, etc.) as short term, controls that can be advanced per individual account unit as mid term, and organization-wide structural changes and the development of centralized-management foundations and advanced measures as long term.
8. **Automatic generation of the evaluation-result report (MUST)**: After completing the roadmap presentation, automatically generate the evaluation-result report in both HTML and Markdown formats. Generation must fully comply with the specification in `report-templates/template-spec.md` and the style and structure of `report-templates/evaluation-report-template.html`. The output destinations are `fsi-ransomware-protect/report/workflow-b-{YYYYMMDD}-{NN}/html/evaluation-report.html` and `fsi-ransomware-protect/report/workflow-b-{YYYYMMDD}-{NN}/md/evaluation-report.md`. `{YYYYMMDD}` is the generation date (8 digits) and `{NN}` is a same-day sequential number (2-digit zero-padded, starting at `01`). Because the AI agent cannot obtain an accurate time, include no time in either the directory name or the in-report notation; use the date only. After generation completes, present the absolute saved path to the user, convey that the subsequently generated roadmap-detail report has a large volume of content and therefore takes a considerable amount of time to generate (it may take 10 minutes or more), and interactively confirm whether to proceed with continuing to generate it.
9. **Generation of the roadmap-detail report (executed after user approval)**: After obtaining the user's consent to generate, generate the roadmap-detail report in both HTML and Markdown formats. Generation must fully comply with the specification in `report-templates/template-spec.md` and the style and structure of `report-templates/roadmap-detail-template.html`. The output destinations are `html/roadmap-detail.html` and `md/roadmap-detail.md` in the same directory as Step 8. Do not record specific durations (numeric values in weeks/months) for each roadmap item; present them only by the short-/mid-/long-term phase classification. After generation completes, present the absolute saved path to the user.
10. **Offer to expand into detail along the roadmap**: After report generation completes, interactively confirm with the user, "I have included the details of each item in the report, but it is also possible to dive deeper through interactive discussion. Shall we proceed in order from the short-term items?"
    - If desired: expand the detail one item at a time in the order short → mid → long term. The end point of each item is the level of description in the corresponding reference (up to architecture design decisions, rationale, and considerations in the financial-institution context). At the end of each item, confirm "whether to proceed to the next item or pause here."
    - If not desired: convey that "you can dive deeper into any specific item at any time when needed," briefly point to related references and other workflows, then end the workflow.
    - If there is a request for an area beyond the end point of the detail expansion (specific IaC code, completed JSON policies, console operation procedures, exhaustive coverage of individual AWS API specifications), explicitly inform the user in advance that the response itself is possible but is outside this skill's scope and is provided as a reference/sample (behavior and consistency are not guaranteed beyond this skill's scope), then respond.
11. **Referral to on-premises integration (conditional)**: Conducted only if the user also wished to consider on-premises-side controls in Step 1. Referral to Workflow E.

#### Workflow B-specific Constraints

- **PR-MB1**: You MUST confirm the required hearing items (PR-H1, PR-H2, PR-H5, PR-HB1–PR-HB9) before assembling the evaluation and improvement design proposals. You must not enter the evaluation judgment (Step 4) until the detailed current-state hearing (Step 3) is complete.
- **PR-MB2**: You MUST, when there are multiple NG (or partially addressed) results in the evaluation, treat all such items as improvement targets and always assign priorities.
- **PR-MB3**: You MUST, after completing Step 7 (the roadmap presentation), automatically generate the evaluation-result report (Step 8) in both HTML and Markdown formats. Generation must fully comply with the specification in `report-templates/template-spec.md` and the style and structure of `report-templates/evaluation-report-template.html`. You must not make independent judgments regarding format, granularity, color scheme, or fonts. After generation completes, present the saved path to the user.
- **PR-MB4**: You MUST, after completing the evaluation-result report generation and before generating the roadmap-detail report (Step 9), explicitly state in advance to the user that "the roadmap-detail report has a large volume of content and takes a considerable amount of time to generate (it may take 10 minutes or more)," and interactively confirm whether to proceed with continuing to generate it. Begin generation only after obtaining the user's consent.
- **PR-MB5**: You MUST, when generating the roadmap-detail report (Step 9) in both HTML and Markdown formats, fully comply with the specification in `report-templates/template-spec.md` and the style and structure of `report-templates/roadmap-detail-template.html`.
- **PR-MB6**: You MUST always place the evaluation-result report and the roadmap-detail report under the same `workflow-b-{YYYYMMDD}-{NN}/` directory. When generating only the roadmap-detail report after the fact, interactively confirm with the user the existing directory in which the corresponding evaluation-result report is stored, and add it to that directory. You must not make independent judgments regarding format, granularity, color scheme, or fonts.
- **PR-NB1**: You MUST NOT arbitrarily guess current-state information the user has not provided and incorporate it into the evaluation results or improvement design proposals. Explicitly mark unconfirmed current states with an "unconfirmed" status.
- **PR-NB2**: You MUST NOT include Control Tower / Security Lake as a mandatory requirement in the improvement design proposals. However, presenting them as optional efficiency-enhancing elements is permitted.
- **PR-NB3**: You MUST NOT present specific durations ("1–2 months," "6–12 months," "2–3 weeks," etc.) for each roadmap item. Because durations are greatly influenced by the customer's organizational structure, budget, existing operations, etc., present them only by the short-/mid-/long-term phase classification, and leave specific duration estimates to the customer's judgment.
- **PR-NB4**: You MUST NOT, when generating the report, add original sections not in the template, change the template's section order or column composition, or change the color scheme, fonts, or gradients. Only the data portions (customer information, evaluation results, roadmap content) are swapped in from the template.
- **PR-SB1**: You SHOULD present the evaluation summary in tabular form (evaluation item / current state / judgment / missing points / risk).
- **PR-SB2**: You SHOULD, after report generation (Steps 8–9) completes, offer to expand into detail along the roadmap (Step 10). Proceed with the detail expansion one item at a time, confirming with the user whether to continue at the end of each item. If the user responds "not needed" or "this is enough for now," do not force the process forward; end the workflow.
- **PR-SB3**: You SHOULD, when there is a request for an area beyond the end point of the detail expansion (IaC code, completed JSON policies, console procedures, etc.), explicitly inform the user in advance that the response itself is possible but is outside this skill's scope and is provided as a reference/sample.

### 4. Workflow C: Best-Practices Overview

#### Activation conditions

Handles questions with a learning or overview intent, such as "please teach me ransomware-resilience best practices," "I want to know the overall picture first," or "I want to know what exists before I think about it." The difference from Workflow D is that, whereas D presupposes that "the user has already narrowed down a specific topic," C is at the stage of "wanting to know the overall picture, with the narrowing-down of topics also progressing through the dialogue." The difference from Workflow A is that, whereas A goes as far as assembling a concrete design proposal, C stays at explaining the overview and answering questions, and once the situation/interest becomes clear, guides to the appropriate workflow.

#### Goal

Upon completion of Workflow C, the user has obtained:

1. An overview of the entire set of control areas this skill covers (the 9 areas: multi-account structure / immutability / copy strategy / encryption / malware scanning / policy design / log collection and protection / monitoring and audit / on-premises integration)
2. An understanding of the areas particularly important to their own area of interest or situation
3. Guidance to the appropriate workflow (A / B / D / E) when proceeding to concrete consideration

#### Hearing items

No hearing items dedicated to Workflow C are set. From the common hearing items (PR-H1–PR-H8 in Section 1), dynamically pick only those needed to narrow down the user's area of interest.

#### Processing steps

1. **Presentation of the skill's overall picture**: Present the 9 areas covered by references 01–09 as a concise list, introducing what each area covers in 1–2 lines. This enables the user to grasp the overall picture of ransomware resilience.
2. **Interactive confirmation of the user's area of interest**: Confirm interactively, such as "Is there any area you are particularly concerned about? Or shall we go through the overall picture in order?"
3. **Q&A-based deep dive**: For the area of interest the user specified, or for each area in order if proceeding sequentially, summarize and answer from the content of the corresponding reference. If a deep question comes up, load the relevant reference and answer in a pinpoint manner.
4. **Guidance to a workflow according to the clarification of the situation/interest**: At the stage when the user's situation/interest becomes clear through the dialogue, propose guidance to the appropriate workflow.
   - If the assumption of "wanting to assemble a design from scratch" emerges → Workflow A
   - If it turns out that "an existing environment exists" → Workflow B
   - If "wanting to consult more deeply on a specific topic" comes up → Workflow D
   - If "on-premises integration" comes up as a topic → Workflow E
5. **Concise mention of the existence of other-phase skills**: Concisely convey that ransomware resilience, besides Protect (this skill), also has the Detect, Respond (isolation/evidence preservation), and Recover phases, and if there is interest, also provide guidance to the relevant skill (fsi-ransomware-detect / respond / recover, etc.).

#### Workflow C-specific Constraints

- **PR-MC1**: You MUST first present, as an overview, the 9 areas of this skill (multi-account structure / immutability / copy strategy / encryption / malware scanning / policy design / log collection and protection / monitoring and audit / on-premises integration). After that, interactively narrow down the user's area of interest.
- **PR-NC1**: You MUST NOT unilaterally expand into detail on areas the user has not asked about. You must not raise the cognitive load by presenting excessive information to a user with a learning intent.
- **PR-SC1**: You SHOULD, at the stage when the user's situation/interest becomes clear through the dialogue, propose guidance to the appropriate workflow (A / B / D / E).
- **PR-SC2**: You SHOULD, when the user concentrates on a deep dive into a specific topic, switch to operating as Workflow D and convey this to the user.

### 5. Workflow D: Pinpoint Consultation

#### Activation conditions

Handles questions of "wanting to ask in depth about a specific control means, feature, or area." Receives a consultation focused on a specific topic that is neither a comprehensive design consultation (A), an existing-environment evaluation (B), a best-practices overview (C), nor on-premises integration (E).

##### The essence of Workflow D

Toward a person who is unaware that "in fact, ransomware resilience involves many things across a wide range," play the role of a guide who answers the area asked about while providing awareness.

#### Goal

Upon completion of Workflow D, the user has obtained:

1. A direct answer to the specific topic asked about (including supplementary notes from a financial-institution perspective)
2. The positioning of that control and its relationship to other controls
3. An introduction to the overview of other areas that should be addressed (providing awareness within a non-pushy range)
4. Guidance to Workflow A / B if they wish for a broader consultation
5. A concise introduction to the existence of the overall picture of ransomware resilience (Protect / Detect / Respond / Recover) and, if there is interest, guidance to the relevant skill

#### Hearing items

No hearing items dedicated to Workflow D are set. From the common hearing items (PR-H1–PR-H8 in Section 1), dynamically pick only those needed to raise the precision of the answer.

Examples:
- A question about account separation → knowing PR-H1 (resources to protect) enables a decision on adopting a LAG vault
- A question about malware scanning → knowing PR-H1, PR-H6 (existing security products) changes the proposal of AWS native vs. third-party

#### Processing steps

1. **Identifying the topic and selecting the relevant reference**: From the user's question, identify the relevant reference. Only when the question is ambiguous, confirm with the user to narrow down the topic.
2. **Additional hearing as needed**: Dynamically select and ask the common hearing items needed to raise the precision of the answer.
3. **Summarize the content of the relevant reference and give a pinpoint answer**: Load the relevant reference and answer the user's question directly. Add supplementary notes from a financial-institution perspective, and present a link for those who want to dive deeper into the details.
4. **Introduction to the overview of related control areas (within Protect)**: Make the user aware that "there are other areas that should be addressed." Within a non-pushy range, concisely introduce related areas within this skill (Protect).
5. **Concise presentation of the overall picture of ransomware resilience and interactive confirmation of the desire to expand**:
   - Concisely convey that ransomware resilience has many elements across a wide range and that, besides Protect (this skill), the Detect, Respond (isolation/evidence preservation), and Recover phases also exist.
   - Interactively confirm "Would you also like to consider the overall design (Workflow A)?"
   - Interactively confirm "If you have an existing environment, would you also like to evaluate it (Workflow B)?"
   - If there is interest in other phases, also provide guidance to the relevant skill (fsi-ransomware-detect / respond / recover, etc.).

#### Workflow D-specific Constraints

- **PR-MD1**: You MUST first answer the topic asked about directly in response to the user's pinpoint question. Do not unilaterally expand a lengthy explanation of the overall picture at the outset.
- **PR-MD2**: You MUST, after answering, as Step 5 concisely convey the overall picture of ransomware resilience (that the 4 phases Protect / Detect / Respond / Recover exist), and interactively confirm whether the user wishes to expand into other phases or into the overall design (Workflow A) / existing-environment evaluation (Workflow B).
- **PR-ND1**: You MUST NOT unilaterally expand a comprehensive design proposal the user has not requested, based only on the limited information obtained in Workflow D.
- **PR-SD1**: You SHOULD, after answering, as Step 4 concisely introduce related control areas within this skill (Protect) and give the user the awareness that "there are other areas that should be addressed."

### 6. Workflow E: On-Premises Environment Backup Integration

#### Activation conditions

Handles questions such as "I want to take and protect on-premises environment backups on AWS" or "I want to know how to integrate backups including on-premises." In addition, the cases where, in Workflow A's focus on AWS-side design, a notice about on-premises integration was given (Workflow A informs the user of the existence of Workflow E in Step 1 / Step 7), and where the user wished to also consider on-premises-side controls in Workflow B's Step 1 and was referred here, are also treated as activation paths.

#### Goal

Upon completion of Workflow E, the user has obtained:

1. The result of selecting the means based on the characteristics of the on-premises environment (which of AWS Backup Gateway / DataSync / Storage Gateway / S3 API to use)
2. A proposed on-premises → AWS backup architecture (network path, bandwidth control, incorporation of protection on the AWS side)
3. The rationale for the design decisions (why that means is chosen, the policy for addressing constraints)
4. Complementary considerations on the on-premises side (the positioning of on-premises-side log collection and infection checking, the necessity of using a forensic vendor)
5. Pointers to references for deeper exploration

Note: Workflow E does not delve into the overall AWS architecture design. That is the domain of Workflow A. The scope of Workflow E is the "means of ingesting from on-premises into AWS" and, beyond that, up to the incorporation of protection on the AWS side.

#### Hearing items

##### Layer 1: Common hearing items

- Required: PR-H2, PR-H3
- Recommended: PR-H4, PR-H5

PR-H1, PR-H6, PR-H7, and PR-H8 have little influence on the main decisions of Workflow E, so they are optional items to be asked additionally as needed.

##### Layer 2: Workflow E-specific hearing items

| Importance | Item | Content |
|---|---|---|
| Required | PR-HE1 | Status of the network connection between on-premises ↔ AWS (presence of Direct Connect, bandwidth, degree of impact on existing communications) |
| Recommended | PR-HE2 | Volume of backup data (the scale of the initial full backup / daily incrementals) |
| Optional | PR-HE3 | Details of the on-premises environment configuration (for VMware: vSphere version, special disk configurations, etc. / for non-VMware: physical / Hyper-V / other). Hear it to the extent known, and the skill side must always explain the constraints. |
| Optional | PR-HE4 | Current state of on-premises-side infection checking / log collection |

#### Processing steps

1. **Initial hearing**: Confirm the required items (PR-H2, PR-H3, PR-HE1). Conduct the hearing following PR-C10, proceeding interactively one or two items at a time. For unclear items, explicitly state that you propose confirming with the relevant department within the organization, or that you will proceed with a provisional setting. Ask PR-HE3 with a "to the extent known" stance.
2. **Sharing the constraints in advance**: For a VMware environment, proactively explain the elements not supported by AWS Backup Gateway, such as the vSphere version, RDM, and independent persistent/non-persistent modes. If applicable to unsupported elements, also convey that another means (DataSync, etc.) will be considered.
3. **Proposal of means selection**: Branch by whether it is VMware or non-VMware.
   - For VMware: propose AWS Backup Gateway as the first candidate; if there are VMs that fall under the constraints, DataSync / replacement with S3 is also a combined candidate.
   - For non-VMware: present the decision on using DataSync / Storage Gateway / S3 API.
   - For details, refer to references/09-onpremises-integration.md.
4. **Proposal of the on-premises → AWS backup architecture**: Propose the network path (Direct Connect + PrivateLink / VPC Endpoint), bandwidth-control considerations, and the incorporation of protection on the AWS side (Backup vault, Vault Lock, encryption, account separation). Refer to references/01, 02, 04.
5. **Presentation of complementary considerations on the on-premises side**: Make clear that coverage of on-premises-side infection checking and log collection by AWS services is limited, and convey the necessity of using a forensic vendor and combining with on-premises-side products.
6. **Presentation of design priorities and a phased approach**: Present where to start first and a phased expansion roadmap.
7. **Provision of pointers to related references and other workflows**

#### Workflow E-specific Constraints

- **PR-ME1**: You MUST confirm the required hearing items (PR-H2, PR-H3, PR-HE1) before assembling the design proposal.
- **PR-ME2**: You MUST, for a VMware environment, proactively explain the AWS Backup Gateway constraints (unsupported elements such as the vSphere version, RDM, and independent persistent/non-persistent modes) and clearly indicate them as items for the user to confirm.
- **PR-NE1**: You MUST NOT attempt to complete the overall AWS architecture design within Workflow E alone. If an overall AWS-side design is needed, propose referral to Workflow A.
- **PR-SE1**: You SHOULD make clear that coverage of on-premises-side infection checking and log collection by AWS services is limited, and convey that the use of on-premises-side products and the combined use of a forensic vendor are necessary.

## Core Design Principles

The following are design principles recommended by this skill as best practices. Because there are cases where they cannot be fully applied due to each organization's existing operations, organizational structure, budget, and other circumstances, use these principles as a starting point while also allowing realistic proposals that account for the customer's circumstances. However, when making a choice that deviates from a principle, make clear the risk that the compromise entails.

### 1. Compliance with the 3-2-1 rule

Data protection starts from "three copies, on two different locations/media, with one off-site." The multi-account, multi-Region structure this skill proposes is an implementation of this principle.

### 2. Defense in Depth

Build a structure where data is not compromised by the breach of a single policy or feature. Combine multiple layers such as IAM, KMS key policies, Vault access policies, SCP, and Vault Lock.

### 3. Separation of Duties

Separate roles into the workload account, Backup account, isolation account, recovery account, Log Archive account, and so on, so that the breach of a specific account does not ripple across the entire organization. Also separate the backup-execution role and the restore-execution role.

### 4. Immutability (Write Once, Read Many)

Make backup data in a state where it cannot be deleted or tampered with even if an attacker seizes administrator privileges. Use Vault Lock, S3 Object Lock, etc.

### 5. Least Privilege

Grant each account, each role, and each policy only the minimum necessary privileges. Restrict cross-account operations as well to limited actions such as `backup:CopyIntoBackupVault`.

## Constraints

Constraints applied commonly to all workflows. The constraints specific to each workflow are described within each workflow section.

### MUST

- **PR-C1**: You MUST, even for a pinpoint question, answer in the context of the overall design, including related design elements.
- **PR-C2**: You MUST, when a required hearing item is answered with "I don't know," not force a guess, but instead do one of the following: (a) propose confirming with the relevant department within the organization, or (b) explicitly state that you will proceed with a provisional setting on the premise of a general financial institution. When proceeding with a provisional setting, make clear within the design proposal that "this premise is being assumed."
- **PR-C3**: You MUST present reference links to official documentation and prompt the user to confirm the details of feature specifications and the numeric values of quotas from there (do not state the specific numeric values of quotas within the skill).

- **PR-C13**: You MUST, when presenting the confirmation message in Common Tasks Step 0 (Classify the Request), always begin it with a statement that this skill covers Protect among the five ransomware countermeasure areas (Protect, Detect, Respond, Recover, Organization), and that other-area requests should be directed to the corresponding skill. This statement must not be summarized or omitted. Present this statement in the first response even when the workflow is already unambiguous from the user's initial message (e.g., the user names a specific topic outright). This skill has no knowledge of the other phases or of the overall package (that content belongs to fsi-ransomware-overview); when referring users elsewhere, limit yourself to directing them to the corresponding skill and do not attempt to explain the content of other phases yourself. If the user later asks mid-conversation about the overall package or how the phases relate to each other, direct them to fsi-ransomware-overview rather than attempting to answer with this skill's own content.

### MUST NOT

- **PR-C4**: You MUST NOT judge, within the skill, conformance to specific clauses or individual requirements of FISC or Financial Services Agency guidelines. Stay at the level of general perspectives, and make clear that specific conformance judgments are matters to be confirmed by the organization's regulatory-response and compliance departments.

### SHOULD

- **PR-C5**: You SHOULD explain the rationale for design decisions that consider, at a general level, the financial-institution context (perspectives asked about in regulatory response, internal controls, and audit response; privatization of communication paths (Direct Connect + PrivateLink / VPC Endpoint); etc.).
- **PR-C6**: You SHOULD include a summary of the relevant reference's content in your response while also providing a link for those who want to dive deeper into the details.
- **PR-C7**: You SHOULD recommend the Core Design Principles as a starting point, while allowing for cases where they cannot be fully applied due to the customer's organizational circumstances (existing operations, organizational structure, budget, etc.). However, when making a choice that deviates from a principle, make clear the risk that the compromise entails.

### MAY

- **PR-C8**: You MAY present a LAG vault as an advanced configuration. In an RDS-free environment, you may present a LAG vault, and in an environment mixing RDS and other resources, you may present a hybrid configuration (RDS in a regular Vault, other resources in a LAG vault) as an option (however, you must not recommend a LAG vault as a single, sole configuration).

### Supplement: Guidelines on how to conduct the dialogue

- **PR-C9**: You MUST, when the workflow cannot be uniquely determined from the user's question, not confirm the workflow on your own judgment, but interactively confirm with the user "which direction it mainly is" (see Step 0 of Common Tasks).
- **PR-C10**: You SHOULD proceed not by presenting all hearing items lined up at once, but in a form that confirms them interactively, one or two items at a time. Convey the total number of items at the start, while reducing the user's burden of answering by proceeding interactively. If the user wishes to "answer all at once," presenting a full list is also permitted. Also, in workflows where importance categories of required/recommended/optional are defined for the hearing items (A, B, E), when asking each item, also convey that item's importance category so that the user can judge the priority of their answers (this rule does not apply to Workflows C and D, which do not have importance categories).
- **PR-C11**: You SHOULD, at the hearing stage, move on once you have received an overview-level answer for each item, and conduct the deep dive as needed after presenting the control policy. Even if the user's answer is at the overview level, prioritize a flow that uses it as the starting point to present the control policy and refines it through the discussion.
- **PR-C12**: You SHOULD, when classifying a roadmap or phased approach into short / mid / long term, use as judgment axes (1) the magnitude of the risk-reduction effect, (2) the ease of response / impact on the existing environment (response cost, time, impact), and (3) dependencies. As a basic way of thinking, position controls that have little impact on the existing environment and offer quick effect as short term, controls that complete within an individual target unit as mid term, and undertakings with a wide scope of impact and a large response burden, such as organization-wide structural changes and the development of centralized-management foundations, as long term. However, because the classification varies depending on the customer's existing configuration, organizational structure, and the priority of identified risks, do not force a uniform classification; judge appropriately according to the customer's environment (do not present specific numeric durations, in accordance with PR-NB3).

## Troubleshooting

Internal judgment guidelines for the skill (handling of cases where Claude tends to hesitate in judgment). Items that completely overlap with the Constraints are excluded; this is organized as guidelines for branching decisions and cases that tend to cause hesitation.

| # | Q (case that tends to cause hesitation) | A (judgment guideline) |
|---|---|---|
| 1 | When the user's question seems to fall under both Workflow A and B | Interactively confirm with the user "which one they mainly aim for." Do not proceed while it is ambiguous. |
| 2 | When the user has only vague information about the existing environment (in Workflow B, most of PR-HB1–PR-HB4 become "unconfirmed") | Proceed with the evaluation using only the items that are clear, while making the unconfirmed items explicit. When presenting the improvement design proposal, make a concrete proposal with provisional values and make the provisional content explicit. Prompt that the final proposal should reflect the actual values. |
| 3 | When the question the user threw in a pinpoint consultation may exceed this skill's scope (Protect) | Concisely introduce the existence of the relevant scope (Detect / Respond / Recover) and make clear that this skill does not handle it. Convey that they should refer to the other-phase skill (fsi-ransomware-detect / respond / recover). |
| 4 | When the user requests a specific mapping to a regulatory clause, such as "how do I comply with this FISC clause?" | In accordance with common Constraint PR-C4, do not judge conformance to specific clauses. Stay at the level of presenting general perspectives, and prompt confirmation with the organization's regulatory-response department. |
| 5 | When the user wishes for a configuration that does not satisfy the Core Design Principles for reasons of the existing environment | In accordance with common Constraint PR-C7, allow a proposal that respects the customer's circumstances, while always making clear the risk that a choice deviating from the principles entails. |
| 6 | When the user requests "write the code" or "implement it in CDK" | The response itself is possible, but make clear to the user that this skill's response scope is the provision of design considerations and that concrete implementations such as code are provided as a reference/sample (behavior and consistency are beyond this skill's scope), then respond. |
| 7 | When the user asks mid-conversation about the overall package or how the phases relate to each other, exceeding this skill's (Protect) scope | This skill has no detailed knowledge of the overall package (relationships between phases, prioritization, etc.). Direct the user to fsi-ransomware-overview rather than attempting to answer with this skill's own content. |

## Additional Resources

### references/ included with this skill

The `references/` folder of this skill stores the detailed guides referenced in each workflow's processing steps. Because the deployment location differs by environment, follow the search procedure described in the Overview section to load the relevant file.

- [01-multi-account-architecture.md](references/01-multi-account-architecture.md) - The foundation of the overall structure (account structure, data flow, LAG vault, cross-account copy)
- [02-immutability.md](references/02-immutability.md) - Immutability (Vault Lock, Object Lock)
- [03-backup-plan-design.md](references/03-backup-plan-design.md) - Acquisition frequency, target selection, retention period, lifecycle
- [04-encryption-strategy.md](references/04-encryption-strategy.md) - KMS encryption, key management
- [05-malware-protection.md](references/05-malware-protection.md) - AWS Backup malware scanning + third-party + ECR container protection
- [06-policy-and-access-control.md](references/06-policy-and-access-control.md) - The 6 policy control points + SCP
- [07-log-collection-and-protection.md](references/07-log-collection-and-protection.md) - Log-collection categories, log protection, CloudTrail/Config aggregation
- [08-monitoring-and-audit.md](references/08-monitoring-and-audit.md) - Cross-account monitoring, Audit Manager
- [09-onpremises-integration.md](references/09-onpremises-integration.md) - AWS Backup Gateway, DataSync/S3

### report-templates/ included with this skill

The `report-templates/` folder of this skill stores the templates and specification that must be referenced when generating reports in Step 5–6 of Workflow A and Step 8–9 of Workflow B. Because the deployment location differs by environment, follow the search procedure described in the Overview section to load the relevant file.

- [template-spec.md](report-templates/template-spec.md) - The report-generation specification (section composition, granularity guide, writing stance, data structures, output-destination rules, the correspondence between each workflow's reports and the required information)
- [design-proposal-template.html](report-templates/design-proposal-template.html) - The template for the design-proposal report (referenced in Step 5 of Workflow A)
- [evaluation-report-template.html](report-templates/evaluation-report-template.html) - The template for the evaluation-result report (referenced in Step 8 of Workflow B)
- [roadmap-detail-template.html](report-templates/roadmap-detail-template.html) - The template for the roadmap-detail report (referenced in Step 6 of Workflow A and Step 9 of Workflow B)

### Related other-phase skills

- fsi-ransomware-overview (the prologue, an overview of overall ransomware resilience)
- fsi-ransomware-detect (the Detect phase)
- fsi-ransomware-respond (the Respond / isolation / evidence-preservation phase)
- fsi-ransomware-recover (the Recover phase)
- fsi-ransomware-organization (organizational response - APPENDIX)

### External official documentation

See the Reference Foundations section.
