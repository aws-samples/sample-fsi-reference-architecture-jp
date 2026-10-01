# Backup Architecture with a Multi-Account Structure

## Overview

This reference presents the overall picture of the ransomware-resilient backup architecture adopted by this skill. Through a multi-account, multi-Region structure centered on AWS Backup, it takes backups of the workloads of business systems operating within the organization and protects them in a form that gives them resistance to tampering and deletion.

After first organizing the foundational mechanism that underpins the architecture (the integration of AWS Backup and AWS Organizations), it then explains, in order, the account structure, data flow, application of the LAG vault, Region strategy, encryption premises, and centralized management at the organization level. For detailed policy design, refer to [06-policy-and-access-control.md](./06-policy-and-access-control.md); for encryption details, [04-encryption-strategy.md](./04-encryption-strategy.md); for Vault Lock details, [02-immutability.md](./02-immutability.md); and for backup plan design, [03-backup-plan-design.md](./03-backup-plan-design.md).

## Foundational Mechanism: Organization-Wide Backup Management with AWS Backup

The foundation of backup acquisition and protection adopted by this skill is **organization-wide management that combines the cross-account management feature of AWS Backup with the backup policies of AWS Organizations**. Among the multiple backup means AWS provides (AWS Backup, per-service native backup features, third-party products, etc.), this is selected and recommended as a configuration that makes it easy to apply uniform backup requirements to the many business accounts within the organization.

### Overall picture of the adopted mechanism

Backup acquisition and protection within the organization is realized by the following mechanism.

```
[Organizations management account]
        │
        │ AWS Organizations
        │ (organization management)
        ▼
[Backup account]
        │ ・Defines the backup policy for the entire organization
        │ ・Delegated the management of AWS Backup from Organizations
        │
        │ Applies the backup policy to an OU or account
        ▼
[Business accounts (multiple)]
        │ ・From the applied backup policy, a corresponding backup plan is created
        │ ・AWS Backup executes backups according to the backup plan
        │
        ▼
   Backup acquisition
   (stored in a Backup vault)
        │
        │ Cross-Region / cross-account copy
        ▼
   Isolation account / Osaka Region / recovery account
```

### The relationship between backup policy and backup plan

Let us organize the concepts important to understanding this configuration.

| Concept | Providing service | Role |
|---|---|---|
| **Backup policy** | AWS Organizations | The definition of backup requirements applied to the entire organization or an OU (describing the backup plan definition, resource assignment, lifecycle, etc. in JSON) |
| **Backup plan** | AWS Backup | A policy that defines backup requirements and is applied to the protection of AWS resources. When a backup policy is applied to an OU or account, a corresponding backup plan is created in each business account |
| **Backup rule** | AWS Backup | The individual rules that compose a backup plan (acquisition frequency, lifecycle, storage-destination Vault, copy destination, etc.) |
| **Backup vault** | AWS Backup | The storage destination for backup data |

Through this mechanism, by changing the backup policy managed in the Backup account, the backup behavior of all business accounts within the organization can be changed in a centralized manner. There is no need to set a backup plan individually in each business account, and controls such as backup immutability, remote storage, and redundancy can be realized effectively.

### Delegation to the Backup account

In this configuration, the management privileges for AWS Backup are delegated from the Organizations management account to the Backup account (the delegated administrator feature of AWS Backup). The delegated Backup account becomes able to manage the backup policy for the entire organization, and separation of duties from the Organizations management account is realized.

### How to select resources to back up

Among the resources within each business account, what to make a backup target is specified by the resource assignment to the backup plan (tag-based, resource-type-based, etc.). For example, in the tag-based case, operations that target only resources with a specific tag are possible.

For specific tag operations and the judgment axes for target selection, refer to [03-backup-plan-design.md](./03-backup-plan-design.md).

## Account Structure

In the ransomware-resilient backup architecture, the following set of accounts with separated duties are combined.

### Accounts directly involved in backups

| Account | Role |
|---|---|
| Organizations management account | The account that manages AWS Organizations. It handles the configuration of SCPs for the entire organization, the delegation of backup management via AWS Backup to the Backup account, the configuration of the organization trail (CloudTrail), and so on |
| Backup account | Delegated the management of AWS Backup from Organizations, it centrally manages the backup policy for the entire organization. It also has the role of monitoring backup/copy/restore jobs within the organization across the board |
| Business accounts (multiple) | The accounts hosting the workloads of the various business systems operating within the organization (existing business accounts, not accounts newly created for ransomware resilience). Backups are taken via AWS Backup according to the backup plan created based on the backup policy applied from the Backup account |
| Isolation account | An additional protection destination for backups, separated from the business accounts. It receives replicas from the business accounts via cross-account copy and ensures tamper/deletion resistance via Vault Lock |
| Recovery account | An environment with the role of forensic analysis, restore testing, and confirmation during recovery in an emergency |

### Peripheral accounts (the scope of other reference files)

| Account | Role |
|---|---|
| Security account | Centralized management of security tools such as Amazon GuardDuty and AWS Security Hub (out of scope for this skill) |
| Log Archive account | A dedicated aggregation destination for log data such as CloudTrail, AWS Config, and VPC Flow Logs (details in [07-log-collection-and-protection.md](./07-log-collection-and-protection.md)) |

The duties of each account are segmented in accordance with the principles of Separation of Duties and Least Privilege, and are designed so that the breach of a specific account does not ripple across the entire organization.

### Resources placed in each account

| Account | Resources placed |
|---|---|
| Organizations management account | SCPs, organization trail configuration |
| Backup account | Backup policy, monitoring of the backup status for the entire organization |
| Business accounts | Business workloads, the backup plan created from the backup policy, the Backup vault of each Region, KMS CMK, the IAM Role for executing Backup |
| Isolation account | Backup vault (Vault Lock applied), KMS CMK, the Vault access policy that accepts cross-account copies from the business accounts |
| Recovery account | Backup vault, KMS CMK, the IAM Role for executing restores, the Vault access policy that accepts copies from the isolation account |

## Data Flow

### The basic flow and implementation mechanism

The backups taken in each business account are replicated and protected via the following paths.

```
Business account (Tokyo)
  ├─→ Business account (Osaka)        [cross-Region copy]
  └─→ Isolation account (Tokyo)       [cross-account copy]
        └─→ Recovery account (Tokyo)  [cross-account copy / standing copy in normal times]
```

Each copy is executed by the Copy Action setting within the backup plan. By describing, within the backup policy (managed in the Backup account), a setting to copy backups taken in Tokyo to the Backup vault of the Osaka Region or the Backup vault of the isolation account, a corresponding copy is created each time a backup is taken in a business account.

Each copy is re-encrypted with an independent KMS CMK managed in the copy-destination account and copy-destination Region (see [04-encryption-strategy.md](./04-encryption-strategy.md)). By permitting the `backup:CopyIntoBackupVault` action in the copy-destination Vault's access policy, the cross-account copy is established (see [06-policy-and-access-control.md](./06-policy-and-access-control.md)).

### The purpose of each copy path

| Copy path | Main purpose | Secondary effect |
|---|---|---|
| Business account (Tokyo) → Business account (Osaka) | 3-2-1 rule compliance (a different Region) | DR (Region failure, natural disaster) measure |
| Business account (Tokyo) → Isolation account (Tokyo) | 3-2-1 rule compliance (a different account) | Security-attack measure (account breach, insider fraud, ransomware) |
| Isolation account → Recovery account | A foundation for rapid recovery in an emergency | A venue for forensic analysis and restore testing |

It takes the form of "distributing backups according to the 3-2-1 rule while, at the same time, account separation also functions as a ransomware-resilience measure." The merit of this configuration is that both disaster recovery (DR) and security-attack measures can be realized with the same configuration.

### Copy policy from the isolation account to the recovery account

This knowledge adopts, as the basic configuration, a design that copies continuously in normal times in order to enable rapid recovery in an emergency. It is also possible to take a design strategy of starting the copy after an incident occurs, but because the start of recovery is delayed by the amount of the copy time required, it becomes a trade-off between cost and the rapidity of starting recovery. We recommend selecting strategically according to each financial institution's recovery-time requirements, internal rules, and so on. Note that the time required until recovery completes (RTO) is ensured by including not only the backup/copy design but also operational elements such as restore, switchover, and verification; this item is positioned as contributing to the readiness to start recovery, which is a portion of that.

Alternative approaches and their trade-offs:

| Approach | Merit | Demerit |
|---|---|---|
| Continuous copy in normal times | Can immediately begin restoration in an emergency; recovery starts rapidly | Double storage cost |
| On-demand copy when an incident occurs | Cost optimization | Copy time is needed before recovery can begin; the start of recovery is delayed |
| LAG vault + RAM sharing (advanced configuration) | No copy needed and immediate access possible, reduced storage cost, and approval control via the Multi-party approval described later is also possible | RDS not supported (described later) |

In an environment where a LAG vault is available, the advanced configuration is preferable, but due to current constraints, the configuration choice follows the judgment axes in the next section.

## Decisions on Adopting a LAG vault

### What a LAG vault is

The **Logically air-gapped vault (LAG vault)** is a type of Vault provided by AWS Backup that has characteristics particularly effective for ransomware resilience. Compared to a regular Backup vault, it has the following features.

1. **Resource sharing via AWS Resource Access Manager (RAM)**: Without physically copying the backup, it can be shared from another account via RAM and accessed. This realizes reduced storage cost and shortened recovery time
2. **Encryption with an AWS owned key**: It is encrypted with an AWS owned key rather than a KMS key managed by the customer. This makes it possible to prevent the backup data from becoming undecryptable even if an attacker seizes the customer account and performs an erroneous or malicious deletion of the KMS key
3. **Multi-party approval**: A feature that requires the approval of multiple people at restore time; even if a single attacker obtains restore privileges, an effect of preventing unauthorized restoration can be expected.
4. **Immutability is enforced**: A LAG vault has tamper/deletion resistance built in at the point of creation, and there is no need to separately configure Vault Lock (for details, see [02-immutability.md](./02-immutability.md))

The combination of a regular Backup vault and Vault Lock is also effective as a ransomware-resilience measure, but the LAG vault is positioned as a further-reaching protection mechanism.

### Resource types supported by the LAG vault

The LAG vault is a highly effective feature for ransomware resilience, but it does not support all the AWS resources that AWS Backup protects. Therefore, it is not always possible to store all resources within the organization uniformly in a LAG vault, and a configuration choice according to the support status per resource type is required.

For example, among the major resources widely used in financial institutions, Amazon RDS (single instance / cluster) is not supported by the LAG vault (as of the time of writing, June 2026). In an environment using RDS in business systems, because RDS backups cannot be protected by a LAG vault, this becomes a candidate for the hybrid configuration or basic configuration shown later in "The 3 patterns of configuration choice."

Because the resource types supported by the LAG vault change from time to time due to AWS feature enhancements, we recommend, at design time and not limited to RDS, checking the support status of the resource types to be protected in the official AWS documentation as appropriate.

### The 3 patterns of configuration choice

According to the situation of the resource types supported by the LAG vault, select the isolation account's Vault configuration from 3 patterns.

| Configuration pattern | Target environment | Isolation account's Vault configuration | Notes |
|---|---|---|---|
| **Basic configuration** | An environment where LAG-vault-unsupported resources (RDS, etc.) are the center of the protection targets | Regular Backup vault + Vault Lock | All resources can be protected uniformly. Tamper/deletion resistance is ensured by Vault Lock's compliance mode |
| **Advanced configuration** | An environment composed only of resources supported by the LAG vault | LAG vault (+ RAM sharing + Multi-party approval) | The characteristics of the LAG vault can be enjoyed |
| **Hybrid configuration** | An environment mixing LAG-vault-supported and unsupported resources | LAG-vault-supported resources in a LAG vault, unsupported resources (RDS, etc.) split-protected in a regular Vault + Vault Lock | Selects the optimal protection mechanism per resource type |

### Supplementary notes when choosing a configuration

- Rather than judging uniformly that "because there are LAG-vault-unsupported resources, everything goes into a regular Vault," the essence of the hybrid configuration is an approach that selects the optimal protection mechanism per resource
- If, in the future, currently unsupported resources such as RDS become supported by the LAG vault, there is room to consider a migration from the hybrid configuration to the advanced configuration
- Because the resource types supported by the LAG vault may change due to AWS feature enhancements, check the latest information in the official documentation at design time
- When adopting a LAG vault, malware scanning of Amazon EC2 recovery points cannot use incremental scanning and requires a full scan, so we recommend also considering the operational-cost and execution-time perspectives (for details, see [05-malware-protection.md](./05-malware-protection.md))

## Region Strategy

The Regions are based on Tokyo (primary) + Osaka (the cross-Region copy destination).

| Region | Role |
|---|---|
| Tokyo (ap-northeast-1) | The primary Region of the business accounts, the isolation account, the recovery account |
| Osaka (ap-northeast-3) | The cross-Region copy destination of the business accounts (DR support) |

The requirement of "a different location/medium" in the 3-2-1 rule is met by Region distribution. Even for financial institutions that have a requirement to store data within Japan, this can be addressed by leveraging both the Tokyo and Osaka Regions.

## Encryption Premises

In this configuration, KMS CMKs managed individually in each account and each Region are used for the encryption of backup data. This is a design that prevents the decryption of all data by the seizure of a single key, by separating the management entity of the encryption key per account.

### Placement of the KMS CMK

| Placement location | Management entity | Use |
|---|---|---|
| KMS CMK of the business account (Tokyo) | The administrator of the business account | Encryption of backups taken in the Tokyo Region |
| KMS CMK of the business account (Osaka) | The administrator of the business account | Re-encryption at the time of copy to the Osaka Region |
| KMS CMK of the isolation account | The administrator of the isolation account | Re-encryption at the time of copy to the isolation account |
| KMS CMK of the recovery account | The administrator of the recovery account | Re-encryption at the time of copy to the recovery account |

At the time of executing a cross-account/cross-Region copy, it is re-encrypted with the copy destination's key. This separates the entity managing the copy-source key from the entity managing the copy-destination key, resulting in a structure where, even if an attacker seizes the copy-source key, the copy-destination data cannot be decrypted.

Note that when a LAG vault is adopted, an AWS owned key is used, so it falls outside the above configuration (see also [02-immutability.md](./02-immutability.md)).

For detailed key policy design, refer to [04-encryption-strategy.md](./04-encryption-strategy.md) and [06-policy-and-access-control.md](./06-policy-and-access-control.md).

## Centralized Management at the Organization Level

### Centralized management via the backup policy

As described above, through the backup policy of AWS Organizations, the AWS Backup settings common to the entire organization can be centrally managed from the Backup account. Various settings, including malware scanning, are also defined in the backup policy and can be applied collectively to the entire organization.

For details on the organization-level configuration of each feature, refer to each feature's reference:
- Malware scanning: [05-malware-protection.md](./05-malware-protection.md)
- Aggregation of log collection (CloudTrail / Config): [07-log-collection-and-protection.md](./07-log-collection-and-protection.md)
- Monitoring of backup operations: [08-monitoring-and-audit.md](./08-monitoring-and-audit.md)

### Preventive controls via SCP

By applying an SCP (Service Control Policy) from the Organizations management account to the accounts under the organization, even when an attacker seizes a workload account, destructive operations on backups and logs can be preventively denied.

For the SCP design that becomes important in the context of ransomware resilience (preventing CloudTrail from being stopped, preventing Vault deletion, preventing KMS key deletion, etc.), refer to [06-policy-and-access-control.md](./06-policy-and-access-control.md).

## Summary Table of Countermeasure Effects

Let us organize which risks each element of this configuration is effective against as a ransomware-resilience measure.

| Countermeasure element | Risk defended against | Effective scenario |
|---|---|---|
| Account separation (business / isolation / recovery) | Damage to backup data and obstruction of recovery operations when a business account is breached | When an attacker seizes the privileges of a business account |
| Cross-account copy (business → isolation) | Loss of backups within the business account alone | Account breach, insider fraud, erroneous operation |
| Cross-Region copy (Tokyo → Osaka) | Data loss from a Region failure or large-scale disaster | A situation where an entire Region becomes unavailable |
| Vault Lock (isolation account) | Deletion/tampering of backups | When an attacker obtains Vault operation privileges |
| Encryption with the LAG vault's AWS owned key (advanced configuration) | Data becoming undecryptable due to deletion/disabling of the customer KMS key | When an attacker maliciously deletes the KMS key |
| The LAG vault's Multi-party approval (advanced configuration) | Unauthorized restoration by a single attacker | When an attacker obtains restore privileges |
| Continuous copy to the recovery account in normal times | Delay in starting recovery in an emergency | When there is a need to begin restoration immediately in an emergency |
| Centralized management by the Backup account | Configuration omissions/inconsistencies in each business account | When there is a need to ensure uniform protection across the entire organization |
| Individual KMS CMK per account and per Region | Decryption of all data by the seizure of a single key | When an attacker seizes the KMS key of a specific account |
| Re-encryption at the time of cross-account copy | Decryption of copy-destination data by an attacker who has seized the copy-source key | Even when a business account is breached, the data on the isolation account side is protected by an independent key |

## Related Other References

- [02-immutability.md](./02-immutability.md): Design details of Vault Lock and Object Lock
- [03-backup-plan-design.md](./03-backup-plan-design.md): Backup plan design (acquisition frequency, target selection, retention period)
- [04-encryption-strategy.md](./04-encryption-strategy.md): Details of KMS encryption and key management strategy
- [05-malware-protection.md](./05-malware-protection.md): Design of malware scanning for backups
- [06-policy-and-access-control.md](./06-policy-and-access-control.md): The 6 policy control points needed for cross-account copy, details of SCP
- [07-log-collection-and-protection.md](./07-log-collection-and-protection.md): Log collection and protection
- [08-monitoring-and-audit.md](./08-monitoring-and-audit.md): Monitoring and audit reporting of backup operations

## Reference: Official Documentation

- [AWS Backup](https://docs.aws.amazon.com/aws-backup/)
- [AWS Organizations](https://docs.aws.amazon.com/organizations/)
- [AWS Key Management Service](https://docs.aws.amazon.com/kms/)

For the per-resource-type support status of the AWS Backup Logically air-gapped vault, the specifications of Multi-party approval, the configuration procedure for cross-account copy, the backup policy JSON syntax of AWS Organizations, and so on, refer to the latest version of the AWS Backup and AWS Organizations official documentation.
