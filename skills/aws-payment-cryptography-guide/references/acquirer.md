# Acquirer Reference Guide — AWS Payment Cryptography

> For merchant acquiring banks, payment processors on the acquiring side, and terminal management providers.

---

## Table of Contents

1. [P2PE Decryption](#p2pe-decryption)
2. [PIN Translation](#pin-translation)
3. [MAC Generation and Verification](#mac-generation-and-verification)
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
| BDK | Master key, never leaves HSM | AWS Payment Cryptography (`TR31_B0_BASE_DERIVATION_KEY`) |
| IPEK | Injected into terminal at provisioning | Terminal secure memory |
| Transaction Key | Derived from IPEK + KSN | Ephemeral, per-transaction |

### DecryptData API with DUKPT

```json
{
  "KeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/abc123",
  "CipherText": "A1B2C3D4E5F6...",
  "DecryptionAttributes": {
    "Dukpt": {
      "KeySerialNumber": "FFFF9876543210E00001",
      "DukptKeyDerivationType": "TDES_2KEY",
      "DukptKeyVariant": "BIDIRECTIONAL",
      "Mode": "CBC"
    }
  }
}
```

### Supported DUKPT Derivation Types

| Derivation Type | Key Length | Use Case |
|----------------|-----------|----------|
| `TDES_2KEY` | 128-bit (112 effective) | TDES DUKPT (ANSI X9.24-1), widely deployed terminals |
| `AES_128` | 128-bit | AES DUKPT (ANSI X9.24-3) terminals |
| `AES_192` | 192-bit | AES DUKPT (ANSI X9.24-3) |
| `AES_256` | 256-bit | AES DUKPT (ANSI X9.24-3), high-security environments |

> The derivation type must be less than or equal to the strength of the BDK. For DUKPT encryption and decryption, a BDK (`TR31_B0_BASE_DERIVATION_KEY`) can be `TDES_2KEY`, `AES_128`, `AES_192`, or `AES_256`.

### Supported Encryption Modes

For DUKPT, the `Mode` parameter accepts `CBC` (default) or `ECB`.

- **CBC** (Cipher Block Chaining) — default and most common for P2PE payloads
- **ECB** (Electronic Codebook) — avoid unless the terminal specification requires it (for example, single-block data). ECB encrypts identical plaintext blocks to identical ciphertext blocks, so it leaks patterns in multi-block data. Prefer CBC.

> Additional modes such as CFB and OFB are available only for non-DUKPT symmetric keys (`Symmetric` attributes), not for DUKPT.

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
  "EncryptedPinBlock": "AC17DC148BDA645E",
  "IncomingKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/terminal-bdk",
  "IncomingDukptAttributes": {
    "KeySerialNumber": "FFFF9876543210E00001",
    "DukptKeyDerivationType": "TDES_2KEY"
  },
  "IncomingTranslationAttributes": {
    "IsoFormat0": { "PrimaryAccountNumber": "4111111111111111" }
  },
  "OutgoingKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/network-zpk",
  "OutgoingTranslationAttributes": {
    "IsoFormat0": { "PrimaryAccountNumber": "4111111111111111" }
  }
}
```

`IncomingKeyIdentifier` is the BDK for DUKPT-encrypted PIN blocks (with `IncomingDukptAttributes`) or a PEK/ZPK otherwise. `PrimaryAccountNumber` takes the full PAN (12–19 digits).

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

## MAC Generation and Verification

### Overview

Message Authentication Codes (MACs) ensure integrity and authenticity of transaction messages between acquirer host systems and card networks.

### GenerateMac / VerifyMac APIs

```json
{
  "KeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/mac-key",
  "MessageData": "0200B238...",
  "GenerationAttributes": {
    "Algorithm": "ISO9797_ALGORITHM3"
  },
  "MacLength": 8
}
```

### Supported MAC Algorithms

| Algorithm | Standard | Key Type (KeyUsage) | Use Case |
|-----------|----------|----------|----------|
| HMAC-SHA256 | FIPS 198-1 | HMAC key (`TR31_M7_HMAC_KEY`) | Modern API-based messaging |
| Retail MAC (ISO 9797-1 Alg 3) | ISO 9797-1 | TDES key (`TR31_M3_ISO_9797_3_MAC_KEY`) | ISO 8583 financial messages |
| CMAC (AES) | NIST SP 800-38B | AES key (`TR31_M6_ISO_9797_5_CMAC_KEY`) | AES-based network protocols |
| ISO 9797-1 Algorithm 1 | ISO 9797-1 | TDES key (`TR31_M1_ISO_9797_1_MAC_KEY`) | Legacy network interfaces |

### DUKPT-Derived MAC Keys

```json
{
  "KeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/bdk",
  "MessageData": "0200B238...",
  "GenerationAttributes": {
    "DukptIso9797Algorithm3": {
      "KeySerialNumber": "FFFF9876543210E00001",
      "DukptDerivationType": "TDES_2KEY",
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

Acquirers must manage cryptographic keys for thousands of POI terminals. AWS Payment Cryptography does not connect to terminals directly. Instead, the `ExportKey` API derives a terminal-specific IPEK from the BDK and the terminal's KSN (`ExportAttributes.ExportDukptInitialKey`) and returns it wrapped in a TR-34 or TR-31 key block. Your key loading system then delivers the key block to the terminal. The generated IPEK is not persisted in AWS Payment Cryptography and is re-generated on each export.

### Remote Key Loading (RKL)

This guide uses the term Remote Key Loading (RKL), also known as Remote Key Injection (RKI). `ExportKey` supports two key block methods for IPEK export:

| Method | `KeyMaterial` | Wrapping key | Typical use |
|--------|---------------|--------------|-------------|
| TR-34 (asymmetric) | `Tr34KeyBlock` | The terminal's (KRD) public key certificate | Initial key load to a terminal that has no shared symmetric key yet |
| TR-31 (symmetric) | `Tr31KeyBlock` | A KEK (`TR31_K0_KEY_ENCRYPTION_KEY` or `TR31_K1_KEY_BLOCK_PROTECTION_KEY`) previously established with the terminal or key injection facility | Key loads after a KEK has been established |

#### TR-34 flow (key wrapped under the terminal's public key)

In TR-34 terminology, AWS Payment Cryptography is the Key Distribution Host (KDH) and the terminal is the Key Receiving Device (KRD).

```
1. Terminal (KRD) holds an RSA key pair and a wrapping certificate issued by the terminal CA
2. Acquirer imports the terminal CA certificate into AWS Payment Cryptography
   (ImportKey with RootCertificatePublicKey)
3. Acquirer obtains an export token and the KDH signing certificate chain
   (GetParametersForExport); the terminal must trust this certificate chain
4. Acquirer calls ExportKey with Tr34KeyBlock: AWS Payment Cryptography derives the IPEK,
   wraps it under the terminal's wrapping certificate, and signs the key block
5. Terminal verifies the KDH signature, unwraps the IPEK, and stores it in secure memory
```

```json
{
  "ExportKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/bdk",
  "KeyMaterial": {
    "Tr34KeyBlock": {
      "CertificateAuthorityPublicKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/terminal-ca",
      "WrappingKeyCertificate": "<Base64-encoded terminal (KRD) wrapping certificate>",
      "ExportToken": "export-token-abcdef1234567890",
      "KeyBlockFormat": "X9_TR34_2012"
    }
  },
  "ExportAttributes": {
    "ExportDukptInitialKey": { "KeySerialNumber": "FFFF9876543210E00001" }
  }
}
```

#### TR-31 flow (key wrapped under an established KEK)

When a KEK is already shared with the terminal or the key injection facility, export the IPEK as a TR-31 key block wrapped under that KEK.

```json
{
  "ExportKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/bdk",
  "KeyMaterial": {
    "Tr31KeyBlock": {
      "WrappingKeyIdentifier": "arn:aws:payment-cryptography:ap-northeast-1:123456789012:key/kek"
    }
  },
  "ExportAttributes": {
    "ExportDukptInitialKey": { "KeySerialNumber": "FFFF9876543210E00001" }
  }
}
```

### Key Loading into POI Terminals

RKL platforms and supported key block formats differ by terminal vendor and model. Confirm the following with each vendor before designing the key loading process.

| Item to confirm | Details |
|-----------------|---------|
| RKL protocol | Whether the vendor's RKL platform accepts TR-34 key blocks for initial load, or requires a KEK to be loaded by another method first |
| Key block format | Whether the terminal accepts TR-31 key blocks. If it accepts only a proprietary envelope, place a bridging HSM or the vendor's key loading service between AWS Payment Cryptography and the terminal |
| Trust setup | How CA certificates are exchanged between the terminal PKI and AWS Payment Cryptography (KDH) |

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
