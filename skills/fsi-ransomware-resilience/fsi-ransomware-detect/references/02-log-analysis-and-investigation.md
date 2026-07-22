# Log-Based Analysis and Investigation

## Overview

This reference describes the analysis and investigation of detected events in the ransomware countermeasures that this skill recommends. The detection stage (noticing / raising alerts) is handled in [01-detection-strategy.md](./01-detection-strategy.md). This reference handles the stage of drilling down into detected events and, by leveraging already-collected logs, narrowing down the possible causes, such as whether the event is due to an external attack and how far the impact has reached.

Detection and analysis are a phased approach, but their order is not fixed. Whereas detection is the stage of noticing that "something happened, somewhere" or that "there are signs of an attack," analysis/investigation is the stage of discerning "whether that event is due to an external attack" and "what path/scope it involves."

This reference organizes the means of analysis/investigation leveraging already-collected logs (Amazon Detective, SIEM on Amazon OpenSearch Service), the checking of signs of infection on servers, and the advance preparation for engaging forensic vendors when there are limits to analysis within one's own organization. Because the specific analysis methods themselves (how to write queries, tool operation procedures, etc.) are beyond this skill's scope, this is limited to presenting concepts and judgment axes, and the details are deferred to references to official documentation.

The analysis/investigation handled in this reference corresponds to "the analysis of detected events" in the detection function of the NIST Cybersecurity Framework, and to the "Analysis" stage in the AWS incident response approach.

Because the design of log collection/protection itself (which logs to aggregate where, and how to protect them) is handled in the Protect phase, it is not handled in this reference. This reference focuses on the perspective of "analyzing and investigating by leveraging already-collected logs." If consideration of log collection/protection is needed, guide the customer to leverage the Protect phase skill (fsi-ransomware-protect).

## Foundational concept: Leveraging already-collected logs and the difficulty of analysis

Analysis/investigation is the effort of understanding the nature, scope, and impact of an event by cross-referencing already-collected logs, starting from the alert obtained at the detection stage. Many of the logs used for analysis (AWS CloudTrail, VPC flow logs, various service logs, OS/application logs, etc.) are common with those used for detection. That these are collected/stored in normal times is the premise for analysis/investigation to hold.

On the other hand, there is an essential difficulty in analysis/investigation. Identifying the root cause (intrusion path) and determining the scope of damage require advanced specialist skills, and because the attacker's tactics and procedures (TTPs) are wide-ranging, there is no uniformly organized investigation method. Therefore, rather than trying to complete everything in-house, it is realistic and important to organize in advance the scope handled in-house and the scope delegated to specialist organizations such as forensic vendors.

## Means of analysis/investigation

### Investigation with Amazon Detective

Amazon Detective is a managed service that supports analyzing and investigating the root cause of security detection results and suspicious activity. It automatically collects log data from AWS resources and, using machine learning, statistical analysis, and graph theory, generates a visualization (behavior graph) that streamlines investigation.

In the ransomware-countermeasure context, the following uses can be considered.

- Starting from Amazon GuardDuty detection results (findings), visualize the connections and time-series behavior of related entities (resources, IPs, accounts, etc.) to grasp the spread of suspicious activity
- Trace the behavior before and after a detected event to narrow down the scope of impact and obtain material for judging whether it is an external attack

Because the data sources Detective uses for analysis and the scope of what can be investigated may change with feature enhancements, we recommend confirming the latest version of the official Amazon Detective documentation at the time of design/investigation.

### Analysis with SIEM on Amazon OpenSearch Service

As a means of collecting, correlating, and visualizing multiple kinds of logs to support the investigation of security incidents, SIEM on Amazon OpenSearch Service can be leveraged. This is a solution that aggregates various logs into Amazon OpenSearch Service and supports the analysis/detection of suspicious activity through correlation analysis and dashboard visualization.

In the ransomware-countermeasure context, by correlating across multiple log sources, the use of catching the flow/traces of an attack that are hard to see from a single log alone can be considered. When there is an existing SIEM foundation, or when integrated analysis of multiple log sources is a challenge, it is worth considering as an option.

### Checking signs of infection on servers

As part of analysis/investigation, it is also effective to log into the target server and directly check for signs of infection. Perspectives confirmed by logging into servers or from OS logs include the following.

- The occurrence of encrypted files (traces of file encryption by ransomware)
- The execution of suspicious processes/programs
- The presence of external communication to suspicious domains / abroad

These overlap with the detection stage (manual checks), but at the analysis/investigation stage, they are positioned as deeper checks for the purpose of corroborating detected events and grasping the scope of impact.

## Advance preparation for engaging forensic vendors

As noted above, identifying the root cause (intrusion path) and determining the scope of damage require advanced specialist skills, and because there is no uniform investigation method, many organizations face limits to analysis/investigation in-house. When the analysis bar from a security perspective is high, it is realistic to consider engaging specialist organizations such as forensic vendors.

What is important is to prepare for engaging forensic vendors in normal times, rather than scrambling to find a partner when an incident occurs. Specifically, the following advance preparations can be considered.

- Organizing the engagement procedures for forensic vendors (who, at what timing, and how to make the request)
- Considering the handover method for the analysis-target data (logs, evidence, etc.) provided to the vendor, and the external coordination of internal rules / contractual aspects regarding data sharing with external organizations
- Organizing the division between the scope handled in-house and the scope delegated to specialist organizations

By considering and developing these in normal times, a posture can be secured for promptly coordinating with specialist organizations in an emergency.

Note that executing evidence preservation for detected events (taking snapshots, evacuating disk images, ensuring the chain of custody, etc.) and conducting full-scale forensic analysis itself are handled in the Respond phase, so they are not handled in this reference. This reference handles, within analysis/investigation, up to "organizing the scope handled in-house versus the scope delegated to specialist organizations, and considering engaging forensic vendors as needed." If executing evidence preservation or full-scale forensic analysis is needed, guide the customer to leverage the Respond phase skill (fsi-ransomware-respond).

## Design decisions in the financial-institution context

### The importance of preparing forensic-vendor engagement in normal times

At financial institutions, because ransomware damage directly affects business continuity, customer response, and reporting to regulatory authorities, it is especially important to be able to move quickly to root-cause investigation and damage-scope identification when an incident occurs. On the premise that there are limits to in-house analysis, preparing the engagement posture with forensic vendors in normal times greatly influences the speed of response in an emergency.

### Log usability as a priority issue for analysis/investigation

For analysis/investigation to hold, the premise is that logs collected/stored in normal times are in a state where they can be promptly referenced/queried at the time of investigation. The priority issue for many organizations is to get the logs useful for forensic analysis into a usable state, and to prepare the operations/mechanisms for promptly coordinating with specialist organizations. Because the design of log collection/protection itself is handled in the Protect phase, this reference focuses on the perspective of "whether already-collected logs can be leveraged for analysis/investigation."

### Perspective of regulatory response / audit response

The results of analysis/investigation, and the logs/evidence referenced in that process, may be questioned in reporting to regulatory authorities and in audit response. However, judging conformance to specific regulatory articles is out of scope for this skill, and we recommend judging it in coordination with the organization's regulatory-response/compliance department.

## Summary table of countermeasure effects

This organizes which risks each design element handled in this reference is effective against, as a ransomware countermeasure.

| Design element | Risk it defends against | Effective scenario |
|---|---|---|
| Analysis/investigation leveraging already-collected logs (Amazon Detective) | Leaving detected events unaddressed / misjudging the scope of impact | Visualizing the spread of suspicious activity starting from detection results, judging whether it is an external attack |
| Correlation analysis with SIEM on Amazon OpenSearch Service | Missing the flow of an attack that is invisible from a single log | Grasping attack traces across multiple log sources |
| Checking signs of infection on servers | Insufficient corroboration of detected events / missing the scope of impact | Direct checking of encrypted files, suspicious processes, suspicious external communication |
| Preparing forensic-vendor engagement in normal times | Delay in root-cause investigation / damage-scope identification in an emergency | Prompt coordination with specialist organizations when there are limits to in-house analysis |
| Advance organization of the response scope between one's own organization and specialist organizations | Confusion of roles / delayed response at the time of an incident | Clarifying who handles what and to what extent |

## Related other references

- [01-detection-strategy.md](./01-detection-strategy.md): Detection design (detection of service impact + detection of security attacks). Handles the stage preceding the analysis/investigation handled in this reference (detection / raising alerts)

## Reference: Official documentation

- [Amazon Detective](https://docs.aws.amazon.com/detective/)
- [SIEM on Amazon OpenSearch Service (aws-samples)](https://github.com/aws-samples/siem-on-amazon-opensearch-service)
- [AWS Security Incident Response guide — Detect and Analyze](https://docs.aws.amazon.com/security-ir/latest/userguide/detect-and-analyze.html)

For the details of Amazon Detective's analysis data sources, scope of investigation targets, and features, and for the supported log types and deployment methods of SIEM on Amazon OpenSearch Service, refer to the latest version of each official document/repository. Note that SIEM on Amazon OpenSearch Service is a solution published in the AWS aws-samples repository, and differs in the nature of its origin from the official AWS documentation (docs.aws.amazon.com).
