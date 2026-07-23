# PCI Compliance with AWS Payment Cryptography

This reference covers PCI compliance aspects of AWS Payment Cryptography (APC),
including certifications held, the shared responsibility model, and guidance for
customers undergoing their own PCI assessments.
---

## Compliance Certifications

AWS Payment Cryptography holds the following PCI compliance certifications,
assessed by an independent Qualified Security Assessor (QSA):

### PCI PIN

- **Attestation of Compliance (AOC)** for PIN security
- Covers HSM key management, PIN block processing, and key injection
- Validates that APC meets PCI PIN Security Requirements for hardware and
  key management controls

### PCI P2PE (Point-to-Point Encryption)

APC holds three separate Attestations of Validation (AOV):

| Component | AOV Type | Scope |
|-----------|----------|-------|
| Decryption Management | DMCP | APC as the decryption environment |
| Key Management | KMCP | Key lifecycle management within APC |
| Key Loading | KLCP | APC key loading / injection capability |

### PCI DSS Level 1

- APC infrastructure is included in AWS's PCI DSS Level 1 Service Provider
  compliance
- Covers the underlying infrastructure, network segmentation, access controls,
  and monitoring

### PCI 3DS (3-D Secure)

- AWS Payment Cryptography is **in scope of AWS's PCI DSS and PCI 3DS
  assessments** (distinct from the APC-specific PCI PIN and PCI P2PE
  attestations listed above). It can provide HSM-based cryptographic operations
  for 3DS Server / ACS / DS implementations.
- Confirm current 3DS coverage and obtain the applicable AOC via AWS Artifact.
---

## Shared Responsibility Model

PCI compliance with AWS Payment Cryptography follows a shared responsibility
model. Understanding the division of responsibilities is critical for scoping
your own PCI assessment.

### AWS Responsibilities

AWS is responsible for the **security OF the cloud** infrastructure:

| Category | AWS Responsibility |
|----------|-------------------|
| HSM Hardware | Procurement, provisioning, lifecycle management, and decommissioning of PCI PTS HSM-certified HSMs (operated in PCI mode) |
| Physical Security | Data center physical access controls, environmental protections, and surveillance |
| Main Key Management | Generation, storage, and rotation of AWS-managed main keys (Key Encryption Keys) |
| Infrastructure Compliance | Network infrastructure, hypervisor security, and service endpoint protection |
| Firmware Management | HSM firmware updates, security patches, and validation |
| Tamper Response | HSM tamper-evident and tamper-responsive mechanisms |
| Availability | Multi-AZ deployment, failover, and disaster recovery of HSM infrastructure |

### Customer Responsibilities

Customers are responsible for **security IN the cloud**:

| Category | Customer Responsibility |
|----------|----------------------|
| Application Security | Secure coding practices, input validation, and secure API integration |
| Key Attribute Management | Correct key usage attributes, algorithm selection, and key purpose assignment |
| Correct API Usage | Proper use of translate, encrypt, decrypt, and generate operations |
| Data Handling After Decryption | Protection of cleartext data once returned from APC |
| Access Controls | IAM policies, resource policies, and least-privilege access to APC APIs |
| Network Security | VPC configuration, security groups, and TLS enforcement for API calls |
| Monitoring & Alerting | Setting up appropriate alarms and responding to security events |
| Compliance Documentation | Maintaining evidence and documentation for their own PCI assessments |
---

## PCI PIN Compliance

### What Shifts to AWS

When using APC for PIN processing, the following PCI PIN requirements shift
to AWS's responsibility:

- **HSM Physical Security**: Physical access controls, tamper detection, and
  secure storage of HSMs in certified data centers
- **Key Storage in Key Blocks**: All keys stored using TR-31 key block format
  with bound key usage attributes (enforced by the service)
- **Tamper Response**: Automatic key zeroization upon physical tamper detection
- **Dual Control for Main Keys**: AWS manages dual-control and split-knowledge
  procedures for main key generation and loading
- **Key Block Binding**: Cryptographic binding of key attributes preventing
  misuse (e.g., using a PIN Encryption Key as a PIN Verification Key)
- **HSM Logical Security**: Firmware integrity verification, secure boot, and
  restricted command sets

### What Remains with the Customer

Customers retain responsibility for:

- **PIN Block Handling in Application**: Ensuring PIN blocks are never logged,
  cached, or stored in cleartext within application memory beyond processing
- **Network Security**: TLS 1.2+ enforcement for all API calls, VPC endpoint
  usage where appropriate, and network segmentation
- **Access Controls**: IAM policies restricting who can call PIN-related APIs,
  separation of duties between key management and PIN operations
- **PIN Try Counters**: Implementation of PIN try limits and lockout mechanisms
  at the application layer
- **PIN Mailer Security** (if applicable): Secure generation and distribution
  of PIN mailers
- **Cardholder Communication**: Secure channels for PIN delivery to cardholders
---

## PCI P2PE Components

### Decryption Management Component Provider (DMCP)

APC serves as the **P2PE Decryption Environment**:

- Encrypted payment data from P2PE-validated POI devices is sent directly to
  APC for decryption
- Decryption occurs exclusively within HSM boundaries
- Cleartext PAN is returned to the customer's application over TLS
- Customer is responsible for protecting data post-decryption
- Decryption keys are bound with appropriate usage attributes

```
[POI Device] → (encrypted data) → [Customer App] → [APC DecryptData API]
                                                            ↓
                                                     [HSM Decryption]
                                                            ↓
                                                (cleartext returned via TLS)
```

### Key Management Component Provider (KMCP)

APC manages the full lifecycle of P2PE decryption keys:

- **Key Generation**: Secure random key generation within HSMs
- **Key Storage**: Keys encrypted under AWS main keys, never exposed in cleartext
- **Key Distribution**: Secure key export using TR-31 key blocks for device injection
- **Key Rotation**: Programmatic key rotation via `CreateKey` and alias updates
- **Key Deletion**: Configurable deletion window with scheduling support

### Key Loading Component Provider (KLCP)

APC's key loading capability supports PCI P2PE key loading:

- Enables secure key injection into payment terminals
- Supports TR-31 and TR-34 key exchange protocols
- Certificate-based mutual authentication between APC and Key Loading Devices
- Audit trail for all key loading operations via CloudTrail
- Supports both initial key loading and key rotation scenarios

---

## Covered Regions — Service Availability vs. PCI Certification

**Critical distinction:** the Regions where AWS Payment Cryptography is
*available* are broader than the Regions where it is *PCI PIN / P2PE certified*.
Availability in a Region does **not** imply PCI PIN/P2PE certification in that
Region.

- **Service availability** includes Asia Pacific Regions such as Tokyo
  (`ap-northeast-1`) and Osaka (`ap-northeast-3`).
- **PCI PIN / P2PE certified Regions are a subset** and are expanded over time
  (for example, PCI PIN/P2PE coverage was extended to South America — São Paulo
  (`sa-east-1`) and Asia Pacific — Sydney (`ap-southeast-2`)). At the time of
  writing, the Tokyo/Osaka Regions are **not confirmed** to be within PCI
  PIN/P2PE certification scope.

> ⚠️ **For Japan-based deployments this is decisive.** Do not assume in-Region
> PCI PIN/P2PE coverage for Tokyo/Osaka. Always confirm the **current**
> certified-Region list for PCI PIN, P2PE, DSS, and 3DS in
> [AWS Artifact](https://console.aws.amazon.com/artifact/) and the
> [AWS Services in Scope](https://aws.amazon.com/compliance/services-in-scope/)
> page before designing for in-Region compliance.

---

## Audit & Logging

### AWS CloudTrail

All APC operations are logged in CloudTrail:

**Key Management Operations**:
- `CreateKey`, `DeleteKey`, `UpdateKeyAttributes`
- `ImportKey`, `ExportKey`
- `ListKeys`, `GetKey`, `GetKeyStatus`
- `CreateAlias`, `UpdateAlias`, `DeleteAlias`

**Cryptographic Operations**:
- `EncryptData`, `DecryptData`
- `TranslatePinData`
- `GeneratePinData`, `VerifyPinData`
- `GenerateCardValidationData`, `VerifyCardValidationData`
- `GenerateMac`, `VerifyMac`

Each log entry includes:
- Timestamp, source IP, IAM identity
- Key ARN used in the operation
- Request parameters (excluding sensitive data)
- Success/failure status and error codes

### Amazon CloudWatch Metrics

Monitor APC usage with CloudWatch:

- `SuccessfulRequests` / `FailedRequests` — per operation
- `Latency` — operation processing time
- `ThrottledRequests` — rate limit events
- `KeyCount` — total active keys

### Compliance Reporting via Key Metadata

Use APC APIs for compliance reporting:

```bash
# List all keys with their attributes for compliance audit
aws payment-cryptography list-keys

# Get detailed key information including creation date and usage
aws payment-cryptography get-key --key-identifier "arn:aws:..."

# Check key status and expiration
aws payment-cryptography get-parameters-for-export \
  --key-material-type KEY_CRYPTOGRAM \
  --signing-key-algorithm RSA_2048
```

---

## Accessing Compliance Reports

### AWS Artifact Portal

PCI compliance reports for APC are available through AWS Artifact:

1. Navigate to the [AWS Artifact console](https://console.aws.amazon.com/artifact/)
2. Search for "Payment Cryptography" or "PCI"
3. Accept the NDA (required for most reports)
4. Download the relevant documents

### NDA Requirements

- Most PCI compliance documents require acceptance of a Non-Disclosure Agreement
- The NDA is presented electronically within the AWS Artifact portal
- Each report may have its own NDA acceptance requirement
- NDA acceptance is logged and associated with your AWS account

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
| PCI 3DS (via AWS PCI DSS/3DS AOC) | APC is covered under AWS's PCI DSS/3DS assessment; refer to the AWS PCI 3DS AOC |

---

## Impact on Customer's PCI Assessment

### SAQ/RoC Scope Reduction

Using APC can significantly reduce your PCI assessment scope:

- **HSM Controls**: All HSM-related controls (physical security, key management
  hardware, tamper response) shift to AWS
- **Key Storage**: No need to demonstrate local key storage controls
- **Facility Security**: HSM facility security requirements are satisfied by
  AWS's compliance

### Evidence Collection

When undergoing your PCI assessment, prepare the following evidence:

1. **AWS Compliance Reports**: Download relevant AOC/AOV from AWS Artifact
2. **Responsibility Matrix**: Reference the AWS Responsibility Summary document
3. **Architecture Diagrams**: Document how your application integrates with APC
4. **IAM Policies**: Show access controls for APC API access
5. **CloudTrail Logs**: Demonstrate audit logging of all cryptographic operations
6. **Key Inventory**: Export key metadata showing proper key management
7. **Network Diagrams**: Show TLS enforcement and network segmentation

### Assessor Expectations

Your QSA will typically want to see:

- **Service Agreement**: Evidence of your AWS service agreement
- **Compliance Inheritance**: Documentation showing which controls AWS owns
- **Compensating Controls**: Any compensating controls for non-standard implementations
- **Operational Procedures**: Your procedures for key rotation, access review,
  and incident response related to APC
- **Testing Evidence**: Results of penetration testing on your application layer
  (not on AWS infrastructure)
- **Monitoring Configuration**: CloudWatch alarms and incident response procedures

### Scope Considerations

| Scenario | Impact on Scope |
|----------|----------------|
| PIN translation only | HSM controls fully delegated; application controls remain |
| P2PE decryption | Decryption environment controls delegated; post-decryption handling in scope |
| Key management only | Key storage and lifecycle delegated; key usage governance remains |
| Full payment processing | Significant reduction but application, network, and access controls remain |

---

## Disclaimer

> **⚠️ Important Notice**
>
> This guide provides general information about PCI compliance aspects of
> AWS Payment Cryptography. It is intended for educational and planning purposes only.
>
> **This document does NOT constitute**:
> - A formal PCI compliance assessment
> - Legal or regulatory advice
> - A guarantee of compliance for any specific implementation
> - A substitute for professional security assessment
>
> **Formal PCI compliance assessment requires engagement with a Qualified
> Security Assessor (QSA)**. The specific scope, requirements, and evidence
> needed for your assessment will depend on your unique implementation,
> business model, and the PCI standards applicable to your organization.
>
> AWS compliance certifications cover AWS's infrastructure and services.
> Customers are responsible for their own compliance with applicable PCI
> standards for the portions of the environment they control.
>
> For the most current compliance status and certified regions, always refer to
> [AWS Artifact](https://console.aws.amazon.com/artifact/) and the
> [AWS Compliance Programs](https://aws.amazon.com/compliance/programs/) page.

---

## Related Resources

- [AWS Payment Cryptography Documentation](https://docs.aws.amazon.com/payment-cryptography/)
- [AWS Artifact](https://console.aws.amazon.com/artifact/)
- [AWS Compliance Programs](https://aws.amazon.com/compliance/programs/)
- [AWS Services in Scope by Compliance Program](https://aws.amazon.com/compliance/services-in-scope/)
- [PCI Security Standards Council](https://www.pcisecuritystandards.org/)
- [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/)
