---
name: fsi-banking-core
description: >-
  Reference architecture knowledge for a bank Core Banking (勘定系) workload on
  AWS from the Financial Reference Architecture Japan Edition (BLEA for FSI).
  Covers mission-critical, highly available multi-region designs: warm-standby
  across Tokyo/Osaka regions, Aurora Global Database (or the experimental Aurora
  DSQL option), DynamoDB global tables, ECS microservices with the Saga pattern,
  Application Recovery Controller + Step Functions failover, Canary external
  monitoring, ransomware-resistant AWS Backup vault lock, and FISC compliance
  mapping. Use when designing, reviewing, or deploying a core banking / 勘定系 /
  deposit / exchange / lending workload, planning region failover (RTO ~5 min),
  or mapping to FISC 安全対策基準.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI Core Banking (勘定系) Reference Architecture

## Workload Overview

A **core banking system (勘定系, "kanjōkei")** handles a bank's fundamental
business operations — deposits, domestic/foreign exchange, and lending. It is
the most mission-critical system a financial institution operates: any outage
directly translates into a business stoppage, and any data inconsistency in a
financial transaction is unacceptable.

This skill captures the AWS reference architecture for such a workload from the
"Financial Reference Architecture Japan Edition" (BLEA for FSI). Its purpose is
to help SAs and architects design, review, and deploy a core banking workload
that satisfies the stringent availability, data-consistency, and disaster-recovery
requirements of Japanese financial institutions.

Key business drivers:

- **Extreme availability** — minimize annual downtime, including planned outages;
  survive large-scale regional disasters and continue operating.
- **Strong data consistency** — no tolerance for inconsistent financial data,
  even during failover or recovery.
- **Regulatory alignment** — demonstrable mapping to FISC 安全対策基準 (Security
  Guidelines, 13th edition) practical standards.
- **Cyber resilience** — ransomware-resistant, immutable backups and automated
  isolation/recovery.

Although modeled on core banking, the architecture is a **general-purpose pattern
for any highly available, mission-critical workload**. Scope is the core banking
domain only; channel and information systems are out of scope. See
`references/architecture.md` for full detail.

## Best Practices and Key Components

### Best Practices

- MUST: deploy in a **multi-region warm-standby** configuration, accounting for
  latency and data consistency (primary = Tokyo, secondary = Osaka, monitoring =
  Oregon in the sample).
- MUST: automate the region switchover (application quiescing, Aurora Global
  Database promotion, etc.) with AWS Step Functions to achieve an RTO of about
  5 minutes or less.
- MUST: run the switchover Step Functions state machine in the **unaffected
  secondary region (Osaka)** so failover can execute reliably even when the
  primary region is degraded.
- MUST: use Amazon Application Recovery Controller (ARC) for reliable, controlled
  region switching, and rely on Route 53 name resolution for on-premises traffic
  since switching depends on DNS.
- MUST: take AWS Backup backups as a recovery path against ransomware that
  encrypts or disables data.
- SHOULD: create the backup vault lock in **compliance mode** to make backups
  immutable until the retention period ends (the sample uses governance mode for
  convenience, where sufficiently privileged IAM users can still delete data).
- SHOULD: implement external (synthetic) monitoring by issuing pseudo-transactions
  from CloudWatch Synthetics Canary in Osaka and Oregon toward Tokyo and checking
  the responses.
- SHOULD: use CloudWatch Application Signals with a CloudWatch Agent sidecar to
  gain OpenTelemetry-based distributed tracing without changing application code.
- SHOULD: apply AWS WAF to the Application Load Balancer, use VPC endpoints,
  security-group network controls, and IAM least-privilege access.
- SHOULD: implement a workflow that isolates the workload when a cyber event
  occurs.
- SHOULD: account separately for replication lag during disaster recovery based
  on business requirements and application characteristics (both DBs normally
  replicate within ~1 second).
- PREFER: Aurora PostgreSQL Global Database for its long track record and high
  PostgreSQL compatibility; MAY adopt Aurora DSQL experimentally where synchronous
  replication, strong consistency, and Active-Active multi-region are decisive
  (see `references/architecture-dsql.md`).
- MAY: substitute Amazon EKS or Amazon EC2 for Amazon ECS as the compute layer to
  match requirements.
- MUST NOT: deploy both provided sample applications (the PHP ECS sample and the
  multi-region microservice app) at the same time — deploy only one.
- WILL: run the transaction worker in the Tokyo region only, even though the same
  microservice app is otherwise deployed to both Tokyo and Osaka, to avoid
  contention.
- WILL: enable an (initially disabled) EventBridge Rule at deploy time to allow
  automatic region switchover when both the Osaka and Oregon monitoring Canaries
  report failure.
- MUST: Apply cdk-nag's AwsSolutionsChecks (via Aspects) to every CDK stack built from this skill, and gate CI (jest etc.) on zero unsuppressed AwsSolutions-* findings; suppress exceptions only with an explicit reason via NagSuppressions (see references/cdk-nag.md).

### Key Components

#### Global Traffic Router / DNS
- **Component Overview**: Routes traffic between primary and secondary regions
  and is the pivot of DNS-based region failover; on-premises callers resolve the
  active region through it.
- **Assumed AWS Services**: Amazon Route 53 (incl. Private Hosted Zone), Amazon
  CloudFront, Amazon API Gateway (edge/API entry, not all in the CDK sample).

#### Inter-Region / Hybrid Network Fabric
- **Component Overview**: Connects the three regions to each other and to
  on-premises data centers over private connectivity, enabling multi-region
  operation and closed-network access.
- **Assumed AWS Services**: AWS Transit Gateway (with cross-region peering),
  AWS Direct Connect / DXGW (hybrid, not in the CDK sample), Amazon VPC.

#### Application Compute (Microservices)
- **Component Overview**: Runs the core banking business logic (balance query,
  deposit, withdrawal, transaction control) as containerized microservices using
  the Saga pattern for distributed-transaction consistency.
- **Assumed AWS Services**: Amazon ECS (default), optionally Amazon EKS or Amazon
  EC2; Elastic Load Balancing (ALB).

#### Transaction / Main Datastore
- **Component Overview**: Stores the authoritative account and transaction data
  with cross-region replication for consistency and disaster recovery.
- **Assumed AWS Services**: Amazon Aurora Global Database (PostgreSQL) or, as an
  experimental option, Amazon Aurora DSQL (serverless, distributed, Active-Active).

#### Transaction State Store
- **Component Overview**: Manages distributed-transaction state (Saga
  orchestration) and requires no manual switchover on failover when using global
  tables.
- **Assumed AWS Services**: Amazon DynamoDB (global tables, PITR enabled).

#### Region Failover Orchestrator
- **Component Overview**: Executes the reliable, automated sequence of region
  switchover — application quiescing, Aurora Global Database promotion, DNS
  switch — to hit the ~5-minute RTO.
- **Assumed AWS Services**: Amazon Application Recovery Controller (ARC),
  AWS Step Functions, AWS Lambda, Amazon EventBridge.

#### External Health Monitoring
- **Component Overview**: Continuously verifies application health from outside
  the primary region using synthetic pseudo-transactions, feeding automatic
  failover decisions.
- **Assumed AWS Services**: Amazon CloudWatch Synthetics Canary.

#### Observability
- **Component Overview**: Provides comprehensive monitoring, service maps, and
  distributed tracing across microservices without application code changes.
- **Assumed AWS Services**: Amazon CloudWatch Application Signals, CloudWatch
  Agent (sidecar), Amazon CloudWatch (metrics/logs).

#### Immutable Backup & Cyber Resilience
- **Component Overview**: Provides ransomware-resistant, immutable backups and an
  automated isolation/recovery capability for cyber events.
- **Assumed AWS Services**: AWS Backup (vault lock, Logically air-gapped Vault),
  Amazon ECR cross-region replication, DynamoDB PITR, GuardDuty-driven isolation
  (EventBridge + Lambda in the sample).

## FISC Compliance Summary

The workload is mapped against the practical standards (実務基準) of the FISC
Security Guidelines (安全対策基準, 13th edition). The mapping distinguishes what
the shared governance-base template covers, what the core banking workload
template itself covers, and what remains as customer-side responsibility (mostly
business-application logic and operational/development processes).

Highlights that the core banking workload template addresses directly:

- **Availability & DR (実 73–実 88)**: multi-region / multi-AZ construction,
  secondary region build-out, use of highly available managed services.
- **Region switchover & recovery (実 71, 実 104)**: documented switchover policy;
  automated switch/switchback via Step Functions; cyber-event recovery guidance.
- **Backup & immutability (実 39, 実 73-1, 実 106)**: AWS Backup, vault lock
  (governance mode in the sample), Logically air-gapped Vault, DynamoDB PITR, ECR
  cross-region replication.
- **Encryption (実 3, 実 13, 実 30, 実 89)**: AWS KMS encryption and key
  management; TLS in transit is customer-implemented.
- **Monitoring & logging (実 10, 実 46, 実 72, 実 101–実 103)**: VPC Flow Logs,
  ALB access logs, CloudWatch monitoring, Canary external monitoring.
- **Threat/vulnerability (実 14, 実 20, 実 21, 実 32)**: WAF on ALB, VPC
  endpoints, security groups, ECR basic scan, automated cyber-event isolation.

Many items are explicitly "対象外" (out of scope) because they are business-app,
operational-process, development-process, or already-handled-by-AWS concerns.
Every mapping entry (実 1 through 実 153, including the vacant numbers 実 127–実 131)
is preserved verbatim in `references/fisc-mapping.md` — consult it for the
authoritative, per-control detail.

## Reference Architecture

One concrete example configuration (see `references/architecture.md` and the
diagrams under `assets/images/`):

- **Three regions**: Tokyo (`ap-northeast-1`, primary), Osaka (`ap-northeast-3`,
  secondary/warm-standby), Oregon (`us-west-2`, monitoring).
- **Networking**: each region has its own VPC, connected via Transit Gateway
  cross-region peering; on-premises connects over Direct Connect (hybrid part not
  in the CDK sample). Route 53 provides DNS-based failover.
- **Compute**: ECS microservices behind an ALB; WAF applied at the ALB.
- **Data**: Aurora Global Database (PostgreSQL) as the main DB, DynamoDB global
  tables for transaction state. Both replicate within ~1 second under normal
  conditions.
- **Failover**: ARC + Step Functions orchestrate switchover with RTO ≈ 5 minutes;
  the state machine runs in Osaka. Canaries in Osaka and Oregon drive automatic
  failover via an EventBridge Rule.
- **Resilience**: AWS Backup with vault lock, DynamoDB PITR, ECR cross-region
  replication, and an automated isolation workflow for cyber events.

Design decisions of note: warm-standby (not active-active) with Aurora PostgreSQL
to balance latency vs. consistency; the transaction worker runs only in Tokyo to
avoid contention; the switchover automation executes from the unaffected region.
An **Aurora DSQL** variant (serverless, distributed, synchronous replication,
Active-Active, strong consistency) is presented as an experimental alternative in
`references/architecture-dsql.md`, along with its trade-offs (optimistic
concurrency control, transaction size/row/time/connection limits, PostgreSQL
feature subset).

## CDK Sample Overview

The CDK sample (TypeScript) is under `assets/sample-cdk/` (directory
`guest-core-banking-sample`). It provisions the multi-region core banking base:
Route 53, Transit Gateway (with the cross-region peering acceptance/route CLI
steps output at deploy time), ELB, ECS, DynamoDB, Aurora Global Database, and AWS
Backup, plus the failover machinery (ARC, Step Functions, Lambda) and CloudWatch
Synthetics Canary external monitoring. It also includes cyber-resilience stacks
(automated isolation, data-bunker account, restore Step Functions).

Two optional sample applications ship with it (deploy only one):

1. A PHP-based `amazon-ecs-sample` container, with an optional test NLB.
2. A **multi-region microservice application** (TypeScript) implementing balance
   query, deposit, and withdrawal via four services (transaction, balance, count,
   worker) using the Saga pattern with compensating transactions — actually
   failover-capable between Tokyo and Osaka.

> **Sample app security notice**: the multi-region microservice app is a
> functional demo of the failover mechanics only. It identifies accounts from an
> unauthenticated `x_account_id` header (no signature/token verification), the
> ALB listens on plain HTTP, WAF managed rules are deployed in count-only
> (non-blocking) mode, and the `region-proxy` Lambda executes arbitrary AWS APIs
> without an allow-list. Do not expose this sample to real traffic or real
> account data — add authentication, TLS, WAF blocking, and input allow-listing
> before adapting it beyond a local demo. The same notice ships inside the CDK
> tree as `assets/sample-cdk/SECURITY_NOTICE.md` and is printed as a warning on
> every `cdk synth` / `cdk deploy`.

The CDK deploys three stacks in order: `BLEAFSI-CoreBanking-primary-*`,
`-secondary-*`, and `-monitoring-*`, each requiring manual Transit Gateway
peering acceptance and route CLI commands emitted as stack Outputs. Full steps
are in `references/deployment.md`; the microservice app detail is in
`references/multi-region-app.md`; deploy-time Docker errors are covered in
`references/sample-app-workaround.md`. The copied
`assets/sample-cdk/test/*.test.ts` files are the
authoritative source of the cdk-nag enforcement pattern; the extracted
suppression ledger and the downstream enforcement guidance are in
`references/cdk-nag.md`.
