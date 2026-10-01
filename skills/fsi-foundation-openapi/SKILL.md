---
name: fsi-foundation-openapi
description: >-
  Reference architecture and CDK samples for building financial Open API (オープンAPI)
  workloads on AWS, from the "BLEA for FSI / Financial Reference Architecture Japan"
  initiative. Use this skill when designing or deploying third-party-accessible bank
  APIs — including basic reference APIs (残高照会 / 株価照会) authenticated with Amazon
  Cognito + API Gateway, and financial-grade APIs (FAPI, 資金移動 / 売買指図) protected by
  mTLS and an OAuth2/OpenID Connect authorization server (Keycloak or Authlete). Covers
  FISC safety-standard mapping, multi-region DR design, and the two provided CDK samples
  (guest-openapi-base-sample and guest-openapi-fapi-sample). Trigger keywords: Open API,
  オープンAPI, FAPI, 金融グレードAPI, 認可サーバー, Keycloak, mTLS, 相互TLS, Cognito API.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Financial Open API (オープン API)

## 1. Workload Overview

An **Open API** in this reference architecture follows the Japanese Bankers Association
(全銀協) definition: an **API accessible to third parties (external companies, etc.)**.
It lets a financial institution expose services to individuals and Fintech partners
through APIs whose scope is one of two permission classes:

- **Reference / inquiry APIs (参照・照会系)** — read-oriented, mainly for end users.
  Examples: stock-price and FX-rate inquiry, bank-balance inquiry, loyalty-point inquiry.
- **Update / execution APIs (更新・実行系)** — state-changing, mainly for external
  Fintech companies that require financial-grade access. Examples: securities and
  investment-trust trade instructions, funds transfer (振込・振替).

**Business drivers.** Open APIs are the technical foundation of open banking and Fintech
collaboration in Japan. They let banks safely publish account, market, and transaction
functionality to partners while keeping strong identity, authorization, and transport
security. This workload does **not** mandate a specific documentation format (OpenAPI
Specification / Swagger), FAPI conformance, or OAuth2/OpenID Connect — those are optional
depending on the API class. Two access styles are provided:

- **Basic API access** — full AWS managed services (Amazon Cognito for auth, Amazon API
  Gateway for API management) for the reference/inquiry class.
- **Financial-grade API (FAPI) access** — an authorization server plus mutual-TLS
  authentication and encryption for the update/execution class, intended for
  development/testing verification of FAPI 1.0 behavior.

## 2. Best Practices and Key Components

### Best Practices

- MUST: Authenticate reference/inquiry API access with an Amazon Cognito user pool fronted by Amazon API Gateway.
- MUST: Authenticate update/execution (financial-grade) API access with mutual TLS (mTLS, client certificate) combined with an authorization server.
- MUST: Encrypt all client-facing traffic with TLS across Amazon API Gateway, Amazon Cognito, and Amazon CloudFront; encrypt API-backend traffic on the consumer side.
- MUST: Encrypt data at rest for Amazon EBS and Amazon Aurora using AWS Key Management Service, and protect the encryption keys with KMS key policies.
- MUST: Apply AWS WAF to Amazon CloudFront and restrict CloudFront distribution by geography (allowlist) to reduce the attack surface.
- MUST: Grant only least-privilege IAM permissions and access resources through temporary credentials from IAM roles.
- MUST: Enable CloudTrail for the authorization server and the DBMS (Amazon Aurora), and capture VPC Flow Logs plus Amazon CloudWatch Logs.
- MUST: Build the workload as multi-region / multi-AZ and prefer highly available AWS managed services for resiliency.
- SHOULD: Use an external IdP so that identity/auth information does not need to be synchronized between regions in the multi-region DR configuration.
- SHOULD: For FAPI 1.0 Advanced, use `tls_client_auth` (client TLS) for client authentication rather than the Keycloak default `private_key_jwt`.
- SHOULD: When Amazon API Gateway is the resource server, implement a Lambda Authorizer to check client-certificate revocation and CRL, because API Gateway mTLS does neither.
- SHOULD: Track server/client certificate expiry and renew both before they lapse; register CloudFront certificates in us-east-1 and API Gateway certificates in ap-northeast-1 (ACM).
- SHOULD: Use a PS256 or ES256 signing key for FAPI ID tokens (Keycloak realms do not create these key pairs by default).
- MUST NOT: Ship the API backend or client/resource-server application as part of these samples — they are out of scope and must be implemented by the consumer.
- MAY: Use AWS Systems Manager to centrally manage EC2 instances, and AWS Inspector to scan authorization-server/backend container images and EC2 for vulnerabilities.
- WILL: The FAPI sample is intended for development/test verification of FAPI 1.0 behavior, not as a turnkey production authorization server.
- WILL: Route 53 distributes requests across regions; how requests are split or failed over depends on the API backend system's policy.
- MUST: Apply cdk-nag's AwsSolutionsChecks (via Aspects) to every CDK stack built from this skill, and gate CI (jest etc.) on zero unsuppressed AwsSolutions-* findings; suppress exceptions only with an explicit reason via NagSuppressions (see references/cdk-nag.md).

### Key Components

#### API Management (Basic)

- **Component Overview**: Creates, publishes, maintains, monitors, and secures the
  reference/inquiry REST API; fronted by a CDN for edge delivery and caching, with WAF
  managed-rule protection and a custom/alternate domain over TLS.
- **Assumed AWS Services**: Amazon API Gateway (REST API, regional custom domain,
  Cognito authorizer), Amazon CloudFront, AWS WAF (WAFv2), AWS Certificate Manager,
  Amazon Route 53, AWS Lambda (sample backend).

#### API Authentication — Basic (IdP)

- **Component Overview**: Web/mobile user authentication, authorization, and user
  management for the reference/inquiry API class; issues ID tokens consumed by the API
  Gateway Cognito authorizer.
- **Assumed AWS Services**: Amazon Cognito (user pool `apiUserPool`, user pool client
  `apiUserPoolClient`).

#### Authorization Server (FAPI)

- **Component Overview**: A FAPI 1.0-capable authorization server (Authorization Server)
  running on the VPC that issues and introspects tokens; supports FAPI 1.0 Baseline and
  Advanced profiles. Offered as either a 3rd-party product (Authlete) or OSS (Keycloak);
  only the OSS Keycloak pattern is provided as a deployable sample.
- **Assumed AWS Services**: Amazon ECS on AWS Fargate (Keycloak container from Amazon
  ECR), Network Load Balancer, Amazon Aurora MySQL / Amazon RDS, AWS Secrets Manager,
  Amazon EC2 (Authlete/authorization-server hosting pattern).

#### mTLS / Certificate Security (FAPI)

- **Component Overview**: Mutual-TLS transport security between client, authorization
  server, and resource server using CA / intermediate-CA / server / client certificates;
  the same client certificate is used toward both the authorization server and the
  resource server.
- **Assumed AWS Services**: AWS Certificate Manager, Amazon API Gateway (mTLS-enabled
  REST/HTTP API as resource server), AWS Lambda (Lambda Authorizer for CRL / revocation).

#### Network & Data Layer (FAPI)

- **Component Overview**: An isolated multi-AZ VPC (public / protected / isolated
  subnets) hosting the Fargate authorization server and encrypted Aurora database, with
  interface/gateway VPC endpoints and encrypted VPC Flow Logs.
- **Assumed AWS Services**: Amazon VPC (VPC endpoints for CloudWatch Logs, ECR, ECR
  Docker, S3), Amazon Aurora MySQL (encrypted), AWS KMS, Amazon S3 (flow-log bucket),
  network ACLs.

#### Monitoring & Governance

- **Component Overview**: Operational monitoring, service-health detection, audit
  logging, and IaC-based configuration/backup for the whole workload.
- **Assumed AWS Services**: Amazon CloudWatch (metrics, Logs, Container Insights), AWS
  Health Dashboard, AWS CloudTrail, AWS Cloud Development Kit (AWS CDK), Amazon Aurora
  automated backups.

## 3. FISC Compliance Summary

The FISC mapping documents how this workload addresses the **FISC Security Guidelines
(安全対策基準), 実務基準 (Practice Standards), 11th edition**. Coverage is split across the
**governance-base template** (共通統制環境) and the **Open API workload template**, and each
row also lists example additional measures for the consumer. Only BLEA-for-FSI measures are
recorded; total system safety still requires the user's application implementation plus
operational/development-process controls.

Key regulatory considerations covered by the workload template:

- **Access control & authentication** (実1, 実2, 実9, 実26): Cognito for reference APIs;
  mTLS client-certificate + authorization-server auth for update/execution APIs.
- **Encryption** (実3, 実4, 実7, 実13, 実30, 実69): AWS KMS for EBS/Aurora at rest; TLS for
  API Gateway / Cognito / CloudFront in transit.
- **Logging & audit** (実6, 実10, 実72): CloudTrail on the authorization server and Aurora;
  VPC Flow Logs and CloudWatch Logs.
- **Network protection** (実14, 実15, 実20): AWS WAF on CloudFront, VPC endpoints, security
  groups controlling ECS/Aurora traffic.
- **Availability / DR** (実84–実88, 実104): multi-region / multi-AZ, highly available
  managed services.
- **Monitoring & operations** (実46, 実47, 実101–実103): CloudWatch monitoring and AWS Health
  Dashboard for service-failure detection.
- **IaC & change management** (実39, 実42, 実43): AWS CDK for build/config and backup; Aurora
  automated backups.

Many items are marked out of scope (business application, management/operation process,
development process, or already handled on the AWS cloud side). See
[references/fisc-mapping.md](references/fisc-mapping.md) for every entry (実1–実148) with the
full three-column table preserved.

## 4. Reference Architecture

The reference architecture presents patterns for both API classes plus a multi-region DR
design. Full technical detail is in [references/architecture.md](references/architecture.md).

**Pattern overview.** See `assets/images/open-api-Arch-Pattern.png` for the full pattern
list. The architecture distinguishes three deployable variants.

**Basic API (reference/inquiry).** End users authenticate through Amazon Cognito; requests
enter through Amazon CloudFront (with AWS WAF and geo-restriction) to a regional Amazon API
Gateway REST API that uses a Cognito user-pool authorizer, backed by AWS Lambda in the
sample. Diagrams: `open-api-Arch-Basic-Diag.png`, `open-api-Arch-Basic-Flow.png`.

**Financial-grade API (FAPI).** Update/execution access requires FAPI 1.0 Advanced-style
mutual TLS. A FAPI-capable authorization server issues and introspects tokens; the resource
server (e.g. Amazon API Gateway + backend) validates tokens and the client certificate. Two
authorization-server sub-variants are documented:

- **FAPI / 3rd Party (Authlete)** — diagrams `open-api-Arch-FAPI-Authlete-Diag.png`,
  `open-api-Arch-FAPI-Authlete-Flow.png`. Documented as an architecture only (no sample).
- **FAPI / OSS (Keycloak)** — diagrams `open-api-Arch-FAPI-keycloak-Diag.png`,
  `open-api-Arch-FAPI-keycloak-Flow.png`. Provided as the deployable `guest-openapi-fapi-sample`.
  Keycloak runs on ECS Fargate behind an internet-facing NLB, backed by Aurora MySQL, in a
  multi-AZ VPC.

**Multi-region DR.** For wide-area disaster events (e.g. a Kanto-region incident), the Open
API stack is deployed independently per region (e.g. Tokyo and Osaka) with Amazon Route 53
distributing requests. Because identity/auth uses an external IdP, no cross-region auth
synchronization is required. Diagram: `open-api-Arch-Multi-region.png`.

## 5. CDK Sample Overview

Two AWS CDK (TypeScript) samples are provided under
[assets/sample-cdk/](assets/sample-cdk/). Both deploy into a guest account that already has
the BLEA-for-FSI governance base. Deployment detail is in
[references/deployment.md](references/deployment.md). The copied
`assets/sample-cdk/.../test/*.test.ts` files are the authoritative source of the cdk-nag
enforcement pattern; see [references/cdk-nag.md](references/cdk-nag.md) for the extracted
suppression ledger and how to reproduce the gate on your own stacks.

> **Sample app security notice**: both CDK samples (base and FAPI) are
> reference/verification demos, not production-ready. In the base sample, WAF
> managed rules run count-only (non-blocking) with no rate limit and Cognito
> allows password auth with MFA optional. In the FAPI sample, the Keycloak-to-
> Aurora DB link is plaintext (`useSSL=false`), the DB security group allows the
> whole VPC CIDR, and FAPI mTLS checks are loose. Enable WAF blocking, DB TLS,
> tight security groups, and strict FAPI mTLS before real use. Each sample ships
> a `SECURITY_NOTICE.md` and prints a warning on every `cdk synth` / `cdk
> deploy`.

**`guest-openapi-base-sample`** — the Basic API environment. Provisions an Amazon Cognito
user pool (`apiUserPool`) + client, an Amazon API Gateway REST API (Cognito authorizer,
CLF access logs, regional custom domain), a Lambda "hello" backend, an AWS WAF (WAFv2)
WebACL with AWS managed rule groups (Common, KnownBadInputs, AmazonIpReputationList, Linux,
SQLi) associated to the API stage, and an Amazon CloudFront distribution (HTTPS-only, geo
allowlist US/GB/JP, S3 access-log bucket). Requires two ACM certificates (CloudFront in
us-east-1, API Gateway in ap-northeast-1) and Route 53 alias records. Verified with a
Cognito ID token via curl.

**`guest-openapi-fapi-sample`** — the FAPI (Keycloak) environment. Provisions a dedicated
multi-AZ VPC (public / protected / isolated subnets, VPC Flow Logs to a KMS-encrypted S3
bucket, VPC endpoints for CloudWatch Logs / ECR / ECR Docker / S3, custom NACLs) and a
Keycloak deployment: ECS Fargate service (task 1024 CPU / 2048 MiB, desired count 2,
autoscale 2–10 at 80% CPU) running a **custom Keycloak 16.1.1** container image from Amazon
ECR, fronted by an internet-facing Network Load Balancer (TCP 443 → 8443, source-IP
stickiness), backed by an encrypted Amazon Aurora MySQL / RDS cluster, with the Keycloak
admin credential auto-generated in AWS Secrets Manager. Deployment requires building and
pushing a custom Keycloak image (server certs baked in), creating CA/intermediate/server/
client certificates, and manual Keycloak realm/client/policy configuration for FAPI 1.0.

> Note: the FAPI deployment doc is flagged as under maintenance because the referenced
> Keycloak (jboss/keycloak) container repository has been retired; the mechanics remain
> valid as a reference.
