---
name: fsi-foundation-mainframe-integration
description: >-
  Reference architecture guidance for integrating on-premises mainframes with AWS in Japanese
  financial institutions (BLEA for FSI / 金融リファレンスアーキテクチャ日本版). Covers three
  data-integration patterns between a mainframe and AWS: data replication (AWS Mainframe
  Modernization Data Replication with Precisely), asynchronous messaging (IBM MQ HA / MQ
  cluster / multi-instance queue managers), and file transfer (HULFT, AWS Transfer Family).
  Use this skill when designing or reviewing mainframe-to-AWS data integration, discussing
  メインフレーム連携 / メインフレーム / データレプリケーション / 非同期メッセージング / ファイル転送 /
  IBM MQ / HULFT / Precisely, or mapping such workloads to the FISC Security Guidelines.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Mainframe Integration (メインフレーム連携)

## Workload Overview

This asset is the "Mainframe Integration (メインフレーム連携)" reference architecture from
BLEA for FSI (金融リファレンスアーキテクチャ日本版) v1.6. In this reference architecture, a
"mainframe" means a large computer that carries a processor with a proprietary instruction
set and runs core (基幹系) business systems processing large volumes of business data on a
proprietary OS. Example mainframe OSes include IBM z/OS, Fujitsu OS IV/MSP, Hitachi VOS3,
and NEC ACOS-4.

The scope of this asset is **data integration between a mainframe and AWS** — it does not
cover the mainframe's internal application logic. It presents three integration patterns:

1. **Data Replication** — replicate mainframe data to AWS to promote data utilization and
   development of new services (analytics/AI/ML, near-real-time business innovation, and
   seamless application migration with near-zero downtime).
2. **Asynchronous Messaging** — exchange data between mainframe systems and AWS-hosted
   systems through a simple API without direct synchronous coupling, using IBM MQ.
3. **File Transfer** — transfer files between the mainframe and AWS for external-system
   linkage, analytics/AI/ML, backup/archive, and data migration during cloud
   modernization.

> AWS does not support or guarantee the operation of the third-party software products
> referenced here. Confirm prerequisites and details with each product's vendor. In
> particular, AWS Mainframe Modernization Data Replication with Precisely only supports
> IBM z/OS and IBM i (AS/400) as replication source environments.

Detailed technical descriptions of all three patterns (basic operation, failover behavior,
monitoring, characteristics, and variations) are in
[references/architecture.md](references/architecture.md).

## Best Practices and Key Components

### Best Practices

- MUST NOT: Rely solely on a mainframe-side queue manager accessed by many AWS-side MQ
  clients; concentrated client access can overload the mainframe, and if the mainframe
  queue manager goes down, MQ clients fail and applications error out.
- SHOULD: Stand up a queue manager on both the mainframe side and the AWS side and
  establish channel connections between them, so a local queue manager keeps accepting
  messages even when the destination queue manager is down.
- MUST NOT: Use the MQ cluster (active/active) pattern when message ordering must be
  preserved (e.g., financial transactions), because ordering is not maintained across the
  cluster.
- SHOULD: Combine the MQ cluster pattern with the HA configuration when persistent
  messages held by a downed queue manager must be recovered quickly, since those messages
  are unavailable until that queue manager restarts.
- MAY: Consider running IBM MQ in containers for the MQ cluster pattern, since it does not
  assume clustering-software-based inter-instance synchronization.
- SHOULD: Avoid modifying mainframe applications or data; implement analytics and new
  services on the AWS side so the added development does not increase mainframe load.
- MAY: Use a COBOL copybook that defines the VSAM file layout as schema information and map
  the input data format to the target table with a Lambda function (Precisely pattern).
- SHOULD: For high availability of the Precisely components, run the z/OS-side Publisher
  agent in an active/standby configuration and run multiple EC2 instances in a Multi-AZ
  configuration on the AWS side feeding the Amazon MSK cluster.
- MAY: Add multiple workers (JVM processes running connector logic) to the Apply agent to
  increase throughput toward Amazon MSK as needed.
- SHOULD: Monitor the CloudWatch Logs and metrics of the Apply agent, MSK, and the
  database, and cross-reference them to identify where a problem occurs.
- SHOULD: For HULFT on AWS in an active/standby configuration, use HULFT-supported
  clustering software to synchronize data between the two instances.
- MAY: Use the HULFT Cloud Storage Option to directly read from and write to Amazon S3
  bucket objects.
- SHOULD: Store backup files in an Amazon S3 bucket to reduce cost versus keeping them on
  the mainframe; set cross-region replication for DR and choose an S3 storage class for
  long-term archival.
- MAY: When retry-on-error and per-item data/character-code conversion are not required,
  use ftp or sftp for file transfer (z/OS Communication Server FTP server with AWS
  Transfer Family, or z/OS OpenSSH for sftp).
- SHOULD: Provide, for the DR-side environment, the same integration architecture that was
  adopted for the primary, matching the DR-side mainframe (FISC 実 71 / 実 74 / 実 106).
- SHOULD: Provide a backup connection via AWS Direct Connect or AWS Site-to-Site VPN as a
  standby for the primary AWS Direct Connect link between the mainframe and AWS (FISC 実 87).
- WILL: The HA configuration preserves message ordering across failover and has an RTO of
  a few minutes; the multi-instance queue manager configuration also preserves ordering
  with an RTO of 30 seconds to a few minutes and requires shared file storage.
- WILL: z/OS does not support the multi-instance queue manager configuration; it is only
  achievable on the AWS side.

### Key Components

#### Data Replication (Precisely)

- **Component Overview**: Replicates mainframe data (Db2 for z/OS, IMS/DB, VSAM on z/OS;
  Db2 for IBM i on IBM i) to AWS data stores. A Log Reader captures the Db2 log to a
  Coupling Facility (CF)-based Log Stream; a primary Publisher agent on an LPAR reads the
  log and publishes it to Apply agents on AWS; the active Apply agent writes to Amazon MSK,
  which updates the AWS data store. Publisher agents run active/standby on z/OS; Apply
  agents run active/active on AWS with a controller daemon handling failover.
- **Assumed AWS Services**: AWS Mainframe Modernization Data Replication with Precisely,
  Amazon Managed Streaming for Apache Kafka (MSK), Amazon RDS (Oracle / Microsoft SQL
  Server / PostgreSQL / Amazon Aurora PostgreSQL) or DB on EC2, Amazon S3, AWS Lambda,
  Amazon EC2, Amazon CloudWatch (Logs and metrics).

#### Asynchronous Messaging (IBM MQ)

- **Component Overview**: Point-to-Point and publish/subscribe messaging with ACID
  transaction guarantees using IBM MQ. Queue managers on the mainframe and AWS sides are
  connected by channels; either side can originate messages, and a correlation ID enables
  request/response correlation. Three high-availability queue-manager patterns are
  provided: (2.1) HA configuration (active/standby), (2.2) MQ cluster (active/active), and
  (2.3) multi-instance queue managers (active/warm-standby).
- **Assumed AWS Services**: IBM MQ on Amazon EC2 (or containers on Amazon ECS / Amazon
  EKS), Amazon Elastic File System (EFS) or Amazon FSx for Windows File Server (shared
  storage for the multi-instance pattern), Amazon CloudWatch.

#### File Transfer (HULFT / AWS Transfer Family)

- **Component Overview**: Transfers files between the mainframe and AWS. HULFT between
  HULFT for z/OS and HULFT on AWS supports binary (no-conversion) transfer, text transfer
  with character-code conversion between platforms, and per-item data-type conversion for
  fixed-length layouts; pre-send, post-send, and post-receive jobs can be registered. The
  HULFT Cloud Storage Option enables direct I/O to Amazon S3 objects. As a variation, ftp
  (via AWS Transfer Family) or sftp can be used when retry/conversion features are not
  needed.
- **Assumed AWS Services**: HULFT on Amazon EC2 (with HULFT-supported clustering software
  for HA), Amazon S3 (including cross-region replication and archival storage classes),
  AWS Transfer Family, Amazon CloudWatch, Amazon ECS / Amazon EKS / Amazon EC2.

## FISC Compliance Summary

This asset is mapped against the FISC Security Guidelines (FISC 安全対策基準) 実務基準
(Practical Standards, 9th edition context in the source table titled 第 12 版) items 実 1
through 実 149. The mapping table records, per item, both the shared control environment
(governance-base template) countermeasure and the additional countermeasures/considerations
for each of the three patterns (Data Replication / Asynchronous Messaging / File Transfer).
Only 実務基準 items are covered; overall system safety must additionally be considered on the
user-application side and in operational/development processes. Many items are marked
対象外 (out of scope) because they belong to the business application, management/operation
process, development process, or are already handled on the AWS cloud side. Representative
in-scope countermeasures include TLS encryption of communications (実 4/実 7/実 69), IAM
Access Analyzer for unused permissions (実 5), least-privilege IAM (実 25), KMS key
rotation/separation of duties (実 13/実 30), Amazon Inspector and security groups (実 20),
CloudWatch monitoring (実 46/実 47/実 101–実 103), Multi-AZ active/standby availability
(実 71/実 84/実 104), and DR via Osaka region and Direct Connect/VPN backup (実 74/実 87/実 106).

The full, per-item table (preserving every entry) is in
[references/fisc-mapping.md](references/fisc-mapping.md).

## Reference Architecture

The full reference architecture — including the three patterns' architecture diagrams,
step-by-step basic operation, failover behavior, monitoring, characteristics, variations,
and source reference links — is in [references/architecture.md](references/architecture.md).
Architecture diagram images are in `assets/images/`.

## CDK Sample Overview

No CDK sample is provided for this asset in BLEA for FSI v1.6; this asset is documentation
only.
