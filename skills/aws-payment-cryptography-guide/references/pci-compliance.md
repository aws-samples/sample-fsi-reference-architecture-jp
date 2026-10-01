# PCI Compliance with AWS Payment Cryptography

This reference explains the PCI compliance of AWS Payment Cryptography (APC),
covering the certifications held, the shared responsibility model, and guidance
for your own PCI assessments.

---

## Compliance Certifications

AWS Payment Cryptography holds the following PCI compliance certifications.
You can obtain and review the latest PCI coverage for AWS services and the applicable **Attestation of Compliance (AOC)** on a self-service basis using [AWS Artifact](https://aws.amazon.com/artifact/).

### PCI DSS

- PCI DSS (Payment Card Industry Data Security Standard) is an international security standard for the credit card industry, established by the PCI SSC (Security Standards Council) with the goal of enabling merchants and service providers to handle cardholder data securely.

### PCI PIN

- PCI PIN is a compliance program that covers HSM key management, PIN block processing, and key injection related to PIN (Personal Identification Number) security.

### PCI P2PE

- PCI P2PE (Point-to-Point Encryption) is an international security standard that protects card information by encrypting it end-to-end and consistently, from the credit card payment terminal through the network to payment processing.
- APC holds three separate Attestations of Validation (AOV):

| Component | AOV Type | Scope |
|-----------|----------|-------|
| Decryption Management | DMCP | APC used as the decryption environment |
| Key Management | KMCP | Key lifecycle management within APC |
| Key Loading | KLCP | APC key loading / injection capability |

- Confirm the latest PCI P2PE coverage and the applicable AOC in AWS Artifact.

### PCI 3DS

- PCI 3DS (3-D Secure) is an international security standard for securely handling the cardholder authentication mechanism used to prevent fraudulent use of credit cards, as well as the protection of that data.
- APC provides HSM-based cryptographic operations for 3DS Server / ACS (Access Control Server) / Directory Server (DS) implementations.
- Confirm the latest PCI 3DS coverage and the applicable AOC in AWS Artifact.

---

## Shared Responsibility Model

Like other AWS services, PCI compliance of APC is based on the **[shared responsibility model](https://aws.amazon.com/compliance/shared-responsibility-model/)**.
Understanding the shared responsibility model is a key point in properly designing the scope of your PCI assessment.

### AWS's Scope of Control

AWS is responsible for (has control over) the **security OF the cloud** (infrastructure):

| Category | AWS Responsibility |
|----------|-------------------|
| HSM Hardware | Procurement, provisioning, lifecycle management, and decommissioning of PCI PTS HSM-certified HSMs (operated in PCI mode) |
| Physical Security | Data center physical access controls, environmental protections, and surveillance |
| Main Key Management | Generation, storage, and rotation of AWS-managed main keys (Key Encryption Keys) |
| Infrastructure Compliance | Network infrastructure, hypervisor security, and service endpoint protection |
| Firmware Management | HSM firmware updates, security patches, and validation |
| Tamper Resistance | HSM tamper-detection and tamper-response mechanisms |
| Availability | Multi-AZ deployment, failover, and disaster recovery of HSM infrastructure |

### Customer's Scope of Control

The customer is responsible for (has control over) the **security IN the cloud**:

| Category | Customer Responsibility |
|----------|----------------------|
| Application Security | Secure coding, input validation, and secure API integration |
| Key Attribute Management | Appropriate key usage attributes, algorithm selection, and key purpose assignment |
| Correct API Usage | Proper use of translate, encrypt, decrypt, and generate operations |
| Data Handling After Decryption | Protection of cleartext data returned from APC |
| Access Controls | IAM policies, resource policies, and least-privilege access to APC APIs |
| Network Security | VPC configuration, security groups, and TLS enforcement for API calls |
| Monitoring & Alerting | Setting up appropriate alarms and responding to security events |
| Compliance Documentation | Managing the evidence and documentation required for your own PCI assessments |

---

## PCI PIN Compliance

### AWS Service's Scope of Control

When using APC for PIN processing, the following PCI PIN requirements can be placed within the AWS service's scope of control:

- **HSM Physical Security**: Physical access controls, tamper detection, and
  secure storage of HSMs in certified data centers
- **Key Storage in Key Blocks**: All keys stored in TR-31 key block format
  with bound key usage attributes (enforced by the AWS service)
- **Tamper Response**: Automatic key zeroization upon physical tamper detection
- **Dual Control for Main Keys**: AWS manages dual-control and split-knowledge
  procedures for main key generation and loading
- **Key Block Binding**: Cryptographic binding of key attributes to prevent
  misuse (e.g., preventing the use of a PIN Encryption Key as a PIN Verification Key)
- **HSM Logical Security**: Firmware integrity verification, secure boot, and
  restricted command sets

### What Remains with the Customer

The customer's scope of control continues to include the following:

- **PIN Block Handling in the Application**: Ensuring that PIN blocks are not
  logged, cached, or stored as cleartext in application memory beyond processing time
- **Network Security**: Enforcing TLS 1.2+ for all API calls,
  using VPC endpoints where appropriate, and network segmentation
- **Access Controls**: IAM policies that restrict who can call PIN-related APIs,
  and separation of duties between key management and PIN operations
- **PIN Try Counters**: Implementation of PIN try limits and lockout
  mechanisms at the application layer
- **PIN Mailer Security** (if applicable): Secure generation and distribution of PIN mailers
- **Cardholder Communication**: Secure channels for delivering PINs to cardholders

---

## PCI P2PE Components

### PCI Decryption Management Component Provider (DMCP)

APC serves as the **P2PE Decryption Environment**:

- Encrypted payment data from P2PE-validated POI devices is sent directly to APC for decryption
- Decryption occurs exclusively within HSM boundaries
- Cleartext PAN is returned to the customer's application over TLS
- The customer is responsible for protecting data after decryption
- Decryption keys are bound with appropriate usage attributes

```
[POI Device] → (encrypted data) → [Customer App] → [APC DecryptData API]
                                                          ↓
                                                   [HSM Decryption]
                                                          ↓
                                              (cleartext returned via TLS)
```

### PCI Key Management Component Provider (KMCP)

APC manages the full lifecycle of P2PE decryption keys:

- **Key Generation**: Secure random key generation within HSMs
- **Key Storage**: Keys are encrypted under AWS main keys and never exposed in cleartext
- **Key Distribution**: Secure key export using TR-31 key blocks for device injection
- **Key Rotation**: Programmatic key rotation via `CreateKey` and alias updates
- **Key Deletion**: Configurable deletion window with scheduling support

### PCI Key Loading Component Provider (KLCP)

You can use APC's key management capabilities to achieve PCI P2PE key loading:

- Enables secure key injection into payment terminals
- Supports the TR-31 and TR-34 key exchange protocols
- Certificate-based mutual authentication between APC and Key Loading Devices
- Audit trail for all key loading operations via CloudTrail
- Supports both initial key loading and key rotation scenarios

---

## Audit & Logging

### AWS CloudTrail

All APC control plane operations are logged in CloudTrail by default:

**Key Management Operations**:
- `CreateKey`, `DeleteKey`, `RestoreKey`, `StartKeyUsage`, `StopKeyUsage`
- `ImportKey`, `ExportKey`, `GetParametersForImport`, `GetParametersForExport`
- `ListKeys`, `GetKey`, `TagResource`, `UntagResource`
- `CreateAlias`, `UpdateAlias`, `DeleteAlias`

In addition, by explicitly enabling **data event logging** on a CloudTrail trail, data plane operations can also be logged in CloudTrail:
(**Data events are not logged by default**)

**Cryptographic Operations**:
- `EncryptData`, `DecryptData`
- `TranslatePinData`
- `GeneratePinData`, `VerifyPinData`
- `GenerateCardValidationData`, `VerifyCardValidationData`
- `GenerateMac`, `VerifyMac`
- `ReEncryptData`, `VerifyAuthRequestCryptogram`

To log data events, configure advanced event selectors on the trail that include the resource types `AWS Payment Cryptography key` and `AWS Payment Cryptography alias`. Additional charges apply. See [Logging AWS Payment Cryptography API calls using AWS CloudTrail](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/monitoring-cloudtrail.html).

Each log entry includes:
- Timestamp, source IP, and the IAM Principal identifier
- The ARN of the key used in the operation
- Request parameters (excluding sensitive data)
- Success/failure status and error codes

### Amazon CloudWatch Metrics

APC publishes primarily the following metrics to Amazon CloudWatch Metrics, allowing you to monitor its usage:

- `SuccessfulRequests` / `FailedRequests` — per operation
- `Latency` — operation processing time
- `ThrottledRequests` — rate limit events
- `KeyCount` — total number of active keys

### Key Metadata

Information (metadata) about the APC keys you use in an account and Region can be obtained through APIs (CLI) such as the following:

```bash
# List all keys with their attributes for compliance audit
aws payment-cryptography list-keys

# Get detailed key information, including KeyState (e.g., CREATE_COMPLETE,
# DELETE_PENDING), Enabled, usage start/stop timestamps, and DeletePendingTimestamp
aws payment-cryptography get-key --key-identifier "arn:aws:..."
```

> **Note**: `get-parameters-for-export` does not return key status. It returns the export
> parameters (signing key certificate, certificate chain, and export token) used to initiate a
> TR-34 key export (`TR34_KEY_BLOCK`). Use `get-key` to check key status.

---

## Accessing Compliance Reports

### AWS Artifact Portal

PCI compliance reports for APC are available through AWS Artifact:

1. Access the [AWS Artifact console](https://console.aws.amazon.com/artifact/)
2. Search for "Payment Cryptography" or "PCI" as the artifact to obtain
3. Accept the Non-Disclosure Agreement (NDA)
4. Download the documents

### Note: About NDA Requirements

- Obtaining most PCI compliance documents requires acceptance of a Non-Disclosure Agreement (NDA)
- A separate NDA acceptance may be required for each report
- NDA acceptance is recorded within AWS Artifact.

### Available Documents

| Document | Description |
|----------|-------------|
| PCI PIN AOC | Attestation of Compliance for PIN security requirements |
| PCI P2PE DMCP AOV | Attestation of Validation for Decryption Management |
| PCI P2PE KMCP AOV | Attestation of Validation for Key Management |
| PCI P2PE KLCP AOV | Attestation of Validation for Key Loading |
| PCI DSS AOC | Level 1 Service Provider Attestation of Compliance |
| Responsibility Summary | Detailed control-by-control responsibility matrix |
| Component User Guide | Guidance for customers integrating APC into their P2PE solution |
| PCI 3DS (via AWS's PCI DSS/3DS AOC) | APC is covered by AWS's PCI DSS/3DS assessment. Refer to AWS's PCI 3DS AOC |

---

## Impact on Customer's PCI Assessment

### PCI Assessment Scope Reduction

In line with the AWS shared responsibility model, using APC as an AWS service contributes to reducing the PCI assessment scope from the customer's perspective:

- **HSM Controls**: All HSM-related controls (physical security,
  key management hardware, tamper response) shift to AWS
- **Key Storage**: No need to demonstrate local key storage controls
- **Facility Security**: HSM facility security requirements are satisfied by AWS's compliance

### General Evidence Collection

When you undergo a PCI assessment, we recommend organizing the following information related to your use of APC.

1. **AWS Compliance Reports**: Download the relevant AOC/AOV from AWS Artifact
2. **Responsibility Matrix**: Reference the AWS Responsibility Summary document
3. **Architecture Diagrams**: Document how your application integrates with APC
4. **IAM Policies**: Present access controls for APC API access
5. **CloudTrail Logs**: Demonstrate audit logs of key management operations and, if data event logging is enabled, cryptographic operations
6. **Key Inventory**: Export key metadata that demonstrates proper key management
7. **Network Diagrams**: Present TLS enforcement and network segmentation

Beyond the above, you may also be required to present the following:

- **Compensating Controls**: The customer's alternative approaches for non-standard implementations
- **APC Operational Procedures**: Procedures for key rotation, access review, and
  incident response related to APC
- **Testing Evidence**: Results of application-layer penetration testing
  (testing against the customer's scope of control, not against AWS infrastructure)
- **Monitoring Configuration**: Monitoring using Amazon CloudWatch alarms and incident response procedures

### Reference: Scope Considerations

| Usage Scenario | Impact on Scope |
|---------|----------------|
| PIN translation only | Controls over the physical HSM itself are within APC's scope of control. Application controls are within the customer's scope of control |
| P2PE decryption | Decryption environment controls are within APC's scope of control. Post-decryption handling is within the customer's scope of control |
| Key management only | Key storage and lifecycle are within APC's scope of control. Key usage and its governance are within the customer's scope of control |
| Full payment processing | Application, network, and access controls are within the customer's scope of control |

---

## Disclaimer

> This guide provides general information about the PCI compliance of
> AWS Payment Cryptography. It is intended for educational and planning purposes only.
>
> **This document does NOT constitute**:
> - A formal PCI compliance assessment
> - Legal or regulatory advice
> - A guarantee of compliance for any specific implementation
> - A substitute for professional security assessment
>
> **A formal PCI compliance assessment requires an assessment by a Qualified
> Security Assessor (QSA)**. The specific scope, requirements, and evidence
> needed for an assessment depend on your unique implementation, business model,
> and the PCI standards applicable to your organization.
>
> AWS's compliance certifications cover AWS's infrastructure and services.
> Compliance with the PCI standards applicable to the portions of the environment
> that the customer manages remains within the customer's own scope of control.
>
> For the latest compliance status and certified Regions, refer to
> [AWS Artifact](https://console.aws.amazon.com/artifact/) and the
> [AWS Compliance Programs](https://aws.amazon.com/compliance/programs/)
> page.

---

## Related Resources

- [AWS Payment Cryptography Documentation](https://docs.aws.amazon.com/payment-cryptography/)
- [AWS Artifact](https://console.aws.amazon.com/artifact/)
- [AWS Compliance Programs](https://aws.amazon.com/compliance/programs/)
- [AWS Services in Scope by Compliance Program](https://aws.amazon.com/compliance/services-in-scope/)
- [PCI Security Standards Council](https://www.pcisecuritystandards.org/)
- [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/)
