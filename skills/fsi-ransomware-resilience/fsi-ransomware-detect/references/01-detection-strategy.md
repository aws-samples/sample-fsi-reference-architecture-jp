# Detection Design (Detection of Service Impact and Detection of Security Attacks)

## Overview

This reference describes the detection design for ransomware countermeasures that this skill recommends. "Detection" here refers to noticing the signs of ransomware damage/threats and initiating the incident response process triggered by an alert (notification). The stage of drilling down into detected events to analyze and investigate them is handled in [02-log-analysis-and-investigation.md](./02-log-analysis-and-investigation.md).

Detection is broadly composed of two perspectives. One is "detection of service impact," which catches the impact on services (impact on users/services); the other is "detection of security attacks," which catches the attack/intrusion/virus introduction itself. The former serves as the starting point for grasping "something happened, somewhere," and the latter leads to a grasp that includes possible causes. The two are in a relationship of phased triage, but their order is not fixed (detection of a security attack may come before detection of service impact).

This reference organizes the concept of detection of service impact (depth of monitoring), the means of detecting security attacks (Amazon GuardDuty protection plans, third-party products), the root-cause triage operation (manual checks by users) that determines, after an alert, whether it is caused by an external attack (ransomware, etc.), aggregation and delegated administration of detection, and initiating the incident response process triggered by alerts. Because the design details of specific monitoring/detection methods themselves are beyond this skill's scope (ransomware countermeasures), they are deferred to references to official AWS guidance.

The detection framework that this reference presupposes corresponds to "detection through continuous monitoring" in the detection function of the NIST Cybersecurity Framework, and to the "Detection" stage in the AWS incident response approach. The analysis of detected events corresponds to the subsequent "analysis" stage.

The design of log collection/protection is within the scope of the Protect phase, and this skill operates on the premise of "leveraging already-collected logs." Account structure design is also within the scope of the Protect phase, and this reference leverages it from the perspective of "aggregation and delegated administration of detection."

## Foundational concept: Initiating the incident response process triggered by alerts

The primary element of detection is the alert (notification). Whether it is detection of service impact or detection of a security attack, the detected event is notified to stakeholders as an alert, and the incident response process is initiated triggered by it.

There is an essential difficulty in the accuracy of alert-based detection. It is not always possible to determine with complete certainty whether an incident has occurred, is in progress, or will occur in the future. This is because detection mechanisms are built on deviations from a baseline, known patterns, and notifications from inside and outside, while the attacker's tactics, techniques, and procedures (TTPs) change over time. Moreover, an alert by itself indicates that "something happened," but its content alone often cannot determine whether it is caused by an external attack (ransomware, etc.) or by an ordinary failure or operational event. Therefore, it is desirable to design so that automated alert-based detection serves as the starting point, combined with a root-cause triage operation centered on manual checks by users to determine whether it is an external attack.

## Detection of service impact

### Design concept

Detection of service impact aims to quickly catch that impact on services/users is occurring due to ransomware damage, etc. This is not limited to security; it is something realized through the design and operation of general service monitoring. At the point of this detection, whether the cause is a security attack is not yet known, but being able to grasp "something happened, somewhere" is an important starting point for the subsequent investigation/response.

An event such as a ransomware infection does not necessarily first manifest in security detection; it may appear earlier as a service anomaly (degraded response, increased errors, outage, etc.). Therefore, there is value in having monitoring that catches service impact itself, on a separate axis from security detection.

### Depth of monitoring

Whether service impact can be detected quickly depends on how deep the monitoring reaches. Monitoring that looks only at resource operating status may not fully catch service anomalies as seen from the user. It is desirable to capture the depth of monitoring in stages and design accordingly, as follows.

| Depth of monitoring | What can be caught (examples) |
|---|---|
| Resource monitoring | Operating status of infrastructure resources such as CPU, memory, disk, connection count |
| Service monitoring | Operating status as a service, such as error rate, latency, throughput |
| Synthetic monitoring | Actually accessing endpoints/screens from the outside to confirm reachability, response, and screen display (Amazon CloudWatch Synthetics, etc.) |
| Application-level monitoring (business metrics) | Business metrics indicating whether business is flowing normally, such as the number of logins, transactions, contracts, and views |

If it stops at resource monitoring only, there is a possibility of missing a situation where the resources appear normal but the service is not being provided to users. By combining service monitoring, synthetic monitoring, and application-level monitoring (business metrics), user impact can be caught more reliably.

### Financial-institution context: Designing monitoring levels according to importance

Rather than designing all systems at a uniform monitoring level, it is desirable to appropriately label monitoring levels according to system importance, and to design the thoroughness of monitoring and the level of detection in stages, distinguishing between important systems (mission-critical / important business systems, etc.) and others. This makes it possible to concentrate limited operational resources on important systems while raising the effectiveness of service impact detection in an emergency.

This concept of "setting required levels in stages according to system importance" is also shown in IPA's (Information-technology Promotion Agency, Japan) Non-Functional Requirements Grades (a procedure that selects an important system = a model system, and decides non-functional requirement levels in stages starting from important items. It includes items related to monitoring operations such as availability and operability/maintainability).

### Where to refer for specific monitoring methods

Because the design details of the specific monitoring methods used for detection of service impact (resource monitoring, service monitoring, synthetic monitoring, application-level monitoring) are beyond the scope of this skill, which is themed on security, this skill does not delve into them and defers to references to the following official AWS guidance.

| Positioning | Guidance |
|---|---|
| Core of the monitoring/observability concept | AWS Well-Architected Framework, Operational Excellence pillar, "Implement observability." Centered on metrics, logs, and traces, it comprehensively covers KPI definition (corresponding to monitoring of business metrics), application telemetry (corresponding to service monitoring), user experience telemetry (corresponding to synthetic monitoring), dependency telemetry, and distributed tracing |
| Guidance on selecting monitoring services | Choosing an AWS monitoring and observability service (AWS Decision Guide). Guidance on differentiating among Amazon CloudWatch, etc. |
| Per-service monitoring recipes | AWS Observability Best Practices. Practices of per-service monitoring for Amazon EC2, Amazon ECS, etc. |
| Financial-institution context (reference) | IPA "Strengthening the upstream process of system development (Non-Functional Requirements Grades)." A reference for the concept of designing monitoring levels according to importance |

URLs are organized in the "Reference: Official documentation" section.

## Detection of security attacks

### Design concept

Detection of security attacks aims to catch malicious attacks/virus introduction, such as suspicious activity and suspicious files. Whereas detection of service impact catches the "impact (result)," this catches the "attack/intrusion (possible cause)," thereby realizing detection that includes not only the impact but also the possible cause.

The means of detection have multiple layers: (1) detection by AWS managed services and (2) detection by third-party products; these are combined to catch attacks from multiple angles. In addition, when these automated detections raise an alert, a root-cause triage operation (manual checks by users) is combined to determine whether it is caused by an external attack.

### Detection by Amazon GuardDuty

Amazon GuardDuty is a managed threat-detection service for AWS environments, and can be leveraged for ransomware-countermeasure detection. When GuardDuty is enabled, the following operate automatically at no additional cost.

- **Foundational threat detection**: Automatically ingests AWS CloudTrail management events, VPC flow logs, and DNS logs to detect threats.
- **Extended Threat Detection**: Detects multi-stage attack sequences spanning multiple data sources, multiple resources, and time. When S3 Protection is enabled, the detection accuracy of multi-stage attacks affecting Amazon S3 resources improves.

In addition, protection plans that are optionally enabled according to the use case are provided. As protection plans closely related to ransomware-countermeasure detection, the following can be cited.

| Protection plan | Overview |
|---|---|
| Malware Protection for EC2 | Scans Amazon EBS volumes attached to Amazon EC2 instances to detect the presence of malware (on-demand execution is also possible) |
| Malware Protection for S3 | Detects malware in objects newly uploaded to Amazon S3 buckets (on-demand execution is also possible) |
| Runtime Monitoring | Monitors OS-level events of Amazon EKS, Amazon EC2, and Amazon ECS (including AWS Fargate) to detect runtime threats |
| S3 Protection | Detects risks such as attempts to exfiltrate/destroy data against Amazon S3 buckets |

Protection plans may be added to/changed, and the detailed specifications of each protection plan (supported resources, the kinds of threats that can be detected, quotas, etc.) may also change with feature enhancements. Therefore, when making design proposals/assessments, we recommend confirming the current protection plans and supported scope against the latest version of the official Amazon GuardDuty documentation before presenting. Which protection plans should be enabled differs depending on the resources to be protected/monitored and the threat model.

### Detection by third-party products

It is also possible to operate third-party products (EDR, etc.) on Amazon EC2 to detect security attacks. At financial institutions, existing security products are often in operation, so present the option of using AWS-native detection (GuardDuty, etc.) in combination with third-party products, while respecting the customer's existing operations/policy.

### The concept of which resources to target for detection

In ransomware-countermeasure detection, which resources to target is organized according to the nature of the resource. This skill focuses on the resources where the customer's workloads (applications) or data directly run/are stored and which are subject to checks for malware infection or ransomware damage. Resources can be broadly organized into the following three.

- **Compute (Amazon EC2, Amazon ECS, Amazon EKS, AWS Fargate, etc.)**: An execution environment where malware execution/infection can occur, and the main target of runtime threat detection and malware scanning. For AWS Fargate, AWS manages the host OS/infrastructure, but the in-container execution environment and data running on it remain the customer's workloads, so it is treated the same as other compute as a target of infection/compromise checks.
- **Storage (Amazon S3, Amazon EFS, Amazon FSx, etc.)**: A target of data encryption/destruction/exfiltration. Amazon S3 is a direct target of malware scanning / suspicious-activity detection. Shared file storage such as Amazon EFS / Amazon FSx is covered not by directly scanning it, but by detection on the mounting compute (EC2, containers) and by catching suspicious access through log-based analysis/investigation ([02-log-analysis-and-investigation.md](./02-log-analysis-and-investigation.md)).
- **Managed services (Amazon RDS, Amazon Aurora, Amazon DynamoDB, Amazon SQS, AWS Lambda, etc.)**: Because the user does not manage the OS/runtime and these are not environments where virus files are executed, runtime malware detection (infection checks) is out of scope for this skill. There can be a risk of the data itself being encrypted/destroyed, but countermeasures for that are caught by data protection (the Protect phase) and by detection of suspicious access in log-based analysis/investigation. Note that, even for managed services, mechanisms to detect suspicious access may be provided depending on the service (for example, Amazon GuardDuty's RDS Protection detects anomalies in the login activity of RDS / Aurora. This is detection of suspicious access, not malware scanning).

Which resources are targets of malware scanning and various threat detections will change with the feature enhancements of AWS services. **The direct targets of malware scanning are, as of this writing, Amazon EC2 (EBS) and Amazon S3**, but because target resources and the kinds of detection may be expanded in the future, confirm the current supported scope against the latest version of the official Amazon GuardDuty documentation before presenting at the time of design proposals/assessments.

### Root-cause triage operation (manual checks) after an alert

When an alert is raised by either detection of service impact or detection of security attacks, its content alone cannot always immediately determine whether it is caused by an external attack (ransomware, etc.) or by an ordinary failure or operational event (an application defect, an expected load increase, a misconfiguration, etc.). This determination is performed by a root-cause triage operation centered on manual checks by users.

Manual checks are not realistic as independent, routine preventive monitoring (there is a limit to continuously checking every system manually at all times). They are effective when positioned as a **triage operation to judge the possibility of an external attack, performed after an alert is raised by detection of service impact or detection of security attacks**. The points to prepare are three: who performs it (first responder, on-duty staff, SOC, etc.), at what timing it is performed (e.g., within how many minutes after the alert), and by what procedure the check is performed.

Specific examples of root-cause triage procedures:

- Actually accessing the web system in a browser to confirm behavior (e.g., whether a ransom note is displayed on the website, or whether an unexpected error screen appears)
- Logging into servers using SSH or AWS Systems Manager Session Manager to check for the presence of suspicious files (e.g., whether encrypted suspicious files exist within the server)

Perspectives for judging whether an event is caused by a ransomware attack, confirmed by logging into servers or from OS logs, include the occurrence of encrypted files, the execution of suspicious processes/programs, and the presence of external communication to suspicious domains / abroad. By preparing these perspectives in advance as a triage procedure to be executed when an alert is raised, the judgment of whether it is an external attack can be made faster.

## Aggregation and delegated administration of detection

In a multi-account environment, rather than confirming detection results individually in each account, it is desirable to centralize organization-wide detection/management by aggregating into a security account. This makes it possible to visualize detection results centrally across the organization, and to prevent missed detections and delayed responses.

- Amazon GuardDuty can aggregate and centrally manage the detection results of accounts within the organization by designating a delegated administrator through AWS Organizations. Management using AWS Organizations is recommended.
- By using AWS Security Hub in combination, the detection results of multiple security services, including GuardDuty, can be aggregated, prioritized, and visualized across the organization.

Because the design of the account structure itself (the positioning of the security account, the Log Archive account, etc.) is handled in the Protect phase, it is not handled in this reference. If consideration of the account structure is needed, guide the customer to leverage the Protect phase skill (fsi-ransomware-protect). This reference focuses, on the premise of the existing account structure, on the perspective of "where to aggregate detection and how to centrally manage it."

## Design decisions in the financial-institution context

### Phased development of the detection posture

Trying to realize the entire detection posture at once carries a large burden. Taking into account the ease of response, the impact on the existing environment, and the risk-reduction effect, it is realistic to develop it in stages. For example, the idea would be to start with countermeasures with small impact on the existing environment and immediate effect (enabling GuardDuty, setting monitoring levels for important systems, etc.), and to position initiatives with a wide impact range, such as organization-wide aggregation/centralized management of detection, in stages. Follow this skill's Constraints (DT-C12) for the judgment axes of the specific phase classification, and do not present specific numeric durations.

### Balance between comprehensiveness of monitoring and operational burden

The more thorough the monitoring/detection, the greater the operational burden/cost. Through the design of monitoring levels according to importance (described above), it is desirable to design so as to place emphasis on important systems while keeping the operational burden sustainable for the organization as a whole.

### Perspective of regulatory response / audit response

The maturity of the detection posture may be questioned during internal audits, external audits, and inspections by regulatory authorities. However, judging conformance to specific regulatory articles is out of scope for this skill, and we recommend judging it in coordination with the organization's regulatory-response/compliance department.

## Summary table of countermeasure effects

This organizes which risks each design element handled in this reference is effective against, as a ransomware countermeasure.

| Design element | Risk it defends against | Effective scenario |
|---|---|---|
| Detection of service impact (ensuring the depth of monitoring) | Missing service impact / user impact | Early grasp of a situation where resources appear normal but the service is not being provided to users |
| Designing monitoring levels according to importance | Missed detection in important systems, dispersion of operational resources | Rapid impact detection in mission-critical / important business systems |
| Attack detection by GuardDuty | Missing attacks/intrusions/malware introduction | Detection of attacks on EC2/S3, etc., malware infection, multi-stage attacks |
| Combination with third-party products | Threats outside the scope of AWS-native detection | Environments where checks by existing EDR are essential, double-check posture |
| Root-cause triage after an alert (manual checks) | The risk that a delay in judging whether an alert is caused by an external attack delays the response | After an alert from service impact / attack detection, directly observing a ransom-note display, the occurrence of encrypted files, etc., to judge whether it is an external attack |
| Aggregation and delegated administration of detection | Missed detection / delayed response due to individual confirmation in each account | Centralized visualization of detection results across the organization |
| Alert-triggered initiation of incident response | Delay from detection to the start of response | Reliably connecting detection to the response process |

## Related other references

- [02-log-analysis-and-investigation.md](./02-log-analysis-and-investigation.md): The stage of analyzing and investigating detected events by leveraging already-collected logs (Amazon Detective / SIEM on Amazon OpenSearch Service, checking for signs of infection, advance preparation for engaging forensic vendors)

## Reference: Official documentation

### Detection of service impact (monitoring/observability)

- [AWS Well-Architected Framework — Operational Excellence pillar, "Implement observability"](https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/implement-observability.html)
- [Choosing an AWS monitoring and observability service (AWS Decision Guide)](https://docs.aws.amazon.com/decision-guides/latest/monitoring-on-aws-how-to-choose/monitoring-on-aws-how-to-choose.html)
- [AWS Observability Best Practices (recipes list)](https://aws-observability.github.io/observability-best-practices/recipes/)
- [IPA "Strengthening the upstream process of system development (Non-Functional Requirements Grades)" introduction page](https://www.ipa.go.jp/archive/digital/iot-en-ci/jyouryuu/hikinou/ent03-b.html) (a reference for the concept of designing monitoring levels according to importance; the project has ended, but the deliverables remain publicly available)

### Detection of security attacks

- [Amazon GuardDuty](https://docs.aws.amazon.com/guardduty/)

For the detailed specifications of Amazon GuardDuty protection plans (supported resources, the kinds of threats that can be detected, enablement procedures, quotas, etc.), refer to the latest version of the official Amazon GuardDuty documentation. For details on aggregating detection results with AWS Security Hub, refer to the official AWS Security Hub documentation.
