---
name: fsi-capital-market-data
description: >-
  Reference architecture for a financial-institution market data (マーケットデータ)
  distribution system built on the "BLEA for FSI / 金融リファレンスアーキテクチャ日本版"
  baseline. The workload ingests, computes and distributes real-time market data
  (stock prices, FX rates, etc.) to internal and external clients over FIX, REST
  and WebSocket, using a three-tier Handler / Composer / Distributor design with
  Amazon Kinesis Data Streams for loose coupling. Use this skill when designing,
  explaining, deploying or FISC-mapping a market data feed / real-time data
  distribution workload on AWS (keywords: market data, マーケットデータ, market data
  distribution, Kinesis, FIX/REST/WebSocket, リアルタイム配信, データ配信).
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Market Data Reference Architecture (BLEA for FSI)

## Workload Overview

A financial institution's market data distribution system generates a wide
variety of market-related data and distributes it to internal and external
clients. The distributed data is typically calculated from data collected from
internal and external data providers. Communication with clients and providers
uses protocols such as FIX, REST, and WebSocket.

Market data is classified into three broad patterns based on how frequently the
data is generated and how fresh it must be by the time it reaches the client:

- **Real-time** — stock prices, FX rates, etc.; more than several thousand
  updates per minute; often latency-sensitive.
- **Near real-time** — market news, non-real-time price distribution, etc.;
  updated once every few minutes.
- **Batch** — interest-rate indices, corporate credit ratings, foreign-exchange
  published rates, etc.; updated once every several hours or more.

This reference architecture targets the **real-time** use case.

The architecture is built on top of the BLEA for FSI governance base (the shared
governance/security account foundation) and is deployed into a guest account.

## Best Practices and Key Components

### Best Practices

- MUST: Compose the system of three application tiers — Handler App, Composer
  App, and Distributor App — each with a distinct responsibility.
- MUST: Have the Handler App write received input data into Amazon Kinesis Data
  Streams as a producer; the protocol and authentication method depend on the
  interface defined by the provider.
- MUST: Have the Composer App calculate the distributed data by consuming the
  Streams provided by the Handler App (or by other Composers) as a consumer.
- MUST: Have the Distributor App consume the Stream provided by the Composer App
  and perform format conversion, distribution-frequency and granularity
  adjustment according to client requirements.
- SHOULD: Make the Distributor App provide the most recent known-good value as a
  fixed value when an upstream Composer App or its Stream becomes unavailable due
  to a failure.
- MUST: Route FIX consumers through an NLB to the Distributor App and perform
  authentication during the FIX Logon process.
- MUST: Route REST and WebSocket consumers through an ALB to the Distributor App;
  the ALB validates the HTTP Authorization header and routes between the
  authentication Lambda and the Distributor App.
- SHOULD: Select the network connectivity to providers and clients (Direct
  Connect, Internet, PrivateLink, etc.) according to requirements.
- MUST: Deploy each container application in the same configuration across
  Multiple AZs and run them Active-Active; present two active endpoints to
  clients and guide failover on failure.
- SHOULD: Adopt Streams for inter-component integration to keep components
  loosely coupled, so producers (Handler, Composer) need not be aware of the
  existence or location of downstream components and the number of consumers can
  vary easily.
- MAY: Extend this configuration by adding a new consumer (for example a new
  database for analytics) as an additional member of the consumer set.
- MUST: Encrypt data with AWS KMS and set appropriate access permissions on the
  encryption key; set appropriate IAM policies on the AWS resources that store
  data to prevent data leakage (FISC 実 3 / 実 30 / 実 69).
- MUST: Access each resource using temporary credentials obtained through IAM
  roles, following the principle of least privilege (FISC 実 9 / 実 25).
- MUST: Restrict communication protocols at the connection endpoints (Amazon ELB,
  Amazon API Gateway, etc.) to prevent unauthorized intrusion from external
  networks, and perform peer authentication on the application side (FISC 実 14 /
  実 15).
- SHOULD: Verify that container images and libraries are trusted at build time
  and run vulnerability scanning of containers in Amazon ECR (FISC 実 20 / 実 21
  / 実 32).
- SHOULD: Monitor compute resources, network bandwidth, ALB, Aurora, DynamoDB and
  Amazon ECS resources with Amazon CloudWatch, and enable VPC Flow Logs and ALB
  access logs (FISC 実 46 / 実 72).
- WILL: The Amazon Kinesis Data Stream stores data in physically isolated
  locations and retains data for up to 24 hours by default (up to 7 days maximum).
- SHOULD: Build a multi-region / multi-AZ configuration and use highly available
  AWS managed services for availability (FISC 実 85–実 88).
- SHOULD: For large-scale failures beyond AZ resilience, decide whether to wait
  for service recovery or switch to a secondary region, accounting for the time
  and cost of switching connection targets and creating resources on both the
  producer and consumer sides (FISC 実 71 / 実 73 / 実 74).
- MUST: Apply cdk-nag's AwsSolutionsChecks (via Aspects) to every CDK stack built from this skill, and gate CI (jest etc.) on zero unsuppressed AwsSolutions-* findings; suppress exceptions only with an explicit reason via NagSuppressions (see references/cdk-nag.md).

### Key Components

#### Handler App

- **Component Overview**: Receives the input that becomes the source of the
  distributed data. The protocol and authentication method depend on the
  interface defined by the provider. It writes the received data into a Kinesis
  Data Stream as a producer. In the CDK sample it is realized as an ECS on
  Fargate service (`sample_handler` container) plus a dedicated Kinesis Data
  Stream.
- **Assumed AWS Services**: Amazon ECS (AWS Fargate), Amazon Kinesis Data
  Streams, Amazon ECR.

#### Composer App

- **Component Overview**: Calculates the distributed data. In most cases the
  distributed data is calculated from upstream Market Data Provider data or
  internal reference data. It consumes the Stream provided by the Handler App as
  input, and may also consume Streams provided by other Composers (for example,
  Composer C computing GBPJPY may consume the Streams of Composer A computing
  GBPUSD and Composer B computing USDJPY). In the CDK sample it is an ECS on
  Fargate service (`sample_composer` container) with its own Kinesis Data Stream,
  and computed results can be stored in DynamoDB.
- **Assumed AWS Services**: Amazon ECS (AWS Fargate), Amazon Kinesis Data
  Streams, Amazon DynamoDB, Amazon ECR.

#### Distributor App

- **Component Overview**: Distributes data toward clients by consuming the Stream
  provided by the Composer App. It performs format conversion and adjusts
  distribution frequency and granularity per client requirements, and provides
  the most recent known-good value as a fixed value when the upstream Composer or
  its Stream is unavailable. FIX consumers connect via an NLB; REST/WebSocket
  consumers connect via an ALB that validates the HTTP Authorization header. In
  the CDK sample it is an ECS on Fargate service (`sample_distributor` container)
  fronted by an ALB with AWS WAF and ALB access logging enabled.
- **Assumed AWS Services**: Amazon ECS (AWS Fargate), Elastic Load Balancing
  (Application Load Balancer / Network Load Balancer), AWS WAF, AWS Lambda
  (authentication), Amazon ECR.

#### Data Store

- **Component Overview**: Stores computed / composed market data. In the CDK
  sample this is an Amazon DynamoDB table with customer-managed KMS encryption, a
  local secondary index, and a CloudWatch alarm on consumed read capacity.
- **Assumed AWS Services**: Amazon DynamoDB, AWS KMS.

#### Encryption Key Management

- **Component Overview**: A customer-managed KMS key (CMK) used to encrypt the
  Kinesis Data Streams, DynamoDB table, CloudWatch Logs, and the SNS monitoring
  topic.
- **Assumed AWS Services**: AWS KMS.

#### Monitoring and Notification

- **Component Overview**: Monitors the guest system and sends notifications. In
  the CDK sample an SNS topic (with an email subscription and TLS-enforced
  publish policy) receives CloudWatch alarms; CloudWatch Container Insights is
  enabled on the ECS clusters.
- **Assumed AWS Services**: Amazon CloudWatch, Amazon SNS.

#### Networking

- **Component Overview**: A public VPC spanning Multiple AZs with private subnets,
  VPC Flow Logs, and VPC endpoints for CloudWatch Logs, DynamoDB, ECR, ECR Docker
  and S3 Gateway. Connectivity to providers and clients uses Direct Connect,
  Internet, or PrivateLink as required.
- **Assumed AWS Services**: Amazon VPC, VPC Endpoints, AWS Direct Connect / AWS
  PrivateLink (as required).

#### Container Image Build Pipeline

- **Component Overview**: Builds the sample container images and pushes them to
  ECR. In the CDK sample a CodeBuild project builds the image from the
  `sample-ecs-app` assets (Dockerfile + buildspec) and is triggered via a custom
  resource at deploy time.
- **Assumed AWS Services**: AWS CodeBuild, Amazon ECR, Amazon S3.

## FISC Compliance Summary

The workload is mapped against the FISC Security Guidelines (第 11 版) practice
standards (実務基準). The mapping distinguishes three columns: the common control
environment (governance-base template), the financial workload template (Market
Data), and examples of additional user-side measures. Because this is not a
service that performs financial transactions and does not send data to
auto-answering terminals or exchange files via storage media, a large number of
standards are marked out-of-scope (対象外) for those reasons.

Key workload-side measures include: AWS KMS encryption with appropriate key
access control (実 3, 実 13, 実 30, 実 69); least-privilege IAM with temporary
credentials (実 9, 実 25); protocol restriction at connection endpoints and
peer authentication (実 14, 実 15); container image trust and ECR vulnerability
scanning (実 20, 実 21, 実 32); GuardDuty anomaly detection (実 22); CloudWatch /
VPC Flow Logs / ALB access log monitoring (実 46, 実 72, 実 101–実 103); Kinesis
Data Streams data retention and CDK/IaC backup (実 39); multi-region / multi-AZ
availability (実 85–実 88); and secondary-region switchover considerations for
large-scale failures (実 71, 実 73, 実 74, 実 84, 実 104, 実 106).

For the complete per-standard mapping table (実 1 through 実 148), see
[references/fisc-mapping.md](references/fisc-mapping.md).

## Reference Architecture

The architecture is composed of three tiers — Handler App, Composer App, and
Distributor App — connected by Amazon Kinesis Data Streams to achieve loose
coupling. Each container application is deployed in the same configuration
across Multiple AZs and runs Active-Active.

![Architecture](assets/images/marketdata-arch.png)

For the full technical detail (tier responsibilities, protocol handling,
inter-component streaming, and the "other points" on availability and
extensibility), see [references/architecture.md](references/architecture.md).

## CDK Sample Overview

A deployable AWS CDK (TypeScript) sample is provided under
[assets/sample-cdk/](assets/sample-cdk/). The sample stack
(`GuestMarketDataStack`, project prefix `BLEAFSI-MarketData`) provisions:

> **Sample app security notice**: this sample is a reference/functional demo, not
> production-ready. It deliberately leaves authentication, TLS, and per-subscriber
> entitlement to the implementer: the Distributor ALB is plain HTTP with
> `open:true`, no authentication Lambda is wired, all tiers share one wildcarded
> Kinesis task role, and the container base image is unpinned. Because false or
> stale prices can drive erroneous trades, add authentication, TLS, entitlement,
> least-privilege roles, and image pinning before using real feeds. The same
> notice ships as `assets/sample-cdk/SECURITY_NOTICE.md` and is printed as a
> warning on every `cdk synth` / `cdk deploy`.

- A customer-managed KMS key (`AppKey`).
- An SNS-based monitoring alarm topic with an email subscription.
- A public VPC (Multi-AZ, VPC Flow Logs, VPC endpoints).
- An ECR repository.
- Handler, Composer and Distributor apps as ECS on Fargate services
  (`desiredCount: 2`, Container Insights enabled), each built from the
  `sample-ecs-app` image via a CodeBuild-based `ImageBuilder`.
- Two Kinesis Data Streams (Handler Stream, Composer Stream), both KMS-encrypted.
- A DynamoDB table for composed data (customer-managed encryption, LSI,
  CloudWatch alarm).
- An ALB (with AWS WAF and access logging) fronting the Distributor app.

It defines Dev / Staging / Prod parameter sets in `bin/parameter.ts`. Deploy the
development stack with `npx cdk deploy BLEAFSI-MarketData-Dev`.

For deployment prerequisites and step-by-step instructions, see
[references/deployment.md](references/deployment.md).

The copied `assets/sample-cdk/.../test/*.test.ts` is the authoritative source of
the cdk-nag enforcement pattern for this workload; see
[references/cdk-nag.md](references/cdk-nag.md) for the extracted suppression
ledger and the reusable enforcement test template.
