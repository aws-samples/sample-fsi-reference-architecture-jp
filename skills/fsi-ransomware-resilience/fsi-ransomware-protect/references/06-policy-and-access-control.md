# Policy Design and Access Control (IAM / KMS / Vault Access / SCP)

## Overview

This reference presents the policy design and access control in the backup/data-protection environment adopted by this skill. In the context of ransomware resilience, multi-layered access control that prevents the destruction, tampering, and unauthorized restoration of backup data is necessary even when an attacker seizes an account's administrator privileges. This reference organizes the design philosophy of least privilege and defense in depth, combining multiple policy mechanisms.

This reference organizes the 6 policy control points, the policy coordination for establishing a cross-account copy, preventive controls via SCP, policy design considerations when adopting a LAG vault, and design decisions in the context of financial institutions.

For the placement of each policy in the multi-account structure, refer to [01-multi-account-architecture.md](./01-multi-account-architecture.md); for the KMS encryption strategy, refer to [04-encryption-strategy.md](./04-encryption-strategy.md).

## Foundational Mechanism: Access Control via Defense in Depth

The access control this skill adopts is based on a defense-in-depth design philosophy that combines multiple policy mechanisms. By appropriately combining the following policy mechanisms for each operation of backup, copy, and restore, it realizes a configuration where an unauthorized operation does not succeed with a single policy breach.

| Policy mechanism | Nature | Main role |
|---|---|---|
| **Identity-based policy (IAM policy)** | Tied to a principal (user/role) | Granting privileges to the entity executing the operation |
| **Resource-based policy (KMS key policy, Vault access policy)** | Tied to a resource | Control of usage permission from the resource side |
| **Service Control Policy (SCP)** | Tied to an organization / OU / account under Organizations | Setting a preventive privilege ceiling (Deny-based) |

By combining these, access control is established from the three perspectives of the operating entity, the operation target, and the organization level, and even when an attacker seizes some privileges, it becomes possible to defend the operation at another layer.

## The 6 Policy Control Points

In this skill's multi-account structure, the following 6 policy control points are combined in the design.

### 1. Organizations delegation policy

- **Target**: The delegation setting from the Organizations management account to the Backup account
- **Control content**: By delegating the management privileges of the backup policy for the entire organization to the Backup account, consolidate the normal-time backup management operations into the Backup account
- **Overview of necessary permissions**: Grant the delegated Backup account privileges such as the creation, update, deletion, attachment/detachment to OUs and accounts, listing, and tag management of the backup policy
- **The least-privilege way of thinking**: Adopt an operational control where normal-time backup management is performed from the Backup account and not performed in the Organizations management account, thereby operationally separating the duties of the two accounts

### 2. KMS key policy of the backup-target resource (business-account side)

- **Target**: The KMS CMK within the business account (the key encrypting the backup-target resource)
- **Control content**: Control the decryption privilege of encrypted data, needed when the copy-destination account's AWS Backup creates a backup copy
- **Overview of necessary permissions**: Grant the copy-destination account's AWS Backup role permissions in the scope necessary for copy operations, such as `kms:Decrypt` and `kms:GenerateDataKey*`
- **The least-privilege way of thinking**: By limiting the permission target to the AWS Backup role and narrowing the operation content to only what is necessary for the copy to succeed, prevent unnecessary access to the business account's encryption key

### 3. IAM role (for backup execution, business-account side)

- **Target**: The IAM Role within the business account (the role assumed when AWS Backup executes a backup operation)
- **Control content**: When taking a backup in the business account, control privileges such as the reading of the backup-target resource, saving to the Backup vault, and use of the encryption key
- **Overview of necessary permissions**: Grant snapshot-creation privileges for the backup-target resources (EC2, RDS, S3, etc.), write privileges to the Backup vault, use privileges of the encryption key, and so on
- **The least-privilege way of thinking**: We recommend not granting restore privileges to the backup-execution role. Through the separation of backup/restore duties, prevent the breach of a specific role from rippling all the way to restore operations

### 4. IAM role (for restore execution, recovery-account side)

- **Target**: The IAM Role within the recovery account (the role assumed when AWS Backup executes a restore operation)
- **Control content**: When creating a new resource from a backup in the recovery account, control privileges such as resource creation, tagging, and use of the encryption key
- **Overview of necessary permissions**: Grant creation privileges for the restore-target resource types, use privileges of the recovery account's encryption key, read privileges from the target Backup vault, and so on
- **The least-privilege way of thinking**: Do not grant backup-acquisition privileges to the restore-execution role; limit it to restore operations. Realize the separation of backup/restore duties at the IAM role level

### 5. Vault access policy (resource-based policy)

- **Target**: The Backup vault of the isolation account and recovery account (the copy-destination vault)
- **Control content**: A resource-based policy that controls cross-account access to the Backup vault. To establish a cross-account copy, permit the `backup:CopyIntoBackupVault` action from the copy-source account
- **Overview of necessary permissions**: Permit `backup:CopyIntoBackupVault` to the copy-source account's IAM role (or the organizational unit of Organizations)
- **The least-privilege way of thinking**: As a specification of AWS Backup, the action executable cross-account is limited to only `backup:CopyIntoBackupVault`, and even if other actions are permitted in the Vault access policy, they are denied. As a result, it forms a structure where unauthorized operations on the copy-destination vault (deletion of recovery points, etc.) cannot be executed cross-account

### 6. KMS key policy for Vault encryption (copy-destination-account side)

- **Target**: The KMS CMK of the isolation account and recovery account (the key used for the encryption of the copy-destination vault)
- **Control content**: Control the permission of the encryption operation to the copy-source account, needed for the backup re-encryption at the copy-destination vault
- **Overview of necessary permissions**: Grant the copy-source account's AWS Backup role permissions in the scope necessary for encryption at copy time, such as `kms:Encrypt` and `kms:GenerateDataKey*`
- **The least-privilege way of thinking**: Limit the permission target to the copy-source AWS Backup role and narrow the operation content to only what is necessary for encryption at copy time. Make control using IAM policies the basis for access to each account's KMS key

## Policy Coordination for Establishing a Cross-Account Copy

For a cross-account copy to be established, the multiple policies above need to coordinate with each other. The design is such that the copy fails unless each is correctly configured at a different layer, and as a result, it functions as defense in depth.

| Necessary policy | Layer | Role |
|---|---|---|
| The business account's IAM role (for backup) | Principal side | The privilege to execute the copy operation |
| The business-account-side KMS key policy | Copy-source resource side | Permission to decrypt copy-source data |
| The Vault access policy of the isolation/recovery account | Copy-destination vault side | Permission to accept a copy from cross-account |
| The isolation/recovery-account-side KMS key policy | Copy-destination resource side | Permission to re-encrypt copy-destination data |

Because the copy does not succeed if any one of these 4 layers is missing, even if an attacker breaches some of the policies, it becomes difficult to destroy the entire configuration of the cross-account copy.

## Preventive Controls via SCP

The Service Control Policy (SCP) of Organizations is a mechanism that sets a privilege ceiling on organizations / OUs / accounts under Organizations, and even an IAM role with root-user or administrator privileges within an account cannot execute an action denied by an SCP. This skill recommends leveraging SCP as a preventive control for ransomware resilience.

### SCP design patterns that become important in the context of ransomware resilience

| Control target | Main intent | Example of control |
|---|---|---|
| **Preventing deletion/tampering of the Backup vault** | Prevent the destruction of the backup data itself | Deny destructive operations such as `backup:DeleteBackupVault` and `backup:DeleteRecoveryPoint` |
| **Preventing deletion/disabling of KMS keys** | Prevent making backup data undecryptable by deleting the encryption key | Deny `kms:ScheduleKeyDeletion`, `kms:DisableKey`, etc. |
| **Preventing the stopping/deletion of CloudTrail** | Prevent the erasure of the attacker's activity logs (securing the foundation for forensic response) | Deny `cloudtrail:StopLogging`, `cloudtrail:DeleteTrail`, `cloudtrail:UpdateTrail`, etc. |
| **Preventing the stopping/deletion of Config** | Prevent the erasure of the configuration-change history | Deny `config:DeleteConfigurationRecorder`, `config:StopConfigurationRecorder`, etc. |
| **Preventing the alteration of S3 bucket policies / Object Lock settings** | Prevent the alteration of the log-storage S3 bucket | Restrict `s3:PutBucketPolicy`, `s3:PutBucketObjectLockConfiguration`, etc. |
| **Preventing departure from the organization** | Prevent data exfiltration by the copy-destination account leaving the organization | Deny `organizations:LeaveOrganization` |

## Policy Design Considerations When Adopting a LAG vault

When adopting a LAG vault (Logically air-gapped vault), a policy design different from a regular Backup vault becomes necessary.

### Resource sharing via RAM

While the cross-account copy of a regular Backup vault is controlled by the Vault access policy (a resource-based policy), in a LAG vault, resource sharing is performed using AWS Resource Access Manager (RAM). When using a LAG vault from another account, the RAM resource-sharing configuration and RAM permission design become necessary.

When adopting a LAG vault, we recommend also designing the permission control of the RAM resource-sharing configuration, in addition to the 6 policy control points described in this reference.

### Restore approval control via Multi-party approval

A LAG vault has a Multi-party approval feature, and it becomes possible to require the approval of multiple people at restore time. This provides an approval-based control, difficult to realize with IAM policies or SCP, that "even if a single attacker obtains privileges, they cannot execute a restore."

In the context of ransomware resilience, even if an attacker seizes restore privileges, it becomes possible to prevent a unilateral restore via Multi-party approval. For the characteristics of the LAG vault, refer to [01-multi-account-architecture.md](./01-multi-account-architecture.md); for the management entity of encryption, refer to [04-encryption-strategy.md](./04-encryption-strategy.md).

## Design Decisions in the Context of Financial Institutions

### Thorough separation of duties

At financial institutions, there are many cases where the segregation of operation privileges (Segregation of Duties) is required as an internal rule or audit requirement. In this skill's recommended design, we recommend realizing the following separation of duties at the IAM role level.

- Separation of the backup-execution role (business account) and the restore-execution role (recovery account)
- Separation of the administrator of the Organizations management account and the administrator of the Backup account
- Separation of the administrator and user of the KMS key (designing the key-management role, backup role, and restore role as separate IAM roles)

### Response to audit requirements

As a result of the policy design, we recommend confirming that the acquisition and storage of operation logs are in a form that meets audit requirements.

- Operations on each IAM role, KMS CMK, and Vault are recorded in AWS CloudTrail
- Because the occurrence of a Deny by an SCP is also recorded in CloudTrail, it can be used for attack-precursor detection and post-incident analysis
- For the details of log collection and protection, refer to [07-log-collection-and-protection.md](./07-log-collection-and-protection.md)

### Organizing exception operations

When applying strong controls with SCP or policies, we recommend organizing the exception procedures needed in an emergency or during an operational change in advance. Because, without exception operations, there is a risk that the controls become a hindrance to operations during an emergency response or operational change, it is preferable to build consensus with the organization's security and operations departments.

## Summary Table of Countermeasure Effects

Let us organize which risks each design element covered in this reference is effective against as a ransomware-resilience measure.

| Design element | Risk defended against | Effective scenario |
|---|---|---|
| Separation of management privileges via the Organizations delegation policy | Configuration change of the entire organization by the breach of the Organizations management account alone | When the Organizations management account is breached |
| Limiting the using entity via the KMS key policy | Unnecessary access to the encryption key | When an attacker seizes some IAM roles |
| Separation of the backup-execution role and the restore-execution role | Simultaneous breach of backup/restore privileges | Limiting the scope of damage when a specific role is breached |
| Limiting cross-account actions via the Vault access policy | Unauthorized deletion/tampering of the copy-destination vault | The cross-account copy is limited to only `backup:CopyIntoBackupVault` |
| Preventive Deny of Vault / KMS key deletion via SCP | Backup destruction by an attacker who has seized account administrator privileges | When an attacker seizes the administrator privileges of a business account |
| Preventing the stopping of CloudTrail / Config via SCP | Erasure of the attacker's activity logs | When an attacker obtains log-operation privileges |
| Preventing departure from the organization via SCP | Data exfiltration by the copy-destination account leaving the organization | Insider fraud, account breach |
| The LAG vault's Multi-party approval | Unauthorized restoration by a single attacker | An additional defense when an attacker obtains restore privileges |

## Related Other References

- [01-multi-account-architecture.md](./01-multi-account-architecture.md): Placement of each policy in the multi-account structure, decisions on adopting a LAG vault
- [02-immutability.md](./02-immutability.md): Linkage with Vault Lock (the combination of deletion prevention via policy and WORM protection)
- [04-encryption-strategy.md](./04-encryption-strategy.md): KMS encryption strategy, details of the CMK strategy
- [07-log-collection-and-protection.md](./07-log-collection-and-protection.md): Coordination with log controls such as CloudTrail protection via SCP

## Reference: Official Documentation

- [AWS Backup](https://docs.aws.amazon.com/aws-backup/)
- [AWS Identity and Access Management](https://docs.aws.amazon.com/iam/)
- [AWS Key Management Service](https://docs.aws.amazon.com/kms/)
- [AWS Organizations](https://docs.aws.amazon.com/organizations/)

For the policy configuration details for establishing a cross-account copy, examples of describing a Vault access policy, the syntax of SCP, the delegation of the Organizations backup policy, the design of resource sharing via AWS Resource Access Manager, the configuration procedure for the LAG vault's Multi-party approval, and so on, refer to the latest version of the AWS Backup, AWS IAM, AWS Key Management Service, and AWS Organizations official documentation.
