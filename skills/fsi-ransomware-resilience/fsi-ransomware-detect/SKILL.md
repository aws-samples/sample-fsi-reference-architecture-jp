---
name: fsi-ransomware-detect
description: >-
  Provides design/assessment support for the detection/analysis aspect of ransomware countermeasures on AWS, for financial services organizations. Use when: (1) designing a detection/analysis posture from scratch, or (2) assessing an existing posture for gaps. Covers service impact detection (resource/service/synthetic/application monitoring), security attack detection (Amazon GuardDuty, third-party products), alert-triggered root-cause triage (manual checks) for external attacks, log-based analysis (Amazon Detective, SIEM on OpenSearch, infection checks), detection aggregation/delegated admin, and forensic vendor engagement prep. Activate on ransomware detection, service monitoring, attack detection, GuardDuty, or incident investigation mentions. Do NOT use for protection/backup, evidence preservation/forensics/isolation, on-prem detection, or unclear phase -- use fsi-ransomware-overview first. Target: FSI detection/analysis staff, incl. security/infra/DevOps and risk/compliance.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Ransomware Countermeasures for Financial Institutions: Detection and Analysis (Detect)

## Overview

This skill supports the design and existing-posture assessment of the posture for "detecting" damage and threats and "analyzing" detected events, within the ransomware countermeasures that financial services industry organizations build on AWS. What this skill provides:

- Design support for detection of service impact (whether the mechanism can quickly detect service impact, going beyond resource monitoring to service monitoring, synthetic monitoring, and application-level monitoring (business metrics))
- Design support for detection of security attacks (Amazon GuardDuty protection plans, third-party products)
- The concept of initiating the incident response process triggered by alerts, and design support for the root-cause triage (manual checks) that determines, after an alert, whether it is caused by an external attack (ransomware, etc.)
- Design support for analysis and investigation of detected events (analysis of suspicious activity via Amazon Detective / SIEM on Amazon OpenSearch Service leveraging already-collected logs, and checking for signs of infection)
- Aggregation and delegated administration of detection and analysis (centralizing organization-wide detection and management by aggregating into a security account)
- The positioning of advance preparation for engaging forensic vendors when the analysis bar is high
- A phased design/improvement roadmap for the detection and analysis posture based on the above, and the generation of customer-facing reports

The scope this skill covers:

- Focuses on the "Detect" phase of ransomware countermeasures, and in addition to detection, covers the analysis of detected events
- The Protect, Respond (response/isolation), and Recover phases are handled by separate skills
- The design of log collection and protection is within the scope of the Protect phase; this skill operates on the premise of "leveraging already-collected logs"
- Executing evidence preservation, full-scale forensic analysis, and isolation are within the scope of the Respond phase; this skill covers up to "organizing the scope handled in-house versus the scope delegated to specialist organizations, and bridging to preservation and specialist investigation"
- Detection of impact/attacks in on-premises environments is out of scope. On-premises detection is mainly realized through a combination of on-premises monitoring products, antivirus products, forensic tools, and operations, rather than being efficiently realized with AWS services, so it is not handled by this skill

The detailed guides and report generation templates of this skill are stored in the `references/` folder and the `report-templates/` folder at the same level as this skill file. When a workflow's processing steps instruct you to "refer to references/XX" or "refer to report-templates/XX," search for the relevant file using the following procedure, load it, and then compose your response.

1. Try `.kiro/skills/fsi-ransomware-detect/{references,report-templates}/` under the workspace
2. If not found, try the user-level `~/.kiro/skills/fsi-ransomware-detect/{references,report-templates}/`
3. If neither is found, ask the user for the deployment path of this skill

Even if loading a reference or template fails, do not compose a response based on general knowledge alone; always inform the user of the situation before deciding how to proceed.

This skill is designed to ensure the accuracy of responses by referring to official AWS documentation. When using it, we recommend setting up the AWS Documentation MCP server in advance (see the README.md attached to this skill for setup instructions).

## Reference Foundations

This skill is structured to complement the design considerations required in the context of financial institutions, based on the following authoritative sources. Links are kept, in principle, at the service-top / major-category level; deep references to individual features are made as needed within the body text and references/.

### Official AWS guidance (comprehensive best practices)

- AWS Well-Architected Framework — Operational Excellence pillar, "Implement observability" (the core of the monitoring/observability concept)
- Choosing an AWS monitoring and observability service (AWS Decision Guide; guidance on selecting monitoring services)
- AWS Observability Best Practices (per-service monitoring recipes)
- AWS Security Incident Response guide (the flow from detection to analysis)

### Per-service official documentation

- Amazon GuardDuty
- Amazon Detective
- Amazon OpenSearch Service (SIEM on Amazon OpenSearch Service)
- Amazon CloudWatch
- AWS Security Hub

### Reference in the context of financial institutions

- IPA "Strengthening the upstream process of system development (Non-Functional Requirements Grades)" (a reference for the concept of designing monitoring levels according to system importance; the project has ended, but the deliverables remain publicly available)

## Common Tasks

### 0. Classify the Request

From the user's question, tentatively select a workflow using the following correspondence.

| User intent | Workflow |
|---|---|
| Want to newly design a detection/analysis posture for ransomware damage in an AWS environment / want to consult on where to start | A |
| Want to assess the sufficiency of an existing detection/analysis posture as a ransomware countermeasure, identify gaps, and improve | B |
| Want an overview-level understanding of detection/analysis best practices / want to drill down interactively for learning purposes | C |
| Want pinpoint, in-depth consultation on a specific detection/analysis topic (service monitoring, attack detection, GuardDuty, log-based analysis/investigation, etc.) | D |

However, since there are many cases where the workflow cannot be uniquely determined from the user's question alone, always confirm interactively with the user "which of the following directions to proceed with" before moving to the appropriate workflow. Specifically, present a confirmation message such as the following. This confirmation message MUST always begin with a statement that this skill covers only Detect among the five areas (see DT-C13). As shown in the example below, output the grouping headings in bold and choices A–D as a Markdown list, preserving this structure; do not collapse it into a single plain-text paragraph (see DT-C14).

> This skill covers "Detect" among the five areas of ransomware countermeasures (Protect, Detect, Respond, Recover, Organization), supporting the design and evaluation of detecting damage/threats and analyzing detected events. If you have questions about other areas, please request the corresponding skill.
>
> Before answering your question, let me confirm which direction to proceed in. In addition to "detecting" ransomware damage/threats, this skill covers the "analysis" of detected events (executing evidence preservation, full-scale forensic analysis, log collection design, and on-premises detection are out of scope for this skill).
>
> **[Generates a design/assessment report]**
> - A. Build the overall design of a detection/analysis posture from scratch
> - B. Assess the sufficiency of an existing detection/analysis posture as a ransomware countermeasure (assess/improve the existing posture)
>
> **[Interactive guidance]**
> - C. First get an overview-level understanding of detection/analysis best practices (drilling down interactively, and guiding to workflows A/B/D as needed)
> - D. Want pinpoint knowledge of a specific topic (service monitoring, attack detection, GuardDuty, log-based analysis, etc.)
>
> Which direction does it mainly correspond to? Please also let me know if multiple apply.

Based on the user's response, proceed to the appropriate workflow.

### 1. Common hearing items

Used in common across workflows A, B, C, and D. These are items for grasping the "requirements, landscape, and policy" that serve as the premise for designing and assessing the detection/analysis posture; they are not items for assessing the current state of detection/analysis maturity itself (the current maturity is handled by the Workflow B-specific current-state hearing items DT-HB1–DT-HB5). The required/recommended classification differs per workflow. Because the design of log collection/protection and account structure design themselves are within the scope of the Protect phase, this skill's hearing is limited to the scope necessary for detection/analysis design.

| # | Hearing item |
|---|---|
| DT-H1 | The in-use resources that are the main targets of infection detection. The focus points of detection design are the resources where the customer's workloads (applications) or data directly run/are stored and which are subject to checks for malware infection or ransomware damage (e.g., Amazon EC2 / Amazon ECS / Amazon EKS / AWS Fargate / Amazon S3 / others). This is the premise for considering the coverage of attack detection and the selection of protection plans |
| DT-H2 | Multi-account structure / organizational structure (whether AWS Organizations / Control Tower is used, the scale in number of accounts, the presence of a security account. This is the premise for designing aggregation/delegated administration of detection/analysis). Account structure design itself is within the scope of the Protect phase |
| DT-H3 | Existing monitoring/security infrastructure and continuation policy (the presence and continued-use policy of existing monitoring infrastructure (centered on Amazon CloudWatch or a third-party monitoring product), EDR / AV, SIEM, etc. This is the premise for a detection/analysis design that leverages existing assets. Here, rather than assessing the sufficiency of maturity, grasp the presence/policy as a premise to incorporate into the design). Log collection/protection itself is within the scope of the Protect phase |
| DT-H4 | Forensic analysis implementation policy (whether the analysis/investigation of detected events will be (a) performed in-house, (b) with the outlook of cultivating analysis skills within the organization, or (c) delegated to external forensic vendors with specialist skills. Combinations are possible. Depending on the policy, whether to place the design's center of gravity on developing an analysis platform or on advance preparation for vendor engagement changes) |

When confirming target resources in DT-H1, the handling of detection differs depending on the nature of the resource. (1) Compute (Amazon EC2, Amazon ECS, Amazon EKS, AWS Fargate, etc.) is an execution environment where malware execution/infection can occur, and is the main target of runtime threat detection and malware scanning (for AWS Fargate as well, the in-container execution environment and data are the customer's workloads, so it is treated the same as other compute as a target of infection checks). (2) Storage (Amazon S3, Amazon EFS, Amazon FSx, etc.) is a target of data encryption/destruction/exfiltration; Amazon S3 is a direct target of detection, while Amazon EFS / FSx, etc., are covered by detection on the mounting compute and by log-based analysis/investigation. (3) Managed services (Amazon RDS, Amazon Aurora, Amazon DynamoDB, AWS Lambda, etc.) are not environments where the user manages the OS/runtime and where virus files are executed, so runtime malware detection (infection checks) is out of scope for this skill; data and suspicious access are caught by log-based analysis/investigation and by the Protect phase (some services provide mechanisms to detect suspicious access; see references/01-detection-strategy.md for details). The direct targets of malware scanning are, as of this writing, Amazon EC2 (EBS) and Amazon S3, but because the supported scope changes with feature enhancements, confirm against the latest version of the official Amazon GuardDuty documentation when making design proposals/assessments.

### 2. Workflow A: Overall design of the detection/analysis posture

#### Trigger conditions

Handles questions such as "I want to newly design a detection/analysis posture for ransomware damage in an AWS environment," "I want to build the detection mechanism from now on," and "I want to consult on where to start." If the purpose is to assess/improve an existing posture, select Workflow B.

#### Goal

Upon completing Workflow A, the user has obtained the following:

1. A design proposal for a posture combining detection through continuous monitoring (service impact / security attacks) and the analysis/investigation of detected events
2. The detection/analysis services to adopt and their respective roles and differentiation (Amazon GuardDuty / Amazon CloudWatch / Amazon Detective / SIEM on Amazon OpenSearch Service, etc.)
3. A design that connects alerts to response as the starting point, and a design for analysis/investigation leveraging already-collected logs
4. The positioning of advance preparation for engaging forensic vendors when the analysis bar is high (preservation execution is bridged to the Respond phase)
5. Design priorities and a phased roadmap (where to start first)
6. A design proposal report (an HTML / Markdown report that consolidates, into a single report, the detection/analysis posture design policy, each design area, and the phased roadmap. In this phase, the design proposal and the roadmap are consolidated into a single report, and a separate roadmap detail report is not generated)
7. Pointers to references, other workflows, and other-phase skills for deeper exploration

#### Hearing items

Select the following from the common hearing items:

- Required: DT-H1, DT-H2, DT-H3
- Recommended: DT-H4

#### Processing steps

1. **Initial hearing**: Confirm the required items (DT-H1, DT-H2, DT-H3). Conduct the hearing interactively, one or two items at a time, following DT-C10. For unknown items, clarify that you will propose confirming with the relevant department in the organization, or proceed with a tentative assumption
2. **Presentation of the broad detection/analysis policy**: Present the broad flow of "detect through continuous monitoring → initiate response triggered by alerts → analyze detected events." Add that the detection of service impact and the detection of attacks may each come first, and that the order of detection is not fixed
3. **Detection design proposal**: Propose detection of service impact (depth of monitoring: resource monitoring, service monitoring, synthetic monitoring, application-level monitoring (business metrics)) and detection of security attacks (GuardDuty protection plans, third parties). Also propose the operational readiness (who performs it and at what timing) of the root-cause triage operation (manual checks) that determines, after an alert, whether it is caused by an external attack (ransomware, etc.). Touch lightly on the concept of designing monitoring levels according to system importance. Defer the details of specific monitoring/detection methods to references to official guidance. Refer to references/01-detection-strategy.md
4. **Analysis/investigation design proposal**: Propose analysis/investigation leveraging already-collected logs (Amazon Detective / SIEM on Amazon OpenSearch Service) and the perspectives for checking signs of infection. Because identifying the root cause and the scope of damage requires advanced specialist skills, convey that when the analysis bar is high, engaging forensic vendors should be considered, along with the positioning of the advance preparation for it (engagement procedures, external coordination). Clarify that log collection/protection itself is deferred to the Protect phase. Refer to references/02-log-analysis-and-investigation.md
5. **Presentation of design priorities and a phased roadmap**: Following the DT-C12 phase judgment axes (risk-reduction effect, ease of response / impact on the existing environment, dependencies), present a short-term / mid-term / long-term roadmap. Do not present specific numeric durations (DT-NA2)
6. **Automatic generation of the design proposal report (MUST)**: After completing the roadmap presentation, automatically generate the design proposal report (consolidating the design policy, each design area, and the phased roadmap into one) in both HTML and Markdown formats. Generate it in full compliance with the specification in `report-templates/template-spec.md` and the style/structure of `report-templates/design-proposal-template.html`. The output destinations are `fsi-ransomware-detect/report/workflow-a-{YYYYMMDD}-{NN}/html/design-proposal.html` and `fsi-ransomware-detect/report/workflow-a-{YYYYMMDD}-{NN}/md/design-proposal.md`. `{YYYYMMDD}` is the generation date (8 digits), and `{NN}` is the same-day sequential number (2-digit zero-padded, starting from `01`). Because the AI agent cannot obtain the exact time, do not include the time in the directory name or in the report's notation; use only the date. In this phase, because the design proposal and the roadmap are consolidated into a single report, a roadmap detail report is not generated separately (state the reason for this within the report; see template-spec.md for details). After generation completes, present the absolute save path to the user
7. **Detail-expansion offer and provision of pointers to related references / other workflows**: After report generation completes, confirm interactively with the user, "The report includes the details of each design area, but it is also possible to drill down through interactive discussion." If desired, expand details one area at a time, confirming continuation with the user at the end of each area. The endpoint of detail expansion is the level of description in the corresponding reference (design decisions, decision rationale, and points to note in the financial-institution context). If not desired, briefly indicate guidance to related references or other workflows and then end the workflow. In addition, if preservation of detected events or full-scale forensic analysis is needed, guide the user to the Respond phase skill

#### Workflow A-specific Constraints

- **DT-MA1**: You MUST confirm the required hearing items (DT-H1, DT-H2, DT-H3) before assembling the design proposal
- **DT-MA2**: You MUST, after completing Step 5 (roadmap presentation), automatically generate the design proposal report (Step 6) in both HTML and Markdown formats. Generate it in full compliance with the specification in `report-templates/template-spec.md` and the style/structure of `report-templates/design-proposal-template.html`. You must not make independent decisions regarding format, granularity, color scheme, or fonts. In this phase, because the design proposal and roadmap are consolidated into a single report, a roadmap detail report is not generated separately. After generation completes, present the save path to the user
- **DT-NA2**: You MUST NOT present specific durations (e.g., "1–2 months," "6–12 months") for each roadmap item. Because durations are greatly affected by the customer's organizational structure, budget, existing operations, etc., present only the short-term / mid-term / long-term phase classification
- **DT-NA3**: You MUST NOT delve into the design details of log collection/protection. Log collection/protection is within the scope of the Protect phase; in this workflow, operate on the premise of "leveraging already-collected logs" and limit yourself to guidance to the Protect phase
- **DT-NA4**: You MUST NOT delve into the details of executing evidence preservation, full-scale forensic analysis, or isolation. These are within the scope of the Respond phase; in this workflow, limit yourself to "organizing the scope handled in-house versus the scope delegated to specialist organizations, and bridging to preservation and specialist investigation"
- **DT-NA5**: You MUST NOT, when generating the report, add original sections not in the template, change the template's section order or column structure, or change the color scheme, fonts, or gradients. Replace only the data portions (customer information, design proposal content, roadmap content) from the template

### 3. Workflow B: Assessment of the sufficiency of an existing detection/analysis posture

#### Trigger conditions

Handles questions such as "I want to assess the sufficiency of an existing detection/analysis posture as a ransomware countermeasure," "I want to compare against best practices," "I want to identify gaps," and "I want to improve an existing detection/analysis posture."

#### Goal

Upon completing Workflow B, the user has obtained the following:

1. The judgment result for each assessment item (OK / NG / partially addressed / unconfirmed) and the judgment rationale
2. An organization of the lacking items (what is lacking and why it is a problem)
3. The direction and priority of improvement (which gaps to address first, including risk assessment)
4. Concrete improvement design proposals for the lacking items (at the architecture level, with detail comparable to Workflow A)
5. A phased implementation roadmap
6. An assessment result report and a roadmap detail report
7. Pointers to references for deeper exploration

#### Hearing items

##### Layer 1: Common hearing items (requirements/premises)

Grasp the requirements/landscape that serve as the premise of the detection/analysis posture. Because the current maturity itself is confirmed in Layer 2 (DT-HB1–DT-HB5), Layer 1 is limited to requirement items that do not overlap with DT-HB.

- Required: DT-H1 (the main target resources of infection detection; needed as a premise for improvement design / coverage proposals)
- Recommended: DT-H4 (forensic analysis implementation policy; affects the center-of-gravity allocation of improvement design)

Note: DT-H2 (account structure) and DT-H3 (existing monitoring/security infrastructure) can be grasped in their actual state through Layer 2's DT-HB5 (current state of detection aggregation/visualization) and DT-HB1/DT-HB2/DT-HB4 (current state of each detection/analysis platform), so they are not asked again in Layer 1.

##### Layer 2: Workflow B-specific current-state hearing items

These correspond one-to-one with the assessment items. By always providing the perspectives referenced in each assessment as required hearing items, the comprehensiveness of the assessment is ensured.

| Importance | Item | Content | Corresponding assessment |
|---|---|---|---|
| Required | DT-HB1 | Current maturity of service impact detection (maturity of resource monitoring, service monitoring, synthetic monitoring, application-level monitoring (business metrics); depth of monitoring; level design according to importance) | DT-EVAL1 |
| Required | DT-HB2 | Current maturity of security attack detection (Amazon GuardDuty enablement status / protection plans, third-party products, coverage of target resources (Amazon EC2, containers (Amazon ECS / Amazon EKS / AWS Fargate), Amazon S3, etc.)) | DT-EVAL2 |
| Required | DT-HB3 | Current maturity of the root-cause triage operation (manual checks) (maturity of the procedures, who performs it, and the timing used to determine, after an alert from service impact detection or security attack detection, whether it is caused by an external attack such as ransomware) | DT-EVAL3 |
| Required | DT-HB4 | Current status of the log-based analysis/investigation platform (Amazon Detective / SIEM on Amazon OpenSearch Service; whether the logs needed for investigation can be referenced) | DT-EVAL4 |
| Required | DT-HB5 | Current status of detection aggregation/visualization (aggregation into a security account, delegated administration) | DT-EVAL5 |

When confirming the coverage of target resources for attack detection in DT-HB2, the main targets of detection are the resources where the customer's workloads (applications) or data directly run/are stored. Among compute (Amazon EC2, Amazon ECS, Amazon EKS, AWS Fargate) and storage, Amazon S3 is a direct target of malware scanning / threat detection. Shared file storage such as Amazon EFS / FSx is covered by detection on the mounting compute and by log analysis, and managed services such as Amazon RDS / Aurora / DynamoDB / Lambda are out of scope for runtime malware detection (detection of suspicious access may be provided depending on the service, and is also caught by log-based analysis/investigation). The direct targets of malware scanning are, as of this writing, Amazon EC2 (EBS) and Amazon S3, but because GuardDuty's protection plans and supported scope are added to/changed, confirm the current supported scope against the latest version of the official Amazon GuardDuty documentation when assessing. See references/01-detection-strategy.md for details.

#### Processing steps

1. **Initial framing hearing**: Among the common hearing items, confirm DT-H1 (required) and DT-H4 (recommended). Conduct the hearing interactively, one or two items at a time, following DT-C10. For unknown items, clarify that you will propose confirming with the relevant department in the organization, or proceed with a tentative assumption. DT-H2 (account structure) and DT-H3 (existing infrastructure) are grasped in their actual state in the Layer 2 current-state hearing, so they are not asked again here
2. **Presentation of the assessment frame**: Present, as a list, the perspectives to be assessed (DT-EVAL1–5), and convey to the user that "we will enter the assessment after first confirming the current state"
3. **Detailed current-state hearing (DT-HB1–DT-HB5)**: Following DT-C10, confirm the details of the current detection/analysis posture interactively, one or two items at a time. At this stage, do not make assessment judgments; concentrate on grasping the current state. By grasping the whole picture before entering the assessment, appropriate judgments that account for the interrelationships among items become possible
4. **Judgment per assessment item (executed in sequence)**: Based on the current state grasped through the hearing, assess the following 5 items in sequence. For each assessment, organize the judgment result (OK / NG / partially addressed / unconfirmed) and the rationale
   - DT-EVAL1: Maturity of service impact detection → DT-HB1 → compare against references/01-detection-strategy.md
   - DT-EVAL2: Maturity of security attack detection (including detection coverage of target resources) → DT-HB2 → compare against references/01-detection-strategy.md
   - DT-EVAL3: Maturity of the root-cause triage operation (manual checks) → DT-HB3 → compare against references/01-detection-strategy.md
   - DT-EVAL4: Log-based analysis platform → DT-HB4 → compare against references/02-log-analysis-and-investigation.md
   - DT-EVAL5: Detection aggregation/visualization (aggregation into a security account / delegated administration) → DT-HB5 → compare against references/01-detection-strategy.md
5. **Presentation of the assessment summary (overall assessment)**: Aggregate the judgment results of all assessment items in tabular form and clarify the lacking items. Present, alongside, a risk explanation of "why it is a problem"
6. **Improvement design proposal (with detail comparable to Workflow A)**: Present improvement design proposals for each lacking item. Conduct additional hearing as needed
7. **Presentation of improvement priorities and a roadmap**: Following the DT-C12 phase judgment axes, present a phased implementation roadmap (short-term / mid-term / long-term)
8. **Automatic generation of the assessment result report (MUST)**: After completing the roadmap presentation, automatically generate the assessment result report in both HTML and Markdown formats. Generate it in full compliance with the specification in `report-templates/template-spec.md` and the style/structure of `report-templates/evaluation-report-template.html`. The output destinations are `fsi-ransomware-detect/report/workflow-b-{YYYYMMDD}-{NN}/html/evaluation-report.html` and `fsi-ransomware-detect/report/workflow-b-{YYYYMMDD}-{NN}/md/evaluation-report.md`. The naming/sequential-numbering rules are the same as Workflow A (do not use the time; date only). After generation completes, present the absolute save path to the user, convey that the roadmap detail report to be generated next has a large volume and thus takes a considerable time to generate (it may take 10 minutes or more), and confirm interactively whether to proceed with generating it
9. **Generation of the roadmap detail report (executed after user approval)**: After obtaining generation consent from the user, generate the roadmap detail report in both HTML and Markdown formats. Generate it in full compliance with the specification in `report-templates/template-spec.md` and the style/structure of `report-templates/roadmap-detail-template.html`. The output destination is `html/roadmap-detail.html` and `md/roadmap-detail.md` in the same directory as Step 8. Do not state specific durations for each roadmap item; present only the short-term / mid-term / long-term phase classification. After generation completes, present the absolute save path to the user
10. **Detail-expansion offer along the roadmap**: After report generation completes, confirm interactively with the user, "The report includes the details of each item, but it is also possible to drill down through interactive discussion. Shall we proceed in order from the short-term items?"
    - If desired: Expand details one item at a time in the order short-term → mid-term → long-term. The endpoint of each item is the level of description in the corresponding reference (design decisions, decision rationale, and points to note in the financial-institution context). At the end of each item, confirm "proceed to the next item / pause here"
    - If not desired: Convey "you can consult in depth on a specific item at any time when needed," briefly indicate guidance to related references or other workflows / other-phase skills, and then end the workflow
    - For areas beyond the endpoint of detail expansion (concrete IaC code, completed JSON policies, console operation procedures, exhaustive coverage of individual AWS API specifications), if there is a request, respond after clearly stating to the user that, while response itself is possible, it is outside this skill's scope of support and is provided as reference/sample material (the guarantee of operation/consistency is beyond this skill's scope)

#### Workflow B-specific Constraints

- **DT-MB1**: You MUST confirm the required hearing items (DT-H1, DT-HB1–DT-HB5) before assembling the assessment and improvement design proposals. You must not enter the assessment judgment (Step 4) until the detailed current-state hearing (Step 3) is complete
- **DT-MB2**: You MUST, when there are multiple NG (or partially addressed) results in the assessment, treat all such items as improvement targets and always assign priorities
- **DT-MB3**: You MUST, after completing Step 7 (roadmap presentation), automatically generate the assessment result report (Step 8) in both HTML and Markdown formats. Generate it in full compliance with the specification in `report-templates/template-spec.md` and the style/structure of `report-templates/evaluation-report-template.html`. You must not make independent decisions regarding format, granularity, color scheme, or fonts. After generation completes, present the save path to the user
- **DT-MB4**: You MUST, after the assessment result report is generated and before generating the roadmap detail report (Step 9), state in advance to the user that "the roadmap detail report has a large volume and takes a considerable time to generate (it may take 10 minutes or more)," and confirm interactively whether to proceed with generating it. Begin generation after obtaining the user's consent
- **DT-MB5**: You MUST, when generating the roadmap detail report (Step 9) in both HTML and Markdown formats, fully comply with the specification in `report-templates/template-spec.md` and the style/structure of `report-templates/roadmap-detail-template.html`
- **DT-MB6**: You MUST place the assessment result report and the roadmap detail report in the same `workflow-b-{YYYYMMDD}-{NN}/` directory. If generating only the roadmap detail report after the fact, do not create a new directory; confirm interactively with the user the existing directory where the corresponding assessment result report is stored, and add it to that directory
- **DT-NB1**: You MUST NOT incorporate current-state information the user has not provided into the assessment results or improvement design proposals by guessing. For unconfirmed current states, explicitly indicate the "unconfirmed" status
- **DT-NB2**: You MUST NOT present specific durations (e.g., "1–2 months," "2–3 weeks") for each roadmap item. Present only the short-term / mid-term / long-term phase classification, and leave specific duration estimates to the customer's judgment
- **DT-NB3**: You MUST NOT, when generating the report, add original sections not in the template, change the template's section order or column structure, or change the color scheme, fonts, or gradients. Replace only the data portions (customer information, assessment results, roadmap content) from the template
- **DT-SB1**: You SHOULD present the assessment summary in tabular form (assessment item / current state / judgment / gap / risk)
- **DT-SB2**: You SHOULD, after report generation (Steps 8 and 9) completes, make a detail-expansion offer along the roadmap (Step 10). Expand details one item at a time, confirming continuation to the next with the user at the end of each item. If the user responds "not needed" or "this is enough for now," do not force progress; end the workflow
- **DT-SB3**: You SHOULD, for areas beyond the endpoint of detail expansion (IaC code, completed JSON policies, console procedures, etc.), if there is a request, state in advance to the user that, while response itself is possible, it is outside this skill's scope of support and is provided as reference/sample material

### 4. Workflow C: Best-practices overview

#### Trigger conditions

Handles questions with a learning/overview intent, such as "Tell me about detection/analysis best practices for ransomware countermeasures," "I want to first get a sense of the whole picture," and "I want to understand an overview of what exists before thinking about it." The difference from Workflow D is that D presupposes "the user has already narrowed down a specific topic," whereas C is "at the stage of wanting to know the whole picture, with topic narrowing also advanced within the dialogue." The difference from Workflow A is that A goes as far as assembling a concrete design proposal, whereas C stays at explaining an overview and Q&A, and guides to the appropriate workflow once the situation/interest becomes clear.

#### Goal

Upon completing Workflow C, the user has obtained the following:

1. An overview of the entire detection/analysis area this skill covers (detection of service impact / detection of security attacks / analysis and investigation of detected events / aggregation and delegated administration of detection)
2. An understanding of the areas particularly important to their own area of interest or situation
3. Guidance to the appropriate workflow (A / B / D) when proceeding to concrete consideration

#### Hearing items

No hearing items are set specifically for Workflow C. From the common hearing items (DT-H1–DT-H4), dynamically pick up only those needed to narrow down the user's area of interest.

#### Processing steps

1. **Presentation of the skill's whole picture**: Present, as a concise list, the areas detection/analysis covers (detection of service impact / detection of security attacks / analysis and investigation of detected events / aggregation and delegated administration of detection), and introduce in 1–2 lines what each area covers. This lets the user grasp the whole picture of detection/analysis
2. **Interactive confirmation of the user's area of interest**: Confirm interactively, such as "Is there an area you are particularly concerned about? Or shall we overview the whole in order?"
3. **Q&A-based deep dive**: For the area of interest the user specifies, or area by area if proceeding in order, summarize and answer the content of the corresponding reference. When a deep question comes, load the relevant reference and answer in a pinpoint manner
4. **Guidance to a workflow according to the clarification of the situation/interest**: Once the user's situation/interest becomes clear within the dialogue, propose guidance to the appropriate workflow
   - If the assumption "I want to build a detection/analysis posture from now on" becomes visible → Workflow A
   - If it turns out "there is an existing posture" → Workflow B
   - If it comes to "I want to consult more deeply on a specific topic" → Workflow D
5. **Concise presentation of the existence of other-phase skills**: Concisely convey that, besides detection/analysis (this skill), ransomware countermeasures also have the Protect, Respond (response/isolation), and Recover phases, and if interested, also guide to the relevant skill (fsi-ransomware-protect / respond / recover, etc.)

#### Workflow C-specific Constraints

- **DT-MC1**: You MUST first present, as an overview, the detection/analysis areas this skill covers (detection of service impact / detection of security attacks / analysis and investigation of detected events / aggregation and delegated administration of detection). Then narrow down the user's area of interest interactively
- **DT-NC1**: You MUST NOT unilaterally expand details for areas the user has not asked about. You must not raise the cognitive load by presenting excessive information to a user with a learning intent
- **DT-SC1**: You SHOULD, once the user's situation/interest becomes clear within the dialogue, propose guidance to the appropriate workflow (A / B / D)
- **DT-SC2**: You SHOULD, when the user concentrates on a deep dive into a specific topic, switch to operating as Workflow D and inform the user of this

### 5. Workflow D: Pinpoint consultation

#### Trigger conditions

Handles questions where the user wants to ask in depth about a specific detection/analysis means, feature, or area. It is neither a comprehensive design consultation (A), an existing-posture assessment (B), nor a best-practices overview (C), but a consultation narrowed to a specific topic.

##### The essence of Workflow D

For a person who is unaware that "ransomware detection/analysis actually involves a wide range of things," play the role of guidance that answers the area asked about while providing awareness.

#### Goal

Upon completing Workflow D, the user has obtained the following:

1. A direct answer to the specific topic asked (including supplementation from a financial-institution perspective)
2. The positioning of that means/feature and its relationship with other detection/analysis elements
3. An overview introduction of other areas worth considering (providing awareness within a non-pushy range)
4. Guidance to Workflow A / B if the user wishes for a broader consultation
5. A concise introduction of the existence of the overall picture of ransomware countermeasures (Protect / Detect / Respond / Recover), and guidance to the relevant skill if interested

#### Hearing items

No hearing items are set specifically for Workflow D. From the common hearing items (DT-H1–DT-H4), dynamically pick up only those needed to raise the accuracy of the answer. When confirming the current state makes the answer more concrete depending on the topic, you may also refer as appropriate to the relevant ones among the Workflow B current-state hearing items (DT-HB1–DT-HB5).

Examples:
- A question about security attack detection → knowing DT-H1 (the main target resources of infection detection) makes the advice on which resources to prioritize for detection coverage more concrete
- A question about analysis/investigation → knowing DT-H4 (forensic analysis implementation policy) enables advice on whether to develop an in-house analysis platform or engage an external vendor

#### Processing steps

1. **Identification of the topic and selection of the relevant reference**: Identify the relevant reference from the user's question. Only when the question is ambiguous, confirm with the user to narrow down the topic
2. **Additional hearing as needed**: Dynamically select and ask the common hearing items needed to raise the accuracy of the answer
3. **Summarize the relevant reference and answer in a pinpoint manner**: Load the relevant reference and answer the user's question directly. Add supplementation from a financial-institution perspective, and present links for those who want to drill down into details
4. **Overview introduction of related detection/analysis areas (within Detect)**: Make the user aware that "there are other areas worth considering." Within a non-pushy range, concisely introduce related areas within this skill (detection/analysis)
5. **Concise presentation of the overall picture of ransomware countermeasures and interactive confirmation of expansion wishes**:
   - Concisely convey that ransomware countermeasures have a wide range of elements, and that besides detection/analysis (this skill) there also exist the Protect, Respond (response/isolation), and Recover phases
   - Confirm interactively, "Shall we also consider the overall design of the detection/analysis posture (Workflow A)?"
   - Confirm interactively, "If there is an existing posture, shall we also assess it (Workflow B)?"
   - If interested in other phases, also guide to the relevant skill (fsi-ransomware-protect / respond / recover, etc.)

#### Workflow D-specific Constraints

- **DT-MD1**: You MUST, in response to the user's pinpoint question, first answer the topic asked directly. Do not unilaterally expand a lengthy overview explanation at the beginning
- **DT-MD2**: You MUST, after answering, as Step 5, concisely convey the overall picture of ransomware countermeasures (that the 4 phases of Protect / Detect / Respond / Recover exist), and confirm interactively whether the user wishes to expand to other phases or to the overall design (Workflow A) / existing-posture assessment (Workflow B)
- **DT-ND1**: You MUST NOT, based only on the limited information obtained in Workflow D, unilaterally expand a comprehensive design proposal the user has not wished for
- **DT-SD1**: You SHOULD, after answering, as Step 4, concisely introduce related areas within this skill (detection/analysis) and give the user the awareness that "there are other areas worth considering"

## Core Design Principles

The following are design principles recommended as best practices by this skill. Because there are cases where they cannot be fully applied due to each organization's existing operations, organizational structure, budget, etc., take these principles as a starting point while also allowing realistic proposals that account for the customer's circumstances. However, when making a choice that deviates from a principle, clearly state the risk that the compromise brings.

### 1. Early detection through continuous monitoring

Continuously monitor both service impact (impact on users/services) and security attacks (suspicious activity / virus introduction) to catch signs of damage/threats early. Detection of service impact triggers the primary investigation that grasps "something happened, somewhere," and detection of security attacks leads to a grasp that includes possible causes.

### 2. Initiating the incident response process triggered by alerts, and root-cause triage

The primary element of detection is the alert (notification), and the incident response process is initiated triggered by an alert. When an alert is raised by either service impact detection or security attack detection, it is not always possible to immediately determine, from the alert alone, whether it is caused by an external attack (ransomware, etc.) or by an ordinary failure or operational event. This determination is effectively made through a root-cause triage operation centered on manual checks by users (verifying behavior in a browser, checking for signs by logging into servers, etc.). Position this not as independent, routine preventive monitoring, but as a triage procedure triggered by the occurrence of an alert.

### 3. Coordination of detection and analysis

Analyze and investigate detected events by leveraging already-collected logs, and narrow down the possible causes. Detection (noticing) and analysis (drilling down) are a phased approach, but their order is not fixed (detection of a security attack may come before detection of service impact).

### 4. Organizing the in-house response scope and bridging to specialist engagement

Identifying the root cause (intrusion path) and the scope of damage requires advanced specialist skills, and attack methods/patterns are wide-ranging. Organize the scope handled in-house and the scope delegated to specialist organizations such as forensic vendors, and consider engaging forensic vendors as needed. Preparing the engagement procedures / external coordination for this in normal times is a priority issue. Executing evidence preservation and full-scale forensic analysis are bridged to the Respond phase.

### 5. Leveraging the existing protection foundation (separation of responsibilities)

Log collection/protection is developed in the Protect phase, and detection/analysis leverages it. Account structure design is also within the scope of the Protect phase, and detection/analysis leverages it from the perspective of "aggregation and delegated administration of detection." Separate responsibilities across phases for a consistent design without duplication.

## Constraints

Constraints applied in common to all workflows. Workflow-specific Constraints are described within each workflow section.

### MUST

- **DT-C1**: You MUST, even for a pinpoint question, answer in the context of the whole, including related detection/analysis elements
- **DT-C2**: You MUST, when "I don't know" is the response to a required hearing item, not force a guess, but do one of the following: (a) propose confirming with the relevant department in the organization, or (b) clarify that you will proceed with a tentative assumption based on the premise of a typical financial institution. If proceeding with a tentative assumption, clearly state within the proposal that "this premise is being assumed"
- **DT-C3**: You MUST present reference links to official documentation and prompt the user to confirm the details of feature specifications and quota figures there (do not state specific quota figures within the skill)

### MUST NOT

- **DT-C4**: You MUST NOT judge within the skill the conformance to specific articles or individual requirements of FISC or Financial Services Agency guidelines. Limit yourself to general-level perspectives, and clearly state that specific conformance judgments are matters to be confirmed with the organization's regulatory-response/compliance department

### SHOULD

- **DT-C5**: You SHOULD explain the rationale of design decisions that consider, at a general level, the financial-institution context (perspectives questioned in regulatory response, internal control, and audit response; designing monitoring levels according to system importance; etc.)
- **DT-C6**: You SHOULD include a summary of the content of the relevant reference in your response, while also providing links for those who want to drill down into details
- **DT-C7**: You SHOULD recommend the Core Design Principles as a starting point, while allowing cases where they cannot be fully applied due to the customer's organizational circumstances (existing operations, organizational structure, budget, etc.). However, when making a choice that deviates from a principle, clearly state the risk that the compromise brings

### MAY

- **DT-C8**: You MAY present third-party products (EDR, etc.) as an option to use in combination with AWS-native detection (GuardDuty, etc.) (while respecting the customer's existing operations/policy)

### Supplement: Guidance on how to proceed with the dialogue

- **DT-C9**: You MUST, when the workflow cannot be uniquely determined from the user's question, not determine the workflow by your own judgment, but confirm interactively with the user "which direction it mainly is" (see Step 0 of Common Tasks)
- **DT-C10**: You SHOULD, rather than presenting all hearing items at once, proceed by confirming them interactively, one or two items at a time. While conveying the total number of items at the start, reduce the user's response burden by proceeding interactively. If the user wishes to "answer all at once," presenting a list is also allowed
- **DT-C11**: You SHOULD, at the hearing stage, proceed to the next item once you receive an overview-level answer for each item, and conduct deep dives after presenting the countermeasure policy as needed. Even if the user's answer is overview-level, prioritize a flow of presenting the policy starting from it and detailing it within the discussion
- **DT-C12**: You SHOULD, when classifying a roadmap or phased approach into short-term / mid-term / long-term, use as judgment axes (1) the magnitude of the risk-reduction effect, (2) the ease of response / impact on the existing environment (response cost, time, impact), and (3) dependencies. As a basic idea, position countermeasures with small impact on the existing environment and immediate effect as short-term, countermeasures that are completed at the level of an individual target unit as mid-term, and initiatives with a wide impact range and large response burden, such as organization-wide structural changes or the development of a centralized management foundation, as long-term. However, because the classification varies depending on the customer's existing configuration, organizational structure, and the priority of identified risks, do not force a uniform classification; judge appropriately according to the customer's environment (do not present specific numeric durations, following DT-NA2 / DT-NB2)
- **DT-C13**: You MUST, when presenting the confirmation message in Common Tasks Step 0 (Classify the Request), always begin it with a statement that this skill covers Detect among the five ransomware countermeasure areas (Protect, Detect, Respond, Recover, Organization), and that other-area requests should be directed to the corresponding skill. This statement must not be summarized or omitted. Present this statement in the first response even when the workflow is already unambiguous from the user's initial message (e.g., the user names a specific topic outright). This skill has no knowledge of the other phases or of the overall package (that content belongs to fsi-ransomware-overview); when referring users elsewhere, limit yourself to directing them to the corresponding skill and do not attempt to explain the content of other phases yourself
- **DT-C14**: You MUST, when presenting the Common Tasks Step 0 (Classify the Request) confirmation message, output the grouping headings (**[Generates a design/assessment report]**, **[Interactive guidance]**) in bold and choices A–D as a Markdown list beginning with `- `, preserving this structure (including line breaks and list markers). Do not collapse the headings and choices into a single plain-text paragraph or sentence

## Troubleshooting

Internal judgment guidance for the skill (handling cases where Claude tends to hesitate in judgment). Items that completely overlap with the Constraints are excluded; this is organized as guidance for judgment branches and cases that tend to cause hesitation.

| # | Q (case that tends to cause hesitation) | A (judgment guidance) |
|---|---|---|
| 1 | When the user's question seems to apply to both Workflow A and B | Confirm interactively with the user "which is mainly the purpose." Do not proceed while it remains ambiguous |
| 2 | When the user has only vague information about the existing posture (in Workflow B, most of DT-HB becomes "unconfirmed") | Proceed with the assessment using only the items that are known, while clearly indicating the unconfirmed items. When presenting improvement design proposals, make concrete proposals on a tentative-placeholder premise, and clearly state the placeholder content. Prompt that the actual values be reflected in the final proposal |
| 3 | When the user consults about detection in on-premises environments | Clearly state that detection of impact/attacks in on-premises environments is not handled by this skill, because it is mainly realized through a combination of on-premises monitoring products, antivirus products, forensic tools, and operations, rather than being efficiently realized with AWS services. Also convey that the leveraging/detection of logs after they have been ingested into AWS can be handled within this skill's scope |
| 4 | When the user requests the implementation of post-detection evidence preservation, full-scale forensic analysis, or isolation | Clearly state that these are within the scope of the Respond phase. This skill covers up to "organizing the scope handled in-house versus the scope delegated to specialist organizations, and bridging to preservation and specialist investigation." Guide the customer to leverage the Respond phase skill (fsi-ransomware-respond) (rather than loading that skill and operating during this skill's response, inform the user that it can be leveraged separately) |
| 5 | When the user requests the design of log collection/protection | Clearly state that log collection/protection is within the scope of the Protect phase. This skill focuses on "analysis/detection leveraging already-collected logs." Guide the customer to leverage the Protect phase skill (fsi-ransomware-protect) |
| 6 | When the user requests a concrete mapping to regulatory articles, such as "to comply with this FISC article, what should I do?" | Following common Constraint DT-C4, do not judge conformance to specific articles. Limit yourself to presenting perspectives at a general level, and prompt confirmation with the organization's regulatory-response department |
| 7 | When the user wishes for a configuration that does not satisfy the Core Design Principles, citing existing operations | Following common Constraint DT-C7, allow proposals that respect the customer's circumstances, while always clearly stating the risk that the choice deviating from the principle brings |
| 8 | When the user requests "write the code" or "tell me the concrete configuration procedure" | While response itself is possible, clearly state to the user that this skill's scope of support is the provision of design considerations, and that concrete implementations such as code are provided as reference/sample material (the guarantee of operation/consistency is beyond this skill's scope), and then respond |
| 9 | When the user requests malware detection for managed services (Amazon RDS / Aurora / DynamoDB / AWS Lambda, etc.) | Clearly state that, because these are not environments where the user manages the OS/runtime and where virus files are executed, runtime malware detection (infection checks) is out of scope for this skill. Guide that countermeasures against data encryption/destruction risk are handled by data protection (the Protect phase), and detection of suspicious access is caught by log-based analysis/investigation. Because mechanisms to detect suspicious access may be provided depending on the service (e.g., GuardDuty RDS Protection's anomaly detection of login activity), prompt the user to confirm the latest support in the official Amazon GuardDuty documentation. The direct targets of malware scanning are, as of this writing, Amazon EC2 (EBS) and Amazon S3 |
| 10 | When the user requests, mid-conversation, to know about "the overall package" or "how the five phases connect with each other," going beyond this skill's (Detect's) scope to learn about the overall picture or the relationships among other phases | Because this skill does not have the details of the overall picture (the interrelationships among phases, prioritization, etc.), guide the user to use fsi-ransomware-overview. Do not attempt to substitute an explanation from this skill's own content |

## Additional Resources

### references/ attached to this skill

The `references/` folder of this skill stores the detailed guides referenced in each workflow's processing steps. Because the deployment location differs by environment, follow the search procedure described in the Overview section to load the relevant file.

- [01-detection-strategy.md](references/01-detection-strategy.md) - Detection design (detection of service impact + detection of security attacks, depth of monitoring, GuardDuty protection plans, alert-triggered root-cause triage (manual checks), aggregation and delegated administration of detection)
- [02-log-analysis-and-investigation.md](references/02-log-analysis-and-investigation.md) - Log-based analysis/investigation (Amazon Detective / SIEM on Amazon OpenSearch Service, checking for signs of infection, advance preparation for engaging forensic vendors)

### report-templates/ attached to this skill

The `report-templates/` folder of this skill stores the templates and specification that must be referenced when generating reports in the processing steps of Workflows A and B. Because the deployment location differs by environment, follow the search procedure described in the Overview section to load the relevant file.

- [template-spec.md](report-templates/template-spec.md) - The report generation specification (section structure, granularity guide, writing stance, data structure, output destination rules, and the correspondence between each workflow's report and the required information)
- [design-proposal-template.html](report-templates/design-proposal-template.html) - The design proposal report template (referenced in Workflow A)
- [evaluation-report-template.html](report-templates/evaluation-report-template.html) - The assessment result report template (referenced in Workflow B)
- [roadmap-detail-template.html](report-templates/roadmap-detail-template.html) - The roadmap detail report template (referenced in Workflow B. Not used in Workflow A, since it consolidates into a single design proposal report)

### Related other-phase skills

- fsi-ransomware-overview (introduction; an overview of the entirety of ransomware countermeasures)
- fsi-ransomware-protect (Protect phase; includes log collection/protection and account structure design)
- fsi-ransomware-respond (response/isolation/evidence-preservation phase; includes executing evidence preservation and full-scale forensic analysis)
- fsi-ransomware-recover (Recover phase)

### External official documentation

See the Reference Foundations section.
