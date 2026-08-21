---
name: fsi-ransomware-overview
description: >-
  Entry point for ransomware-countermeasure consultations on AWS for financial services organizations. Explains the 5-phase skill package (Protect, Detect, Respond, Recover, Organization) and guides users to the right phase. Activates broadly when the user does not know where to start, wants an overview, or cannot tell which phase (Protect/Detect/Respond/Recover/Organization) applies. Also activates on general mentions of ransomware countermeasures, where to start, or financial-institution ransomware countermeasures. Does not itself perform design/assessment (backup design, detection-posture assessment, etc.); these are handled by fsi-ransomware-protect, fsi-ransomware-detect, fsi-ransomware-respond, fsi-ransomware-recover, and fsi-ransomware-organization respectively. Recommended to use before those skills so consultations are triaged accurately.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Ransomware Countermeasures for Financial Institutions: Overview

## Overview

The areas covered by ransomware countermeasures range widely, from prevention to post-intrusion response. This skill package aims to **support resilience against ransomware attacks and the design of system recovery infrastructure (recovery-oriented workload design)**. Because preventing intrusion 100% is not realistically achievable, how effectively an organization can contain damage and recover its business swiftly, on the premise that intrusion may occur, determines a financial institution's credibility.

Because the areas to address (Protect, Detect, Respond, Recover, and Organization) range widely, this package supports users either by producing a systematic design proposal or by assessing an existing workload and translating the findings into improvements. Users can receive guidance in the following forms:

- Interactive guidance through chat-style conversation with the AI agent
- Confirmation of design proposals / assessment results through automatically generated reports (HTML / Markdown)
- Presentation of an adoption roadmap (short-term / mid-term / long-term) for realizing countermeasures step by step

Through these, ransomware countermeasure designs grounded in AWS best practices and knowledge accumulated by Solutions Architects can be adopted effectively.

This skill (Overview) serves as the entry point to this support. Any ransomware-related consultation is first received by this skill, which presents the overall picture and provides guidance to the appropriate phase. Using this skill, the user can obtain the following kinds of dialogue and outcomes:

- If unsure "what to consider, in which phase" regarding ransomware countermeasures in general, an explanation of the overall 5-phase structure and what each phase concretely covers
- If the consultation content is already decided (e.g., backup design, detection with GuardDuty), guidance to the corresponding specialized skill (fsi-ransomware-protect, etc.) along with a brief overview
- If interested in Respond, Recover, or Organization, information about their future planned content (it is also made clear that these are currently not available for substantive consultation)

What this skill provides:

- An overview explanation of the entire skill package (5-phase structure: Protect, Detect, Respond, Recover, Organization)
- Guidance to the appropriate phase (triage) based on the user's consultation content and issues
- Clarification of the current availability status of each phase (available / planned for future release)

The scope this skill covers:

- Focuses on being the entry point / triage role for ransomware-countermeasure consultations
- The concrete design, assessment, and implementation work for each phase (chat-based dialogue, report generation, roadmap presentation, etc.) is handled by the respective specialized skill (Protect: fsi-ransomware-protect, Detect: fsi-ransomware-detect, Respond: fsi-ransomware-respond, Recover: fsi-ransomware-recover, Organization: fsi-ransomware-organization). This skill only guides the customer toward using those skills, and does not itself delve into concrete work such as backup design or detection-posture assessment

## Current Availability Status

As of the initial release in July 2026, this skill is a provisional version. Triage to the Protect and Detect phases is actually functional, but the three phases Respond, Recover, and Organization are not yet released, so consultations corresponding to these are limited to guidance that they are "planned for future release." See the table in the Ransomware Resilience Framework section for detailed availability status.

## Ransomware Resilience Framework (Overall Package Structure)

This package consists of 6 skills, including this skill (Overview). Overview serves as the entry point / triage role, and the actual countermeasure work is handled by the following 5 phase skills.

| Phase | Skill name | Availability |
|---|---|---|
| Protect | fsi-ransomware-protect | Available |
| Detect | fsi-ransomware-detect | Available |
| Respond | fsi-ransomware-respond | Planned for future release |
| Recover | fsi-ransomware-recover | Planned for future release |
| Organization | fsi-ransomware-organization | Planned for future release |

### Protect: fsi-ransomware-protect

Performs architecture design and existing-environment assessment for backup/data-protection environments. Covers a multi-account role-separation strategy, an AWS Backup-centered backup architecture, immutabilization (Vault Lock / S3 Object Lock) and encryption, policy design via IAM / KMS / SCP, malware scanning strategy (including AWS Backup malware protection and ECR container protection), log collection/protection in preparation for forensic response, monitoring/auditing of backup operations, and on-premises backup integration (AWS Backup Gateway / DataSync / Storage Gateway).

### Detect: fsi-ransomware-detect

Handles detection of damage/threats and analysis of detected events. Covers detection of service impact (resource, service, synthetic, and business-metric monitoring), detection of security attacks (Amazon GuardDuty protection plans, third-party products), alert-triggered root-cause triage, log-based analysis/investigation leveraging already-collected logs (Amazon Detective, SIEM on Amazon OpenSearch Service), aggregation/delegated administration of detection and analysis, and advance preparation for engaging forensic vendors when the analysis bar is high.

### Respond: fsi-ransomware-respond

Envisioned to cover isolation, evidence preservation, and bridging to full-scale forensic analysis for detected events (concept stage).

### Recover: fsi-ransomware-recover

Envisioned to cover restoration procedures from backups, infection checks during recovery, and phased service restoration (concept stage).

### Organization: fsi-ransomware-organization

Envisioned to cover organizational-operation considerations such as organizational structure during an incident, internal/external communication flows, and reporting to regulators and relevant authorities (concept stage).

## Reference Foundations

The 5-phase structure presented by this skill is organized based on the concepts of the NIST Cybersecurity Framework (CSF), adapted into a breakdown suited to the practice of ransomware countermeasures for financial institutions. Detailed authoritative sources for each phase are found in the Reference Foundations section of the respective phase skill (fsi-ransomware-protect / fsi-ransomware-detect, etc.).

## Common Tasks

### Workflow A: Entry-Point Guidance

This skill consists of a single workflow (entry-point guidance). Any ransomware-related consultation is first received by this workflow.

#### Trigger conditions

Handles ransomware-countermeasure consultations in general. This includes vague questions such as "I don't know where to start" or "I want to know the overall picture," as well as topics close to a specific phase (backup, detection, etc.); in all cases, this skill first presents an overview and then bridges to the appropriate phase as the entry point.

#### Goal

Upon completing Workflow A, the user has obtained either of the following:

1. Identification of the phase corresponding to their consultation, or an understanding of the overall picture
2. An overview explanation of the corresponding phase and guidance toward using it, or, for Respond/Recover/Organization, notice that it is planned for future release

#### Processing steps

1. **Initial confirmation (conditional; verbatim output required)**: If the user's first question already states one of the phase names (Protect/Detect/Respond/Recover/Organization) or an equivalent concrete service/topic (e.g., "I want to ask about backup Vault Lock design"), skip this confirmation and proceed directly to Step 3. If not stated (including a vague consultation such as "I want to consider ransomware countermeasures"), output the following confirmation text **verbatim, preserving the Markdown list structure (including line breaks and indentation)**, at the beginning of the first response. Do not provide an overview explanation, a summary, or a paraphrase, and do not output any other content (such as the Ransomware Resilience Framework table) before this confirmation text. Do not collapse the list into a single plain-text paragraph.

   > Thank you for using the AWS-provided ransomware countermeasures Skill package for the financial industry, "fsi-ransomware-resilience." To make use of this skill, please choose one of the following depending on your purpose.
   >
   > - **A.** I want to start with the overall picture of this skill / I want an explanation and guidance on what it can do
   > - **B.** My consultation content is already decided, so please directly guide me to the skill that covers the corresponding phase
   >     - **B-1. Protect** — Architecture design/assessment of backup and data protection (multi-account structure, immutabilization, encryption, malware scanning, log collection/protection, etc.)
   >     - **B-2. Detect** — Detection and analysis of service impact/attacks (monitoring design, GuardDuty, investigation using Detective/SIEM, etc.)
   >     - **B-3. Respond** — Isolation and evidence preservation after detection, bridging to forensic response (currently unavailable, planned for future release)
   >     - **B-4. Recover** — Restoration procedures from backups, infection checks, phased service restoration (currently unavailable, planned for future release)
   >     - **B-5. Organization** — Organizational structure during an incident, internal/external communication, reporting to regulators, etc. (currently unavailable, planned for future release)

2. **If A: Presentation of the overall picture (verbatim output required)**: Output the following overall-picture explanation text **verbatim, preserving the Markdown structure (headings, paragraphs, lists, tables, and line breaks)**. Do not summarize, paraphrase, or omit any part.

   > The areas covered by ransomware countermeasures range widely, from prevention to post-intrusion response. This skill package aims to support resilience against ransomware attacks and the design of system recovery infrastructure (recovery-oriented workload design). Because preventing intrusion 100% is not realistically achievable, how effectively an organization can contain damage and recover its business swiftly, on the premise that intrusion may occur, determines a financial institution's credibility.
   >
   > Because the areas to address (Protect, Detect, Respond, Recover, and Organization) range widely, this package supports users either by producing a systematic design proposal or by assessing an existing workload and translating the findings into improvements. Guidance can be received in the following forms.
   >
   > - Interactive guidance through chat-style conversation with the AI agent
   > - Confirmation of design proposals / assessment results through automatically generated reports (HTML / Markdown)
   > - Presentation of an adoption roadmap (short-term / mid-term / long-term) for realizing countermeasures step by step
   >
   > Through these, ransomware countermeasure designs grounded in AWS best practices and knowledge accumulated by Solutions Architects can be adopted effectively.
   >
   > This package consists of the following 5 phases.
   >
   > | Phase | Skill name | Overview | Availability |
   > |---|---|---|---|
   > | Protect | fsi-ransomware-protect | Architecture design/assessment of backup and data protection | Available |
   > | Detect | fsi-ransomware-detect | Detection and analysis of service impact/attacks | Available |
   > | Respond | fsi-ransomware-respond | Isolation and evidence preservation after detection, bridging to forensic response | Planned for future release |
   > | Recover | fsi-ransomware-recover | Restoration procedures from backups, infection checks, phased service restoration | Planned for future release |
   > | Organization | fsi-ransomware-organization | Organizational structure during an incident, internal/external communication, reporting to regulators, etc. | Planned for future release |
   >
   > Which phase would you like to proceed with?
   >
   > - **B-1. Protect** — Architecture design/assessment of backup and data protection (multi-account structure, immutabilization, encryption, malware scanning, log collection/protection, etc.)
   > - **B-2. Detect** — Detection and analysis of service impact/attacks (monitoring design, GuardDuty, investigation using Detective/SIEM, etc.)
   > - **B-3. Respond** — Isolation and evidence preservation after detection, bridging to forensic response (currently unavailable, planned for future release)
   > - **B-4. Recover** — Restoration procedures from backups, infection checks, phased service restoration (currently unavailable, planned for future release)
   > - **B-5. Organization** — Organizational structure during an incident, internal/external communication, reporting to regulators, etc. (currently unavailable, planned for future release)

   The choices at the end of this step MUST be limited to B-1 through B-5 only, and MUST NOT include A (re-confirming the overall picture). The user has already confirmed the overall picture, so re-presenting A would loop the user back into re-answering the same question.

3. **Phase determination and guidance**: Respond according to the phase the user specified/selected, using one of the following. However, if the confirmation was skipped in Step 1 (because the corresponding phase was already clear from the user's first question), do not repeat the overview explanation below; provide only the direct usage guidance and handoff
   - For Protect (B-1): Explain the overview of fsi-ransomware-protect in 1–2 lines, then guide the user to use it
   - For Detect (B-2): Explain the overview of fsi-ransomware-detect in 1–2 lines, then guide the user to use it
   - For Respond/Recover/Organization (B-3–B-5): Introduce an overview of the corresponding phase, then clarify that it is currently unavailable and planned for future release
   - If interested in multiple phases: Present the overviews of the relevant phases side by side, and let the user choose which to proceed with first

4. **Handling after handoff**: If the user continues with more specific questions about the phase they were guided to, that content naturally matches the trigger conditions of the corresponding phase's skill, so Claude loads that skill and continues the response. This skill itself does not need to explicitly load another skill's files

## Constraints

### MUST

- **OV-C1**: You MUST NOT load and operate based on another phase skill's files (SKILL.md / SKILL_ja.md / references/, etc.) while handling this skill (principle of skill independence). References to other phases must always be limited to the expression "guiding the customer toward using it"
- **OV-C2**: You MUST, if the user's first question does not state one of the phase names (Protect/Detect/Respond/Recover/Organization) or an equivalent concrete service/topic, output the confirmation text described in processing Step 1 verbatim, preserving the Markdown list structure (including line breaks and indentation), at the beginning of the first response. Do not provide an overview explanation, a summary, or a paraphrase, and do not output any other content (such as the Ransomware Resilience Framework table) before this confirmation text. Do not collapse the list into a single plain-text paragraph. This confirmation may be skipped only if the first question already states a concrete phase name or topic
- **OV-C3**: You MUST, in Step 2 (presentation of the overall picture), output the overall-picture explanation text described in processing Step 2 verbatim, preserving the Markdown structure (headings, paragraphs, lists, tables, and line breaks). Do not summarize, paraphrase, or omit any part. The choices at the end MUST be limited to B-1 through B-5 only, and MUST NOT re-present A (re-confirming the overall picture)
- **OV-C4**: You MUST, when guiding toward Protect or Detect, explain the overview of the respective skill in 1–2 lines before guiding the user to use it. However, if the confirmation in OV-C2 was skipped, do not repeat this overview explanation; provide only the direct usage guidance and handoff
- **OV-C5**: You MUST, for consultations corresponding to Respond, Recover, or Organization, introduce an overview of the corresponding phase and then clarify that it is currently unavailable and planned for future release
- **OV-C6**: You MUST always include the B-1 through B-5 5-choice set (including Respond/Recover/Organization) in the choices presented at the end of Step 2 (presentation of the overall picture). Do not narrow the choices down to only the currently available phases (Protect/Detect)

### MUST NOT

- **OV-C7**: You MUST NOT perform, by yourself, the concrete design/assessment work that each phase skill is responsible for, such as backup design or detection-posture assessment
- **OV-C8**: You MUST NOT present a definitive release date or timing for Respond, Recover, or Organization consultations

### SHOULD

- **OV-C9**: You SHOULD, if the user shows interest in multiple phases, present the overviews of the relevant phases side by side and let the user choose which to proceed with first
- **OV-C10**: You SHOULD, if the user wants to continue discussing the overall picture even after being guided to a phase, continue the overview-level explanation within this skill

### MAY

(No applicable items at this time. This section is retained for future extension.)

## Troubleshooting

Internal judgment guidance for this skill (handling of cases where Claude may be uncertain in its judgment).

| # | Q (case prone to hesitation) | A (judgment guidance) |
|---|---|---|
| 1 | The user asks a very pinpointed technical question from the start (e.g., "What is the difference between Vault Lock's compliance mode and governance mode?") | Because skill activation is controlled by intent matching against each skill's description, this skill is not necessarily always invoked first (fsi-ransomware-protect, etc., may activate directly). If this skill is activated, follow OV-C2: since the corresponding phase/topic is already stated, skip outputting the confirmation text and proceed directly to usage guidance and handoff |
| 2 | The user strongly requests a detailed consultation on Respond/Recover/Organization | Following OV-C5 and OV-C8, clarify that it is planned for future release. Where it would not feel like an unwanted push, you may propose a horizontal expansion into what can be started now from the Protect/Detect perspective |
| 3 | The user answers that they are interested in multiple phases | Following OV-C9, present the overviews of the relevant phases side by side and let the user choose which to proceed with first |
| 4 | The user asks something like "How do I comply with this FISC provision?", seeking a concrete mapping to a regulatory provision | Do not judge compliance with specific provisions; limit yourself to presenting general-level perspectives, and encourage confirmation with the organization's regulatory compliance department |
| 5 | After the user selects A (wanting the overall picture) in Step 1, the choice "A. I want to start with the overall picture" is presented again, making it look like the same question is looping | A violation of OV-C3. The end of Step 2 must be limited to B-1 through B-5 only, and must not re-present A. There is no need to have the user select A again after the overall picture has already been presented |

## Additional Resources

### Related skills for other phases

- fsi-ransomware-protect (Protect phase. Available. Architecture design/assessment of backup and data protection)
- fsi-ransomware-detect (Detect phase. Available. Detection and analysis of service impact/attacks)
- fsi-ransomware-respond (Respond phase. Planned for future release. Isolation and evidence preservation)
- fsi-ransomware-recover (Recover phase. Planned for future release. Restoration procedures and infection checks)
- fsi-ransomware-organization (Organization phase. Planned for future release. Organizational-operation considerations)

### Reference: NIST Cybersecurity Framework (CSF)

The 5-phase structure of this package is organized based on the concepts of the NIST CSF (Identify / Protect / Detect / Respond / Recover, plus Govern, which covers organizational controls). See the Reference Foundations section of each phase skill for details of the framework.
