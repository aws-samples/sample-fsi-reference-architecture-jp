---
name: fsi-foundation-hybrid-cloud
description: >-
  Reference architecture for hybrid financial workloads (ハイブリッド, オンプレミス連携)
  built on AWS Outposts in the "BLEA for FSI" v1.6 program. Use when designing or
  reviewing workloads that combine AWS cloud and on-premises / customer data centers
  via Outposts — e.g. low-latency securities trading systems (証券取引システム),
  mainframe peripheral / integration systems (メインフレーム周辺システム), data residency
  (データレジデンシー) requirements, or low-latency access to on-premises databases,
  and their FISC (金融情報システムセンター 安全対策基準) compliance considerations.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI Hybrid (AWS Outposts) Reference Architecture

## Workload Overview

This skill covers the **Hybrid (ハイブリッド)** reference architecture from the
"金融リファレンスアーキテクチャ日本版 / BLEA for FSI" v1.6 program. It targets workloads
that **combine AWS cloud and on-premises**, and specifically documents reference
architectures built on **AWS Outposts**.

A key premise is the **shared responsibility model for Outposts**, which differs from
the AWS Region model: the **physical security, power, network, and capacity management
of the customer data center where the Outpost is installed are the customer's
responsibility**. See the AWS whitepaper "AWS Outposts high availability design and
architecture considerations" for details.

Important Outposts terminology used throughout (all defined in the same whitepaper):

- **AWS Outposts** — a fully managed service that delivers the same AWS infrastructure,
  AWS services, APIs, and tools to virtually any data center, colocation space, or
  on-premises facility, providing a truly consistent hybrid experience.
- **Outpost (logical Outpost)** — an environment that manages the physically connected
  AWS Outposts racks as a single logical entity, deploying a pool of AWS compute,
  storage, and networking at the customer site.
- **Parent Region** — the AWS Region that provides the management, control-plane services,
  and Region-level AWS services required to deploy the Outpost.
- **Anchor Availability Zone (Anchor AZ)** — the Availability Zone in the parent Region
  that hosts the Outpost's anchor point; the Outpost functions as an extension of the
  anchor AZ.
- **Anchor point** — the endpoint in the anchor AZ that receives connections from the
  remotely deployed Outposts.
- **Service link** — the set of encrypted VPN tunnels that connect the Outpost to the
  anchor AZ of the parent Region.
- **Local Gateway (LGW)** — the logical interconnect virtual router that enables
  communication between the Outpost and the on-premises network.

This asset presents four representative use cases: a low-latency **securities trading
system**, a **mainframe peripheral system**, **data residency** enforcement, and
**low-latency access to on-premises databases**. Detailed technical descriptions of each,
plus the physical network layer between Outposts and AWS, are in
[references/architecture.md](references/architecture.md).

## Best Practices and Key Components

### Best Practices

- MUST: Provision the on-premises network to give each Outpost rack redundant network
  connectivity and reliable connectivity to the anchor point in the AWS cloud, because
  a resilient connection to the anchor AZ is essential for the logical Outpost's
  management, monitoring, and service operations to work correctly.
- SHOULD: Use multiple AWS Direct Connect connections across multiple Direct Connect
  locations to make the connection to the AWS Region resilient.
- SHOULD: Provide a backup for the AWS Direct Connect link between Outposts and AWS, such
  as AWS Direct Connect at a separate location or an AWS Site-to-Site VPN connection.
- SHOULD: Run functions with low-latency requirements (multicast, high-speed program
  execution) on EC2 instances, and run functions without low-latency requirements as
  Amazon ECS tasks on containers for resource-efficient operation.
- SHOULD: Place a securities trading system's execution management system (EMS) and order
  management system (OMS) — which require high-speed communication with the exchange — on
  Outposts racks equipped with AWS Outposts bmn-sf2e instances, operated in a data center
  near the securities exchange to enable high-speed trading.
- SHOULD: Take advantage of AWS cloud scalability for front ends and for databases that
  do not require low-latency access.
- SHOULD: Adopt an Outposts multi-AZ configuration for mainframe peripheral systems that
  require high availability.
- SHOULD: Create a dedicated VPC for the Outposts subnet and separate it from the AWS
  Region to clearly govern a VPC that is closed to the Outpost when data residency is
  required.
- SHOULD: Store Amazon EBS local snapshots on Outposts to S3 on Outposts so that snapshot
  data is isolated from the AWS Region and kept closed to the Outpost.
- SHOULD: Store snapshots of single-AZ RDS on Outposts instances to S3 on Outposts so that
  snapshot data is isolated from the AWS Region and kept closed to the Outpost.
- SHOULD: Apply Service Control Policies (SCPs) to deny data transfer/copy to the AWS
  Region and EC2 snapshot creation, in order to enforce data residency by separating the
  Outposts environment from the AWS Region (see architecture.md for the concrete SCP JSON).
- SHOULD: Place the backend instances and the database in the same data center so that the
  database can be accessed with low latency when a database cannot be migrated off premises.
- SHOULD: Take an active/standby configuration across multiple AZs, or configure across
  multiple AZs / Outposts racks, to achieve high availability.
- SHOULD: Set up spares for the customer network devices that communicate with Outposts.
- SHOULD: Install Outposts in multiple data centers for higher availability.
- MUST: Operate a firewall and take appropriate measures on the customer side in the
  on-premises environment.
- MUST: Perform the physical security and control of the customer data center where the
  Outpost is installed on the customer's own responsibility.
- MAY: Perform the relay processing between the on-premises mainframe and the cloud data
  lake / OLAP on Outposts.
- MAY: Consider using AWS Fault Injection Service to reproduce failures during verification.
- WILL: A VPC created within the AWS account that ordered the Outposts is seamlessly
  extended to the Outposts.
- WILL: In the event of an AWS Region failure, the Outposts inside the customer data
  center continue to operate normally.

### Key Components

#### Outposts Rack with bmn-sf2e Instances (Securities Trading)

- **Component Overview**: Runs the mission-critical, low-latency securities trading system
  (EMS and OMS) on an Outposts rack located near the securities exchange. The bmn-sf2e
  (bare metal) instance supports bare-metal networking and Precision Time Protocol (PTP),
  runs on the AWS Nitro architecture, is equipped with an AMD Solarflare X2522 network
  card, and supports Layer 2 multicast. It processes market data delivered by multicast
  from the exchange or from financial-information vendors and distributes it to systems.
- **Assumed AWS Services**: AWS Outposts (bmn-sf2e instance), Amazon EC2, Amazon ECS,
  Amazon Aurora, Amazon ElastiCache.

#### Physical Network Layer between Outposts and AWS

- **Component Overview**: Provides the fault-tolerant physical connectivity that links the
  logical Outpost to its anchor AZ. Each Outpost rack is given redundant network
  connectivity; private connectivity to the AWS Region is provided over AWS Direct Connect,
  made resilient with multiple connections across multiple Direct Connect locations.
- **Assumed AWS Services**: AWS Direct Connect, AWS Site-to-Site VPN (as a backup link),
  Local Gateway (LGW), service link.

#### Mainframe Peripheral / Integration System

- **Component Overview**: A multi-AZ Outposts configuration for high availability. The
  front end takes advantage of AWS cloud scalability and is built in the AWS Region with an
  Application Load Balancer and EC2 instances; the backend is processed on Outposts to also
  leverage on-premises data such as the mainframe. Outposts can also perform the relay
  processing between the on-premises mainframe and the cloud data lake / OLAP.
- **Assumed AWS Services**: AWS Outposts, Application Load Balancer, Amazon EC2, plus AWS
  cloud data lake / OLAP services for the analytics variant.

#### Data Residency Enforcement (Outposts-closed VPC)

- **Component Overview**: Enforces data residency by creating a dedicated VPC for the
  Outposts subnet separated from the AWS Region, so data stays closed to the customer data
  center. Service Control Policies (SCPs) deny data transfer/copy to the Region and EC2
  snapshot creation. EBS local snapshots on Outposts and single-AZ RDS on Outposts
  snapshots are stored to S3 on Outposts to keep snapshot data isolated from the Region.
- **Assumed AWS Services**: AWS Outposts, Amazon VPC, AWS Organizations Service Control
  Policies (SCPs), Amazon EBS (local snapshots on Outposts), Amazon RDS on Outposts,
  Amazon S3 on Outposts.

#### Low-Latency Access to On-Premises Database

- **Component Overview**: For legacy workloads where the accumulation of network latency
  per transaction (e.g. batch processing) is critical, processing runs on Outposts placed
  in the same on-premises data center as the database. The front end is migrated to the
  AWS Region and the backend to Outposts, enabling low-latency access to the on-premises
  database that cannot be migrated.
- **Assumed AWS Services**: AWS Outposts, Amazon EC2 (backend instances), on-premises
  database (customer-managed).

## FISC Compliance Summary

This asset is mapped against the **FISC 安全対策基準 実務基準 (FISC Security Guidelines,
practical standards)** for AWS Outposts-based hybrid workloads. The mapping distinguishes
the controls provided by the common control environment (**governance base template**)
from the additional measures / considerations expected on the reference architecture and
user side.

Highlights include: IAM Identity Center for user protection and MFA; AWS Control Tower
guardrails; encryption via AWS KMS CMK; TLS for data-in-transit; CloudTrail and AWS Config
for audit trails; Amazon GuardDuty / Security Hub for detection; CloudWatch monitoring; and
Outposts-specific items such as customer responsibility for the data center physical
security, customer-side firewall operation in the on-premises environment, Direct Connect
redundancy, and continued Outposts operation during an AWS Region failure. Many process,
development, and application-layer controls are marked out of scope.

The complete, entry-by-entry FISC mapping table (実 1 through 実 149) is preserved in
[references/fisc-mapping.md](references/fisc-mapping.md).

## Reference Architecture

Full technical detail — the prerequisites and Outposts terminology, the physical network
layer between Outposts and AWS, the four use cases (securities trading system with its
step-by-step trade and market-data flows, mainframe peripheral system and its analytics
variant, data residency with the concrete SCP JSON policies, and low-latency on-premises
database access), the architecture diagrams, and the reference links — is provided in
[references/architecture.md](references/architecture.md).

## CDK Sample Overview

No CDK sample is provided for this asset in BLEA for FSI v1.6; this asset is documentation
only.
