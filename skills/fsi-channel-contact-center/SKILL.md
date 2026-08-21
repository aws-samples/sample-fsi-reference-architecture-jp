---
name: fsi-channel-contact-center
description: >-
  Reference architecture for building a secure, compliant, and reliable omnichannel
  contact center (顧客チャネル / Customer Channel) for Japanese financial institutions on AWS,
  centered on Amazon Connect. Covers inbound/outbound voice, web chat/web calling, AI
  assistance (Amazon Q in Connect, Amazon Bedrock), call monitoring/compliance checks,
  multi-region DR, and FISC compliance mapping. Use this skill when designing, explaining,
  or deploying a financial contact center / コンタクトセンター / コールセンター workload, when
  mapping Amazon Connect controls to the FISC 安全対策基準, or when working with the BLEA for
  FSI guest-customer-channel-sample CDK.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI Customer Channel (顧客チャネル)

## Workload Overview

The Customer Channel workload is a reference architecture for an **omnichannel contact
center** built for Japanese financial institutions, centered on **Amazon Connect**.
Financial institutions increasingly invest in contact centers that improve both customer
experience and employee experience across multiple channels: text chat on a web portal,
voice calls with a call-center agent, and chatbots. This workload shows how to combine
Amazon Connect with other AWS services and machine-learning technology to build a contact
center that meets the security, compliance, and reliability requirements demanded of
financial institutions.

**Business scenarios covered:**

- **Channels**: public-switched-telephone-network voice, or chat from a web portal.
- **Inbound**: customer desks, agency desks, automated reception (telephone banking,
  provisional card-loan screening), and call concentration.
- **Outbound**: call-backs, telemarketing, and collection/dunning operations.
- **Compliance**: detecting words that violate internal compliance rules from the
  transcription of voice-channel conversations.

**Significance in financial services:** Contact centers handle sensitive customer data
(phone numbers, contract details, identity information) and are subject to the FISC
安全対策基準 (Security Guidelines on Computer Systems for Financial Institutions). This
workload provides an implementation baseline that addresses encryption, access control,
audit logging, disaster recovery, and identity verification, deployed on top of the BLEA
for FSI governance base.

## Best Practices and Key Components

### Best Practices

- MUST: Manage users in the primary region via SAML federation with AWS IAM Identity
  Center so password policy and MFA are enforced.
- MUST: Encrypt data stored in Amazon S3 (call recordings, chat transcripts, contact
  trace records) with AWS KMS keys and protect access via IAM policies and S3 bucket
  policies.
- MUST: Use TLS for all communication with and between AWS services (Amazon Connect,
  Amazon S3, etc.) for both confidentiality and tamper detection.
- MUST: Control access to sensitive contact history (phone numbers, recordings, contact
  flows) using Amazon Connect security profiles.
- MUST: Grant IAM policies, resource policies, and SCPs with the least privilege possible,
  including the roles attached to Lambda functions.
- SHOULD: Enable KMS key rotation and manage key policies; consider separation of duties
  between the encryption-key administrator and the data owner.
- SHOULD: Back up important settings such as contact flows periodically using Amazon
  EventBridge and AWS Lambda so they can be restored after unauthorized changes.
- SHOULD: Monitor key Amazon Connect metrics with Amazon CloudWatch (e.g.
  LongestQueueWaitTime, MissedCalls, CallsBreachingConcurrencyQuota,
  ContactFlowErrors, ThrottledCalls) to detect quota breaches and errors.
- SHOULD: Export the Amazon Connect login/logout report to S3 because it is limited to
  10,000 rows.
- SHOULD: Record Lambda function execution logs, since most other services are managed.
- MAY: Use Amazon Connect Voice ID for voice-based identity verification (voiceprint),
  with operator confirmation available as an alternative.
- MAY: Adopt a secondary region for wide-area disaster recovery; it is optional and can be
  omitted when multi-AZ redundancy is sufficient or data-residency is a concern.
- WILL: In the secondary (DR) region, AWS IAM Identity Center is not used, so password
  policy, MFA, and login-failure logging are not enforced there — account for this.
- WILL: The sample template uses the Amazon Connect Preview API, which is subject to
  change, and implements only part of the full architecture (e.g. periodic configuration
  backup is not yet implemented).
- MUST: Apply cdk-nag's AwsSolutionsChecks (via Aspects) to every CDK stack built from this skill, and gate CI (jest etc.) on zero unsuppressed AwsSolutions-* findings; suppress exceptions only with an explicit reason via NagSuppressions (see references/cdk-nag.md).

### Key Components

#### Contact Center Platform

- **Component Overview**: The core engine that receives inbound/outbound voice, web chat,
  and web calls, routes contacts to agents, records interactions, and hosts contact flows
  and the agent workspace. It runs across multiple Availability Zones for high
  availability.
- **Assumed AWS Services**: Amazon Connect.

#### Identity and Authentication

- **Component Overview**: Enforces password policy and MFA for agents/administrators and
  centralizes identity, verifying end-customer identity where required.
- **Assumed AWS Services**: AWS IAM Identity Center (SAML federation), Amazon Connect user
  management (secondary region), Amazon Connect Voice ID; optionally an external IdP.

#### Inbound Contact Handling

- **Component Overview**: Receives incoming voice/chat contacts, performs automated
  reception and identity prompts, and connects customers to agents. Supports both
  agent-connected flows and immediate-acceptance flows used by the communication widget.
- **Assumed AWS Services**: Amazon Connect (contact flows, queues), Amazon Lex (identity
  bot), Amazon Polly.

#### Outbound Contact Automation

- **Component Overview**: Automates outbound dialing via an API and manages the state of
  each dial (initiated, disconnected) for call-backs, telemarketing, and dunning.
- **Assumed AWS Services**: Amazon API Gateway (IAM auth), AWS Step Functions, Amazon
  DynamoDB, Amazon EventBridge, Amazon Connect.

#### AI Assistance and Compliance Monitoring

- **Component Overview**: Provides agent assist / self-service answers from a knowledge
  base, real-time call monitoring, conversation summarization, and compliance checks that
  detect rule-violating statements in transcripts.
- **Assumed AWS Services**: Amazon Q in Connect, Amazon Bedrock (Anthropic Claude, Amazon
  Nova models), Amazon Kinesis Data Streams, AWS Lambda, AWS AppSync, Amazon DynamoDB.

#### Customer Data and Case Management

- **Component Overview**: Unifies customer profiles across contacts and manages
  customer-issue cases integrated with the contact center.
- **Assumed AWS Services**: Amazon Connect Customer Profiles, Amazon Connect Cases, Amazon
  AppIntegrations.

#### Recording Storage, Backup, and DR

- **Component Overview**: Stores encrypted call recordings, chat transcripts, and contact
  trace records, and replicates them cross-region for remote backup and disaster recovery.
- **Assumed AWS Services**: Amazon S3 (KMS-encrypted, versioned, cross-region
  replication), AWS KMS, Amazon Data Firehose.

#### Web Frontend and Edge Protection

- **Component Overview**: Delivers the customer-facing web site (with the communication
  widget) and the internal call-monitoring UI, protected at the edge by IP-based
  filtering.
- **Assumed AWS Services**: Amazon CloudFront, AWS WAF, Amazon S3, Amazon Cognito.

## FISC Compliance Summary

The FISC mapping documents how BLEA for FSI addresses the practical standards (実務基準) of
the FISC 安全対策基準 (11th edition) for the Customer Channel workload. It covers all 148
items (実 1 through 実 148). Only the measures provided by BLEA for FSI are listed; overall
system safety must additionally be considered in the user application and in
system-operation/development processes.

Key regulatory considerations addressed by this workload:

- **Access control and identity (実 1, 5, 8, 9, 25, 26)**: SAML federation with IAM
  Identity Center for password policy and MFA (primary region), least-privilege IAM,
  Amazon Connect security profiles, and Voice ID for identity verification. Note the DR
  secondary region does not use IAM Identity Center.
- **Data protection (実 3, 4, 5, 7, 13, 30)**: KMS encryption of S3 data, TLS in transit
  (confidentiality and tamper detection), and appropriate KMS key policies.
- **Audit and monitoring (実 10, 16, 19, 20, 46, 47, 101–103)**: CloudTrail for Amazon
  Connect API calls, Connect login/logout reports, CloudWatch monitoring of key metrics,
  and Lambda execution logging.
- **Resilience / DR (実 39, 71, 73, 74, 104)**: Multi-AZ Amazon Connect, multi-region
  configuration for wide-area disaster, S3 versioning + cross-region replication, and CDK
  (IaC) for configuration backup.
- **Out of scope**: many items are handled by the AWS cloud, by the business application,
  or by management/operation/development processes, and are marked as such.

Full row-by-row detail (all 148 items, no omissions) is in
[references/fisc-mapping.md](references/fisc-mapping.md).

## Reference Architecture

The reference architecture is a multi-region Amazon Connect contact center. Example
region layout used by the sample: primary in Tokyo (ap-northeast-1), an optional secondary
DR region, a tertiary region (e.g. Osaka, ap-northeast-3) for backup, and a us-east-1
stack for the CloudFront WAF.

Key design decisions:

- **Amazon Connect as the core**, with S3 storage configs for call recordings, chat
  transcripts, and scheduled reports, and Amazon Data Firehose delivery of contact trace
  records — all KMS-encrypted.
- **Identity via SAML/IAM Identity Center** in the primary region; Amazon Connect-managed
  users in the DR region.
- **Wide-area DR** by pre-provisioning a Connect instance and phone number in the
  secondary region and replicating recordings/CTR/settings to another region. The
  secondary region is optional.
- **AI capabilities** through Amazon Q in Connect (assistant, knowledge base, AI agents
  with Japanese prompts on Amazon Bedrock models) and real-time call monitoring with
  Bedrock-based compliance checks and summarization.
- **Edge protection** via CloudFront + AWS WAF (IP allow-listing).

Architecture diagrams (note: diagrams predate some newly added resources) and full
technical detail are in [references/architecture.md](references/architecture.md).

## CDK Sample Overview

The CDK sample (TypeScript) provisions a multi-region Amazon Connect contact center under
the project prefix `BLEAFSI-CustomerChannel`:

> **Sample app security notice**: this sample is a reference/functional demo, not
> production-ready. The call-monitoring sample has no object-level authorization
> (a known developer TODO): any single authenticated agent can read every
> customer's call transcripts, AI summaries, and compliance findings. Bedrock
> `invokeModel` is also granted on `Resource:'*'`. Implement per-caller row-level
> authorization (and scope Bedrock/MFA/WAF) before handling real customer data.
> The same notice ships as `assets/sample-cdk/SECURITY_NOTICE.md` and is printed
> as a warning on every `cdk synth` / `cdk deploy`.

- **Primary stack**: Amazon Connect instance (with S3/KMS recording configs, CTR via
  Firehose, optional SAML), plus samples for inbound, immediate-inbound, outbound, Amazon
  Q in Connect, Customer Profiles, and Cases; conditionally the call-monitoring and
  web-call samples.
- **Tertiary stack**: backup KMS key and S3 bucket (cross-region replication target).
- **Secondary stack** (optional): DR Amazon Connect instance.
- **WAF stack** (us-east-1): CloudFront WAF Web ACL.

It uses the Amazon Connect Preview API and implements only part of the full architecture.
Deployment steps (context configuration, CDK bootstrap/deploy, SAML setup, communication
widget, testing) are in [references/deployment.md](references/deployment.md). A detailed,
source-grounded walkthrough of every stack and construct is in
[references/cdk-sample.md](references/cdk-sample.md). The sample source is under
[assets/sample-cdk/](assets/sample-cdk/). The copied
`assets/sample-cdk/test/*.test.ts` is the authoritative source of the cdk-nag
enforcement pattern; see [references/cdk-nag.md](references/cdk-nag.md) for the extracted
enforcement layers and suppression ledger (this asset passes with zero suppressions).
