# Monitoring and Auditing of Backup Operations

## Overview

This reference presents the continuous monitoring and auditing of backup operations adopted by this skill. In the context of ransomware resilience, merely building a mechanism to take and protect backups is insufficient; it is important to continuously monitor whether they continue to operate as expected and whether the settings have been changed. Also, from the perspective of regulatory and audit response, continuously recording the trail of backup activities and storing it in a form that can be referenced later is required.

This reference organizes the cross-account monitoring feature provided by AWS Backup, the reporting feature via AWS Backup Audit Manager, the organization of the implementation accounts for monitoring/auditing, and design decisions in the context of financial institutions.

For the positioning of the Backup account in the multi-account structure, refer to [01-multi-account-architecture.md](./01-multi-account-architecture.md); for log collection and protection in general, refer to [07-log-collection-and-protection.md](./07-log-collection-and-protection.md).

## Foundational Mechanism: AWS Backup's Organization-Wide Management Features

In the multi-account structure this skill adopts, a mechanism is provided to centrally grasp, from the Backup account (the delegated administrator of AWS Backup), the backup/copy/restore jobs executed in multiple accounts within the organization. AWS Backup provides the following two features to realize organization-wide operation and auditing.

| Feature | Nature | Main role |
|---|---|---|
| **Cross-account monitoring** | Real-time situational awareness | Confirm the execution status of backup/copy/restore jobs across the organization |
| **AWS Backup Audit Manager reports** | Periodic output of an audit trail | Automatically output a report of backup activities to S3 |

Because the two features have different roles, this skill recommends using them together. It forms a design that grasps the day-to-day operational status with cross-account monitoring while continuously securing an audit trail with Audit Manager reports.

## Cross-Account Monitoring

### Feature overview

Cross-account monitoring is a feature that enables centrally confirming, from the Organizations management account and the Backup account (delegated administrator), the backup/copy/restore jobs executed in accounts under AWS Organizations. It eliminates the need to individually log in to each account to confirm job status, making organization-wide operations more efficient.

### Information that can be confirmed

The following information can be confirmed on the AWS Backup console.

- Job status (success, failure, in progress, etc.)
- Account ID
- Resource name, resource ID, resource type
- Job ID
- Execution date and time

It is organized by job type into backup jobs, restore jobs, and copy jobs, and filtering/searching by account ID, status, job ID, and so on, is also possible.

### Notes on enabling

Cross-account monitoring is an opt-in feature and needs to be enabled on the Organizations management account side. The specification is that only jobs created after enabling are displayed in the aggregated view, and past jobs cannot be displayed retroactively.

When disabled, past jobs are displayed for a certain period after reaching a terminal state, but are no longer displayed thereafter. Because the specific retention period may change due to feature enhancements, we recommend referring to the latest version of [Managing AWS Backup resources across multiple AWS accounts](https://docs.aws.amazon.com/aws-backup/latest/devguide/manage-cross-account.html) in the AWS Backup official documentation.

## AWS Backup Audit Manager Reports

### Feature overview

AWS Backup Audit Manager provides a feature that automatically outputs the backup activities within the organization as a report to S3. It can be leveraged for securing a continuous audit trail and as part of regulatory compliance. Through the automatic output of reports, a system can be established that can provide pre-prepared trails at the time of an audit response.

### Types of reports

| Report type | Content |
|---|---|
| **Jobs report** | Outputs information on jobs completed in the past 24 hours and all active jobs. Includes context such as Vault properties, backup plan configuration, and lifecycle settings |
| **Compliance report** | A report that monitors the resource-level status of applied controls |

Because the jobs report includes context information such as Vault type, Lock status, encryption information, backup plan name, schedule, and retention period, it forms a structure that can obtain comprehensive job information without additional API calls.

### Output specifications

| Item | Content |
|---|---|
| Delivery destination | The specified S3 bucket (only an S3 bucket owned by the account from which the report plan was created; cross-account S3 delivery is not supported) |
| Output format | CSV or JSON when destined for the same Region and same account; otherwise CSV |
| Frequency | Every 24 hours (automatic). On-demand execution is also possible |

The execution timing has a specification that introduces a randomization of several hours for performance reasons.

### Scope and constraints

- All account holders can create a cross-Region report
- The Organizations management account and the Backup account (delegated administrator) can also create a cross-account report (a report aggregating the activity of member accounts)
- There is an upper limit on the number of report plans per AWS account

For the detailed specifications, we recommend referring to the latest version of [Working with audit reports](https://docs.aws.amazon.com/aws-backup/latest/devguide/working-with-audit-reports.html) in the AWS Backup official documentation.

### Use of malware-scan results in reports

In AWS Backup Audit Manager reports, the history of scan jobs by GuardDuty Malware Protection for Backup can also be confirmed. By performing continuous monitoring of the scan results (clean / threat detected) with Audit Manager reports, an operation that grasps the soundness of backups across the organization can be realized. For the details of malware scanning, refer to [05-malware-protection.md](./05-malware-protection.md).

### Protection of the report-storage S3 bucket

We recommend applying to the S3 bucket that stores Audit Manager reports protection mechanisms equivalent to the log-storage S3 bucket this skill adopts. Specifically, it is a combination of S3 Object Lock, S3 Versioning, MFA Delete, and least-privileged access control. For details, refer to [02-immutability.md](./02-immutability.md) (S3 Object Lock) and [07-log-collection-and-protection.md](./07-log-collection-and-protection.md) (S3 defense in depth).

## Organizing the Implementation Accounts for Monitoring/Auditing

The implementation accounts for the monitoring/auditing features in the multi-account structure this skill adopts are as follows.

| Feature | Main implementation account |
|---|---|
| Enabling cross-account monitoring | Organizations management account |
| Confirming cross-account monitoring | Organizations management account and Backup account |
| Creating the Audit Manager report plan | Backup account (executed as delegated administrator to create cross-account reports) |
| Placement of the report-storage S3 bucket | Backup account (because of the constraint of delivery to an S3 bucket owned by the account from which the report plan was created) |

By consolidating the organization-wide operation/audit features into the Backup account, it forms a configuration that makes management operations more efficient.

## Design Decisions in the Context of Financial Institutions

### Use for regulatory and audit response

At financial institutions, there are many cases where the presentation of a trail of backup operations is required during an internal audit, external audit, or inspection by a regulatory authority. By leveraging the Audit Manager reports described in this reference, responses such as the following become possible.

- Automatically record daily backup activities to S3 and immediately present the trail at the time of an audit request
- Continuously monitor the enablement status of Vault Lock, retention-period settings, encryption settings, and so on, with the Compliance report
- Continuously verify the compliance status of the backup policy and detect configuration deviations early

However, the judgment of conformance to specific regulatory clauses is outside this skill's scope, and we recommend deciding in coordination with the organization's regulatory-response and compliance departments.

### Design of the report-storage period

We recommend designing the retention period of the reports stored as an audit trail according to internal rules and regulatory requirements. At financial institutions, there are many cases where the storage periods of business records and transaction records are stipulated by law or industry regulation, and it is preferable to set an equivalent storage period for Audit Manager reports as well. For long-term storage, a design that migrates to cold storage such as Amazon S3 Glacier in consideration of cost efficiency can also be used.

## Summary Table of Countermeasure Effects

Let us organize which risks each design element covered in this reference is effective against as a ransomware-resilience measure.

| Design element | Risk defended against | Effective scenario |
|---|---|---|
| Organization-wide situational awareness via cross-account monitoring | Overlooking backup-execution failures | Operational efficiency in organizations with many accounts, early detection of unexpected job failures |
| Automatic recording of the trail via the Audit Manager jobs report | Insufficiency of the trail at the time of an audit response | Trail presentation in regulatory response, internal audits, and external audits |
| Continuous verification of configuration compliance via the Audit Manager compliance report | Deviation of the backup policy configuration | Early detection of Vault Lock configuration omissions, unintended shortening of the retention period, etc. |
| Monitoring of malware-scan results via Audit Manager | Overlooking infection detection | Continuous organization-wide grasping of scan results |
| Defense in depth for the report-storage S3 | Tampering/deletion of the report itself | Ensuring the integrity of the report used as an audit trail |
| Consolidation of monitoring/audit features into the Backup account | Configuration inconsistencies due to individual operation in each account | Securing a uniform organization-wide operation/audit foundation |

## Related Other References

- [01-multi-account-architecture.md](./01-multi-account-architecture.md): Multi-account structure (the positioning of the Backup account)
- [02-immutability.md](./02-immutability.md): Details of S3 Object Lock (application to the report-storage bucket)
- [05-malware-protection.md](./05-malware-protection.md): Use of malware-scan results in reports
- [07-log-collection-and-protection.md](./07-log-collection-and-protection.md): Defense in depth for the log-storage S3 (applied equivalently to the report-storage S3)

## Reference: Official Documentation

- [AWS Backup](https://docs.aws.amazon.com/aws-backup/)

For the procedure to enable AWS Backup cross-account monitoring, the procedure to create an Audit Manager report plan, the detailed specifications of the jobs report and compliance report, the output-format specifications, the report-plan quotas, and so on, refer to the latest version of the AWS Backup official documentation.
