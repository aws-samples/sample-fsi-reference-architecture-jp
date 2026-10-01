# Log Collection and Protection

## Overview

This reference presents the collection and protection of logs in the ransomware resilience adopted by this skill. When subjected to a ransomware attack, systematic log collection from normal times is indispensable for performing analysis such as identifying the intrusion path, grasping the scope of damage, determining the scope of recovery, and investigating the cause. Starting to collect logs after an attack occurs is too late; to grasp the situation before and after the infection, the premise is to acquire and protect logs continuously from before the attack occurs.

In addition, because the collected logs themselves are also subject to an attacker's tampering and deletion, the protection of the logs themselves also needs to be designed. This reference organizes the categories of logs to be collected and the specific targets in the AWS environment, the protection of the logs themselves, countermeasures against log stopping/deletion by an attack, the specialization of forensic analysis and the use of external vendors, and the use of optional integration services.

For the application of Object Lock to the log-storage S3 bucket, refer to [02-immutability.md](./02-immutability.md); for preventive controls via SCP, refer to [06-policy-and-access-control.md](./06-policy-and-access-control.md).

## Foundational Mechanism: Log Collection and Protection from Normal Times

### The 2 axes of log collection and protection

In the context of ransomware resilience, merely "collecting" logs is insufficient; "protecting" the collected logs also needs to be designed. Because an attacker is assumed to take actions such as stopping/deleting the log acquisition itself to erase analysis traces, and tampering with/deleting the stored logs, we recommend proceeding with the design along the following 2 axes.

| Axis | Content |
|---|---|
| **Collection** | The design of what logs to acquire, at what granularity, and from where |
| **Protection** | The design of how to store the acquired logs and protect them from tampering, deletion, and acquisition stoppage |

## Categories of Logs to Be Collected

Log collection is not an approach of acquiring everything comprehensively; we recommend selecting the logs needed for analysis in an emergency according to the services used and characteristics of the organization's systems and workloads. A design that considers the balance of comprehensiveness with cost and operational burden is important.

Under that premise, the main categories of logs that become candidates for consideration in preparation for analysis after a ransomware attack are organized below.

| Category | Content | Main use scenario |
|---|---|---|
| Network / communication logs | Source, destination, port, protocol, traffic volume, etc. | Detection of lateral movement and C2 communication, detection of exfiltration to the outside |
| OS logs | OS-level events, process launches, file-system operations, etc. | Tracking of post-intrusion activity, identification of the infection path |
| Authentication / access-control logs | Login history, privilege escalation, IAM operations, etc. | Identification of the intrusion path and the scope of the attacker's activity |
| Application logs | Application-specific events, errors, history of business operations | Identification of the scope of business impact, confirmation of the attack's spread to business systems |
| Storage operation logs | Creation, update, deletion, viewing of files/objects, etc. | Identification of the scope of damage, detection of data exfiltration |
| DB operation logs | DB queries, data changes, authentication history | Identification of the scope of damage at the DB layer |
| Security tool logs | Detection/blocking history of EDR, AV, IDS/IPS, WAF, etc. | Tracking of detected attacks, clues to undetected attacks |
| External service operation logs | Operation history of SaaS, external APIs, third-party integrations | Tracking of attacks via services outside the organization |

## Specific Log Targets in the AWS Environment

Let us organize the main logs that become candidates for collection in the AWS environment, by layer. As described above, this does not recommend acquiring all of these; we recommend selecting them according to the organization's workload configuration and analysis requirements.

### Control-plane / foundation level

| Log | Main role |
|---|---|
| AWS CloudTrail logs | API call history. The most important as a trail of AWS operations |
| AWS Config recorder logs | Configuration-change history of AWS resources |
| VPC Flow Logs | Network-traffic metadata within the VPC |
| Amazon Route 53 Resolver query logs | DNS query logs. Useful for detecting C2 communication and data exfiltration |

### Application layer / network perimeter

| Log | Main role |
|---|---|
| Elastic Load Balancing logs | Access logs of ALB/NLB |
| Amazon CloudFront logs | CDN access logs |
| Amazon API Gateway logs | API access logs |
| AWS WAF logs | Request/blocking logs of the Web ACL |

### Compute / application

| Log | Main role |
|---|---|
| OS logs of EC2 instances | syslog, Windows Event Log, etc. |
| Application logs of EC2 instances | Application-specific logs (aggregated by the CloudWatch Logs Agent, etc.) |
| Application logs of ECS on Fargate | Logs of container applications |
| Application logs of AWS Lambda | Logs at Lambda execution (output to CloudWatch Logs) |

### Storage / database

| Log | Main role |
|---|---|
| Amazon RDS / Amazon Aurora audit logs | Audit logs of DB access and queries |
| Amazon DynamoDB Streams logs | Change history of tables |
| Amazon EFS file operation logs | Acquired on the mounting client-side OS (file-unit operation logs cannot be acquired by EFS itself) |
| Amazon FSx for Windows audit logs | Audit logs of Windows file access |

### Third-party product integration

We recommend designing the collection path for the logs of third-party security tools (EDR, AV, IDS/IPS, etc.) as well, so that they can be analyzed by cross-checking against the logs of the AWS environment.

## Protection of the Logs Themselves

The collected logs themselves also become a target of the attacker. Because subsequent analysis becomes impossible if an attacker tampers with or deletes the logs, the protection of the logs themselves needs to be designed.

### Local-storage risk and transfer to a monitoring service

When application logs are stored locally on an EC2 instance or the like, the following risks accompany it.

- They become a target of encryption by ransomware
- Tampering with/deletion of the logs by an attacker becomes possible
- The logs themselves are lost at the time of an instance failure

As an approach to reduce these risks, real-time log transfer to a monitoring service such as Amazon CloudWatch Logs is effective. Because logs are transferred externally at the point they are written on the instance, even if the logs on the instance are later encrypted, tampered with, or deleted, the already-transferred logs are preserved.

For the transfer, the CloudWatch Logs agent, the Unified CloudWatch agent, and third-party log-transfer agents (Fluentd, Fluent Bit, etc.) can be leveraged.

### Centralized storage in the Log Archive account

We recommend aggregation into a Log Archive account (a dedicated storage account for log data) separated from the workload accounts. This is a form adopted as a standard configuration in the AWS Security Reference Architecture (SRA) and the landing zone of AWS Control Tower, and it is common to place it under the Security OU in parallel with the security-tool account. For the positioning of the Log Archive account in the account structure this skill adopts, refer to [01-multi-account-architecture.md](./01-multi-account-architecture.md).

Specifically, aggregation such as the following is effective.

- Aggregate the CloudTrail logs of the entire organization via the AWS Organizations trail feature into the Log Archive account
- Transfer the VPC Flow Logs of each account and each VPC to the S3 bucket of the Log Archive account
- Aggregate various logs into the Log Archive account

Even if a workload account is breached, because alteration to the aggregation-destination account is protected by another defense layer, it forms a configuration that improves the preservation of logs.

### Combination of S3 defense in depth

For the log-storage S3 bucket, we recommend defense in depth combining the following features. For the details of Object Lock, refer to [02-immutability.md](./02-immutability.md).

| Protection mechanism | Role |
|---|---|
| **S3 Versioning** | Even if there is an overwrite or deletion of an object, it remains as an old version, making restoration possible |
| **S3 Object Lock (Compliance mode recommended)** | WORM-protects objects within the retention period and prevents deletion/overwriting |
| **MFA Delete** | The complete deletion of a version requires MFA authentication, effectively preventing deletion by an attacker |
| **Least-privilege access control** | Via the bucket policy and IAM policy, restrict access to the logs to only a limited analysis team |

By combining these, it forms a configuration where logs are protected by other layers even if any one defense layer is breached.

## Countermeasures Against Log Stopping/Deletion by an Attack

An attacker may try to stop/delete the log acquisition itself, such as CloudTrail, to erase analysis traces. Against this, we recommend combining multi-stage defenses such as the following.

| Stage | Countermeasure | Role |
|---|---|---|
| **Prevention** | Deny of stopping/deletion actions via SCP | Even if the credentials on the workload-account side are breached, the log stopping/deletion operation itself is denied (for details, see [06-policy-and-access-control.md](./06-policy-and-access-control.md)) |
| **Detection** | Immediate notification via Amazon EventBridge | Detect events indicating a log stopping/deletion action and immediately notify the security team via SNS or the like |
| **Automatic recovery** | Automatic remediation via AWS Config Rules | When log acquisition is stopped, detect it with Config Rules and automatically re-enable it with Systems Manager Automation or Lambda |
| **Data preservation** | Defense in depth for the log-storage S3 | When the above cannot fully prevent it and the actual logs are about to be erased, the last line of defense that prevents loss on the storage side |

By combining these, it becomes possible to realize multi-stage protection: "prevent the stopping/deletion → immediately detect if it is stopped → automatically recover → even if the actual logs are erased, retain them on the storage side."

## Optional: Use of Integration Services

The log collection and protection described in this reference can be realized with a combination of standard AWS features, but by leveraging the following integration services, the implementation and operation can be made more efficient. These are optional efficiency-enhancing elements and are not positioned as mandatory requirements this time.

### AWS Control Tower

By leveraging AWS Control Tower, it becomes possible to introduce the following countermeasures organized in this reference as features of Control Tower.

- The collection configuration of CloudTrail / AWS Config data is automated in the landing-zone setup
- Preventive controls, including the Deny of log stopping/deletion, are provided as standard as Control Tower guardrails (management policies)

When building a landing zone newly with Control Tower, because these settings are applied in a standardized form, the effort of individual implementation is reduced.

### Amazon Security Lake

As a measure to make log aggregation more efficient, leveraging Amazon Security Lake is effective.

- Provides a mechanism to centrally manage security logs/events from multiple AWS accounts
- Supports, as aggregation targets, AWS CloudTrail, VPC Flow Logs, Amazon Route 53 Resolver query logs, AWS Security Hub findings, AWS WAF, partner security solutions, and so on
- Because the aggregated logs are automatically converted to the OCSF (Open Cybersecurity Schema Framework) format, integration with various security analysis tools (SIEM, UEBA, etc.) becomes easy

Instead of implementing the manual aggregation to S3 and format conversion oneself, it becomes possible to realize it in a standardized form via Security Lake.

### Points for the adoption decision

While these services are highly convenient, there are also cases of caution in their adoption for the following reasons.

- Consistency with the existing landing-zone design (a self-built configuration that does not use Control Tower)
- The connection design with existing assets such as the security operations foundation and SIEM
- The perspective of accountability in regulatory response

While the decision to adopt Control Tower / Security Lake at the timing of a new introduction or a large-scale cloud migration is reasonable, we recommend sufficiently considering the trade-offs for a retrofit introduction into an existing environment. This skill recommends implementation with a combination of standard features as the basic configuration, and positions the optional efficiency enhancement via Control Tower / Security Lake as a separate option.

## The Specialization of Forensic Analysis and the Use of Vendors

The collected logs are used for analysis such as the following.

- Identification of the intrusion path (from where and how the attacker intruded)
- Identification of the intrusion time (identification of the infection-occurrence time and the initially infected resource)
- Analysis of the scope of damage (which resources/data are affected)
- Tracking of lateral movement (how the attacker moved within the organization)
- Confirmation of whether data was exfiltrated (whether an information leak occurred)

These forensic analyses are a domain that requires advanced specialization such as memory analysis, malware analysis, understanding of the attacker's TTPs (Tactics, Techniques and Procedures), and evidence preservation that holds up in court. It is also assumed that it is difficult for an organization that has not accumulated experience from normal times to perform it in-house.

Therefore, at financial institutions, we recommend also keeping the following options in view.

- Realize rapid and reliable analysis by requesting a vendor specializing in forensic analysis
- Because it is unrealistic to hastily proceed with a contract at the time of an incident, consider and contract in advance, from normal times, "which vendor to request," "what the contract form will be," and "to what extent the analysis will be entrusted"

## Design Decisions in the Context of Financial Institutions

### Design of the retention period

At financial institutions, there are many cases where the storage periods of business records and transaction records are stipulated by law or industry regulation. When logs are positioned as part of regulatory compliance, we recommend reflecting the following points in the design.

- A lifecycle design that meets the storage period stipulated by regulatory requirements (e.g., 7 years)
- For incident analysis, store in an immediately accessible state within a certain period
- For long-term storage, also use a design that migrates to cold storage such as Amazon S3 Glacier in consideration of cost efficiency

However, the judgment of conformance to specific regulatory clauses is outside this skill's scope, and we recommend deciding in coordination with the organization's regulatory-response and compliance departments.

### Design of access control

We recommend restricting access to logs with least privilege and making tampering/deletion physically difficult. A design that grants read privileges to only a limited analysis team is also preferable.

- Limit the read privileges of the log-storage bucket to the analysis team
- Grant write privileges to the logs only to the log-transfer mechanism, preventing manual rewriting
- Separately acquire the access logs to the log-storage bucket itself as well, making access to the logs themselves auditable

## Summary Table of Countermeasure Effects

Let us organize which risks each design element covered in this reference is effective against as a ransomware-resilience measure.

| Design element | Risk defended against | Effective scenario |
|---|---|---|
| Systematic log collection (category coverage) | Insufficiency of analysis material after an attack | Identification of the intrusion path and scope of damage, securing the foundation for forensic analysis |
| Real-time transfer to a monitoring service | Encryption/tampering/deletion of locally stored logs | Encryption by ransomware, log tampering by an attacker |
| Centralized storage in the Log Archive account | Loss of logs when a workload account is breached | Even when a business account is breached, the aggregation-destination logs are protected by another defense layer |
| S3 defense in depth (Versioning, Object Lock, MFA Delete) | Unauthorized alteration/deletion of the log-storage bucket | When an attacker obtains privileges to the log-aggregation-destination S3 bucket |
| Preventing the stopping of CloudTrail / Config via SCP | Erasure of the attacker's activity logs | An attacker who has seized the administrator privileges of a workload account |
| Automatic recovery via Config Rules | Detection delay after log acquisition is stopped | Immediate recovery when an attacker stops the logs |
| Immediate notification via EventBridge | Overlooking log stopping/deletion | Detection of attack precursors, rapid start of response |
| Least-privilege access control | Unauthorized access to / alteration of the logs themselves | Insider fraud, access after privilege escalation by an attacker |
| Retention-period design meeting regulatory requirements | Log insufficiency for regulatory compliance | Business systems where the storage period is stipulated by law or industry regulation |

## Related Other References

- [01-multi-account-architecture.md](./01-multi-account-architecture.md): Multi-account structure (the positioning of the Log Archive account)
- [02-immutability.md](./02-immutability.md): Details of S3 Object Lock (application to the log-storage bucket)
- [06-policy-and-access-control.md](./06-policy-and-access-control.md): Preventive controls such as preventing the stopping of CloudTrail / Config via SCP
- [08-monitoring-and-audit.md](./08-monitoring-and-audit.md): Monitoring and audit reporting of backup operations

## Reference: Official Documentation

- [AWS CloudTrail](https://docs.aws.amazon.com/awscloudtrail/)
- [AWS Config](https://docs.aws.amazon.com/config/)
- [Amazon CloudWatch](https://docs.aws.amazon.com/cloudwatch/)
- [AWS Control Tower](https://docs.aws.amazon.com/controltower/)
- [Amazon Security Lake](https://docs.aws.amazon.com/security-lake/)
- [Amazon S3](https://docs.aws.amazon.com/AmazonS3/)

For the log-acquisition configuration details of each AWS service, the organization-trail configuration procedure of CloudTrail, the aggregation configuration of AWS Config, the output-destination configuration of VPC Flow Logs, the landing-zone design of AWS Control Tower, the aggregation configuration details of Amazon Security Lake, the configuration procedures of S3 Object Lock / Versioning / MFA Delete, and so on, refer to the latest version of each service's official documentation.
