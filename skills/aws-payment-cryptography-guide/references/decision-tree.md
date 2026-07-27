# Decision Tree: Which AWS Cryptography Service Should I Use?

Use this decision flow to determine whether AWS Payment Cryptography (APC)
is the right service for your workload.

---

## Decision Flow

```
Q1: Does your workload involve payment-specific cryptographic operations?
    (PIN verification, PIN translation, CVV generation, ARQC validation,
     card data encryption with DUKPT, P2PE decryption)
    │
    ├─ YES → Q2
    └─ NO  → Consider AWS KMS (general encryption) or AWS CloudHSM (custom crypto)

Q2: Do you need full control over dedicated HSM hardware?
    │
    ├─ YES → AWS CloudHSM (single-tenant, FIPS 140-2 Level 3, you manage clusters)
    └─ NO  → Q3

Q3: Do you need PCI PIN / PCI P2PE compliance for your HSM layer?
    │
    ├─ YES → AWS Payment Cryptography ✓ (PCI PIN, P2PE DMCP/KMCP/KLCP certified)
    └─ NO  → Q4

Q4: Do you need payment-specific APIs (PIN translate, ARQC verify, etc.)?
    │
    ├─ YES → AWS Payment Cryptography ✓
    └─ NO  → AWS KMS or CloudHSM depending on use case
```

---

## Service Comparison Table

| Criteria | AWS KMS | AWS CloudHSM | AWS Payment Cryptography |
|----------|---------|--------------|--------------------------|
| Use case | General encryption | Custom crypto, PKCS#11 | Payment-specific operations |
| Tenancy | Multi-tenant | Single-tenant dedicated | Multi-tenant managed |
| PCI PIN | No | Customer-managed | AWS-managed, certified |
| PCI P2PE | No | Customer-managed | AWS-managed, certified |
| Key types | Symmetric/asymmetric | Any (you control) | Payment keys (PEK, CVK, BDK, etc.) |
| API style | RESTful | PKCS#11, JCE | RESTful (payment-specific) |
| Pricing | Per key + per request | Per HSM hour | Per key + per API call |
| Management | Fully managed | Customer manages cluster | Fully managed |

---

## ✅ When to Use AWS Payment Cryptography

Use APC when **any** of the following apply:

- [ ] You perform PIN verification or PIN translation (e.g., issuer processing, ATM acquiring)
- [ ] You generate or validate CVV/CVV2/dCVV values
- [ ] You validate EMV ARQC/ARPC cryptograms
- [ ] You encrypt/decrypt card data using DUKPT or symmetric payment keys
- [ ] You operate a Point-to-Point Encryption (P2PE) decryption environment
- [ ] You need PCI PIN and/or PCI P2PE certified HSM infrastructure
- [ ] You want AWS to manage HSM hardware lifecycle, patching, and compliance audits
- [ ] You need elastic scaling of payment cryptographic operations without managing clusters
- [ ] You are migrating from on-premises payment HSMs (e.g., Thales payShield, Atalla)
- [ ] You want RESTful APIs instead of legacy HSM host command interfaces

---

## ❌ When NOT to Use AWS Payment Cryptography

APC is **not** the right choice when:

- **General-purpose encryption/decryption** — Use AWS KMS for encrypting S3 objects,
  EBS volumes, database fields, or application secrets.
- **TLS termination or certificate management** — Use AWS Certificate Manager (ACM)
  or CloudHSM with PKCS#11.
- **Custom cryptographic algorithms** — Use AWS CloudHSM if you need non-standard
  algorithms, custom firmware, or direct PKCS#11/JCE access.
- **Non-payment FIPS 140-2 Level 3 compliance** — Use AWS CloudHSM for generic
  FIPS 140-2 Level 3 single-tenant requirements outside of payments.
- **Digital signing for non-payment use cases** — Use AWS KMS asymmetric keys or
  CloudHSM for code signing, document signing, or blockchain operations.
- **Token vault / tokenization storage** — APC provides cryptographic operations,
  not token storage. Pair it with DynamoDB or a dedicated token vault.
- **You require PKCS#11 or JCE interfaces** — APC is API-only (REST); if your
  application requires PKCS#11 integration, use CloudHSM.

---

## Decision Summary

```
┌─────────────────────────────────────────────────────────────────┐
│  Payment crypto operations needed?                              │
│    NO  → AWS KMS / CloudHSM                                    │
│    YES → Dedicated hardware needed?                             │
│            YES → AWS CloudHSM                                   │
│            NO  → PCI PIN / P2PE compliance needed?              │
│                    YES → AWS Payment Cryptography ✓             │
│                    NO  → Payment-specific APIs needed?          │
│                            YES → AWS Payment Cryptography ✓     │
│                            NO  → AWS KMS / CloudHSM             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference: Key Differentiators of APC

1. **Purpose-built for payments** — APIs map directly to payment industry operations
2. **Compliance included** — PCI PIN and PCI P2PE certifications are AWS-managed
3. **No HSM management** — No clusters to provision, patch, or rotate hardware
4. **Elastic scaling** — Automatically scales with transaction volume
5. **Key import/export** — Supports TR-31, TR-34 key exchange for interoperability
6. **Multi-region** — Available in multiple AWS regions for geographic redundancy
