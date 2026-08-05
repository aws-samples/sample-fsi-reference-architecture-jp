# Backup Plan Design (Acquisition Frequency, Target Selection, Retention Period, Lifecycle)

## Overview

This reference presents the backup plan design adopted by this skill. The backup plan is the core component of AWS Backup, and it has the role of defining which resources within the organization are stored, at what frequency, in which storage destination, and for how long.

In the context of ransomware resilience, designing the backup plan appropriately based on the backup requirements required per business-impact level (acquisition frequency/cadence/retention period) and the regulatory requirements (storage-period obligations, etc.) is directly connected to recovery capability in an emergency. This reference organizes the design of acquisition frequency, the selection of target resources, the design of the retention period, lifecycle management, and design decisions in the context of financial institutions.

For placement in the multi-account structure, refer to [01-multi-account-architecture.md](./01-multi-account-architecture.md); for the relationship with Vault Lock, refer to [02-immutability.md](./02-immutability.md).

## Foundational Mechanism: Backup Plans and Backup Rules

### Composition of a backup plan

An AWS Backup backup plan is composed of one or more backup rules. Furthermore, by separately configuring a "resource assignment" that associates the AWS resources to be protected with the backup plan, the scope on which backups are executed is determined.

| Component | Role |
|---|---|
| **Backup plan** | The unit that defines backup requirements. Composed of one or more backup rules |
| **Backup rule** | The individual rules that compose a backup plan. Defines acquisition frequency, backup window, lifecycle, storage-destination Vault, copy destination, etc. |
| **Resource assignment** | The setting that associates the AWS resources to be protected with the backup plan. Narrowing-down by resource-type unit, resource-ID unit, and tag condition is possible |

When multiple backup requirements coexist within the organization (e.g., a high-business-impact system every hour, a low-impact system daily), it is possible to operate by creating backup plans separated by business-impact level, each with a different backup rule and resource assignment.

### Relationship with the Organizations backup policy

In this configuration, the backup plan is deployed to the entire organization through the AWS Organizations backup policy (see [01-multi-account-architecture.md](./01-multi-account-architecture.md)). The design content of the backup plan is described in JSON as a backup policy managed in the Backup account, and a corresponding backup plan is created when it is applied to each business account within the organization.

Therefore, the design decisions described in this reference will be expressed as the JSON definition of the backup policy.

## Design of Acquisition Frequency

### Options for acquisition frequency

In the AWS Backup backup rule, the following acquisition frequencies can be configured.

| Type | Overview |
|---|---|
| **Scheduled backup (console options)** | Choose from every hour, every 12 hours, daily, weekly (day-of-week specified), monthly (date specified) |
| **Arbitrary schedule via a Cron expression** | Specify an arbitrary schedule, from as short as every hour, with a Cron expression. It can be specified similarly via the AWS CLI / API |
| **Continuous backup** | Available for supported resource types. Realizes Point-in-Time Recovery (PITR) |

### Design decision on acquisition frequency

The acquisition frequency is determined from the backup requirements required per business-impact level (the acquisition interval according to the degree of tolerable data loss). By taking backups at an interval shorter than the tolerance for data loss, it becomes possible to keep data loss in an emergency within the tolerable range.

In the context of ransomware resilience, we recommend designing the acquisition frequency from the following perspectives.

- **High-business-impact systems**: Consider hourly backup acquisition or the use of Continuous backup. By meeting the requirement for a short acquisition interval, minimize data loss
- **Low-business-impact systems**: Judge the backup cycle while balancing business impact, cost optimization, and business requirements, such as weekly/monthly
- **Systems where the acquisition frequency is specified by regulation**: Comply with the frequency stipulated by regulation

When subjected to a ransomware attack, it is necessary to restore to a clean backup from before the infection, but because there are cases where an attacker lurks for a long period after intruding into an account, retaining multiple generations of backups becomes important. We recommend a design that retains a sufficient number of generations of backups through the combination of acquisition frequency and retention period.

### Use of Continuous backup

Continuous backup is available for supported resource types (RDS, Aurora, S3, etc.) and realizes Point-in-Time Recovery. Because it enables specifying a recovery point at the second-to-minute level, it can be used for systems where the tolerable data loss is extremely small (a short acquisition interval is required).

However, because Continuous backup has the following constraints, note them at design time. We recommend confirming the detailed latest specifications in the official guidelines.

- The retention period is limited to a maximum of 35 days (a scheduled backup via snapshot is up to 100 years or indefinite)
- Continuous backup does not support migration to cold storage (because the maximum retention period of Continuous backup is below the minimum storage period required for cold-storage migration)
- A resource that has Continuous backup enabled requires a separate configuration from scheduled backups

## Selection of Target Resources

### Methods of resource assignment

Resource assignment to a backup plan supports the following methods.

| Method | Overview |
|---|---|
| **Target all resource types** | Target all resources that AWS Backup supports. In addition to existing resources, resources added in the future are also automatically targeted |
| **Selection per resource type** | Select specific resource types (EC2, RDS, S3, etc.) and narrow the scope. Furthermore, selection/exclusion of individual resources and exclusion per resource ID can also be specified |
| **Narrowing-down by tag** | A tag condition can be added to the above selection. When multiple tags are specified, they are evaluated as an AND condition |

In tag conditions, the following operators can be specified.

- `Equals` (exact match), `Contains` (partial match), `Begins with` (prefix match), `Ends with` (suffix match)
- The negated form of each of the above operators

As an example, it is possible to operate by targeting for backup only resources that have both the `env: prod` AND `role: application` tags.

### Recommendation of tag-based operation

This skill recommends adopting tag-based resource assignment. The reasons are as follows.

- Even when a new resource is created, by granting the corresponding tag, it can be operated so that it is automatically included in the backup targets
- It becomes easy to apply different backup rules according to the difference in business impact (e.g., the tags `Backup-Tier: critical` / `Backup-Tier: standard`)
- Compared to management per resource ID, the operational burden is greatly reduced

When adopting tag-based operation, standardizing the tag-naming convention within the organization becomes important. By also using the tag-policy feature of AWS Organizations, uniformity of tag naming across the entire organization can be realized.

## Design of the Retention Period

### Options for the retention period

The retention period that can be set in a backup rule is as follows. We recommend confirming the latest specifications in the official guidelines.

| Type | Setting range |
|---|---|
| **Snapshot (scheduled backup)** | 1 day to 100 years, or indefinite (Always) |
| **Continuous backup** | 1 day to 35 days |

### Design decision on the retention period

Design the retention period from the perspectives of business requirements, regulatory requirements, and ransomware resilience.

- **Business requirements**: Consider how far in the past a backup might be recovered from at the time of a failure. Because there are cases where not only the most recent failure but also a backup from a specific past point is needed, determine the retention period from the perspective of business continuity
- **Regulatory requirements**: At financial institutions, there are many cases where the storage periods of business records and audit records are stipulated by law or industry regulation (e.g., a 7-year storage obligation). When a backup is positioned as part of regulatory compliance, set a retention period that meets the regulatory requirements
- **Ransomware resilience**: Because there are cases where an attacker lurks for a long period after intruding into an account, secure a period sufficient to retain a clean backup from before the infection

### Consistency with Vault Lock's retention period

As described in [02-immutability.md](./02-immutability.md), Vault Lock's minimum/maximum retention period and the backup lifecycle retention period are linked. Because a backup lifecycle setting outside Vault Lock's retention-period range is not permitted, the two must be designed consistently.

In particular, when adopting Vault Lock in Compliance mode, because the retention period cannot be changed after the grace time elapses, it is important to decide carefully at the design stage.

## Lifecycle Management

### Migration between storage classes

In AWS Backup's lifecycle management, it is possible to automatically migrate a backup from warm storage to low-cost cold storage. This optimizes the storage cost of backups that require long-term storage.

| Storage class | Use |
|---|---|
| **Warm storage** | Normal backup storage. Rapid restore is possible |
| **Cold storage** | Low-cost storage for long-term storage. Restore time is long, but storage cost is greatly reduced |

### Constraints at the time of cold-storage migration

When migrating to cold storage, note the following constraints.

- Cold storage has a stipulated minimum-storage-period specification, and the design of the retention period (the total of the period stored in warm storage and the period stored in cold storage) must be done in a form that meets this specification
- A backup once migrated to cold storage cannot have its migration setting (the timing of migration to cold storage) changed afterward
- Because the resource types supported by cold storage are limited, confirm in the official documentation whether the target resource is supported
- In a Vault protected by Vault Lock's compliance mode, the cold-storage migration setting is also subject to the Lock, so the migration design must be done carefully

### Recommended approach to lifecycle design

This skill recommends the following approach for lifecycle design.

- **Recent backups frequently referenced from a business-continuity perspective**: Store in warm storage to enable rapid restore. The AWS Backup official documentation also recommends storing in warm storage for at least a certain period
- **Backups requiring long-term storage for regulatory or audit response**: After a certain period, migrate to cold storage to achieve cost optimization
- **Consistency with Vault Lock**: Design the timing of cold-storage migration and the retention period in alignment with Vault Lock's constraints

## Backup Window and Copy Destination

### Backup window

In a backup rule, it is possible to control the timing of backup execution with the following 3 elements.

- **Start time**: The time at which the backup begins
- **Start window (grace time)**: The tolerable time when execution is delayed from the start time
- **Completion window (grace time)**: The tolerable time until the backup completes

A design that executes backups avoiding the business system's busy hours, and a design that accounts for the balance with nightly batch processing, become possible.

### The specification of start timing and its implication for financial institutions

Backup execution in AWS Backup does not begin exactly at the configured start time; the specification is that it begins somewhere within the start window (start grace time) from the start time. The default of the start window is 8 hours, and the minimum settable value is 60 minutes. This specification applies equally not only to scheduled execution by the AWS Backup backup policy (backup plan) but also to on-demand execution by the StartBackupJob API.

In addition, for AWS database services such as RDS and for FSx, there is a specification that a backup does not begin immediately before or during the maintenance window, and in addition to the start-window delay, a further start constraint may be added. Because the target services and specific constraints may change due to feature enhancements, we recommend referring to the latest version of [Backup plan options and configuration](https://docs.aws.amazon.com/aws-backup/latest/devguide/plan-options-and-configuration.html) in the AWS Backup official documentation.

These specifications can become an issue when a financial institution has strict business requirements such as the following.

- A requirement to strictly capture the business system's quiescent point (a state of consistency after the nightly batch, etc.)
- A system requirement with a time constraint, such as "the acquisition must always be completed within a specific time slot outside business hours"
- A requirement to take a backup by bringing multiple related systems into a quiescent state at the same time

### Options for the response policy

Because it is difficult by specification to strictly control the start timing with the AWS Backup features at the time of writing, when there is a requirement such as the above, we recommend considering the design by combining the following options.

- **Use of Continuous backup (PITR)**: For supported resource types, because it becomes possible to restore to an arbitrary point without setting a specific quiescent point, the issue of start-timing strictness itself can be avoided
- **Combined use of AWS Backup and per-service native backup features**: When the requirement cannot be met by AWS Backup's schedule specification, consider the design including combined use with the native backup features each service provides (RDS automated backups, various snapshot features, etc.). However, because the effects of the multi-account structure, immutability, and organization-wide management that this skill recommends are obtained within the scope that goes through AWS Backup, when combining service-specific features, the consistency of the protection mechanism must be separately confirmed

### Supplement: Organizing the operation of quiescent-point backups

The start-timing specification described here is not an issue specific to AWS Backup; essentially similar organization is needed when directly using the native snapshot features of each AWS service as well. To acquire an application-consistent quiescent point, the operational order "the business-side job completes → the business application is brought into a quiescent state → the backup is taken" is the premise, and this is the same whether going through AWS Backup or using a native snapshot feature. The design of coordination with the completion of the business-side job, etc., is essentially required in either case.

However, when going through AWS Backup, because a time difference can arise between the API execution time and the actual start of the backup due to the start-window specification, the time during which the business system's quiescent state is maintained may be extended by that amount. When there is a strict tolerable range for business impact, we recommend operational designs such as setting the start window within the tolerable range or coordinating with the completion of the business-side job.

Note that how much this point actually becomes a problem differs greatly depending on the resource type to be protected.

- **Database services (PITR-supporting services such as RDS, Aurora, S3)**: By using Continuous backup (PITR), restoration to an arbitrary point becomes possible without presupposing scheduled execution at a specific time, so the start-window delay risk can be addressed. However, what PITR provides is restoration based on the database's transaction consistency, and ensuring consistency at the business-processing-cycle unit may separately require coordination design on the business side
- **Compute resources such as EC2 designed to be stateless**: When adopting a design that stores persistent data in external services (RDS, S3, etc.) as per AWS best practices, the quiescent-point strictness at the time of the compute resource's snapshot is essentially considered not to be a point of contention. This pattern is also preferable from the perspective of recommending cloud-native design
- **File storage such as EFS / FSx, or EC2 holding persistent data**: Because they are outside PITR support, coordination with the completion of the business-side job and ensuring a quiescent state through operations are still necessary. We assume that the main targets where this point becomes an actual operational issue fall into this category.

We recommend an approach that organizes the degree of impact of this point per resource type and incorporates a design response policy for resources of high impact.

### Copy-destination setting

By the copy setting (Copy Action) within a backup rule, it is possible to create a cross-account/cross-Region copy at the same time as backup acquisition. In the multi-account structure this skill adopts, the design is such that a copy to the isolation account and the Osaka Region is created at the same time as acquisition in the business account (for details, see [01-multi-account-architecture.md](./01-multi-account-architecture.md)).

## Design Decisions in the Context of Financial Institutions

### Backup plan division according to business impact

The business systems of financial institutions are diverse, and in many cases the difference in business impact is large. For example, a core banking system requires an acquisition interval at the second-to-minute level, while an internal-management system may be sufficient with daily backups.

In such an environment, rather than acquiring all resources uniformly with a single backup plan, we recommend a design that **creates multiple backup plans separated by business impact**, each with a different acquisition frequency and retention period. Specifically, configurations such as the following are conceivable.

- Business impact: high (tag `Backup-Tier: critical`) → Continuous backup or hourly acquisition, long-term storage
- Business impact: medium (tag `Backup-Tier: standard`) → every-12-hour or daily acquisition, mid-term storage
- Business impact: low (tag `Backup-Tier: low`) → daily or weekly acquisition, short-to-mid-term storage

We recommend determining the business-impact judgment by comparing against the organization's business continuity plan (BCP).

### Response to regulatory requirements

At financial institutions, there are many cases where the storage periods of business records and transaction records are stipulated by law or industry regulation. When a backup is positioned as part of regulatory compliance, reflect the following points in the design.

- A Vault Lock retention-period setting that meets the storage period stipulated by regulatory requirements
- Ensuring tamper/deletion resistance via Vault Lock compliance mode (see [02-immutability.md](./02-immutability.md))
- Backup acquisition in a state usable as an audit trail

However, the judgment of conformance to specific regulatory clauses is outside this skill's scope, and we recommend deciding in coordination with the organization's regulatory-response and compliance departments.

### Balance between cost optimization and business requirements

In the design of a backup plan, be conscious of the following trade-offs.

- Increasing the acquisition frequency / lengthening the retention period → recovery capability and regulatory-compliance capability increase, but storage cost increases
- Migrating to cold storage via lifecycle → cost can be reduced, but restore time becomes longer
- Dividing the backup plan by business impact → cost optimization becomes possible while realizing necessary and sufficient protection

In the context of financial institutions, an approach that incorporates cost optimization while giving top priority to business continuity and regulatory compliance is preferable.

## Summary Table of Countermeasure Effects

Let us organize which risks each design element covered in this reference is effective against as a ransomware-resilience measure.

| Design element | Risk defended against | Effective scenario |
|---|---|---|
| Design of acquisition frequency according to business requirements | Data loss (loss of data exceeding the tolerance) | Reduces the risk of data loss exceeding the tolerable range occurring at the time of a failure or attack |
| Retention of multiple backup generations | A situation where only infected backups exist due to an attacker's long-term lurking | When an attacker executes ransomware weeks to months after intrusion |
| Use of Continuous backup | Data loss in systems requiring a short acquisition interval | Minute-level recovery requirements in systems of extremely high business impact |
| Tag-based resource assignment | Backup-target omission (new resources are not protected) | When the increase/decrease of resources within the organization occurs frequently |
| Plan division by business impact | Cost increase and insufficient protection due to a single all-resource plan | Efficient protection in an organization with a large difference in business impact |
| Retention-period design meeting regulatory requirements | Backup insufficiency for regulatory compliance | Business systems where the storage period is stipulated by law or industry regulation |
| Cold-storage migration via lifecycle | Swelling of storage cost during long-term storage | Backups requiring long-term storage for regulatory compliance |

## Related Other References

- [01-multi-account-architecture.md](./01-multi-account-architecture.md): Multi-account structure, organization-wide management via the Organizations backup policy
- [02-immutability.md](./02-immutability.md): Linkage with Vault Lock, constraints of retention-period design
- [04-encryption-strategy.md](./04-encryption-strategy.md): Encryption at the time of backup acquisition
- [05-malware-protection.md](./05-malware-protection.md): Malware scanning for backups
- [06-policy-and-access-control.md](./06-policy-and-access-control.md): IAM privileges needed for backup plan management

## Reference: Official Documentation

- [AWS Backup](https://docs.aws.amazon.com/aws-backup/)
- [AWS Organizations](https://docs.aws.amazon.com/organizations/)

For the details of AWS Backup backup plan settings, the syntax of Cron expressions, the supported resources and retention-period upper limit of Continuous backup, the cold-storage-supported resources, the constraints of lifecycle settings, the tag-policy feature of AWS Organizations, and so on, refer to the latest version of the AWS Backup and AWS Organizations official documentation.
