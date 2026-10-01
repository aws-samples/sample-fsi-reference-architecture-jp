# External Resources

A curated collection of links and references for AWS Payment Cryptography,
organized by category. Use these resources for deeper learning, implementation
guidance, and staying current with service updates.

---

## Official Documentation

Core AWS documentation for Payment Cryptography service:

| Resource | URL |
|----------|-----|
| **User Guide** | https://docs.aws.amazon.com/payment-cryptography/latest/userguide/ |
| **Control Plane API Reference** | https://docs.aws.amazon.com/payment-cryptography/latest/APIReference/ |
| **Data Plane API Reference** | https://docs.aws.amazon.com/payment-cryptography/latest/DataAPIReference/ |
| **Service Endpoints & Quotas** | https://docs.aws.amazon.com/general/latest/gr/payment-cryptography.html |

### Key CLI Commands

The AWS CLI provides full access to Payment Cryptography operations:

- `aws payment-cryptography create-key` — Create symmetric or asymmetric keys
- `aws payment-cryptography import-key` — Import keys via TR-31/TR-34 or root certificate
- `aws payment-cryptography export-key` — Export keys wrapped under KEK
- `aws payment-cryptography list-keys` — List keys with optional filters
- `aws payment-cryptography get-key` — Retrieve key metadata and attributes
- `aws payment-cryptography delete-key` — Schedule key deletion (waiting period of 3–180 days; default 7 days)
  - ⚠️ **Caution**: Key deletion is irreversible once the waiting period ends.
    Data protected by the deleted key (and its aliases) becomes permanently
    unrecoverable unless a copy of the key exists outside APC. Before
    scheduling deletion, inventory every system and partner that depends on
    the key, and prefer `stop-key-usage` (disable) first to confirm nothing
    breaks. During the waiting period (`DeleteKeyInDays`, 3–180 days) the key
    is `DELETE_PENDING` and `restore-key` can cancel the deletion. For
    Multi-Region key replication, deleting a primary Region key also deletes
    its replica Region keys.
- `aws payment-cryptography-data generate-pin-data` — Generate PIN block
- `aws payment-cryptography-data verify-pin-data` — Verify PIN
- `aws payment-cryptography-data translate-pin-data` — Translate PIN between formats
- `aws payment-cryptography-data generate-card-validation-data` — CVV/CVC generation
- `aws payment-cryptography-data verify-card-validation-data` — CVV/CVC verification
- `aws payment-cryptography-data encrypt-data` — Encrypt payment data
- `aws payment-cryptography-data decrypt-data` — Decrypt payment data
- `aws payment-cryptography-data generate-mac` — Generate MAC
- `aws payment-cryptography-data verify-mac` — Verify MAC value

Full CLI reference: https://docs.aws.amazon.com/cli/latest/reference/payment-cryptography/

---

## AWS Blog Posts

### Launch & Service Announcements

- **"New – Move Payment Processing to the Cloud with AWS Payment Cryptography"** (June 2023)
  Service launch announcement covering core capabilities, key management, and
  cryptographic operations for payment workloads.
  https://aws.amazon.com/blogs/aws/new-move-payment-processing-to-the-cloud-with-aws-payment-cryptography/

- **"AWS Payment Cryptography is PCI PIN and P2PE certified"** (February 2024)
  Announcement of PCI PIN v3.1 and P2PE v3.1 certifications, enabling customers
  to reduce their compliance assessment scope.
  https://aws.amazon.com/blogs/security/aws-payment-cryptography-is-pci-pin-and-p2pe-certified/

- **"PCI PIN and P2PE compliance packages for AWS Payment Cryptography are now available"** (May 2026)
  Updated compliance packages available through AWS Artifact, including
  Attestation of Compliance and shared responsibility documentation.
  https://aws.amazon.com/blogs/security/pci-pin-and-p2pe-compliance-packages-for-aws-payment-cryptography-are-now-available/

### Technical Deep-Dives

- **"Synchronize keys automatically from payment HSMs to AWS Payment Cryptography"** (June 2025)
  Detailed walkthrough of automated key synchronization from on-premises HSMs
  using TR-31 key blocks and event-driven architectures.
  https://aws.amazon.com/blogs/industries/synchronize-keys-automatically-from-payment-hsms-to-aws-payment-cryptography/

- **"How to use AWS Payment Cryptography Service to simplify payment flows"** (March 2026)
  End-to-end tutorial covering PIN translation, card verification, and MAC
  generation in a typical acquirer-to-issuer flow.
  https://aws.amazon.com/blogs/industries/how-to-use-aws-payment-cryptography-service-to-simplify-payment-flows/

- **"Transforming transactions: Streamlining PCI compliance using AWS serverless architecture"** (October 2023)
  Architecture pattern combining Payment Cryptography with Lambda, API Gateway,
  and Step Functions for serverless payment processing.
  https://aws.amazon.com/blogs/security/transforming-transactions-streamlining-pci-compliance-using-aws-serverless-architecture/

---

## Sample Code & SDKs

### GitHub Repositories

- **AWS Samples — Payment Cryptography Service**
  https://github.com/aws-samples/samples-for-payment-cryptography-service

  Contains:
  - Java SDK examples for key management and cryptographic operations
  - Python ECDH key exchange flows
  - PIN translation workflow samples
  - Card verification data generation/verification
  - CloudFormation templates for infrastructure setup

### SDK Integration

| SDK | Package |
|-----|---------|
| Java | `software.amazon.awssdk:paymentcryptography` |
| Python (boto3) | `boto3.client('payment-cryptography')` |
| JavaScript/TypeScript | `@aws-sdk/client-payment-cryptography` |
| .NET | `AWSSDK.PaymentCryptography` |
| Go | `github.com/aws/aws-sdk-go-v2/service/paymentcryptography` |

### Migration Tools

- **AWS Transform Custom — AWS-Managed Transformations**
  https://docs.aws.amazon.com/transform/latest/userguide/transform-aws-customs.html#transform-aws-customs-available

  `AWS/payshield-hsm-to-aws-payment-cryptography` (Generally available): Rewrites Java
  applications that use the Thales payShield HSM socket-based command protocol to use
  the APC API via AWS SDK for Java v2 (includes command mapping, TR-31/TR-34 key import,
  KCV verification, and parity testing).

---

## Pricing & SLA

| Resource | URL |
|----------|-----|
| **Pricing** | https://aws.amazon.com/payment-cryptography/pricing/ |
| **Features Overview** | https://aws.amazon.com/payment-cryptography/features/ |
| **FAQ** | https://aws.amazon.com/payment-cryptography/faqs/ |
| **Service Level Agreement** | https://aws.amazon.com/payment-cryptography/sla/ |

### Pricing Model Summary

- Per-key charges (active keys per month)
- Per-API-call charges (cryptographic operations)
- No upfront fees or long-term commitments
- No charges for keys pending deletion

---

## Compliance Resources

### AWS-Provided Compliance Artifacts

- **AWS Artifact** — Download PCI PIN AOC, P2PE AOV, and Shared Responsibility
  Summary documents directly from the AWS Management Console.
  https://aws.amazon.com/artifact/

- **AWS Compliance Programs** — Overview of all AWS compliance certifications.
  https://aws.amazon.com/compliance/programs/

- **PCI DSS on AWS** — FAQ covering PCI DSS Level 1 compliance and shared
  responsibility for payment workloads.
  https://aws.amazon.com/compliance/pci-faqs/

### Key Compliance Certifications (Payment Cryptography)

| Standard | Status | Scope |
|----------|--------|-------|
| PCI PIN v3.1 | Certified | PIN processing and key management |
| PCI P2PE v3.1 | Certified | Point-to-point encryption decryption |
| PCI DSS v4.0 | In-scope | Part of AWS PCI DSS assessment |
| PCI 3DS | In-scope | Covered under AWS's PCI DSS/3DS assessment |
| SOC 1/2/3 | In-scope | Included in AWS SOC reports |

---

## Industry Standards (External)

### Payment Card Industry

- **PCI Security Standards Council (PCI SSC)**
  https://www.pcisecuritystandards.org/
  Governing body for PCI DSS, PCI PIN, PCI P2PE, and PA-DSS standards.

- **PCI PIN Security Requirements**
  https://www.pcisecuritystandards.org/document_library/
  Requirements for secure PIN handling in payment transactions.

### Key Management Standards

- **ANSI X9.143 (TR-31)** — Interoperable Secure Key Exchange Key Block
  Specification. Defines key block format used for key import/export in
  AWS Payment Cryptography.

- **ANSI X9.24-2 (TR-34)** — Retail Financial Services Symmetric Key
  Management Part 2: Using Asymmetric Techniques for the Distribution of
  Symmetric Keys. Used for initial key injection via asymmetric wrapping.

### EMV Standards

- **EMVCo**
  https://www.emvco.com/
  Global technical body managing EMV specifications for chip-based payment
  cards, contactless payments, tokenization, and 3-D Secure.

---

## Additional Resources

- **AWS re:Invent Sessions** — Search "payment cryptography" on
  https://www.youtube.com/@AWSEventsChannel for recorded presentations.

- **AWS Well-Architected Framework — Financial Services Lens**
  Guidance on building secure, resilient payment architectures on AWS.

- **AWS Partner Solutions (Financial Services)** — AWS Financial Services
  Competency Partners, including a Payments category, with links to the AWS
  Partner Solutions Finder.
  https://aws.amazon.com/financial-services/partner-solutions/

---
