---
name: fsi-banking-mobile
description: >-
  Reference architecture for a resilient, event-driven mobile / online banking
  workload (モバイルバンキング / オンラインバンキング) on AWS, built as three AWS CDK
  stacks (React SPA frontend, serverless microservices backend, mock core-banking
  API). Demonstrates account opening, balance inquiry, and fund transfer using
  Event Sourcing, Transaction Outbox, Saga, and CQRS patterns on Lambda, DynamoDB,
  API Gateway, EventBridge, and SQS, with FISC compliance mapping. Use this skill
  when designing, explaining, or deploying a microservices-based banking workload,
  or when the user asks about resilience patterns, eventual consistency, or the
  BLEA for FSI mobile-banking sample (金融リファレンスアーキテクチャ日本版).
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI Mobile Banking (Resilience - Modern Architecture)

## Workload Overview

This reference architecture models a **mobile / online banking application** and
was built to demonstrate the value of a microservices architecture from a
**resilience** perspective. It covers three core banking functions — **account
opening (口座開設)**, **balance inquiry (残高照会)**, and **fund transfer (振込)** —
and is intended as a general-purpose, highly available and scalable pattern that
applies to mission-critical systems beyond the financial sector.

The workload is delivered as three AWS CDK stacks:

- **OnlineBankingAppFrontendStack** — a React SPA served through Amazon S3,
  Amazon CloudFront, and AWS WAF.
- **OnlineBankingAppBackendStack** — a set of serverless microservices on AWS
  Lambda with Amazon DynamoDB as the main data store, fronted by Amazon API
  Gateway, and coordinated through Amazon EventBridge and Amazon SQS.
- **TemporaryCoreBankingSystemStack** — a mock ("temporary") core-banking API
  that stands in for an existing core-banking (勘定系) system (account, balance,
  transaction, and customer management).

Account opening and fund transfer are processed **asynchronously**: a request is
accepted, and state changes are recorded as events (an audit trail) using
**Event Sourcing**. To keep calls into the core-banking API consistent, a
**Transaction Outbox** is used, and retry logic is embedded inside the Lambda
functions. The sample was developed with Kiro and Amazon Q Developer, largely
through "vibe coding" from an architecture diagram.

The companion core-banking (勘定系) reference architecture also uses the Saga
pattern with compensating transactions; this mobile-banking sample intentionally
adopts a *different* set of distributed-system patterns to illustrate an
alternative approach. See `references/architecture.md` for full detail, the app
walkthrough, and multi-region considerations.

## Best Practices and Key Components

### Best Practices

- MUST: Encrypt all data stores with AWS KMS customer-managed keys — DynamoDB
  tables, Lambda environment variables, S3 buckets, and SQS queues all use a
  customer-managed key (FISC 実3 / 実13 / 実30).
- MUST: Enable automatic KMS key rotation and design the key policy for
  segregation of duties (separating the key administrator from the data owner).
- MUST: Enforce TLS 1.2 or higher at API Gateway and CloudFront, and require SSL
  on S3 buckets and SQS queues (`enforceSSL`).
- MUST: Enable DynamoDB Point-in-Time Recovery (PITR) on tables holding event
  and audit data (FISC 実6 / 実39).
- MUST: Guard the write path with the Transaction Outbox pattern so a database
  update and an event publication commit atomically, then relay the event to
  external systems from the outbox table.
- MUST: Record every state change as an immutable event in an event store
  (Event Sourcing) to satisfy strict audit-trail requirements for financial
  systems.
- MUST: Ensure idempotency for external (core-banking) API calls, since
  asynchronous retries and at-least-once delivery can reproduce a message.
- MUST: Manage the JWT signing secret in AWS Secrets Manager rather than in code
  or plaintext environment variables.
- MUST: Attach AWS WAF to API Gateway (rate-based rule plus AWS managed rule
  groups: Common, KnownBadInputs, Linux) and to CloudFront.
- SHOULD: Apply the principle of least privilege — give each Lambda function its
  own IAM role scoped to the specific tables, indexes, event bus, and keys it
  needs.
- SHOULD: Separate withdrawal and deposit into independent services so a failure
  in one is localized and does not affect the other.
- SHOULD: Attach a dead-letter queue (DLQ) with a bounded receive count
  (maxReceiveCount = 3) to each SQS queue so failed processing is retried and
  captured for investigation.
- SHOULD: Enforce API Gateway usage plans with per-key throttling and daily
  quotas, and require an API Key on each method.
- SHOULD: Enable API Gateway access logging, execution logging, X-Ray tracing,
  and CloudWatch metrics, and consolidate logs in CloudWatch Logs.
- SHOULD: Restrict the core-banking API to internal callers using IAM
  authorization plus an API Key and a resource policy scoped to the account and
  region.
- PREFER: Use CloudFront Origin Access Control (OAC) over the older Origin
  Access Identity (OAI) for S3 origins.
- PREFER: Use EventBridge as the integration backbone so additional asynchronous
  fan-out processing (e.g. AI-based identity-document review, risk scoring,
  human review, customer notification) can be added without changing existing
  services.
- MAY: For multi-region resilience without a custom domain, use a CloudFront
  Origin Group with S3 Cross-Region Replication to fail over between a primary
  and secondary region; for production with a custom domain, use Route 53
  Application Recovery Controller or a Standby-Takes-Over-Primary (STOP) design.
- MAY: Enable DynamoDB Global Tables with strong consistency to synchronize
  event state across regions, then re-drive stalled events after a region
  switch.
- MUST NOT: Assume real-time consistency — because processing is asynchronous
  and eventually consistent, add explicit handling when an operation needs an
  immediate confirmed state.
- WILL: A monolith stops the whole service when one component fails and must be
  scaled as a unit, whereas microservices keep other services running and can be
  scaled independently, localizing fault impact.
- WILL: In this sample the mail-delivery Lambda is a stub that only writes log
  output; real email/notification delivery is expected to call a separate
  external system.
- MUST: Apply cdk-nag's AwsSolutionsChecks (via Aspects) to every CDK stack built from this skill, and gate CI (jest etc.) on zero unsuppressed AwsSolutions-* findings; suppress exceptions only with an explicit reason via NagSuppressions (see references/cdk-nag.md).

### Key Components

#### Frontend Delivery (OnlineBankingAppFrontendStack)

- **Component Overview**: Hosts the React single-page application. Static content
  is stored in a private, versioned, KMS-encrypted S3 bucket and served through a
  CloudFront distribution (OAC, redirect-to-HTTPS, TLS 1.2+ minimum, Japan-only
  geo-restriction). Access logs go to a dedicated S3 log bucket; a CloudFront WAF
  Web ACL is created when deployed to us-east-1.
- **Assumed AWS Services**: Amazon S3, Amazon CloudFront, AWS WAF, AWS KMS, AWS
  Systems Manager Parameter Store.

#### API Layer (OnlineBankingAppBackendStack)

- **Component Overview**: A single Amazon API Gateway REST API ("Banking API")
  exposes customer, auth, admin, balance, and transfer endpoints. It uses a JWT
  Lambda token authorizer for protected routes, per-audience API Keys
  (customer / admin / auth) with usage plans, request validation, access/exec
  logging, and a regional WAF Web ACL.
- **Assumed AWS Services**: Amazon API Gateway, AWS Lambda (authorizer), AWS WAF,
  Amazon CloudWatch Logs, AWS Systems Manager Parameter Store.

#### Account Opening Service

- **Component Overview**: Implements the 3-stage account-opening flow (customer
  application, admin approval, automated processing) using Event Sourcing plus
  Transaction Outbox. Application state is written to a dedicated event store; an
  outbox table with a DynamoDB Stream drives the outbox processor that calls the
  core-banking API to create the customer and account and registers the login
  user.
- **Assumed AWS Services**: AWS Lambda, Amazon DynamoDB (event store + outbox
  table with Streams and a StatusIndex GSI), Amazon EventBridge.

#### Transfer (Withdraw / Deposit) Service

- **Component Overview**: Splits a transfer into independent withdrawal and
  deposit microservices. A transfer request records a `TransferRequested` event
  and publishes `WithdrawRequested` to EventBridge; SQS-queued worker Lambdas and
  DynamoDB-Stream-driven outbox Lambdas advance the state (WITHDRAW_REQUESTED →
  processing → completed → DepositRequested → … → TransferCompleted) while
  calling the core-banking API with retries.
- **Assumed AWS Services**: AWS Lambda, Amazon EventBridge, Amazon SQS (with
  DLQs), Amazon DynamoDB (event store + outbox table with Streams).

#### Query Services (CQRS Read Model)

- **Component Overview**: Read-optimized balance and transaction-history
  endpoints, separated from the write path per CQRS. Balance is served from a
  dedicated read-model table and/or the core-banking API; transaction history is
  read from the core-banking API.
- **Assumed AWS Services**: AWS Lambda, Amazon DynamoDB (balance read model),
  Amazon API Gateway.

#### Authentication & User Management

- **Component Overview**: JWT-based login, token verification, and user
  registration. Users and sessions are stored in DynamoDB (with GSIs and a TTL on
  sessions); the JWT signing secret lives in AWS Secrets Manager.
- **Assumed AWS Services**: AWS Lambda, Amazon DynamoDB, AWS Secrets Manager,
  AWS KMS.

#### Admin Functions

- **Component Overview**: Minimal bank-administrator features for pseudo-approval
  of account openings and for visualizing the event-sourced state transitions of
  a transfer by transaction ID.
- **Assumed AWS Services**: AWS Lambda, Amazon DynamoDB, Amazon API Gateway.

#### Mock Core Banking System (TemporaryCoreBankingSystemStack)

- **Component Overview**: A stand-in core-banking (勘定系) API providing customer,
  account, balance, and transaction management. Fronted by an internal-only
  regional API Gateway using IAM authorization plus an API Key and a resource
  policy; data lives in KMS-encrypted DynamoDB tables. In production this stack is
  replaced by the existing core system via the `CORE_API_BASE_URL` override.
- **Assumed AWS Services**: Amazon API Gateway, AWS Lambda, Amazon DynamoDB, AWS
  KMS, Amazon SQS (Lambda DLQ), Amazon CloudWatch Logs.

## FISC Compliance Summary

The workload includes a mapping of the **FISC Security Guidelines (安全対策基準),
practice standards (実務基準), 13th edition** to the controls implemented in the
sample. The scope is limited to the **backend system (online-banking-app-backend:
API Gateway, Lambda, DynamoDB, etc.)**; the mock core-banking system and the
frontend are out of scope, and overall system safety must be assessed together
with the governance-base template and operational processes.

Representative controls: KMS customer-managed-key encryption (実3, 実13, 実30,
実69), TLS enforcement (実4, 実7), IAM / API Key / JWT access control (実1, 実5,
実8, 実25, 実61), DynamoDB PITR and IaC backup (実6, 実39), WAF and rate limiting
(実14, 実16, 実20), Event Sourcing / Outbox / DynamoDB Streams for change
tracking and consistency (実17, 実19, 実65, 実66), and managed-service
availability / multi-AZ design (実84–実88, 実104, 実106).

The full row-by-row table (governance-base control vs. workload control vs.
customer-side additional considerations) is preserved in
`references/fisc-mapping.md`.

## Reference Architecture

For the full architecture explanation — the account-opening and transfer
processing flows (with sequence diagrams), the mail-delivery caveat, multi-region
considerations, and the discussion of monolith vs. microservices trade-offs and
distributed-system design patterns (Saga, Transaction Outbox, Event Sourcing,
CQRS) — see `references/architecture.md`. The end-user and administrator
application walkthrough is included there as well.

## CDK Sample Overview

The deployable AWS CDK sample (TypeScript) is under `assets/sample-cdk/`. It
contains the three stacks (`bin/app.ts`, `lib/*-stack.ts`), the Lambda function
sources (`lib/lambda-functions/`), the mock core-banking backend
(`lib/temporary-core-banking-system-backend/`), the shared KMS construct
(`lib/constructs/kms-construct.ts`), and the React frontend (`lib/frontend/`).
Deployment is controlled by the `DEPLOY_CORE_SYSTEM`, `DEPLOY_BACKEND`, and
`DEPLOY_FRONTEND` environment variables so stacks can be deployed individually,
and the core endpoint can be overridden with `CORE_API_BASE_URL` to point at a
real core system. Full step-by-step deployment and teardown instructions are in
`references/deployment.md`.

> **Sample app security notice**: this sample is a reference/functional demo, not
> production-ready. The application layer has Critical authorization defects:
> money transfer and balance/transaction queries do not verify account ownership
> (IDOR), and the admin API is protected only by an API key published in the
> frontend config (with plaintext temporary passwords). Implement ownership
> checks and real admin authentication before handling real accounts. The same
> notice ships as `assets/sample-cdk/SECURITY_NOTICE.md` and is printed as a
> warning on every `cdk synth` / `cdk deploy`.

The copied `assets/sample-cdk/.../test/*.test.ts` is the authoritative source of
the cdk-nag enforcement pattern; see `references/cdk-nag.md` for the extracted
suppression ledger and the reproduction guidance.
