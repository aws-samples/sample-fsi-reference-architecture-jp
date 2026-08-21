# Making Backup Data Immutable (Vault Lock / S3 Object Lock)

## Overview

This reference presents the design adopted by this skill for making backup data immutable (granting resistance to tampering and deletion). From a ransomware-resilience perspective, building a configuration where backup data is not deleted or tampered with even if an attacker seizes an account's administrator privileges becomes the last line of defense for recovery.

As the primary features for realizing immutability, AWS Backup's **Vault Lock** (for backup data stored in a Backup vault) and Amazon S3's **S3 Object Lock** (for objects stored in an S3 bucket, usable for log data and the like) are provided. This reference organizes the characteristics of both features, the decision between compliance mode and governance mode, the design of the retention period, the combination of defense in depth, and the relationship with the LAG vault.

For placement in the multi-account structure, refer to [01-multi-account-architecture.md](./01-multi-account-architecture.md); for the application of Object Lock in the context of log protection, refer to [07-log-collection-and-protection.md](./07-log-collection-and-protection.md).

## Foundational Mechanism: Tamper/Deletion Resistance via WORM Protection

Vault Lock and S3 Object Lock both protect data with the **WORM (Write Once, Read Many)** model. Backup data or objects, once written, cannot be deleted or overwritten by anyone within the configured retention period (depending on the mode, not even changeable by AWS Support).

From a ransomware-resilience perspective, they deliver the following effects.

- Even if an attacker seizes account administrator privileges, backups within the retention period cannot be deleted
- Prevents loss of backups due to insider fraud or erroneous operation
- Because not even the root user can shorten the retention period, it is also resistant to privilege-control mistakes within the organization

However, Vault Lock and S3 Object Lock are **separate features with different protection targets**. In this configuration, the two are used differently according to the protection target.

| Feature | Protection target | Main use |
|---|---|---|
| AWS Backup Vault Lock | Backup data (recovery points) stored in a Backup vault | Protection of backups taken with AWS Backup |
| Amazon S3 Object Lock | Objects stored in an S3 bucket | Protection of log data (CloudTrail, Config, VPC Flow Logs, etc.), protection of direct S3 backups from on-premises |

## AWS Backup Vault Lock

### Overview

AWS Backup Vault Lock is a feature that realizes WORM protection for a Backup vault. When Vault Lock is enabled, the recovery points within the Vault can no longer be deleted or changed within the configured retention period.

Vault Lock is provided as a standard feature of AWS Backup and incurs no additional charge. A conformance evaluation for use in environments under SEC 17a-4, CFTC, and FINRA regulations has been performed by Cohasset Associates, making it a feature that is easy to adopt even at financial institutions where regulatory compliance is required.

### Vault Lock modes

Vault Lock has the following two modes.

| Mode | Overview | Main use |
|---|---|---|
| **Governance mode** | The Lock cannot be released or changed at all unless by a user with specific IAM privileges | Can be used when you want to meet the organization's governance requirements while leaving change privileges with specific administrators |
| **Compliance mode** | After the grace time (cooling-off period) elapses, the Lock cannot be released or changed by any user/privilege, nor from the AWS side | Can be used when regulatory compliance is strictly required and tampering/deletion can absolutely not be tolerated |

The **grace time** of compliance mode is the grace period set immediately after Vault Lock is enabled. During the grace time, it is possible to change the Vault Lock settings or release the Lock itself, but once the grace time elapses, those operations can no longer be performed at all.

### Judgment axes for mode selection

From the perspectives of ransomware resilience and the regulatory compliance of financial institutions, this skill **recommends the adoption of Compliance mode as the basic configuration**. The reasons are as follows.

- Even if an attacker seizes administrator privileges, with compliance mode the release of the Lock and the shortening of the retention period are impossible, and the strongest protection as a ransomware-resilience measure is obtained
- In business systems that require regulatory compliance such as SEC 17a-4, there are many cases where compliance mode is necessary to meet the regulatory requirements
- It is also protected from the risks of insider fraud and erroneous operation

However, when adopting compliance mode, note the following points.

- Once the grace time elapses, changing the retention period or releasing the Lock is entirely impossible, so **the retention period must be set carefully**
- If the retention period is set too long, there is a risk that storage costs will swell beyond expectations, so set an appropriate period after comparing against business and regulatory requirements
- If a setting where the retention period becomes "indefinite (Always)" is applied by mistake, recovery points can never be deleted, and costs accumulate

Governance mode is an option to adopt when you want to leave operational flexibility, or at the verification stage before full operation. However, from a ransomware-resilience perspective, because the risk remains that the Lock could be released if an attacker seizes IAM privileges, permanent adoption in a production environment is not recommended.

### Design of the retention period

In Vault Lock, the following two kinds of retention periods are involved.

| Retention period | Overview |
|---|---|
| **Vault Lock's minimum / maximum retention period** | The range of retention period, set on the Vault Lock itself, that the recovery points within the Vault must follow |
| **Backup lifecycle retention period** | The individual retention period set on the backup-plan side at the time of each backup acquisition |

The two operate independently, but a backup lifecycle setting that violates Vault Lock's minimum/maximum retention period is not permitted. At design time, consider the following.

- Set Vault Lock's retention period by working backward from business and regulatory requirements (e.g., a 7-year storage obligation)
- Design the backup-lifecycle-side retention period uniformly as well so that it falls within Vault Lock's range
- For cost optimization, also consider migration to cold storage via lifecycle management (however, since in compliance mode the post-migration retention period is also subject to the Lock, design the migration carefully)

## Amazon S3 Object Lock

### Overview

S3 Object Lock is a feature that realizes WORM protection for objects stored in an S3 bucket. This skill uses it for the protection of S3 buckets that store log data (CloudTrail, Config, VPC Flow Logs, etc.) and for the protection of data backed up directly from an on-premises environment to S3.

As with Vault Lock, a conformance evaluation for the SEC 17a-4, CFTC, and FINRA regulations has been performed by Cohasset Associates.

### Retention period and Legal hold

In S3 Object Lock, the retention of objects is managed by the following two methods.

| Feature | Overview |
|---|---|
| **Retention period** | Sets a fixed retention period on individual objects. During the period, the object cannot be deleted or overwritten. It is also possible to set a default retention period at the bucket level |
| **Legal hold** | Without setting a deadline, it maintains the protection of an object until it is explicitly released. It is independent of the retention period, and the two can also be used together |

From the perspectives of ransomware resilience and regulatory compliance, the setting of a retention period via Retention period is the basis. Legal hold is an auxiliary feature used when "a need has arisen to protect a specific object without a deadline" in litigation response or audit response.

### Retention mode

The retention period has two modes, as with Vault Lock.

| Mode | Overview |
|---|---|
| **Governance mode** | A user with special IAM privileges can change or delete the retention period |
| **Compliance mode** | No user (including the AWS account's root user) can delete or change it during the retention period |

From the perspectives of ransomware resilience and the regulatory compliance of financial institutions, this skill **recommends the adoption of Compliance mode as the basic configuration**. The judgment axes are the same as for Vault Lock; to ensure resistance against an attacker's seizure of IAM privileges, Compliance mode is necessary.

### Combination with S3 Versioning (prerequisite)

S3 Object Lock **operates only on a bucket where S3 Versioning is enabled**. This is because Object Lock has a mechanism that applies protection per object version.

The combination of S3 Versioning and Object Lock realizes the following protection.

- When an object with the same key is overwritten, a new version is added, but the protected old version is retained
- Even if a delete operation is performed, the protected version is not deleted, and only a delete marker is added

## Combination of Defense in Depth

For ransomware resilience, we recommend adopting defense in depth that combines multiple protection mechanisms, rather than Vault Lock or Object Lock alone. This is to realize a configuration that is protected by other layers even if a single defense layer is breached.

### Defense in depth for backup data (AWS Backup)

| Protection layer | Role |
|---|---|
| Vault Lock (Compliance mode) | WORM-protects the recovery points within the Backup vault |
| Cross-account copy | Prevents loss of backups within the business account alone (see [01-multi-account-architecture.md](./01-multi-account-architecture.md)) |
| KMS encryption (an independent CMK per account) | Prevents decryption of copy-destination data even if an attacker seizes the key of a specific account (see [04-encryption-strategy.md](./04-encryption-strategy.md)) |
| Deny of Vault deletion operations via SCP | Preventively denies the Vault deletion action at the Organizations level (see [06-policy-and-access-control.md](./06-policy-and-access-control.md)) |

### Defense in depth for log data (Amazon S3)

| Protection layer | Role |
|---|---|
| S3 Object Lock (Compliance mode) | WORM-protects objects |
| S3 Versioning | Retains old versions even if there is an overwrite or deletion |
| MFA Delete | The complete deletion of a version requires MFA authentication, effectively preventing deletion by an attacker |
| Deny of S3 bucket deletion / policy change via SCP | Preventively denies destructive operations on the S3 bucket at the Organizations level |

By combining these, the configuration becomes one where data is protected by other layers even if any one defense layer is breached.

## Relationship with the LAG vault

The LAG vault (Logically air-gapped vault) is a Vault where immutability equivalent to Vault Lock is **enforced from the point of creation**. There is no need to go through the procedure of configuring Vault Lock on a regular Backup vault; tamper/deletion resistance is built in at the point the LAG vault is created.

| Item | Regular Backup vault + Vault Lock | LAG vault |
|---|---|---|
| Application of immutability | After Vault creation, Vault Lock must be separately enabled | Automatically applied at the point of creation |
| Mode selection | Choose from Governance mode / Compliance mode | The equivalent of Compliance mode is enforced |
| Room for setting changes | Changeable during the grace time | Set the minimum/maximum retention period at creation; not changeable thereafter |

When adopting a LAG vault, there is no need to separately configure Vault Lock on the user side; only the retention period needs to be set. For the decision on adopting a LAG vault, refer to "The 3 patterns of configuration choice" in [01-multi-account-architecture.md](./01-multi-account-architecture.md).

## Summary Table of Countermeasure Effects

Let us organize which risks each element covered in this reference is effective against as a ransomware-resilience measure.

| Countermeasure element | Risk defended against | Effective scenario |
|---|---|---|
| Vault Lock (Compliance mode) | Deletion/tampering of backups | When an attacker seizes IAM privileges or root privileges |
| Vault Lock (Governance mode) | Loss of backups due to erroneous operation in normal operations | When the internal erroneous-operation risk is the main concern and you want to leave room for administrator operations in an emergency |
| S3 Object Lock (Compliance mode) | Deletion/tampering of log data | When an attacker obtains privileges to the S3 bucket that is the log-aggregation destination |
| S3 Object Lock (Legal hold) | A need to protect specific objects without a deadline for litigation/audit response | At the occurrence of an incident requiring legal response |
| S3 Versioning | Loss due to object overwrite/deletion | Deletion by erroneous operation or insider fraud |
| MFA Delete | Complete deletion of a version by an attacker | When an attacker seizes the management privileges of the S3 bucket |
| Enforcement of immutability by the LAG vault | Incomplete protection due to a Vault Lock configuration omission | When you want to protect reliably while reducing the operational burden |

## Related Other References

- [01-multi-account-architecture.md](./01-multi-account-architecture.md): Vault placement in the multi-account structure, decisions on adopting a LAG vault
- [04-encryption-strategy.md](./04-encryption-strategy.md): Details of KMS encryption and key management strategy
- [06-policy-and-access-control.md](./06-policy-and-access-control.md): Policy design such as the Deny of Vault deletion operations via SCP
- [07-log-collection-and-protection.md](./07-log-collection-and-protection.md): Use of Object Lock in log protection

## Reference: Official Documentation

- [AWS Backup](https://docs.aws.amazon.com/aws-backup/)
- [Amazon S3](https://docs.aws.amazon.com/AmazonS3/)

For the behavior specifications of AWS Backup Vault Lock's grace time, the details of retention-period settings in compliance mode, the compliance evaluation report by Cohasset Associates, the configuration procedure for S3 Object Lock's Retention period and Legal hold, the details of the combination with S3 Versioning, and so on, refer to the latest version of the AWS Backup and Amazon S3 official documentation.
