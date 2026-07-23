---
name: fsi-cyber-resilience
description: >-
  Reference architecture and implementation guidance for cyber resilience in
  Japanese financial institutions (BLEA for FSI, サイバーレジリエンス). Covers logically
  air-gapped backup to an isolated Data Bunker account, cross-account restore to a
  fresh account, and automated network isolation of a compromised core-banking
  workload. Use this skill when designing or reviewing recovery from ransomware
  (ランサムウェア), DDoS, or other cyber events for financial workloads on AWS — including
  AWS Backup Logically Air-gapped Vault, RAM cross-account restore, GuardDuty-driven
  Network ACL isolation, and the FSA / FISC cyber-security guidelines that motivate them.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI Cyber Resilience

## Workload Overview

Cyber resilience is the ability to holistically strengthen an organization's
capacity to prevent, detect, respond to, and recover from cyber attacks, on the
assumption that attacks *will* happen. The traditional "focus on prevention"
mindset must shift to "continue the business even when attacked, and recover
quickly." Defending against availability-affecting cyber events such as DDoS and
ransomware is considered especially urgent.

This asset is a **documentation-only** reference architecture for financial
institutions. It builds on the BLEA for FSI **core-banking workload** and adds
three capabilities delivered as CDK samples in that core-banking usecase:

1. **Logically air-gapped backup** — replicating AWS Backup recovery points into
   an isolated **Data Bunker account** so ransomware-infected data cannot be
   silently propagated into, or tampered with in, the backup copy.
2. **Cross-account restore to a fresh environment** — recovering in a brand-new
   **Restore account** (assuming the production data center may still be infected),
   sharing the backup via AWS Resource Access Manager (RAM) rather than granting
   direct access to the Data Bunker account.
3. **Automated network isolation** — using Amazon GuardDuty to detect Critical
   threats and a Lambda function to rewrite Network ACLs, isolating the compromised
   core-banking workload to contain blast radius.

The design explicitly assumes a ransomware scenario: because infected data could
be copied into backups, backups are logically isolated, and recovery targets an
environment completely separate from production. Reference: FSA "Guidelines on
Cyber Security in the Financial Sector," section 2.3.3 (Data Protection).

## Best Practices and Key Components

### Best Practices

- MUST: Take backups in the workload account with AWS Backup and replicate the
  recovery points into a separate, logically isolated Data Bunker account.
- MUST: Store the replicated backups in an **AWS Backup Logically Air-gapped Vault**
  so that read, modify, and delete operations are impossible during the retention
  period — even for users with administrator privileges or an attacker.
- MUST: Keep the workload account and the Data Bunker account within the **same
  AWS Organizations**, which is required for the cross-account backup copy and RAM
  sharing to work.
- MUST NOT: Access the Data Bunker account directly when a restore is needed;
  share the backup vault to the Restore account via **AWS Resource Access Manager**
  instead, to prevent unauthorized access to and tampering with backup data.
- MUST: Recover into a fresh **Restore account** on the assumption that the
  production environment is compromised, rather than restoring back into production.
- SHOULD: Rebuild application and infrastructure in the Restore account
  automatically with CDK, and automate database restore-from-backup with AWS Step
  Functions.
- MUST NOT: Automate reconnection of recovered databases to the workload; business
  impact assessment and risk judgment are required, so keep the cutover as a manual
  operational step (update the ECS task definition environment variables to point
  at the restored database, then restart the ECS tasks).
- MUST: Before starting recovery from backup, evaluate the integrity of the backup
  data.
- MUST: On a cyber event, promptly isolate affected systems and preserve evidence
  for incident investigation.
- SHOULD: Trigger automated network isolation only on GuardDuty findings of
  **Severity 9.0 or higher (Critical)**; this mechanism reacts to Critical-level
  findings only.
- SHOULD: For isolation, dynamically create a Network ACL that permits only
  communication between the workload's subnets across the two Availability Zones
  and blocks all other inbound/outbound traffic.
- MUST: Notify administrators via Amazon SNS when isolation completes, and also
  send a notification on error.
- PREFER: Insert a human decision step between the Critical notification and the
  isolation action when isolation carries business impact, rather than isolating
  fully automatically.
- WILL: Because the core-banking workload runs on Amazon ECS Fargate, the container
  host is under AWS management responsibility, so investigation scope is limited and
  the Forensic account deploy/procedure is omitted from this asset.
- MAY: Deploy a separate Forensic account for tamper detection, malware scanning,
  and verification of data integrity and application dependencies; it is out of
  scope for this workload (see the AWS Security IR forensic resources).

### Key Components

#### Workload Account

- **Component Overview**: Production account running the core-banking system (and
  similar workloads). AWS Backup takes backups here, and its backup plan is
  configured to copy recovery points to the Data Bunker account's air-gapped vault.
- **Assumed AWS Services**: AWS Backup, Amazon ECS (Fargate), Amazon Aurora,
  Amazon DynamoDB, Amazon VPC.

#### Data Bunker Account

- **Component Overview**: A logically isolated account holding the backup data. It
  hosts an AWS Backup Logically Air-gapped Vault that receives cross-account copies
  of recovery points, and shares that vault to the Restore account via RAM on demand
  rather than allowing direct access.
- **Assumed AWS Services**: AWS Backup (Logically Air-gapped Vault), AWS Resource
  Access Manager, AWS Organizations.

#### Restore Account

- **Component Overview**: A fresh account that becomes the recovery target,
  assuming production is compromised. Application and infrastructure are rebuilt via
  CDK; database restore from the shared backup is automated with Step Functions;
  reconnection of the workload to the restored database is performed manually.
- **Assumed AWS Services**: AWS Step Functions, Amazon Aurora, Amazon DynamoDB,
  Amazon ECS (Fargate), Elastic Load Balancing (ALB), AWS Resource Access Manager.

#### Forensic Account (out of scope)

- **Component Overview**: Account for tamper detection, malware scanning, and
  verification of data integrity and application dependencies on compromised
  systems. Deployment and procedures are omitted because the ECS Fargate host is
  under AWS management responsibility, limiting investigation scope.
- **Assumed AWS Services**: Not deployed in this asset; see AWS Security Incident
  Response forensic resources.

#### Automated Network Isolation

- **Component Overview**: On a Critical GuardDuty finding, an EventBridge rule
  triggers a Lambda function that creates and applies a Network ACL to the
  core-banking Protected Subnets, permitting only inter-AZ subnet traffic and
  blocking all other communication, then notifies administrators via SNS. Operates
  in the Primary Region only.
- **Assumed AWS Services**: Amazon GuardDuty, Amazon EventBridge, AWS Lambda,
  Amazon SNS, Amazon VPC (Network ACL).

## FISC Compliance Summary

There is **no dedicated FISC mapping file for this asset** in the BLEA for FSI
v1.6 source. The following regulatory considerations are the only ones present in
the source documentation:

- The Japan Financial Services Agency (FSA) established the "Guidelines on Cyber
  Security in the Financial Sector," which define requirements for backup-related
  rule development and for responding to ransomware attacks. This asset cites its
  section 2.3.3 (Data Protection) as motivation for logically isolating backups and
  recovering in a completely separate environment.
- In response to those FSA guidelines, the **FISC Security Guidelines (安全対策基準)**
  added new criteria on strengthening cyber resilience, and the countermeasure
  content leveraging this reference architecture has been updated. The source points
  to the **core-banking asset's** FISC mapping file for the practical-standard
  countermeasures (`fisc-mapping-core-banking.md`), not to a mapping file of its own.

No FISC control-to-service mappings specific to cyber-resilience exist in the
source, so none are asserted here.

## Reference Architecture

The end-to-end architecture — account design (Workload / Data Bunker / Restore /
Forensic), the three-step backup-restore flow, the automated network isolation
flow, and all referenced AWS documentation, whitepapers, and guidelines — is
detailed in `references/architecture.md`.

Operational, step-by-step procedures are captured in:

- `references/backup-procedures.md` — deploying the Logically Air-gapped Vault to
  the Data Bunker account and configuring cross-account backup copy.
- `references/restore-procedures.md` — RAM sharing, Step Functions database
  restore, and manual workload reconnection in the Restore account.
- `references/isolation-procedures.md` — GuardDuty-triggered automated network
  isolation architecture, deployment, testing, and limitations.

## CDK Sample Overview

No standalone CDK sample directory is provided for this asset in BLEA for FSI v1.6;
this asset is documentation only. The CDK deployment assets referenced by the
procedures live inside the **core-banking** usecase
(`usecases/guest-core-banking-sample`), selected via the `CyberResilienceParameter`
`option` array (`'backup' | 'restore' | 'isolation'`) in that usecase's
`bin/parameter.ts`. See the reference files for the exact deploy commands as
documented in the source.
