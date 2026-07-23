# Acquirer Reference Guide — AWS Payment Cryptography

> For merchant acquiring banks, payment processors on the acquiring side, and terminal management providers.

---

## Table of Contents

1. [P2PE Decryption](#p2pe-decryption)
2. [PIN Translation](#pin-translation)
3. [MAC Generation & Verification](#mac-generation--verification)
4. [Terminal Key Management](#terminal-key-management)

---

## P2PE Decryption

### Overview

Point-to-Point Encryption (P2PE) protects cardholder data from the Point of Interaction (POI) terminal through to the acquirer's secure decryption environment. AWS Payment Cryptography serves as a **PCI P2PE Decryption Component** certified under the PCI P2PE DMCP program.

### DUKPT Key Hierarchy

```
Base Derivation Key (BDK)
  └── Initial PIN Encryption Key (IPEK)
        └── Future Keys (derived per transaction via KSN)
```

| Key Level | Purpose | Storage |
|-----------|---------|---------|
| BDK | Master key, never leaves HSM | AWS Payment Cryptography (TR31_P0_PIN_ENCRYPTION_KEY) |
| IPEK | Injected into terminal at provisioning | Terminal secure memory |
| Transaction Key | Derived from IPEK + KSN | Ephemeral, per-transaction |

### DecryptData API with DUKPT

```json
{
  "KeyIdentifier": "arn:aws:payment-cryptography:us-east-1:123456789012:key/abc123",
  "CipherText": "A1B2C3D4E5F6...",
  "DecryptionAttributes": {
    "Dukpt": {
      "KeySerialNumber": "FFFF9876543210E00001",
      "DukptKeyDerivationType": "TDES_3KEY",
      "DukptKeyVariant": "BIDIRECTIONAL",
      "Mode": "CBC"
    }
  }
}
```

### Supported DUKPT Derivation Types

| Derivation Type | Key Length | Use Case |
|----------------|-----------|----------|
| `TDES_2KEY` | 128-bit (112 effective) | Legacy terminals |
| `TDES_3KEY` | 192-bit (168 effective) | Standard POS terminals |
| `AES_128` | 128-bit | Modern terminals (ANSI X9.24-3) |
| `AES_256` | 256-bit | High-security environments |

### Supported Encryption Modes

- **CBC** (Cipher Block Chaining) — most common for P2PE payloads
- **ECB** (Electronic Codebook) — limited use cases
- **CFB** (streaming decryption in certain terminal implementations)

### P2PE DMCP Certification Benefits

- Reduces PCI DSS scope for acquirers (SAQ P2PE eligibility for merchants)
- AWS manages HSM compliance and audit evidence
- Decryption environment isolation within AWS Payment Cryptography service boundary

---

## PIN Translation

### Overview

PIN translation converts an encrypted PIN block from one key to another without exposing cleartext PIN. Essential when routing transactions from terminal-level keys (DUKPT/ZPK) to network-level keys.

### TranslatePinData API

```json
{
  "IncomingKeyIdentifier": "arn:aws:payment-cryptography:us-east-1:123456789012:key/terminal-key",
  "OutgoingKeyIdentifier": "arn:aws:payment-cryptography:us-east-1:123456789012:key/network-zpk",
  "IncomingTranslationAttributes": {
    "DukptIso2004": {
      "KeySerialNumber": "FFFF9876543210E00001",
      "DukptKeyDerivationType": "TDES_3KEY",
      "DukptKeyVariant": "PIN"
    }
  },
  "OutgoingTranslationAttributes": {
    "IsoPin0": { "PrimaryAccountNumber": "4111111111111111" }
  }
}
```

### PIN Block Formats

| Format | Standard | Characteristics |
|--------|----------|----------------|
| ISO-0 (Format 0) | Visa PVV, most networks | PAN-dependent, XOR with PAN |
| ISO-1 (Format 1) | PAN-independent | Random padding, no PAN dependency |
| ISO-3 (Format 3) | Mastercard preferred | PAN-dependent with random fill |
| ISO-4 (Format 4) | AES-based | AES encryption, 16-byte block |

### Translation Scenarios

**DUKPT-to-ZPK (Terminal → Network):**
```
POI Terminal (DUKPT-encrypted PIN)
  → Acquirer Host (TranslatePinData API)
    → Network ZPK-encrypted PIN Block → Card Network / Issuer
```

**ZPK-to-ZPK (Acquirer → Network):**
Used when multiple ZPK zones exist in routing architecture; common in multi-network configurations.

### Key Types for PIN Translation

| Key Usage | TR-31 Header | Purpose |
|-----------|-------------|---------|
| ZPK (Zone PIN Key) | `P0` | PIN encryption between zones |
| BDK (Base Derivation Key) | `B0` | DUKPT base key for terminal derivation |
| PEK (PIN Encryption Key) | `P0` | Generic PIN encryption |

### PCI PIN Compliance

- PIN blocks must never be decrypted outside a Secure Cryptographic Device (SCD)
- AWS Payment Cryptography translate operation keeps PIN in encrypted state
- Audit logs (CloudTrail) demonstrate key-to-key translation without exposure
- Supports PCI PIN Security Requirements v3.1 controls

---

## MAC Generation & Verification

### Overview

Message Authentication Codes (MACs) ensure integrity and authenticity of transaction messages between acquirer host systems and card networks.

### GenerateMac / VerifyMac APIs

```json
{
  "KeyIdentifier": "arn:aws:payment-cryptography:us-east-1:123456789012:key/mac-key",
  "MessageData": "0200B238...",
  "GenerationAttributes": {
    "Algorithm": "ISO9797_ALGORITHM3",
    "MacLength": 8
  }
}
```

### Supported MAC Algorithms

| Algorithm | Standard | Key Type | Use Case |
|-----------|----------|----------|----------|
| HMAC-SHA256 | FIPS 198-1 | HMAC key | Modern API-based messaging |
| Retail MAC (ISO 9797-1 Alg 3) | ISO 9797-1 | TDES key | ISO 8583 financial messages |
| CMAC (AES) | NIST SP 800-38B | AES key | AES-based network protocols |
| ISO 9797-1 Algorithm 1 | ISO 9797-1 | TDES key | Legacy network interfaces |

### DUKPT-Derived MAC Keys

```json
{
  "KeyIdentifier": "arn:aws:payment-cryptography:us-east-1:123456789012:key/bdk",
  "MessageData": "0200B238...",
  "GenerationAttributes": {
    "DukptIso9797Algorithm3": {
      "KeySerialNumber": "FFFF9876543210E00001",
      "DukptKeyDerivationType": "TDES_3KEY",
      "DukptKeyVariant": "BIDIRECTIONAL"
    }
  }
}
```

### Transaction Message Integrity Use Cases

1. **ISO 8583 Message MAC** — MAC on authorization request/response (DE-64/DE-128)
2. **Batch Settlement MAC** — Integrity of settlement file transmissions
3. **Administrative Messages** — Key change notifications, network management
4. **Terminal-to-Host** — MAC verification on messages from POI terminals

---

## Terminal Key Management

### Overview

Acquirers must manage cryptographic keys for thousands of POI terminals. AWS Payment Cryptography provides APIs for key export, supporting Remote Key Injection (RKI) and initial key provisioning.

### Remote Key Loading (RKI)

```
1. Terminal generates RSA key pair
2. Terminal sends public key (with certificate) to acquirer host
3. Acquirer validates certificate chain
4. Acquirer exports IPEK encrypted under terminal public key (ExportKey API)
5. Terminal decrypts and stores IPEK in secure memory
```

### ExportKey API for IPEK Distribution

```json
{
  "ExportKeyIdentifier": "arn:aws:payment-cryptography:us-east-1:123456789012:key/bdk",
  "KeyMaterial": {
    "Tr31KeyBlock": {
      "WrappingKeyIdentifier": "arn:aws:payment-cryptography:us-east-1:123456789012:key/kek"
    }
  },
  "ExportAttributes": {
    "ExportDukptInitialKey": { "KeySerialNumber": "FFFF9876543210E00001" }
  }
}
```

### Key Lifecycle & Best Practices

- Use unique BDKs per terminal group/merchant to limit blast radius
- Monitor KSN counters to detect exhaustion (2^21 for TDES DUKPT)
- Rotate BDKs on a 2–3 year lifecycle
- Maintain key inventory mapping (BDK → terminal serial → merchant ID)

---

## Related Resources

- [AWS Payment Cryptography Developer Guide](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/)
- [PCI P2PE Standard](https://www.pcisecuritystandards.org/document_library/)
- [ANSI X9.24-3 (AES DUKPT)](https://webstore.ansi.org/)
- [ISO 9564 (PIN Security)](https://www.iso.org/standard/68014.html)
