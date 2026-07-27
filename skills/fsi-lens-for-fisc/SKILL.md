---
name: fsi-lens-for-fisc
description: >-
  Well-Architected FSI Lens for FISC (FSI Lens) knowledge base for evaluating
  Japanese financial (FSI) workloads on AWS against the AWS Well-Architected
  Framework and the FISC Security Guidelines (FISC 安全対策基準). Use this skill
  when reviewing or designing a financial workload against FISC practice
  standards (FISC 実務基準), mapping Well-Architected pillars (Operational
  Excellence, Security, Reliability) to FISC considerations, or answering
  questions about the FSI Lens best practices. Triggers: FSI Lens, FISC,
  金融情報システムセンター, 安全対策基準, Well-Architected, ウェルアーキテクテッド,
  FISCOPS, FISCSEC, FISCREL, 実務基準.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Well-Architected FSI Lens for FISC

## Workload Overview

The **AWS Well-Architected Framework FSI Lens for FISC** (FSI Lens) is a
Well-Architected "lens" that provides context-specific guidance for designing,
deploying, and operating **Japanese Financial Services Industry (FSI)** workloads
on AWS. It extends the general-purpose AWS Well-Architected Framework with best
practices aligned to the **FISC Security Guidelines and Commentary** (金融機関等
コンピュータシステムの安全対策基準・解説書), published by the Financial Information
System Center (FISC / 金融情報システムセンター). The FISC guidelines are one of the
de-facto industry standards for financial institutions in Japan and are cited by
the Financial Services Agency (FSA) supervisory guidelines as a reference for
system-risk and security controls.

**Purpose.** The lens focuses on how FSI workloads can be built to promote
**resilience, security, and operational performance** in line with the FISC
Security Guidelines. It lets architects measure an architecture consistently
against best practices and identify areas for improvement.

**How it is used.** The lens is organized into **three pillars** — Operational
Excellence, Security, and Reliability — each containing **FISC questions**
(prefixed `FISCOPS`, `FISCSEC`, `FISCREL`) and **best practices** (`-BPnn`). Every
best practice is tied to one or more FISC practice-standard numbers (FISC
実務基準, notated 実 N). A cross-reference table maps each FISC practice standard
(実 1–実 153) to the relevant Well-Architected Framework questions and FSI Lens
questions, distinguishing the mappings for the 12th and 13th editions of the FISC
guidelines. For general (non-FSI-specific) best practices, the base AWS
Well-Architected Framework should also be consulted.

**Important caveats (from the source).**
- The FISC Security Guidelines have **no certification/conformity program**; this
  lens does **not** guarantee conformance. Each organization must perform its own
  compliance check against the guidelines, including business applications.
- The **13th edition** of the FISC guidelines (published March 2025) added new
  AI / generative-AI safety criteria. For AI workloads, AWS recommends combining
  this lens with the **Machine Learning Lens** (for ML workloads) and the
  **Generative AI Lens** (for generative-AI workloads).

## Best Practices and Key Components

### Best Practices

The following are the lens's own best practices, restated as indicator-prefixed
rules. Each traces to a FISC question / practice standard in the source docs.

Operational Excellence (FISCOPS):
- MUST: Record operations — both automated processes and manual operations (console, CLI, EC2 login) must be recorded and verified so that legitimately authorized actors can be shown to have acted correctly (FISCOPS1-BP01, 実 38).
- SHOULD: Implement infrastructure as code so entire environments can be built, isolated, and recovered programmatically (FISCOPS1-BP02, 実 42).
- MUST: Prevent application tampering by version-controlling code/artifacts and separating production from in-development code/artifacts (FISCOPS1-BP03, 実 40/実 96).
- SHOULD: Improve quality from the development stage by automating code review to reduce new bugs and vulnerabilities (FISCOPS1-BP04, 実 96).
- SHOULD: Monitor cloud-provider events so alerts and remediation guidance are available when events could affect the workload (FISCOPS2-BP01, 実 46).
- SHOULD: Centralize monitoring and standardize cloud-monitoring practices across the organization to avoid information silos (FISCOPS2-BP02, 実 46).
- SHOULD: Run periodic load tests to identify key metrics and validate that alerts and automated remediation work, minimizing mean time to detection (FISCOPS2-BP03, 実 46).
- MUST: Understand data backup and retention requirements, including regulatory requirements applicable to the workload (FISCOPS3-BP01, 実 39).
- SHOULD: Incorporate short-retention anti-ransomware backups into the backup strategy, with strictly limited and encrypted access (FISCOPS3-BP02, 実 39).
- SHOULD: Create backup lifecycle policies to retain and purge data per regulatory requirements (FISCOPS3-BP03, 実 39).
- MUST: Ensure continuous or periodic data-file backups whose frequency satisfies the RPO and that support point-in-time recovery (FISCOPS3-BP04, 実 39).
- MUST: Back up infrastructure configuration (not just data) needed to redeploy the workload and meet the RTO (FISCOPS3-BP05, 実 43).
- MUST: Version-control important operational documents (design docs, procedures) and require owner approval on updates to prevent unintended change/tampering (FISCOPS4-BP01, 実 44).
- MUST: Restrict document viewing to appropriate individuals or teams (FISCOPS4-BP02, 実 44).
- SHOULD: Back up documents required for disaster recovery (FISCOPS4-BP03, 実 45).

Security (FISCSEC):
- MUST: Apply appropriate access control to important files to protect them from unauthorized access, using least privilege and defense-in-depth (security groups, NACLs, subnets, Network Firewall, VPC-only access) (FISCSEC1-BP01, 実 5).
- MUST: Identify terminals capable of operation outside fixed locations and clearly define the scope of their privileges (FISCSEC1-BP02, 実 61).
- SHOULD: Make grant/revoke operations for identity-data systems explicit, with separation between requester and approver and periodic access reviews (FISCSEC1-BP03, 実 27).
- MUST: Monitor AWS account activity by enabling CloudTrail in every supported region and storing logs in a tightly restricted central logging account with log-file integrity validation (FISCSEC2-BP01, 実 63/実 10).
- MUST: Enable verification of the association between account activity and the actual operator (e.g., centralized identity provider integrated with HR) (FISCSEC2-BP02, 実 63).
- SHOULD: Check service time zones and use UTC at the database layer to avoid time drift across systems (FISCSEC2-BP03, 実 10).
- SHOULD: Protect input data from bad-data injection and fraud via application-layer input checks plus collection/management of data-processing history (FISCSEC3-BP01, 実 6/実 65).
- MUST: Use data classification to determine appropriate control levels; it is the customer's responsibility to classify data and implement controls such as encryption (FISCSEC4-BP01, 実 69).
- MUST: Set a strong password policy for users (FISCSEC5-BP01, 実 1/実 26).
- MUST: Force a password change at first sign-in (FISCSEC5-BP02, 実 1/実 26).
- SHOULD: Restrict connection sources to the minimum necessary (credentials, IP address, client certificate) (FISCSEC5-BP03, 実 8).
- SHOULD: Centralize identity and connection management to reduce password-reuse/leak risk (FISCSEC5-BP04, 実 26).
- MUST: Enable multi-factor authentication (MFA) to protect AWS resources, including root and IAM users (FISCSEC5-BP05, 実 26).
- SHOULD: Notify customers on specific transactions and add supplementary authentication (e.g., SMS) to detect/prevent misuse (FISCSEC6-BP01, 実 112).
- MUST: Manage access history and state — collect application/login logs and restrict access by MFA and source IP (FISCSEC7-BP01, 実 11/実 16/実 113).
- MUST: Protect the application by monitoring expected vs. unexpected traffic and defending public sites from DoS/DDoS with AWS WAF and AWS Shield (FISCSEC7-BP02, 実 16).
- SHOULD: Monitor application behavior by analyzing collected logs and restricting access to logs to prevent tampering/deletion (FISCSEC7-BP03, 実 18).
- MUST: Manage encryption keys securely using AWS KMS envelope encryption; customer-managed CMKs are recommended for many financial customers (FISCSEC8-BP01, 実 13/実 30).
- SHOULD: Rotate encryption keys and enable automatic key rotation on CMKs (FISCSEC8-BP02, 実 30).
- SHOULD: Separate key-management duties from resource ownership to strengthen security (FISCSEC8-BP03, 実 30).
- SHOULD: Delete encryption keys at end of data use to make decryption infeasible and serve as evidence of disposal, after confirming the key is not used by other data (FISCSEC8-BP04, 実 82).
- MUST: Protect compute resources to prevent malware — patch vulnerabilities, use approved golden images, and scan AMIs/containers with Amazon Inspector (FISCSEC9-BP01, 実 22/実 32).
- MUST: Take frequent backups so data can be restored after an attack; AWS Backup Vault Lock can prevent modification of backup data (FISCSEC9-BP02, 実 22/実 32).
- SHOULD: Protect email from spoofing and tampering using SPF, DKIM, and DMARC, plus DNSSEC and BIMI (FISCSEC10-BP01, 実 138).
- SHOULD: Protect sent email data using S/MIME or PGP encryption and scan shared files for malware (FISCSEC10-BP02, 実 138).

Reliability (FISCREL):
- MUST: Use business criticality to drive recovery objectives; resilience requirements must be proportional to the criticality of the business service, informing RTO/RPO and availability metrics (FISCREL1-BP01, 実 74).
- SHOULD: Apply detailed per-component recovery requirements rather than designing the whole application to the strictest requirement (FISCREL1-BP02, 実 74).
- MUST: Use a defined recovery strategy (Backup & Restore, Pilot Light, Warm Standby, or Multi-Region Active/Active) to meet RTO/RPO (FISCREL1-BP03, 実 74).
- SHOULD: Manage configuration drift at the DR site/region via delivery pipelines to all locations, AWS Config drift detection, and CloudFormation (FISCREL1-BP04, 実 74).
- SHOULD: Automate recovery so systems recover automatically under all conditions (e.g., Elastic Disaster Recovery) (FISCREL1-BP05, 実 74).
- MAY: For wide-area disaster DR scenarios (e.g., Tokyo-wide disaster), decide multi-region system configuration across the Tokyo and Osaka regions, accounting for inter-region service differences (FISCREL1-BP06, 実 74).
- SHOULD: Have a multi-account strategy to isolate SDLC environments (dev/test/prod); BLEA for FSI is available as a secure-baseline template (FISCREL2-BP01, 実 76).
- SHOULD: Implement IAM separation across SDLC accounts using AWS Organizations and SCPs (FISCREL2-BP02, 実 76).
- SHOULD: Implement network separation between production and non-production resources (FISCREL2-BP03, 実 76).
- SHOULD: Establish a baseline of expected network traffic to trigger operational responses under abnormal load (FISCREL2-BP04, 実 76).
- MUST: Deploy workloads across multiple locations (multiple Availability Zones, and Regions where required) with failover to healthy resources (FISCREL3-BP01, 実 104).
- SHOULD: Implement infrastructure as code and automation to recover environments in minutes (FISCREL3-BP02, 実 106).
- SHOULD: Perform periodic recovery of data to verify backup integrity and process against RTO/RPO, using point-in-time recovery where available (FISCREL3-BP03, 実 106).
- WILL: The FISC Security Guidelines have no conformity program, so this lens does not guarantee conformance; each organization must perform its own compliance check (source caveat).

### Key Components

The FSI Lens is process-oriented; its logical components are its three pillars.
Each pillar groups FISC questions and best practices. "Assumed AWS Services" are
the services the source docs associate with that pillar's best practices.

#### Operational Excellence Pillar (運用上の優秀性)

- **Component Overview**: Covers managing workload changes (FISCOPS1), rapidly
  detecting workload failures (FISCOPS2), taking workload backups (FISCOPS3), and
  managing important documents (FISCOPS4). Maps to FISC 実務基準 including 実 38,
  40, 42, 43, 44, 45, 46, 39, 96.
- **Assumed AWS Services**: AWS CloudTrail, AWS Systems Manager (Session Manager,
  Automation), AWS CloudFormation, AWS Config, AWS CodeCommit, Amazon S3 (Object
  Lock, lifecycle, CRR, versioning), AWS Lambda (code signing), Amazon CodeGuru
  Reviewer, AWS Health Dashboard/API, Amazon CloudWatch, AWS Backup, Amazon EBS,
  Amazon DynamoDB, Amazon RDS, Amazon Aurora, Amazon EFS, Amazon Redshift, Amazon
  Neptune, AWS Storage Gateway, Amazon FSx, Amazon EC2 / AMI.

#### Security Pillar (セキュリティ)

- **Component Overview**: Covers access-permission setup/management (FISCSEC1),
  operation-record verification (FISCSEC2), input-data protection (FISCSEC3), data
  classification (FISCSEC4), identity protection (FISCSEC5), misuse prevention
  (FISCSEC6), incident response (FISCSEC7), encryption-key management (FISCSEC8),
  malware protection (FISCSEC9), and secure email (FISCSEC10). Maps to FISC 実務
  基準 including 実 1, 5, 6, 8, 10, 11, 13, 16, 22, 26, 27, 30, 32, 61, 63, 65,
  69, 82, 112, 113, 138.
- **Assumed AWS Services**: AWS IAM (Access Advisor, Access Analyzer, permissions
  boundaries, IAM Roles Anywhere), AWS Organizations / SCP, Amazon VPC (security
  groups, NACLs, VPC endpoints, Network Firewall), Amazon S3 (versioning, access
  logs, Object Lock, public block), AWS CloudTrail, Amazon GuardDuty (incl.
  Malware Protection for S3), AWS Security Incident Response, Amazon CloudWatch
  (Logs Insights, metric filters, Alarm), AWS Config, AWS Lambda, Amazon SQS, AWS
  KMS / CloudHSM, AWS IAM Identity Center, Amazon RDS, Amazon SNS, AWS WAF, AWS
  Shield (Standard/Advanced), VPC Flow Logs, EC2 Image Builder, Amazon Inspector,
  AWS Systems Manager Session Manager, AWS Backup (Vault Lock), Amazon SES, Amazon
  Route 53 (DNSSEC), Amazon Kinesis, Amazon OpenSearch Service, FireLens.

#### Reliability Pillar (信頼性)

- **Component Overview**: Covers determining disaster recovery requirements
  (FISCREL1), ensuring SDLC environment separation (FISCREL2), and protecting/
  recovering workloads from component failures (FISCREL3). Includes DR strategy
  selection (Backup & Restore, Pilot Light, Warm Standby, Multi-Region Active/
  Active) and wide-area disaster planning across the Tokyo and Osaka regions. Maps
  to FISC 実務基準 including 実 74, 76, 104, 106.
- **Assumed AWS Services**: AWS Resilience Hub, AWS Elastic Disaster Recovery,
  Amazon Route 53, AWS Global Accelerator, AWS Config, AWS CloudFormation (incl.
  StackSets), AWS Organizations / SCP, Amazon VPC (peering, security groups,
  NACLs), AWS WAF, AWS Shield / Shield Advanced, Amazon CloudFront, Elastic Load
  Balancing, Amazon EC2, AWS Systems Manager (Automation), Amazon RDS, Amazon
  DynamoDB (point-in-time recovery), BLEA for FSI (secure-baseline template).

## FISC Compliance Summary

This lens **is** the FISC guidance. It maps AWS Well-Architected Framework pillars
to FISC considerations at two levels:

1. **FSI Lens questions & best practices** — each pillar's FISC questions
   (`FISCOPS`/`FISCSEC`/`FISCREL`) and best practices (`-BPnn`) explicitly cite the
   FISC practice-standard number(s) (実 N) they address.
2. **Reference cross-reference table** — a table maps each FISC practice standard
   (実 1 through 実 153) to the relevant base Well-Architected Framework questions
   (SEC/OPS/REL/PERF) and to FSI Lens questions, with **separate columns for the
   12th and 13th editions** of the FISC guidelines and a rationale column
   explaining why a given WA pillar was added in the 13th edition. The 13th
   edition additions include new AI / generative-AI criteria (実 150–実 152) that
   point to the Machine Learning Lens and Generative AI Lens.

The base of this cross-reference is the FISC compliance reference published by AWS
for the FISC Security Guidelines (11th edition). The guidelines have no conformity
program, so the mapping is guidance — not a conformance guarantee.

The full pillar/question/best-practice detail and the complete 実 1–実 153
cross-reference table are preserved in:
- `references/lens-overview.md` — lens purpose, caveats, and pillar index.
- `references/operational-excellence.md` — FISCOPS questions and best practices.
- `references/security.md` — FISCSEC questions and best practices.
- `references/reliability.md` — FISCREL questions and best practices.
- `references/fisc-mapping.md` — the full 実 1–実 153 → WA / FSI Lens table.

## Reference Architecture

The FSI Lens does **not** prescribe a single reference architecture. It is a
Well-Architected lens: a set of pillars, questions, and best practices used to
evaluate and improve an FSI workload's architecture against the FISC Security
Guidelines. Where the lens gives architectural guidance, it does so as options:

- **Disaster-recovery strategies** (Reliability): Backup & Restore, Pilot Light,
  Warm Standby, and Multi-Region Active/Active, listed in increasing complexity and
  decreasing RTO/RPO; and multi-region planning across the Tokyo and Osaka regions
  for wide-area disaster scenarios.
- **Multi-account isolation** (Reliability): separate AWS accounts per SDLC stage,
  with the **BLEA for FSI** secure-baseline template referenced as an example.

The lens's structure and its evaluation approach are documented in
`references/lens-overview.md` (structure, pillars, caveats). The lens does not ship
a bespoke architecture diagram; see the DR-strategy and multi-account guidance in
`references/reliability.md`.

## CDK Sample Overview

No CDK sample is provided for this asset.
