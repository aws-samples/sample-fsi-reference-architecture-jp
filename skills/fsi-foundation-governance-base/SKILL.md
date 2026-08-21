---
name: fsi-foundation-governance-base
description: >-
  Shared multi-account governance baseline (ガバナンスベース / Governance Base) of the BLEA
  for FSI (金融リファレンスアーキテクチャ日本版) reference architecture. Establishes a secure,
  FISC-aligned foundation across an AWS Control Tower / AWS Organizations environment:
  guardrails (ガードレール / Control Tower コントロール), centralized logging (ログ集約),
  security-service enablement (Security Hub, GuardDuty, Config, CloudTrail, IAM Access
  Analyzer), security alerting, auto-remediation, and IAM baselines. Use this skill when
  designing, deploying, or explaining the governance base that every other FSI workload
  builds on, when mapping controls to FISC 安全対策基準 実務基準, when working with the
  base-ct-guest / base-ct-logging CDK samples, or for Control Tower AFC auto-provisioning
  and non-Control-Tower setup.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI Governance Base (ガバナンスベース)

## Workload Overview

The Governance Base is the shared, foundational layer of BLEA for FSI (Baseline
Environment on AWS for Financial Services Institute). It establishes a secure baseline
across a multi-account AWS environment so that every other FSI workload (core-banking,
customer-channel, open-api, market-data, analytics-platform, etc.) is deployed on top of
consistent, FISC-aligned governance.

It is built on top of AWS Control Tower and AWS Organizations and provides, across all
accounts in the organization:

- **Multi-account governance** — AWS Control Tower manages the landing zone (management,
  Audit, and Log Archive accounts plus guest accounts). Security services that Control
  Tower does not cover are bulk-enabled at the AWS Organizations level so that newly
  created accounts inherit them automatically.
- **Guardrails (Control Tower コントロール)** — preventive and detective controls
  (implemented internally with SCPs and AWS Config rules) selected against FISC
  安全対策基準 第11版 実務基準.
- **Centralized logging (ログ集約)** — CloudTrail management-event logs and AWS Config
  configuration history are aggregated into the Log Archive account; a dedicated
  aggregation S3 bucket is provisioned there for CloudTrail S3 data-event logs.
- **Security detection & notification** — Security Hub, GuardDuty, Config, CloudTrail and
  IAM Access Analyzer enablement, plus CloudWatch metric-filter alarms and EventBridge
  rules that deliver security alerts by email through SNS, and Config auto-remediation.
- **IAM baseline** — sample IAM policies/roles/groups for four administrator roles.

The Governance Base is deployed with two CDK samples: `base-ct-guest` (per guest account
baseline, primary + optional secondary/Osaka region) and `base-ct-logging` (the Log
Archive account aggregation bucket). It targets an AWS Control Tower environment but can
also be reproduced in a single-account / non-Control-Tower environment.

## Best Practices and Key Components

### Best Practices

- MUST: Set up AWS Control Tower first; several governance features are configured
  automatically by Control Tower when the landing zone is established.
- MUST: Enable AWS Security Hub, Amazon GuardDuty and IAM Access Analyzer for the whole
  AWS Organization, delegating administration to the Audit account, so that every new
  account inherits them automatically.
- MUST: Deploy the Log Archive account governance base (`base-ct-logging`) before enabling
  CloudTrail S3 data-event capture, because the aggregation S3 bucket it creates is the
  destination for those logs.
- MUST: Enable the additional Control Tower guardrails recommended for FISC on the target
  OUs from the Control Tower management account (marked "◯" in the FISC mapping).
- MUST: Ensure the deployment `account` value in `parameter.ts` matches the account of the
  AWS CLI profile used, so a workload is never deployed to the wrong account.
- MUST: Block Amazon S3 public access at the account level for each guest account after
  deployment.
- MUST NOT: Create the `AWSControlTowerBlueprintAccess` IAM role for Control Tower AFC
  under any role other than `AWSControlTowerExecution` in the Service Catalog hub account
  — SCPs will otherwise cause the operation to fail.
- SHOULD: Use AWS IAM Identity Center (formerly AWS SSO) for authentication in a Control
  Tower environment rather than long-lived credentials, and enforce MFA on every sign-in.
- SHOULD: Enable CloudTrail S3 data-event recording for buckets that hold user data, to
  meet FISC 実務基準 expectations (optional, off by default).
- SHOULD: Remediate CRITICAL / HIGH Security Hub findings that remain after deployment;
  the baseline does not resolve all of them automatically.
- SHOULD: Specify the `account` field explicitly for Staging and Production environments
  in `parameter.ts`.
- PREFER: Provision the guest-account governance base automatically at account-creation
  time via Control Tower Account Factory Customization (AFC) using a Service Catalog
  blueprint, over manual per-account CDK deployment, when onboarding many accounts.
- MAY: Deploy the guest governance base to the Osaka region (ap-northeast-3) as a
  secondary region for a multi-region configuration; omit `secondary.region` if not used.
- MAY: Enable additional operational baselines manually (Systems Manager Quick Setup,
  Trusted Advisor reports, Amazon Macie) per requirements.
- WILL: Control Tower Landing Zone v3.0 aggregates CloudTrail logs into the management
  account's CloudWatch Logs and stops creating a per-guest-account log group, which
  requires the `base-ct-guest` source to be adjusted for some environments.
- WILL: Because BLEA for FSI creates its own guest-account CloudTrail trail for alerting,
  CloudTrail trails may be recorded in duplicate (the Control Tower organization-level
  trail and the BLEA for FSI guest-account trail).
- WILL: Auto-remediation of the default security group (Config rule
  `VPC_DEFAULT_SECURITY_GROUP_CLOSED`) is not deployed in the Osaka region because the
  SSM document `AWSConfigRemediation-RemoveVPCDefaultSecurityGroupRules` is unavailable
  there.
- MUST: Apply cdk-nag's AwsSolutionsChecks (via Aspects) to every CDK stack built from this skill, and gate CI (jest etc.) on zero unsuppressed AwsSolutions-* findings; suppress exceptions only with an explicit reason via NagSuppressions (see references/cdk-nag.md).

### Key Components

#### base-ct-logging Stack (Log Archive account)

- **Component Overview**: Deployed to the Control Tower Log Archive account. Creates the
  aggregation S3 bucket (`BLEAFSI-LogBase`, name `bleafsi-logbase-shared-log-<account>`)
  used to store CloudTrail S3 data-event logs and Osaka-region Config data, with a
  1825-day (5-year) lifecycle expiration, a policy denying `s3:DeleteObject`, and delivery
  permissions for `cloudtrail.amazonaws.com` and `config.amazonaws.com`. The bucket name
  is emitted as a CloudFormation output.
- **Assumed AWS Services**: Amazon S3, AWS IAM, AWS CloudFormation (via AWS CDK).

#### CloudTrail Trail (base-ct-guest)

- **Component Overview**: Creates a guest-account CloudTrail trail so that account-local
  alerting works even after Control Tower LZ v3.0. Provisions a trail-log S3 bucket
  (180-day lifecycle), a KMS CMK for CloudTrail-log encryption, and a CloudWatch Logs log
  group (3-month retention) with file validation and global service events enabled. This
  block can be swapped for referencing the existing `aws-controltower/CloudTrailLogs` log
  group, depending on the Landing Zone version.
- **Assumed AWS Services**: AWS CloudTrail, Amazon S3, AWS KMS, Amazon CloudWatch Logs.

#### Security Alarm (base-ct-guest)

- **Component Overview**: Defines security alerts delivered by email through an SNS topic.
  Uses four CloudWatch Logs metric-filter alarms over the CloudTrail log group (IAM policy
  change, multiple unauthorized/failed attempts, new access-key creation, root-user
  activity) and seven EventBridge rules (Config rule compliance change, AWS Health events,
  Security Group changes, Network ACL changes, CloudTrail configuration changes, Security
  Hub CRITICAL/HIGH findings, GuardDuty findings of severity 4 and above). The SNS topic
  enforces publish-over-SSL only.
- **Assumed AWS Services**: Amazon CloudWatch (alarms & Logs), Amazon EventBridge, Amazon
  SNS, AWS IAM.

#### Security Auto-Remediation (base-ct-guest)

- **Component Overview**: Creates the AWS Config managed rule
  `VPC_DEFAULT_SECURITY_GROUP_CLOSED` (rule name `bb-default-security-group-closed`) and an
  automatic remediation that runs the SSM document
  `AWSConfigRemediation-RemoveVPCDefaultSecurityGroupRules` (removing all rules from the
  default security group) via an SSM automation role. Not deployed in the Osaka region.
- **Assumed AWS Services**: AWS Config, AWS Systems Manager (Automation), AWS IAM.

#### Session Manager Log (base-ct-guest)

- **Component Overview**: Creates an S3 bucket
  (`bleafsi-base-sm-auditlog-<account>`) on the guest account for SSM Session Manager
  audit logs, with a policy denying `s3:DeleteObject`, and a customer-managed IAM policy
  (attached to EC2 instance profiles) that allows writing logs under `AWSLogs/*`. The
  bucket name is a CloudFormation output. Session Manager log aggregation to the Log
  Archive account is not supported, so logs stay in the guest account.
- **Assumed AWS Services**: Amazon S3, AWS IAM, AWS Systems Manager (Session Manager).

#### IAM Sample (base-ct-guest)

- **Component Overview**: Creates sample IAM policies/roles and IAM groups for four
  administrative roles: SysAdmin (system administrator), IamAdmin (IAM-only administrator),
  ReadOnlyAdmin (read-only administrator), and InstanceOps (EC2-focused administrator).
  Privileged roles require MFA (`aws:MultiFactorAuthPresent`) and deny billing, CloudTrail
  tampering, and destructive KMS actions.
- **Assumed AWS Services**: AWS IAM.

#### CloudTrail Data Event (base-ct-guest, optional)

- **Component Overview**: Optional (commented out by default). Creates a CloudTrail trail
  for S3 data events on specified target buckets, encrypted with the Control Tower KMS key,
  writing to the Log Archive aggregation bucket, with a 2-week CloudWatch Logs group.
  Enabled by setting `controlTowerKMSKeyArn`, `cloudTrailBucketName`, `targetBuckets` in
  `parameter.ts` and uncommenting the block in the guest stack.
- **Assumed AWS Services**: AWS CloudTrail, Amazon S3, AWS KMS, Amazon CloudWatch Logs.

#### Organization-Level Security Services

- **Component Overview**: Enabled outside CDK, at the AWS Organizations / Control Tower
  level. AWS Security Hub, Amazon GuardDuty and IAM Access Analyzer are enabled across the
  organization with the Audit account as delegated administrator; AWS CloudTrail
  (management-event logging) and AWS Config (configuration recording) are enabled by
  Control Tower; AWS Trusted Advisor organizational view is optional. New member accounts
  inherit these automatically.
- **Assumed AWS Services**: AWS Security Hub, Amazon GuardDuty, AWS IAM Access Analyzer,
  AWS CloudTrail, AWS Config, AWS Trusted Advisor, AWS Organizations, AWS Control Tower.

## FISC Compliance Summary

The Governance Base maps AWS Control Tower コントロール (guardrails) to the FISC 安全対策基準
第11版 実務基準. As of 2023/10/13 there were 459 total Control Tower controls; excluding
proactive-behavior controls and mandatory-guidance controls, 224 controls were analyzed
and those worth enabling from a FISC 実務基準 perspective were selected across EC2, IAM,
RDS, S3, CloudTrail, KMS, ECR, ECS, Lambda and GuardDuty. Controls are implemented either
as AWS Config rules or SCPs, with guidance levels "強く推奨" (strongly recommended) and
"選択的" (elective).

For the complete, unabridged mapping table (every control ID, its FISC 実務基準 item,
guidance level, severity, service, whether enabling is recommended, and comments), see
[references/fisc-mapping.md](references/fisc-mapping.md).

## Reference Architecture

The Governance Base spans the Control Tower management, Audit and Log Archive accounts and
each guest account, across a primary region (Tokyo, ap-northeast-1) and an optional
secondary region (Osaka, ap-northeast-3). It combines organization-level security-service
enablement, Control Tower guardrails, centralized logging in the Log Archive account, and
per-guest-account CDK constructs for alerting, auto-remediation, Session Manager logging,
and IAM baselines.

For full technical detail — component functions, AWS-service mapping, non-Control-Tower
setup, Landing Zone v3.0 considerations, and the difference from upstream BLEA — see:

- [references/architecture.md](references/architecture.md) — architecture and component
  breakdown.
- [references/non-ct-setup.md](references/non-ct-setup.md) — single-account /
  non-Control-Tower setup, including the Config-rule and security-alert inventories.
- [references/landing-zone-v3.md](references/landing-zone-v3.md) — Control Tower Landing
  Zone v3.0 update considerations and required source edits.
- [references/diff-from-blea.md](references/diff-from-blea.md) — how BLEA for FSI differs
  from upstream BLEA.

## CDK Sample Overview

Two CDK samples under [assets/sample-cdk/](assets/sample-cdk/) provision the Governance
Base (TypeScript, AWS CDK):

> **Baseline security notice**: this skill *is* the security governance baseline,
> so its guardrails, audit logging, and detective controls are the product and
> most threats are already mitigated. Residual, downstream-owned decisions
> remain: the bundled IAM sample roles are intentionally broad and must be
> narrowed to least privilege, CloudTrail S3 data events are off by default, the
> default-SG auto-remediation runs automatically, and the aggregated log bucket
> has no Object Lock. Each sample ships a `SECURITY_NOTICE.md` and prints a
> warning on every `cdk synth` / `cdk deploy`.

- **`base-ct-logging`** — deployed to the Control Tower **Log Archive** account. Creates
  the centralized aggregation S3 bucket (5-year lifecycle) used to store CloudTrail S3
  data-event logs and Osaka-region Config data. Project prefix `BLEAFSI-LogBase`.
- **`base-ct-guest`** — deployed to each **guest** account (primary and optional secondary
  region). Provisions the guest baseline: CloudTrail trail + KMS + CloudWatch Logs,
  CloudWatch/EventBridge security alarms with SNS email delivery, Config default-SG
  auto-remediation, Session Manager audit-log bucket, IAM sample roles/groups, and the
  optional CloudTrail S3 data-event trail. Project prefix `BLEAFSI-Base`; stacks
  `BLEAFSI-Base-Primary-Dev`, `BLEAFSI-Base-Secondary-Dev`, and `BLEAFSI-Base-AFC` (for
  Control Tower AFC blueprint generation via `cdk synth`).

Deployment order: enable Control Tower and org-level security services → create guest
accounts → deploy `base-ct-logging` to Log Archive → deploy `base-ct-guest` to each guest
account (manually or via Control Tower AFC).

The copied `assets/sample-cdk/.../test/*.test.ts` files are the authoritative source of the
cdk-nag enforcement pattern; see [references/cdk-nag.md](references/cdk-nag.md) for the
extracted suppression ledger and how to enforce it on your own stacks.

For step-by-step deployment, AFC auto-provisioning, and Osaka-region setup, see
[references/deployment.md](references/deployment.md).
