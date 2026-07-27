# Key Management Best Practices for AWS Payment Cryptography

## Overview

Key management is the foundation of payment security. AWS Payment Cryptography (APC) provides
a fully managed service for cryptographic key lifecycle management compliant with PCI PIN,
PCI P2PE, and PCI DSS standards. This guide covers import/export methods, key hierarchies,
rotation strategies, and handling non-standard vendor integrations.

---

## Key Import Methods

### TR-34 (Asymmetric Key Exchange)

TR-34 is the **preferred method** for importing Key Encryption Keys (KEKs) into APC.

- **Protocol**: Asymmetric (RSA-based) key transport
- **Use Case**: Initial KEK establishment between two parties
- **Supported Key Types**: TDES (2-key, 3-key) and AES-128
- **Roles**: Key Distribution Host (KDH) sends key to Key Receiving Device (KRD)
- **APC Role**: Acts as KRD during import

```
┌─────────────┐         TR-34         ┌─────────────┐
│  External   │  ───────────────────►  │     APC     │
│  HSM (KDH)  │   Wrapped KEK in      │    (KRD)    │
│             │   TR-34 envelope       │             │
└─────────────┘                        └─────────────┘
```

**Workflow**:
1. APC generates an RSA key pair and provides the public key certificate
2. External KDH wraps the KEK using APC's public key
3. KDH signs the payload with its private key
4. APC verifies the signature using the imported KDH certificate
5. APC unwraps and stores the KEK

### TR-31 (Symmetric Key Wrapping)

TR-31 is used for importing **working keys** under an already-established KEK.

- **Protocol**: Symmetric key wrapping per ANSI X9.143
- **Use Case**: Importing PIN encryption keys, MAC keys, data encryption keys
- **Prerequisite**: A KEK must already exist in APC (imported via TR-34 or other method)
- **Key Block Format**: Includes key usage, mode of use, and exportability attributes

### RSA Wrap/Unwrap

For environments that cannot support TR-34 but can use asymmetric encryption:

- **Protocol**: RSA OAEP key wrapping
- **Supported Key Types**: TDES and AES-128
- **Use Case**: Simpler asymmetric import when TR-34 tooling is unavailable
- **Security**: Less metadata protection than TR-34 (no key block attributes in transit)

### ECDH (Elliptic Curve Diffie-Hellman)

The most modern and flexible key agreement method:

- **Protocol**: ECDH key agreement (NIST P-256, P-384, P-521 curves)
- **Supported Key Types**: Up to **AES-256** (strongest supported)
- **Use Case**: Establishing shared secrets for AES-256 keys
- **Advantage**: Supports higher key strengths than TR-34 or RSA Wrap

### Root Public Key Certificate Import

For establishing trust anchors:

- **Use Case**: Importing CA certificates of external partners for TR-34 verification
- **Format**: X.509 certificate (DER or PEM encoded)
- **Trust Model**: Imported certificates validate KDH signatures during TR-34 import

---

## Key Export Methods

### TR-34 Export (APC as KDH)

APC can act as the Key Distribution Host to export KEKs to external systems:

- **APC Role**: KDH (sender)
- **Use Case**: Distributing KEKs to partner HSMs, payment terminals
- **Process**: APC wraps the KEK using the receiving party's public key

### TR-31 Export

Export working keys wrapped under a shared KEK:

- **Use Case**: Distributing PIN keys, MAC keys to processing partners
- **Prerequisite**: Shared KEK between APC and the receiving party

### DUKPT IPEK Export from BDK

Derive and export Initial PIN Encryption Keys (IPEKs) from a Base Derivation Key (BDK):

- **Use Case**: Terminal key injection for DUKPT-based POS devices
- **Process**: APC derives IPEK from BDK + Initial KSN, exports wrapped in TR-31

---

## Handling Non-Standard Vendors

When external partners (card bureaus, legacy processors, network gateways) do NOT
support TR-31, TR-34, or ECDH:

### Option A: Bridge HSM Approach

Use an intermediary HSM to translate between formats:

```
┌──────────────┐    Proprietary    ┌──────────────┐    TR-31/34    ┌─────────┐
│   Legacy     │  ──────────────►  │  Bridge HSM  │  ───────────►  │   APC   │
│   Partner    │    Format         │  (CloudHSM   │   Standard     │         │
│              │                   │  or On-Prem) │   Format       │         │
└──────────────┘                   └──────────────┘                └─────────┘
```

- **AWS CloudHSM**: Deploy in your VPC, load partner's proprietary firmware/keys
- **On-Premises HSM**: Use existing HSM infrastructure as translation layer

### Option B: Clear-Text Key Component Exchange

When no other option is available:

- **Method**: Dual-control, split-knowledge key components
- **Transport**: Separate secure channels for each component
- **PCI Risks**: Requires compensating controls documented in ROC
- **Controls Required**: Background checks, tamper-evident packaging, chain of custody logs, immediate destruction after loading, QSA approval

### Option C: Negotiation Strategy

Push partners toward standards adoption:

1. **Educate**: Share TR-31/TR-34 implementation guides with partner
2. **Timeline**: Propose 6-12 month migration roadmap
3. **Interim**: Use Bridge HSM during transition period
4. **Incentivize**: Highlight reduced ceremony costs and faster key rotation
5. **Escalate**: Involve partner's compliance team (PCI requirements favor electronic exchange)

---

## DUKPT Key Hierarchy

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                    BDK (Base Derivation Key)          │
│                    Stored in APC                      │
└───────────────────────────┬─────────────────────────┘
                            │ Derivation
                ┌───────────┼───────────┐
                ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  IPEK 1  │ │  IPEK 2  │ │  IPEK N  │
        │(Terminal1)│ │(Terminal2)│ │(TerminalN)│
        └─────┬────┘ └─────┬────┘ └─────┬────┘
              ▼             ▼             ▼
        Session Keys   Session Keys   Session Keys
```

### KSN (Key Serial Number) Structure

| Field | Bits | Description |
|-------|------|-------------|
| BDK ID | 22 | Identifies the BDK |
| Terminal ID | 10 | Unique terminal identifier |
| Transaction Counter | 21 | Increments per transaction |

### Terminal Key Injection Workflow

1. **BDK Creation**: Generate or import BDK into APC
2. **IPEK Derivation**: APC derives IPEK from BDK + Initial KSN
3. **IPEK Export**: Export IPEK wrapped in TR-31 key block
4. **Injection**: Load IPEK into terminal via secure key injection facility
5. **Operation**: Terminal derives session keys from IPEK for each transaction
6. **Decryption**: APC uses BDK to derive the same session key for decryption

---

## Key Rotation Strategy

### Rotation Frequency by Key Type

| Key Type | Recommended Frequency | Method |
|----------|----------------------|--------|
| KEK (Zone Master Key) | Annual | Manual (TR-34 re-exchange) |
| PIN Encryption Key (PEK) | Quarterly | Automated (TR-31 under KEK) |
| MAC Key | Quarterly | Automated (TR-31 under KEK) |
| Data Encryption Key | Monthly or per-session | Automated |
| BDK (DUKPT) | Every 1M transactions or annual | Manual (new BDK + re-injection) |
| Card Verification Key | Annual | Coordinated with card network |

### Zero-Downtime Rotation Pattern

```python
# Pseudocode for zero-downtime key rotation
def rotate_working_key(current_key_arn, kek_arn):
    # 1. Create new key
    new_key = apc.create_key(key_attributes=current_key.attributes)
    # 2. Export new key (TR-31) for partner distribution
    tr31_block = apc.export_key(new_key.arn, wrapping_key=kek_arn)
    # 3. Distribute to partner
    distribute_to_partner(tr31_block)
    # 4. Cutover: Update alias to point to new key
    apc.update_alias(alias="alias/pin-key-prod", target=new_key.arn)
    # 5. Grace period: Keep old key active for in-flight transactions
    schedule_deactivation(current_key_arn, delay="24h")
    # 6. Delete old key after grace period
    schedule_deletion(current_key_arn, delay="7d")
```

**Steps**: Create → Distribute → Dual-active period → Cutover → Grace period → Delete

---

## Key Lifecycle

### State Machine

```
┌────────┐    Create    ┌────────┐   Rotate    ┌──────────┐
│  None  │ ──────────►  │ Active │ ──────────►  │ Rotated  │
└────────┘              └───┬────┘              └────┬─────┘
                            │ Delete                  │ Delete
                            ▼                        ▼
                       ┌─────────┐              ┌─────────┐
                       │Scheduled│ ───────────► │ Deleted  │
                       │  Delete │   (7 days)   │          │
                       └─────────┘              └─────────┘
```

### CloudTrail Auditing

All key operations are logged: `CreateKey`, `ImportKey`, `ExportKey`, `DeleteKey`, `TagResource`, `UntagResource`.

### Tag-Based Tracking

| Tag Key | Example Value | Purpose |
|---------|---------------|---------|
| `Environment` | `production` | Deployment stage |
| `KeyPurpose` | `pin-encryption` | Functional role |
| `Partner` | `first-data` | External party association |
| `RotationDate` | `2025-06-15` | Next rotation target |
| `Owner` | `payments-team` | Responsible team |
| `ComplianceScope` | `pci-pin` | Regulatory requirement |

---

## Multi-Region Keys

### Replication Architecture

```
┌─────────────────┐         Replication         ┌─────────────────┐
│   us-east-1     │  ◄─────────────────────────► │   eu-west-1     │
│   (Primary)     │       Synchronized          │   (Replica)     │
│  KEK/PEK/BDK   │                              │  KEK/PEK/BDK   │
└─────────────────┘                              └─────────────────┘
```

### Use Cases

- **Disaster Recovery**: Automatic failover to replica region
- **Latency Optimization**: Process transactions in region closest to terminal
- **Compliance**: Data residency requirements for specific geographies
- **Active-Active**: Simultaneous processing across regions with same keys

### Considerations

- Replication is asynchronous (eventual consistency)
- Key attributes and tags replicate with the key
- Deletion replicates across all regions
- Monitor replication lag via CloudWatch metrics

---

## ANSI TR-31 Key Block Format

### Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  Header  │  Key Length  │  Key Data (Encrypted)  │    MAC       │
│ (16+ B)  │   (4 hex)   │                        │  (8-16 B)   │
└─────────────────────────────────────────────────────────────────┘
```

### Header Fields

| Field | Length | Description |
|-------|--------|-------------|
| Version | 1 char | `A`/`B`/`C`=TDES, `D`=AES |
| Key Block Length | 4 hex | Total block length |
| Key Usage | 2 char | Purpose code (e.g., `P0`=PIN Encryption) |
| Algorithm | 1 char | `T`=TDES, `A`=AES, `R`=RSA |
| Mode of Use | 1 char | `E`=Encrypt, `D`=Decrypt, `B`=Both, `N`=No restriction |
| Exportability | 1 char | `E`=Exportable, `N`=Non-exportable, `S`=Sensitive |

### Key Usage Codes

| Code | Meaning | Code | Meaning |
|------|---------|------|---------|
| `P0` | PIN Encryption Key | `K0` | Key Encryption (KEK) |
| `B0` | BDK | `K1` | Key Block Protection Key |
| `M1` | MAC (Algorithm 1) | `V0` | PIN Verification (Visa PVV) |
| `M3` | MAC (Algorithm 3) | `V1` | PIN Verification (IBM 3624) |
| `D0` | Data Encryption | | |

### Modes of Use

| Code | Meaning | Code | Meaning |
|------|---------|------|---------|
| `B` | Both Encrypt/Decrypt | `G` | Generate only |
| `C` | Compute (generate MAC) | `N` | No restriction |
| `D` | Decrypt/Unwrap only | `S` | Signature only |
| `E` | Encrypt/Wrap only | `V` | Verify only |
| `X` | Key derivation | | |

---

## Key Synchronization from External HSMs

### Reference: Blog Post

> **"Synchronize keys automatically from payment HSMs to AWS Payment Cryptography"**
> Published: June 2025
> https://aws.amazon.com/blogs/security/synchronize-keys-automatically-from-payment-hsms-to-aws-payment-cryptography/

**Key Concepts**: Automated TR-31 key export from on-premises HSM → S3 → Lambda event-driven import into APC. Maintains key attribute parity, supports gradual migration without disrupting production.

```
┌───────────┐    TR-31 Export    ┌─────────┐    S3 Event    ┌────────┐    Import    ┌─────┐
│ On-Prem   │ ───────────────►  │   S3    │ ─────────────► │ Lambda │ ──────────►  │ APC │
│ HSM       │   (Scheduled)     │ Bucket  │                │        │   TR-31     │     │
└───────────┘                   └─────────┘                └────────┘             └─────┘
```

---

## Key Exchange Decision Matrix

| Partner Capability | Recommended Method | Fallback | Cost |
|---|---|---|---|
| Supports TR-34 | TR-34 (electronic) | — | Low |
| Supports TR-31 only | TR-31 under existing KEK | TR-34 for KEK first | Low |
| Supports ECDH | ECDH key agreement | — | Low |
| Supports RSA only | RSA Wrap/Unwrap | — | Low |
| No electronic capability | Bridge HSM translation | Dual-control clear-text components (last resort) | Medium |
| Proprietary format only | Bridge HSM translation | Partner standards adoption | Medium |
| Clear-text components only | Dual-control components | Bridge HSM | Medium (+ PCI risk) |

---

## References

- [AWS Payment Cryptography User Guide – Key Management](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/keys.html)
- [ANSI X9.143 (TR-31) Standard](https://x9.org/)
- [ASC X9 TR-34 Key Distribution](https://x9.org/)
- [Synchronize keys automatically from payment HSMs to AWS Payment Cryptography (June 2025)](https://aws.amazon.com/blogs/security/synchronize-keys-automatically-from-payment-hsms-to-aws-payment-cryptography/)
- [PCI PIN Security Requirements](https://www.pcisecuritystandards.org/)
- [NIST SP 800-57 Key Management Recommendations](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)
