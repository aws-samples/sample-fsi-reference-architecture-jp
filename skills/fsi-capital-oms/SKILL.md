---
name: fsi-capital-oms
description: >-
  Case study of a cloud-native Order Management System (OMS) for capital markets / securities firms
  (資本市場 OMS, オーダー管理システム, 証券会社 受発注), based on real domestic and overseas brokerage OMS
  architectures. It shows how to balance the latency / scalability / high-availability trilemma by
  separating "order receipt & fill" from "order placement & execution" and connecting them with a
  low-latency messaging tier (Amazon ElastiCache for Redis / Redis Streams), plus AWS Outposts for
  exchange-proximity execution and AWS Auto Zone Shift for AZ failover. Use this skill when designing
  or reviewing an OMS / EMS / low-latency trading platform on AWS for a securities firm (証券取引システム,
  トレードライフサイクル, 低レイテンシー, 取引所連携), or when the user references BLEA for FSI capital-oms.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI Capital Market OMS (資本市場 OMS)

## Workload Overview

This is a **case study** (not a deployable reference implementation) describing a cloud-native
architecture for a securities firm's **Order Management System (OMS)** — the core system that
sits in the **front-to-middle** layer of a brokerage's system landscape. The design is modeled on
real OMS architectures currently running in domestic and overseas securities firms, and is shaped to
meet the latency and availability requirements those firms demand.

**Scenario.** The OMS accepts orders from retail investors, institutional investors, and traders,
manages fills, and places orders to exchanges. It also delivers real-time market information
(price movements, quotes) received from information vendors to investors. During trading hours the
front-to-middle system performs real-time processing of customer orders and provisional
add/subtract of positions, balances, and buying power. A separate **back-office system** — outside
this OMS scope — receives and processes final settlement data from exchanges and clearing houses
after the market closes, computes confirmed values, and transfers that confirmed data to the
front-to-middle system via **overnight batch** so it can be refreshed before the next business day.

**Purpose and significance.** Brokerage OMSs face a **trilemma of latency, scalability, and high
availability**. Historically each firm developed its own OMS and maintained it on-premises for a
long time; large systems still commonly run on mainframes. The purpose of this reference
architecture is to provide guidance for a cloud-native OMS that achieves the optimal balance across
that trilemma according to each firm's diversifying needs.

**Business drivers / challenges.** Recent sharp growth in trading volume drives expectations for
cloud adoption to enable flexible capacity adjustment and cost optimization of the
order-receipt/placement system. Three challenges are called out:

- **Latency requirement.** To minimize price slippage between order acceptance and execution and to
  raise the probability of filling at the best quote, extremely low latency is required. Firms
  traditionally used exchange colocation services or same-datacenter placement, but as products and
  investor services diversify, uniformly spending large cost to prioritize latency above all else no
  longer always has the best return on investment.
- **Scalability.** Continuously increasing trading volume and unpredictable sharp peaks during market
  events widen the gap between required capacity at peak versus normal times, making the cost of
  securing peak-handling resources a challenge.
- **High availability.** As securities trading grows in importance as social infrastructure, the
  availability requirement for the OMS — the center of the trade lifecycle — is becoming ever more
  stringent.

**Real cloud-native OMS references cited by the case study:** Vanguard critical trading platform;
Fidelity Asset Management's Equity Trading Platform; Santander trading platform. (Public case links
are collected in `references/architecture.md`.)

For an architecture that runs the EMS (Execution Management System) together on AWS Outposts, the
case study points to the BLEA for FSI **Hybrid** securities-trading system reference architecture.

## Best Practices and Key Components

### Best Practices

- MUST: Separate the "order receipt & fill" (受注・約定) processing from the "order placement &
  execution result" (発注・出来) processing, and connect the two through an asynchronous messaging
  tier — this decoupling lets each layer scale independently, keeps consistency within each layer,
  and lets firms swap the messaging backbone to fit their needs.
- SHOULD: Place the "order placement & execution result" processing close to the EMS (Execution
  Management System) that routes orders to exchanges, to minimize exchange-communication latency.
- PREFER: When extremely low latency is required, disable cross-AZ communication and complete all
  processing within a single AZ using an AZ-level Active/Standby architecture; when the latency
  requirement is relaxed, the same architecture can be configured as a cross-AZ Active/Active
  multi-AZ deployment.
- SHOULD: Enable AWS Auto Zone Shift so that when an AZ fails, traffic is automatically shifted away
  from the affected AZ — it is recommended for both the Active/Standby (cross-AZ disabled) and the
  Active/Active (cross-AZ allowed) configurations to quickly detach a failing AZ.
- MUST: For services not directly supported by Auto Zone Shift (as of 2025/08, Amazon ECS and Amazon
  ElastiCache for Redis), implement custom failover using an Auto Zone Shift start-event notification
  delivered via Amazon EventBridge and orchestrated with AWS Step Functions and AWS Lambda.
- SHOULD: Combine reactive load-based autoscaling with scheduled scaling — e.g. predict opening-auction
  order volume and scale out before the market opens — because the reaction speed of load-based
  scaling alone is a limitation against sudden bursts.
- SHOULD: For OMS-to-back-office data linkage (positions/balances, customer master, credit info,
  fee/tax calculation results), use managed services — Amazon S3 as the data-exchange relay point,
  AWS Step Functions for workflow control, and AWS Lambda for execution — to gain scalability and
  reduce operational load in the overnight batch (ingest, consistency verification, refresh).
- PREFER: For mission-critical DR, adopt a multi-region configuration; use Aurora cross-region
  replication to avoid data loss, but note messaging-tier data needs separate loss-pattern protection.
- SHOULD: Plan the DR switchover as a deliberate, largely manual process (re-establishing exchange
  connectivity, verifying back-office data consistency), reserving a realistic window of several hours
  to about one business day and choosing timing that minimizes business impact.
- MAY: Consider AWS Outposts placed near the exchange or in a colocation center to minimize
  FIX-protocol communication delay to the exchange; a single Outposts is the base configuration, and
  multiple Outposts can be considered for higher availability at the cost of added data-consistency
  work.
- MUST NOT: Assume the Auto-Zone-Shift custom-failover implementation for out-of-scope services will
  work during an AWS control-plane outage — it depends on the AWS control plane and may not function
  then.
- WILL: The architecture uses containerized microservices on Amazon ECS because the front (order
  receipt) and execution/exchange-facing processing have different load characteristics and different
  business-logic change frequencies.
- WILL: The loosely-coupled, messaging-connected component design lets the messaging backbone be
  chosen or swapped flexibly — Amazon MSK when long message retention or many consumer groups are
  needed, or Amazon SQS when ordering matters less and simple queueing suffices.

### Key Components

#### Order Receipt & Fill (Front) Microservice

- **Component Overview**: Accepts orders from retail investors, institutional investors, and traders,
  and manages fills. Runs as a container-based microservice because its load characteristics and
  business-logic change frequency differ from the execution side; it can scale independently.
- **Assumed AWS Services**: Amazon Elastic Container Service (ECS)

#### Order Placement & Execution-Result (Execution) Microservice

- **Component Overview**: Handles order placement to and execution results from exchanges, positioned
  logically close to the EMS to minimize exchange-communication latency. Can be relocated onto AWS
  Outposts near the exchange for the lowest latency. Scales independently from the front layer.
- **Assumed AWS Services**: Amazon Elastic Container Service (ECS); optionally AWS Outposts

#### Low-Latency Messaging Backbone

- **Component Overview**: Asynchronous messaging tier connecting the "order receipt & fill" and
  "order placement & execution result" layers. Uses in-memory Redis Streams for high-speed, low-latency
  processing with simple operations. The component is swappable: MSK for long retention / many
  consumer groups, or SQS for simple queueing where ordering is less important.
- **Assumed AWS Services**: Amazon ElastiCache for Redis (Redis Streams); alternatives Amazon MSK,
  Amazon SQS

#### Primary Relational Database

- **Component Overview**: Main relational database for OMS data. Supports cross-AZ replication for
  data durability during an AZ failure, and cross-region replication for DR.
- **Assumed AWS Services**: Amazon Aurora

#### Market Data Distribution

- **Component Overview**: Receives market information (price movements, quotes) from information
  vendors and distributes it to investor clients in real time over WebSocket.
- **Assumed AWS Services**: WebSocket-based real-time distribution (delivered from the OMS application tier)

#### Back-Office Data Linkage / Overnight Batch

- **Component Overview**: Daily linkage with the securities back-office system to refresh OMS data
  with confirmed customer positions/balances, customer master, credit information, and fee/tax
  results. Uses S3 as the data-exchange relay point, Step Functions for workflow control, and Lambda
  for execution (ingest, consistency verification, refresh).
- **Assumed AWS Services**: Amazon S3, AWS Step Functions, AWS Lambda

#### AZ Failover Orchestration

- **Component Overview**: Provides automatic AZ failover. AWS Auto Zone Shift evacuates traffic from a
  failed AZ. For services not directly supported (Amazon ECS, ElastiCache for Redis, as of 2025/08),
  a custom failover is driven by an Auto Zone Shift start event via EventBridge, orchestrated by Step
  Functions and Lambda.
- **Assumed AWS Services**: AWS Auto Zone Shift, Amazon EventBridge, AWS Step Functions, AWS Lambda

#### Exchange Connectivity

- **Component Overview**: Network connection point to exchanges, assumed to be located in the
  on-premises environment; communicates with exchanges via the FIX protocol. Placing the execution
  side on AWS Outposts near the exchange minimizes this network delay.
- **Assumed AWS Services**: On-premises network connection point; AWS Outposts (for proximity)

## FISC Compliance Summary

There is **no dedicated FISC mapping file** for this case study, and the source case-study document
does not contain a FISC safety-standards mapping or explicit FISC control references. Accordingly, no
FISC/regulatory control mapping is reproduced here (none is fabricated).

The regulatory-relevant points that *are* present in the source are business/operational
resilience characteristics rather than FISC control mappings: securities trading is treated as
important social infrastructure with increasingly stringent availability requirements; the design
therefore emphasizes AZ-fault tolerance (Auto Zone Shift plus custom failover), data durability
(Aurora cross-AZ replication and synchronous writes to multiple ElastiCache for Redis clusters), and
mission-critical DR via multi-region configuration with a deliberate, largely manual switchover
window of several hours to about one business day.

## Reference Architecture

The full architecture description — base architecture, the latency-minimized multi-AZ
(Active/Standby, cross-AZ disabled) configuration, the AWS Outposts configuration, the DR
configuration, and the FAQ (latency figures, messaging choice, data durability, burst handling) —
is preserved in **`references/architecture.md`**, along with the architecture diagrams and the
public reference links.

Architecture diagrams (in `assets/images/`):

- Reference architecture: `assets/images/reference-architecture.png`
- Latency-minimized multi-AZ configuration: `assets/images/multiaz-architecture.png`
- AWS Outposts configuration: `assets/images/outposts-architecture.png`

## CDK Sample Overview

No CDK sample is provided for this case study.
