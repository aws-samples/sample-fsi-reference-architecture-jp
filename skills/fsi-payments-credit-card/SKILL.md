---
name: fsi-payments-credit-card
description: >-
  Reference architecture case study for a credit card issuer (イシュア) system built
  on the "BLEA for FSI / 金融リファレンスアーキテクチャ日本版" initiative. It describes how to
  incrementally migrate a mission-critical card payment / issuer workload from
  on-premises to AWS using a microservices, multi-region Active-Active design that
  handles high-TPS real-time Authorization and Reconciliation while keeping
  Settlement on-premises (Strangler Pattern). Use this skill when designing,
  explaining, or discussing a credit card issuer / card payment processing workload
  on AWS (keywords: credit card, クレジットカード, カード決済, イシュア, issuer, card payment,
  Authorization, Reconciliation, request hedging, リクエストヘッジ, PCI DSS).
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Credit Card Issuer Reference Architecture (BLEA for FSI)

## Workload Overview

This case study is a reference for incrementally migrating and operating a **credit
card issuer (イシュア) system** on AWS, moving it in stages from an on-premises
environment to the cloud.

A credit card issuer system processing consists mainly of three processes:

- **Authorization** — real-time approval of card usage. When a customer uses a card,
  information is relayed in the flow merchant → payment processor / acquirer → card
  issuer to make the approval decision.
- **Reconciliation** — exchange and matching of approved transaction data. The
  acquirer sends clearing data (sales information) to the issuer, and it is matched
  against the approval data.
- **Settlement** — the clearing, settlement, and fund movement between acquirer and
  issuer over the payment network.

Purpose / significance of this architecture:

- Flexibly handle high-traffic processing driven by payment demand (e.g., large-scale
  sales or point-reward campaigns) and real-time approval requirements.
- Build an IT foundation that lets services / functions be added or changed
  efficiently when new payment technologies or industry standards are introduced, or
  when financial regulatory requirements change.
- Build a highly resilient architecture that supports business continuity for a
  mission-critical card payment system requiring high availability.

Business / technical drivers (requirements):

- **Performance**: up to 5,000 TPS, response time ≤ 200 msec, processing more than 1
  million transactions per day / over 300 million per month. A microservices
  architecture is adopted so each function scales out independently.
- **Availability**: 99.99%, realized by making maximum use of AWS mechanisms such as
  multi-region / multi-AZ.

Overall composition: this architecture builds **Authorization** and **Reconciliation**
on AWS while building **Settlement** (fund clearing) on-premises. By adopting the
Strangler Pattern to migrate the workload to AWS in stages, migration risk and cost
are reduced while the benefits of the cloud are still enjoyed in a balanced way. On
AWS, reconciled clearing data is created and the file is then handed off to
on-premises where the Settlement process is executed.

## Best Practices and Key Components

### Best Practices

- MUST: Build Authorization (approval) and Reconciliation (matching clearing files
  against approved data) on AWS, and keep Settlement (fund clearing) on-premises.
- SHOULD: Adopt the Strangler Pattern to migrate the workload to AWS in stages,
  reducing migration risk and cost while gaining cloud benefits in a balanced way.
- MUST: Adopt a microservices architecture so each function scales out independently,
  to flexibly meet the credit card industry's high-traffic and real-time approval
  requirements.
- MUST: Adopt a multi-AZ configuration to raise service continuity within a region;
  redundantly deploy ECS compute, Amazon MSK, Amazon EMR, ElastiCache for Valkey, and
  AWS SFTP across multiple AZs.
- MUST: Adopt a multi-region Active-Active configuration; determine, per data content
  (card number, customer ID, etc.), which region on-premises routes to, so that each
  region has a separated processing scope, achieving both consistency and availability.
- MUST: Synchronize data across regions using Aurora Global Database and DynamoDB
  Global Tables (typically replicating within 1 second).
- SHOULD: Prepare countermeasures for data loss caused by replication lag during
  failure recovery — e.g., archive write events to S3 via DynamoDB Streams and Kinesis
  Data Firehose, forward application processing-result logs to S3 and inspect them with
  Athena during regional recovery, reconcile against external payment systems to detect
  and complete unreflected transactions, and recover from store POS systems, EC
  operators' order records, and customer app history.
- MUST: Use AWS Application Recovery Controller (ARC) routing control to achieve
  reliable switchover on regional failure.
- MUST: Connect on-premises and AWS with a redundant configuration using
  multi-location Direct Connect + Direct Connect Gateway + Transit Gateway.
- MUST: Maintain connectivity to the international card brand networks on the
  on-premises side.
- SHOULD: Implement communication from the on-premises side using Route 53 name
  resolution.
- SHOULD: Adopt Amazon ECS deployed across multiple AZs within a VPC; Amazon EKS may be
  selected instead of Amazon ECS to match requirements.
- MUST: Use Amazon MSK to queue data and achieve loose coupling between functions
  (task groups such as "Auth Gateway" to receive external approval requests and "Auth
  Decisioning" to execute approval processing).
- PREFER: Choose Amazon MSK for inter-function messaging, because credit card
  transactions can include large metadata (product info, customer info, risk score,
  etc.) so a large supported message size plus strong throughput / latency
  characteristics make MSK an effective choice.
- MUST: Select the right database for the right job based on the data and processing
  handled.
- MUST: Store and process card-transaction account information (balance / transaction
  data) in DynamoDB, leveraging NoSQL performance characteristics to meet the low
  latency and high throughput requirements.
- MUST: Manage per-customer business rules (card limit amount, allowed PIN error count,
  etc.) in Aurora, leveraging RDB characteristics for complex conditional reference,
  search, and aggregation.
- MUST: Process card-information tokenization in ElastiCache for Valkey; tokenize card
  numbers and authentication codes before sharing data with merchants and payment
  agents (for security / PCI DSS), using the in-memory database to tokenize at
  microsecond-level low latency.
- SHOULD: Introduce request hedging as a countermeasure for DynamoDB tail latency,
  where the application automatically sends a second request when a request exceeds a
  specified time threshold (delta value) and uses the fastest of the two responses,
  improving overall tail latency.
- WILL: DynamoDB is a distributed system, so tail latency can occur at the 99th or
  99.9th percentile due to rare internal-component performance degradation.
- MUST: Run the Reconciliation batch (matching clearing files against approved data)
  on Amazon EMR, export the result to S3, and transfer it to on-premises over SFTP
  using AWS Transfer Family.
- MUST: Rely on AWS handling PCI DSS standards within the AWS responsibility area of
  each managed service, reducing the user-side burden even when regulations change.
- SHOULD: Use the microservices architecture to limit the impact scope of regulatory
  changes on the user-side responsibility area (e.g., a regulatory change about card
  information processing can be addressed by updating only the relevant Authorization
  part).
- SHOULD: Implement comprehensive tokenization, encryption, access control, and audit
  logging of card information on the user-side responsibility area to comply with PCI
  DSS and other financial regulations.
- SHOULD: Use AWS Config, CloudTrail, and Security Hub for compliance monitoring to
  enable continuous monitoring of regulatory requirements and rapid response.

### Key Components

#### Auth Gateway / Auth Decisioning (Computing)

- **Component Overview**: Task groups placed by purpose on Amazon ECS (deployed
  multi-AZ within a VPC). "Auth Gateway" receives external approval requests and "Auth
  Decisioning" executes approval processing. Amazon MSK queues data between functions
  to achieve loose coupling. Amazon EKS may be selected instead of ECS to match
  requirements.
- **Assumed AWS Services**: Amazon ECS (or Amazon EKS), Amazon MSK, Amazon VPC.

#### Account Data Store (DynamoDB)

- **Component Overview**: Stores and processes card-transaction account information
  (balance / transaction data). NoSQL performance characteristics meet the low-latency,
  high-throughput requirements. Request hedging is applied as a tail-latency
  countermeasure. Cross-region synchronization uses DynamoDB Global Tables.
- **Assumed AWS Services**: Amazon DynamoDB, DynamoDB Global Tables, DynamoDB Streams.

#### Business Rule Store (Aurora)

- **Component Overview**: Manages per-customer business rules such as card limit amount
  and allowed PIN error count. RDB characteristics support complex conditional
  reference, search, and aggregation. Redundant via a quorum configuration (storage
  across 3 AZs with 6 copies) as a service specification, with instances built
  multi-AZ; cross-region synchronization uses Aurora Global Database.
- **Assumed AWS Services**: Amazon Aurora, Aurora Global Database.

#### Tokenization (ElastiCache for Valkey)

- **Component Overview**: Tokenizes card numbers, authentication codes, etc., before
  sharing data with merchants and payment agents, addressing security / PCI DSS
  requirements. The in-memory database processes tokenization at microsecond-level low
  latency. Deployed multi-AZ.
- **Assumed AWS Services**: Amazon ElastiCache for Valkey.

#### File Integration for Reconciliation (EMR + Transfer Family)

- **Component Overview**: Runs the Reconciliation batch (matching clearing files
  against approved data) on Amazon EMR, exports the result to S3, and transfers it to
  on-premises over SFTP via AWS Transfer Family. Authorization is relayed to
  on-premises in real time, while Reconciliation confirms in batch that there are no
  differences or mismatches in transaction detail data.
- **Assumed AWS Services**: Amazon EMR, Amazon S3, AWS Transfer Family (SFTP).

#### Data Archive & Recovery Support

- **Component Overview**: Handles data-loss cases caused by replication lag during
  failure recovery. DynamoDB Streams archives write events to S3 via Kinesis Data
  Firehose; application processing-result logs are forwarded to S3 and inspected with
  Athena during regional recovery.
- **Assumed AWS Services**: DynamoDB Streams, Amazon Kinesis Data Firehose, Amazon S3,
  Amazon Athena.

#### Network Connectivity

- **Component Overview**: Redundant on-premises-to-AWS connectivity using
  multi-location Direct Connect + Direct Connect Gateway + Transit Gateway. Connection
  to the international card brand networks is maintained on the on-premises side.
  On-premises communication uses Route 53 name resolution.
- **Assumed AWS Services**: AWS Direct Connect, Direct Connect Gateway, AWS Transit
  Gateway, Amazon Route 53.

#### Regional Failover Control

- **Component Overview**: Provides reliable switchover on regional failure via AWS
  Application Recovery Controller routing control.
- **Assumed AWS Services**: AWS Application Recovery Controller (ARC).

#### Compliance Monitoring

- **Component Overview**: Continuously monitors regulatory / PCI DSS-related compliance
  posture and enables rapid response to regulatory changes.
- **Assumed AWS Services**: AWS Config, AWS CloudTrail, AWS Security Hub.

## FISC Compliance Summary

No dedicated FISC mapping file (fisc-mapping) is provided for this case study, so no
per-standard mapping table exists. The source document does not contain a
standard-by-standard FISC mapping.

The regulatory points present in the source are limited to PCI DSS and general
financial-regulation handling, summarized as follows:

- For each AWS managed service, the AWS responsibility area is covered by AWS against
  PCI DSS standards, reducing the user-side burden even when regulations change.
- On the user-side responsibility area, the microservices architecture limits the
  impact scope of regulatory changes (e.g., a card-information-processing regulatory
  change can be handled by updating only the relevant Authorization part).
- Card information is protected by comprehensive tokenization, encryption, access
  control, and audit logging to comply with PCI DSS and other financial regulations.
- AWS Config, CloudTrail, and Security Hub provide compliance monitoring for continuous
  monitoring and rapid response.

## Reference Architecture

The architecture builds Authorization and Reconciliation on AWS as microservices, keeps
Settlement on-premises, and adopts multi-AZ + multi-region Active-Active for high
availability. Databases are selected per workload (DynamoDB for account data, Aurora
for business rules, ElastiCache for Valkey for tokenization), and request hedging is
used to address DynamoDB tail latency.

![Overview](assets/images/overview.png)

For the full technical detail (multi-AZ / multi-region design, cross-region data
synchronization and recovery, network, computing, database selection and request
hedging, and file integration), see [references/architecture.md](references/architecture.md).

## CDK Sample Overview

No CDK sample is provided for this case study.
