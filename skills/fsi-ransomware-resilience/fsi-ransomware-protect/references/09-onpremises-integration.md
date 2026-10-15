# On-Premises Environment Backup Integration

## Overview

This reference presents the design adopted by this skill for taking and protecting on-premises environment backups on AWS. At Japanese financial institutions, there are still many cases where important systems are held in on-premises environments, and VMware-based virtualization environments in particular are widely in operation. These on-premises environments are also exposed to the threat of ransomware, and we recommend designing backup/data protection as ransomware resilience in an integrated manner, including not only the AWS environment but also the on-premises environment.

By storing on-premises backups on the AWS side, it becomes possible to incorporate the on-premises environment into the 3-2-1 rule and realize a configuration where a clean backup remains on the AWS side even if the on-premises environment is breached.

This reference organizes the backup of VMware environments via AWS Backup Gateway, the backup to S3 via DataSync / Storage Gateway / S3 API, the differentiation between the two approaches, the privatization of the communication path, bandwidth design, the VMware-environment-specific infection-checking workaround, and log collection and protection in the on-premises environment.

For placement in the multi-account structure, refer to [01-multi-account-architecture.md](./01-multi-account-architecture.md); for the details of Vault Lock, refer to [02-immutability.md](./02-immutability.md); for KMS encryption, refer to [04-encryption-strategy.md](./04-encryption-strategy.md).

## Foundational Mechanism: The Significance of Integrated Protection on AWS

The design of storing on-premises environment backups on the AWS side brings the following effects from a ransomware-resilience perspective.

- **Incorporation of the on-premises environment into the 3-2-1 rule**: By placing backups in an AWS environment that is physically and logically separated from on-premises, it forms a configuration where a clean backup remains on the AWS side even if the on-premises side is fully breached
- **Application of AWS-side data protection features**: It becomes possible to apply protection features such as AWS Backup's Vault Lock (immutability), KMS encryption, and cross-account/cross-Region copy to on-premises backups as well
- **Integrated operation and auditing**: By centrally operating and auditing the backups of the on-premises and AWS environments on the AWS side, a ransomware-resilience system can be built across the organization

The approaches to protecting on-premises data on AWS can be broadly organized into the following two.

| Approach | Main target environment |
|---|---|
| **Backup of VMware environments via AWS Backup Gateway** | VMware vSphere environment |
| **Backup to S3 via DataSync / Storage Gateway / S3 API** | Non-VMware environments, or VMs that fall under the constraints of AWS Backup Gateway |

## Approach 1: Backup of VMware Environments via AWS Backup Gateway

### Feature overview

By placing AWS Backup Gateway in the on-premises VMware environment, it becomes possible to take backups of on-premises VMs using AWS Backup. The Backup Gateway plays the role of a bridge between the VMware environment and AWS Backup, and through AWS Backup's backup plan feature, it can take periodic backups such as daily, weekly, and monthly. A restore from a backup to the VMware environment is also possible, and in an emergency, recovery can be performed on the on-premises side.

### Application of AWS Backup's protection features

Because backups taken via AWS Backup Gateway are stored in an AWS Backup Backup vault, it becomes possible to apply the same protection features as backups of the AWS environment.

- Immutability via Vault Lock (see [02-immutability.md](./02-immutability.md))
- Encryption via KMS (see [04-encryption-strategy.md](./04-encryption-strategy.md))
- Multiple protection via cross-account/cross-Region copy (see [01-multi-account-architecture.md](./01-multi-account-architecture.md))
- Recording of the audit trail via Audit Manager reports (see [08-monitoring-and-audit.md](./08-monitoring-and-audit.md))

### Constraints

When adopting AWS Backup Gateway, note the following constraints. Because the specific version numbers and support status may change due to feature enhancements, we recommend referring to the latest version of [Working with hypervisors](https://docs.aws.amazon.com/aws-backup/latest/devguide/working-with-hypervisors.html) in the AWS Backup official documentation at design time.

- **vSphere supported-version constraint**: There is a limitation on the supported vSphere versions
- **Unsupported disk configurations**: RDM (Raw Device Mapping) disks, NVMe controllers and their disks, the Independent Persistent disk mode, the Independent Non-Persistent disk mode, and so on, may be unsupported

For VMs that include these unsupported elements, consider also using Approach 2 described later.

## Approach 2: Backup to S3 via DataSync / Storage Gateway / S3 API

### Feature overview

For on-premises systems that are not VMware environments, or VMs that fall under the constraints of AWS Backup Gateway, we recommend an approach that uploads the on-premises data to an Amazon S3 bucket and protects it immutably via S3 Object Lock and the like.

### Available transfer means

| Transfer means | Main characteristics |
|---|---|
| **AWS DataSync** | Suited for the periodic transfer of large volumes of data. Equipped with features such as scheduled execution, bandwidth control, and data-integrity verification |
| **AWS Storage Gateway (File Gateway)** | Stores data from on-premises to S3 via NFS / SMB. From the on-premises application, it appears as an ordinary file system |
| **S3 API (direct upload)** | Direct upload using the AWS CLI's `aws s3 sync` command or the S3 API. Flexible script-based operation is possible |

| Condition | Recommended means |
|---|---|
| Periodic transfer of large volumes of data, bandwidth control needed | AWS DataSync |
| Want to access from an on-premises app via NFS / SMB | AWS Storage Gateway (File Gateway) |
| Flexible script-based operation, integration with existing transfer jobs | S3 API / `aws s3 sync` |

### Data protection

For the data uploaded to S3, we recommend defense in depth combining the following protection mechanisms. For details, refer to [02-immutability.md](./02-immutability.md) and [07-log-collection-and-protection.md](./07-log-collection-and-protection.md).

- **S3 Object Lock**: Protects the uploaded data immutably. Choose between compliance mode / governance mode according to regulatory requirements
- **S3 Versioning**: Enablement is required as a prerequisite for Object Lock. Because an old version remains even if there is an overwrite or deletion, it becomes an additional protection layer against erroneous operations and attacks
- **S3 encryption**: Storage-time encryption via SSE-S3 or SSE-KMS

## Differentiation Between the Two Approaches

| Condition | Recommended approach |
|---|---|
| On-premises is a VMware environment, and per-VM backup/restore is needed | Approach 1: AWS Backup Gateway |
| A non-VMware environment (physical servers, Microsoft Hyper-V, etc.) | Approach 2: DataSync / Storage Gateway / S3 API |
| A VMware environment, but VMs that include unsupported elements such as RDM / NVMe / independent disk mode | Approach 2: DataSync / Storage Gateway / S3 API |
| Per-file backup is sufficient (a restore of the entire VM is not needed) | Approach 2: DataSync / Storage Gateway / S3 API |

Because not all VMs satisfy the support conditions of AWS Backup Gateway even in a VMware environment, after confirming the VM configuration within the organization, a design that uses Approach 1 and Approach 2 together in a hybrid manner also becomes an option.

## Privatization of the Communication Path

At many financial institutions, there are many cases where private-path communication, rather than via the internet, is chosen as the communication path for backup data. This skill, standing on that premise, recommends the privatization of the communication path from on-premises to AWS.

### In the case of Approach 1 (AWS Backup Gateway)

```
On-premises system
  → AWS Backup Gateway (placed on-premises)
    → AWS Direct Connect
      → VPC
        → AWS PrivateLink
          → AWS Backup
```

By the combination of AWS Direct Connect and AWS PrivateLink, it forms a configuration where backup data is transferred via a private path that does not go through the internet.

### In the case of Approach 2 (backup to S3)

```
On-premises system
  → AWS Direct Connect
    → VPC
      → VPC Endpoint (S3 Gateway Endpoint)
        → Amazon S3 bucket
```

By the combination of AWS Direct Connect and a VPC Endpoint (Gateway Endpoint for S3), data transfer via a private path that does not go through the internet becomes possible.

## Bandwidth Design and Impact on Existing Communications

Because periodic backups from on-premises to AWS consume the bandwidth of AWS Direct Connect, a design that accounts for the impact on existing business communications becomes necessary.

### Bandwidth control of AWS Backup Gateway

AWS Backup Gateway is equipped with a bandwidth-throttling feature, and operations such as restricting bandwidth use during business hours are possible. This can suppress the impact on existing communications through Direct Connect.

### Reduction of traffic volume via incremental backups

A VMware backup by AWS Backup is a full backup the first time, but thereafter it becomes an incremental backup using CBT (Changed Block Tracking). Therefore, the traffic volume and execution time accompanying backups after the first time are limited compared to the first time.

For systems of high business impact, a design is conceivable that performs the initial full backup during a time slot with little business impact (a holiday night, etc.) and executes the subsequent incremental backups distributed across weekdays as well.

## Infection Checking of Backup Data (VMware-Environment-Specific Workaround)

Malware-infection checking of backups of a VMware environment requires an approach different from backups of the AWS environment due to the following constraints.

### Constraints

- **The AWS Backup Restore testing feature does not support VMware**: In the AWS environment (Amazon EC2, etc.), an automatic restore + verification can be performed with the Restore testing feature, but in a VMware environment, this feature cannot be used. Therefore, to automate periodic restore + infection checking, building an original mechanism becomes necessary
- **Spare capacity in the on-premises environment**: In many cases, spare capacity for restoration is not secured in the on-premises environment, and it may be difficult to perform periodic restores

### The approach of restoring to EC2 and its constraints

The approach of restoring a VMware backup to Amazon EC2 and performing infection checking is also conceivable, but note the following constraints. For details, we recommend referring to the AWS Backup official documentation and the [VM Import/Export official documentation](https://docs.aws.amazon.com/vm-import/latest/userguide/prerequisites.html).

| Constraint | Content |
|---|---|
| **OS license** | Confirmation of the handling of the OS license (AWS-provided license / BYOL) when restoring to EC2 becomes necessary |
| **Supported-OS constraint** | The OSes that can be imported to EC2 are limited to those supported by VM Import/Export |
| **Upper limit on disk size and number of disks** | VMs that fall under the size upper limit of each virtual machine disk or the upper limit on the number of disks may not be restorable to EC2 as is |
| **Third-party product licenses** | Whether the licenses of the virus-checking products, EDR, etc. used on-premises are valid on EC2 depends on each product's license system, so separate confirmation is necessary |

Considering these constraints, the infection checking of backups of a VMware environment can be conceived as choosing one of the following according to the organization's resources, licenses, and operational structure.

- Restore to the VMware environment and scan with the existing on-premises product (original automation is needed)
- Restore to EC2 and scan with the AWS environment or the existing product (confirmation of constraints such as license and OS is needed)
- Use, in combination, continuous malware detection for the running systems in the on-premises environment that is the backup source, and operate the infection checking of the backups themselves in a limited manner

## Log Collection and Protection in the On-Premises Environment

In the on-premises environment as well, log collection in preparation for analysis after a ransomware attack (tracing the attack path, time, and behavior) becomes necessary. However, the effect of AWS services on log collection and infection checking in the on-premises environment is limited compared to the AWS environment.

### The limits of the effect of AWS services

Log collection and analysis on the on-premises side is a domain of product use and operation on the on-premises side. This skill takes the policy of only showing "the necessity and the way of thinking" and not delving into specific product selection and configuration procedures.

### Conceivable approaches

- **Syslog forwarding**: Perform Syslog forwarding from the VMware environment or on-premises third-party products to coordinate and detect management actions and audit events
- **Aggregation into an on-premises SIEM or a SIEM on AWS**: Aggregate the on-premises-side logs into a SIEM to make them analyzable in an integrated manner with the logs of the AWS environment

These designs are a domain that requires coordination with the organization's security department and SOC team, and we recommend consideration including the use of a forensic vendor.

## Design Decisions in the Context of Financial Institutions

### Design stance on the privatization of the communication path

At many financial institutions, there are many cases where private-path communication, rather than via the internet, is chosen as the communication path for backup data. This skill, standing on that premise, recommends a design premised on the privatization of the communication path (AWS Direct Connect + AWS PrivateLink / VPC Endpoint).

### Response to on-premises-environment-specific constraints

At design time, it is necessary to confirm the on-premises-side configuration (VMware version, disk configuration, OS, third-party product licenses, etc.). Because the premise of these confirmations is coordination with the organization's on-premises operations department, we recommend advancing consensus-building with the relevant departments at the early design stage.

### The necessity of complementary countermeasures on the on-premises side

The backup/protection by AWS services described in this reference delivers value in the scope of storing on-premises data on the AWS side. On the other hand, malware detection, log collection, forensic response, and so on, for the running systems on the on-premises side are outside the scope of AWS services, and the premise is combined use with on-premises products and operations. We recommend the development of an organization-wide system, including the SOC system and the use of a forensic vendor.

## Summary Table of Countermeasure Effects

Let us organize which risks each design element covered in this reference is effective against as a ransomware-resilience measure.

| Design element | Risk defended against | Effective scenario |
|---|---|---|
| VMware backup via AWS Backup Gateway | Data loss at the time of ransomware damage in the on-premises environment | A clean backup remains on the AWS side even if the on-premises side is fully breached |
| S3 backup via DataSync / Storage Gateway / S3 API | Data loss of VMware-unsupported environments and unsupported VMs | Protection of physical servers, Hyper-V, and VMs falling under the AWS Backup Gateway constraints |
| Application of AWS Backup's protection features (Vault Lock, encryption, copy) | Alteration/deletion of the backup data itself | An attack on the backups stored in the cloud |
| Privatization of the communication path (Direct Connect + PrivateLink / VPC Endpoint) | Attack/eavesdropping on the communication path of the backup data | Conformance to the security requirements of financial institutions |
| Bandwidth control of AWS Backup Gateway | Impact on existing business communications | Reduction of operational burden in an environment sharing Direct Connect bandwidth |
| Incremental backup via CBT | Prolongation of traffic volume and execution time | Continuous backup in a large-scale VMware environment |
| Combined use of malware detection / log collection on the on-premises side | Missed infection detection of running on-premises systems | Continuous threat monitoring on the on-premises side that cannot be addressed on the AWS side |

## Related Other References

- [01-multi-account-architecture.md](./01-multi-account-architecture.md): Multi-account structure (the account design of the on-premises-backup acceptance destination)
- [02-immutability.md](./02-immutability.md): Details of Vault Lock and S3 Object Lock
- [04-encryption-strategy.md](./04-encryption-strategy.md): KMS encryption, key management strategy
- [07-log-collection-and-protection.md](./07-log-collection-and-protection.md): S3 defense in depth, log protection

## Reference: Official Documentation

- [AWS Backup](https://docs.aws.amazon.com/aws-backup/)
- [AWS DataSync](https://docs.aws.amazon.com/datasync/)
- [AWS Storage Gateway](https://docs.aws.amazon.com/storagegateway/)
- [Amazon S3](https://docs.aws.amazon.com/AmazonS3/)
- [AWS Direct Connect](https://docs.aws.amazon.com/directconnect/)

For the vSphere versions supported by AWS Backup Gateway, the details of supported/unsupported disk configurations, the transfer configuration of AWS DataSync, the per-type specifications of AWS Storage Gateway, the limitations of VM Import/Export, the quotas of each service, and so on, refer to the latest version of the AWS Backup, AWS DataSync, AWS Storage Gateway, and VM Import/Export official documentation.
