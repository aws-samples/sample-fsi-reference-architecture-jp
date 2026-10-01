# Encryption Strategy for Backup Data (KMS / Key Management)

## Overview

This reference presents the encryption strategy for backup data adopted by this skill. In the context of ransomware resilience, encryption becomes an important element of defense in depth: "building a configuration where, even if an attacker seizes an account, the copy-destination backup data cannot be decrypted."

This reference organizes the foundational mechanism of encryption in AWS Backup, the per-account/per-Region KMS CMK separation strategy this skill adopts, the encryption behavior at the time of cross-account/cross-Region copy, the main perspectives of the key management strategy, the positioning of the LAG vault and the AWS owned key, and design decisions in the context of financial institutions.

For the placement of KMS keys in the multi-account structure, refer to [01-multi-account-architecture.md](./01-multi-account-architecture.md); for the details of KMS key policy design, refer to [06-policy-and-access-control.md](./06-policy-and-access-control.md).

## Foundational Mechanism: Encryption in AWS Backup

### Whether independent encryption is supported

The encryption of AWS Backup behaves differently depending on the target resource type. For resource types that are fully managed by AWS Backup, they are encrypted independently with the KMS key set on the Backup vault (independent encryption). On the other hand, for resource types that are not fully managed by AWS Backup, they are encrypted by inheriting the encryption key of the source resource as is.

| Category | Main resource types (at the time of writing) | Encryption behavior |
|---|---|---|
| **Independent encryption supported** | Amazon S3, Amazon EFS, Amazon DynamoDB (when Advanced backup is enabled), Amazon Timestream, AWS CloudFormation, SAP HANA on Amazon EC2, VMware virtual machines | Encrypted with the KMS key set on the Backup vault. Independent of the source resource's encryption method |
| **Independent encryption not supported** | Amazon EBS, Amazon EC2, Amazon RDS, Amazon Aurora, Amazon DocumentDB, Amazon Neptune, Amazon Redshift, AWS Storage Gateway, Amazon FSx, Amazon DynamoDB (when Advanced backup is disabled), etc. | The encryption key of the source resource (or no encryption) is inherited |

Because the supported resource types may change due to AWS feature enhancements, we recommend referring to the latest version of [Encryption for backups in AWS Backup](https://docs.aws.amazon.com/aws-backup/latest/devguide/encryption.html) in the AWS Backup official documentation at design time.

When independent encryption is applied, AWS Backup encrypts the backup data with the AES-256 encryption algorithm.

### Encryption behavior at the time of cross-account/cross-Region copy

In a cross-account/cross-Region copy by AWS Backup, it is encrypted with the KMS key set on the copy-destination Backup vault. This behavior is common regardless of whether the copy source is an independent-encryption-supported or unsupported resource.

In a cross-account copy, for an independent-encryption-supported resource, a KMS CMK or AWS Backup's AWS managed key (`aws/backup`) can be used. On the other hand, for an independent-encryption-unsupported resource, a KMS CMK or the corresponding service-specific managed key (e.g., `aws/ebs` for Amazon EBS) is required. Because the AWS managed key has an unchangeable (immutable) key policy, the specification is that it cannot be used for the cross-account copy of independent-encryption-unsupported resources.

For the detailed behavior and prerequisites, we recommend referring to the latest version of [Encryption for a backup copy to a different account or AWS Region](https://docs.aws.amazon.com/aws-backup/latest/devguide/encryption.html) in the AWS Backup official documentation.

### Important implications for the design

Let us organize what impact whether independent encryption is supported has in the configuration this skill adopts (a multi-account structure premised on cross-account/cross-Region copy).

- **Backups after a cross-account/cross-Region copy**: Regardless of whether independent encryption is supported, they are re-encrypted with the KMS CMK set on the copy-destination Backup vault. As a result, the backup data stored at copy destinations such as the isolation account, the recovery account, and the Osaka Region forms a configuration where encryption that is centrally controlled by this skill's per-account/per-Region KMS CMK strategy is reliably realized
- **The initial backup acquisition in the business account**: While independent-encryption-supported resources are encrypted with the KMS CMK set on the Backup vault, independent-encryption-unsupported resources (Amazon EBS, Amazon RDS, Amazon Aurora, etc.) have the specification of inheriting the source resource's encryption key. Therefore, if the source resource itself is not encrypted with a KMS CMK, there are cases where the initial backup in the business account is also not encrypted

The difference in encryption behavior at the initial backup in the business account does not become a practical problem if the resource-encryption rules within the organization are thoroughly enforced. On the other hand, if unencrypted resources remain in the existing environment, we recommend also considering the encryption of the source resource itself. Because the copy-destination data is re-encrypted with the copy-destination vault's KMS CMK as described above, the robustness of encryption for the entire multi-account structure this skill recommends is maintained.

## The Key Strategy This Skill Adopts: Per-Account/Per-Region KMS CMK Separation

### The adopted strategy

This skill adopts and recommends a strategy of setting a KMS CMK managed individually in each account and each Region on the Backup vault. We recommend referring to [01-multi-account-architecture.md](./01-multi-account-architecture.md) for the specific placement configuration, but it forms a configuration where independent KMS CMKs are placed in each Region of the business account, isolation account, and recovery account, as follows.

### The reasons for adopting this strategy

The strategy of separating the KMS CMK per account and per Region makes it possible to obtain the following merits from the perspective of ransomware-resilience defense in depth.

- **Avoidance of single-key-seizure risk**: Even if an attacker seizes the KMS CMK of a specific account, because the KMS CMK of the copy-destination account and copy-destination Region is managed independently, it becomes possible to prevent the decryption of the copy-destination backup data
- **Realization of separation of duties**: By separating the management entity of the KMS CMK per account (the administrator of the business account, the administrator of the isolation account, the administrator of the recovery account), it forms a configuration where the breach of a specific account's administrator privileges does not ripple to the encryption keys of the entire organization
- **Clarification of the audit unit**: Because KMS API calls are recorded in AWS CloudTrail, by separating the KMS CMK per account, it becomes possible to clearly track which account's key was used and when
- **Avoidance of the KMS managed key constraint**: Because the AWS managed key has an unchangeable key policy and cannot be used for the cross-account copy of independent-encryption-unsupported resources, by adopting a KMS CMK, a uniform copy strategy can be realized without limiting the protected resource types

### Re-encryption at the time of cross-account/cross-Region copy

In this configuration, in all of the copy from the business account to the isolation account, the copy from the business account to the Osaka Region, and the copy from the isolation account to the recovery account, it is re-encrypted with the KMS CMK set on the copy-destination vault. As a result, it forms a structure where, even an attacker who has seized the copy-source key cannot decrypt the copy-destination data, because it is protected by an independent KMS CMK.

To establish a cross-account copy, the key policy of the copy-destination KMS CMK must set the appropriate permission so that the copy-source account's IAM role can use the copy-destination KMS CMK. For details, we recommend referring to [06-policy-and-access-control.md](./06-policy-and-access-control.md).

## Main Perspectives of the Key Management Strategy

In the key policy design and operation of the KMS CMK, we recommend considering the following perspectives in the context of ransomware resilience. For the specific key policy design details, we recommend referring to [06-policy-and-access-control.md](./06-policy-and-access-control.md).

- **Separation of key-using entities**: Design the backup-execution role, the restore-execution role, and the key-administrator role as separate IAM roles, and via the key policy grant each role only the minimum necessary privileges
- **Minimization of the permission scope for cross-account copy**: Narrow the usage permission to the copy-source account to the scope necessary for copy operations, such as `kms:Encrypt`, `kms:Decrypt`, `kms:ReEncrypt*`, and `kms:GenerateDataKey*`
- **Configuration of key rotation**: By enabling automatic key rotation of the KMS CMK, reduce the risk of the same key material continuing to be used for a long period
- **Ensuring resistance to key deletion**: Although a deletion waiting period is set for the deletion of a KMS CMK, as an additional defense against the risk of an attacker scheduling a deletion, we recommend incorporating a preventive Deny of `kms:ScheduleKeyDeletion` via SCP (for details, see [06-policy-and-access-control.md](./06-policy-and-access-control.md))
- **Key-usage auditing via CloudTrail**: Record the API calls of all KMS CMKs in CloudTrail and establish a system that can detect unexpected key usage and deletion attempts

## Positioning of the LAG vault and the AWS Owned Key

The LAG vault (Logically air-gapped vault), while being a type of Backup vault, has the specification that an **AWS owned key** is used for encryption. This means it is encrypted not with a KMS CMK managed on the customer-account side, but with a key owned and managed by AWS.

### A comparison of the LAG vault's AWS owned key encryption with the customer KMS CMK configuration

| Item | Customer KMS CMK configuration (regular Backup vault) | LAG vault (AWS owned key) |
|---|---|---|
| Key management entity | An administrator within the customer account | AWS (the customer does not have management privileges) |
| Key policy configuration | Designed and operated on the customer side | Not changeable from the customer side |
| Key deletion risk | If an attacker seizes the customer account, the risk of deletion remains (mitigated by preventive controls such as SCP) | A deletion operation from the customer side itself does not succeed |

### The significance this specification has from a ransomware-resilience perspective

In a normal KMS CMK configuration, if an attacker seizes the administrator privileges of the customer account, the threat scenario of attempting to delete or disable the KMS CMK remains. Because deleting a KMS CMK makes the decryption of backup data impossible, it leads to particularly serious damage even among ransomware attacks.

Because the LAG vault is encrypted with an AWS owned key, the customer-side key-deletion risk itself is eliminated. This is one of the reasons the LAG vault is positioned as a robust protection mechanism for ransomware resilience. On the other hand, because the customer-side key management flexibility of a KMS CMK configuration (key policy design, rotation configuration, etc.) is not obtained, we recommend making the adoption decision after confirming consistency with the organization's key management policy.

In a hybrid configuration (LAG-vault-supported resources in a LAG vault, unsupported resources in a regular Vault + Vault Lock), it forms a configuration where the encryption management entity is split per resource type. For details, refer to "The 3 patterns of configuration choice" in [01-multi-account-architecture.md](./01-multi-account-architecture.md).

## Design Decisions in the Context of Financial Institutions

### Consistency with the organization's key management policy

At financial institutions, there are many cases where the management policy for encryption keys is stipulated as an internal rule. When adopting the KMS CMK strategy this skill recommends, we recommend confirming consistency with the internal rules from the following perspectives.

- Whether the use of a KMS CMK (customer-managed key) is permitted by the internal rules
- Consistency with operational rules such as key policy design, key rotation cycle, and key deletion procedures
- The system for key-usage auditing (the storage period of CloudTrail logs, review cycle, etc.)

### Response to regulatory requirements

At financial institutions, there are many cases where regulatory requirements related to encryption are stipulated. When the encryption of backup data is positioned as part of regulatory compliance, reflect the following points in the design.

- Consistency with the encryption-algorithm strength stipulated by regulatory requirements (AWS Backup's independent encryption adopts AES-256)
- Requirements related to the management of encryption keys (separation of key administrators, storage of key-usage logs, etc.)
- Acquisition of key-usage logs in a state usable as an audit trail

However, the judgment of conformance to specific regulatory clauses is outside this skill's scope, and we recommend deciding in coordination with the organization's regulatory-response and compliance departments.

### Trade-off with key management flexibility when adopting a LAG vault

Because the LAG vault is encrypted with an AWS owned key, the customer-side management flexibility of key policy design, key rotation configuration, etc. is not obtained. When the organization's internal key management policy strictly requires "encryption with a customer-managed key," internal approval may be needed for the adoption of a LAG vault. On the other hand, because the LAG vault is a robust protection mechanism that structurally eliminates the customer-side key-deletion risk, we recommend making the adoption decision based on the merits from a ransomware-resilience perspective and consistency with the internal rules.

## Summary Table of Countermeasure Effects

Let us organize which risks each design element covered in this reference is effective against as a ransomware-resilience measure.

| Design element | Risk defended against | Effective scenario |
|---|---|---|
| Per-account/per-Region KMS CMK separation | Decryption of all data by the seizure of a single key | Prevents the decryption of copy-destination data even when an attacker seizes the KMS CMK of a specific account |
| Re-encryption at the time of cross-account copy | Decryption of copy-destination data by an attacker who has seized the copy-source key | Even when a business account is breached, the data on the isolation account side is protected by an independent KMS CMK |
| Separation of using entities via KMS CMK key policy | Unauthorized operation due to the breach of backup/restore privileges | Risk reduction when an attacker seizes some IAM roles |
| Automatic key rotation | The risk of the same key being used for a long period | Long-term risk reduction such as key leakage |
| Preventive Deny of KMS key deletion via SCP | Making data undecryptable by an attacker's key deletion | An additional defense when an attacker seizes the administrator privileges of the customer account |
| The LAG vault's AWS owned key encryption | Key deletion/disabling by a customer-side operation | Even when the customer-side administrator privileges are breached, a deletion operation of the AWS owned key from the customer side is impossible |
| Key-usage auditing via CloudTrail | Overlooking unexpected key usage or deletion attempts | Detection of attack precursors, post-incident analysis, audit response |

## Related Other References

- [01-multi-account-architecture.md](./01-multi-account-architecture.md): KMS CMK placement in the multi-account structure, the re-encryption policy at the time of cross-account copy
- [02-immutability.md](./02-immutability.md): Linkage with Vault Lock (the combination of encryption and tamper/deletion resistance)
- [06-policy-and-access-control.md](./06-policy-and-access-control.md): KMS key policy design, details of preventive controls via SCP

## Reference: Official Documentation

- [AWS Key Management Service](https://docs.aws.amazon.com/kms/)
- [AWS Backup](https://docs.aws.amazon.com/aws-backup/)

For the independent-encryption-supported resources of AWS Backup, the encryption behavior at the time of cross-account/cross-Region copy, the KMS CMK key policy design details, the difference between the AWS managed key and the customer-managed key, the configuration procedure for automatic key rotation, the KMS API specifications, and so on, refer to the latest version of the AWS Key Management Service and AWS Backup official documentation.
