# Issuer Reference Guide — AWS Payment Cryptography

## Overview

This guide is intended for **card-issuing banks and financial institutions** that leverage AWS Payment Cryptography (APC) for PIN management, card verification, EMV transaction authentication, and integration with external partners such as card personalization bureaus.

APC provides a cloud-native, PCI PTS HSM-certified environment that eliminates on-premises HSM management while maintaining full compliance with payment network standards.

---

## PIN Generation & Verification

### Overview

PIN operations are core to issuer processing. APC supports both random PIN generation and PIN verification through industry-standard methods.

### GeneratePinData API

The `GeneratePinData` API generates a PIN and its associated verification data (PVV or offset) in a single atomic operation.

**Key Parameters:**
- `GenerationKeyIdentifier` — ARN or alias of the PIN generation key (PGK)
- `GenerationAttributes` — specifies the method (PVV or IBM 3624)
- `PinBlockFormat` — ISO format (e.g., ISO_FORMAT_0, ISO_FORMAT_3, ISO_FORMAT_4)
- `PrimaryAccountNumber` — the cardholder's PAN
- `EncryptionKeyIdentifier` — key used to encrypt the returned PIN block

**Example:**
```json
{
  "GenerationKeyIdentifier": "arn:aws:payment-cryptography:us-east-1:123456789012:key/abc123",
  "GenerationAttributes": {
    "VisaPinVerificationValue": {
      "EncryptedPinBlock": "...",
      "PinVerificationKeyIndex": 1
    }
  },
  "PinBlockFormat": "ISO_FORMAT_0",
  "PrimaryAccountNumber": "171234567890123",
  "EncryptionKeyIdentifier": "arn:aws:payment-cryptography:us-east-1:123456789012:key/def456"
}
```

### VerifyPinData API

The `VerifyPinData` API validates a PIN block against stored verification data without exposing the clear-text PIN.

**Key Parameters:**
- `VerificationKeyIdentifier` — ARN of the PIN verification key (PVK)
- `VerificationAttributes` — method-specific parameters
- `EncryptedPinBlock` — the encrypted PIN block from the transaction
- `PinBlockFormat` — must match the format used during generation
- `PrimaryAccountNumber` — cardholder's PAN

### PVV (PIN Verification Value) Method

The Visa PVV method derives a 4-digit verification value from:
1. The PIN Verification Key (PVK) — a double-length DES or AES key
2. The PAN (rightmost 12 digits excluding check digit)
3. The PIN Verification Key Index (PVKI) — a single digit (1–6)
4. The leftmost digits of the PIN

**Advantages:**
- Compact storage (4-digit value on card database)
- No PIN offset stored — reduces exposure risk
- Widely supported by Visa and most international networks

### IBM 3624 Offset Method

The IBM 3624 method generates a "natural PIN" from the PAN using a decimalization table and PIN validation key. The offset is the difference between the customer-selected PIN and the natural PIN.

**Characteristics:**
- Offset stored on issuer database or card magnetic stripe
- Decimalization table must be consistent across all verification points
- Legacy method still prevalent in ATM networks and domestic debit schemes

**Security Note:** Ensure the decimalization table and PIN validation key are protected with the same rigor as the PIN itself. APC stores these securely within its HSM boundary.

---

## Select PIN (ECDH)

### Overview

Modern issuers support cardholder-selected PINs via mobile apps. APC provides an ECDH (Elliptic Curve Diffie-Hellman) key agreement mechanism enabling secure PIN transport from mobile device to HSM without clear-text exposure at any intermediate point.

### Architecture Components

1. **Mobile Application** — cardholder-facing app that captures the selected PIN
2. **AWS Private CA** — issues short-lived certificates for ephemeral ECDH key pairs
3. **APC ECDH Key Derivation** — derives a shared symmetric key for PIN block encryption

### Flow Diagram

```
┌──────────┐       ┌─────────────┐       ┌─────────────┐
│  Mobile  │       │  Issuer     │       │    APC      │
│   App    │◄─────►│  Backend    │◄─────►│   (HSM)     │
└──────────┘       └─────────────┘       └─────────────┘
     │                    │                      │
     │ 1. Request PIN change                     │
     │────────────────────►│                      │
     │                    │ 2. Get ECDH pubkey   │
     │                    │─────────────────────►│
     │                    │◄─────────────────────│
     │ 3. Server pubkey   │                      │
     │◄────────────────────│                      │
     │ 4. Encrypt PIN with shared key            │
     │────────────────────►│                      │
     │                    │ 5. Forward PIN block │
     │                    │─────────────────────►│
     │                    │ 6. Translate to PEK  │
     │                    │◄─────────────────────│
     │ 7. Confirmation    │                      │
     │◄────────────────────│                      │
```

### Keys Used

- **ECDH key agreement key** — `TR31_K3_ASYMMETRIC_KEY_FOR_KEY_AGREEMENT` (ECC key pair, `DeriveKey` mode). Its public certificate is obtained with `GetPublicKeyCertificate` and provided to the device
- **Device CA public key** — imported as `TR31_S0_ASYMMETRIC_KEY_FOR_DIGITAL_SIGNATURE` so that AWS Payment Cryptography can verify the device certificate
- **PIN Encryption Key (PEK)** — `TR31_P0_PIN_ENCRYPTION_KEY`. `TranslatePinData` translates the ECDH-protected ISO format 4 PIN block onto the PEK (or the reverse for Reveal PIN), with the ECDH parameters passed in `IncomingWrappedKey`/`OutgoingWrappedKey` (`DiffieHellmanSymmetricKey`)
- **PIN verification key** — `TR31_V2_VISA_PIN_VERIFICATION_KEY` for PVV generation with `GeneratePinData`

### Sub-Flows

#### Reset PIN
Cardholder forgot PIN → step-up authentication (OTP, biometric) → new PIN selection via mobile app.

#### Set PIN
Initial PIN selection during card activation. Mobile app captures PIN, encrypts with ECDH-derived key, sends to APC.

#### Reveal PIN
Cardholder views current PIN (e.g., before travel). PIN encrypted under ECDH-derived key, decrypted only in mobile device secure enclave.

### Certificate Management

- **Short-lived certificates** (minutes to hours) minimize compromise window
- **AWS Private CA** handles issuance and revocation
- **Certificate pinning** in mobile app prevents MITM attacks

### Reference Implementation

[AWS Samples — ECDH Flows for Payment Cryptography](https://github.com/aws-samples/samples-for-payment-cryptography-service/blob/main/python_sdk_example/ecdh_flows/README.md)

---

## CVV / iCVV / dCVV

### CVV/CVV2

Static verification value on magnetic stripe (CVV1) or printed on card (CVV2).

- **GenerateCardValidationData** — generates CVV using Card Verification Key (CVK), PAN, expiration, service code
- **VerifyCardValidationData** — validates CVV, returns pass/fail without exposing expected value

### iCVV (Integrated Circuit Card Verification Value)

Used in chip-to-magnetic-stripe fallback scenarios. Differs from stripe CVV to detect cloning.

- Service code `999` used in iCVV calculation (vs. actual service code for CVV1)
- If iCVV appears in a magnetic stripe transaction, indicates possible chip card cloning

### dCVV (Dynamic CVV)

Changes periodically (e.g., every 20 minutes) for enhanced e-commerce security.

**Issuer Considerations:**
- Time-synchronized algorithm required between card and issuer
- Configure appropriate clock drift tolerance
- Higher verification call volumes due to time-sensitivity
- APC supports the underlying cryptographic operations

---

## ARQC Verification

### EMV Online Authentication

When a chip card initiates an online transaction, it generates an ARQC using session keys derived from the card's master key.

### VerifyAuthRequestCryptogram API

```json
{
  "KeyIdentifier": "arn:aws:payment-cryptography:...:key/issuer-mk",
  "TransactionData": "<hex-encoded transaction data>",
  "AuthRequestCryptogram": "<8-byte ARQC>",
  "MajorKeyDerivationMode": "EMV_OPTION_A",
  "SessionKeyDerivationAttributes": {
    "Mastercard": {
      "ApplicationTransactionCounter": "001C",
      "PanSequenceNumber": "00",
      "PrimaryAccountNumber": "171234567890123",
      "UnpredictableNumber": "00000001"
    }
  }
}
```

### Session Key Derivation Methods

#### Mastercard (CVN12/CVN13, `Mastercard` attributes)
1. Derive ICC Master Key from Issuer Master Key using PAN + PAN Sequence Number
2. Derive Session Key using ATC (Application Transaction Counter) and the Unpredictable Number
3. Calculate MAC over transaction data
4. Compare with ARQC from the card

Mastercard CVN14/CVN15 use the EMV Common Session Key (CSK) method instead (`EmvCommon` attributes).

#### Visa (EMV Option A)
1. Similar derivation with different diversification data
2. Visa-specific padding and key derivation constants
3. CVN (Cryptogram Version Number) determines exact algorithm variant

### ARPC Generation

After ARQC verification, generate ARPC to authenticate issuer back to the card:
- **Method 1:** ARPC = DES(SK)[ARQC ⊕ ARC]
- **Method 2:** Uses 4-byte proprietary data field for richer response

APC's `GenerateAuthResponseCryptogram` handles both methods.

### Best Practices

- Store IMK as `TR31_E0_EMV_MKEY_APP_CRYPTOGRAMS` key type
- Use separate IMKs for MAC, encryption, and data authentication
- Monitor ARQC failure rates — sudden spikes may indicate compromise
- Implement velocity checks alongside cryptographic verification

---

## External Partner Integration Challenges

### The Problem

Card personalization bureaus and print vendors require cryptographic keys for stripe encoding, chip personalization, and PIN generation. Many operate legacy HSMs that do **not** support TR-31 or TR-34 — APC's native key exchange methods.

### Workaround Options

#### (a) Bridge HSM

Intermediary HSM supporting both APC formats and partner legacy format.

**Option 1 — AWS CloudHSM:**
```
APC ──(TR-31)──► CloudHSM ──(legacy format)──► Partner
```

**Option 2 — Existing On-Premises HSM:**
```
APC ──(TR-34)──► On-Prem HSM ──(partner protocol)──► Partner
```

#### (b) Request Partner to Adopt Standards

- Provide timeline (12–18 months) for mandatory TR-31 support
- Reference PCI PIN Security Requirements v3.1 (key blocks mandatory by 2025)
- Offer testing assistance with APC's TR-31 export capabilities
- Escalate through Visa/Mastercard compliance programs

#### (c) Clear-Text Key Components

Last resort — keys exchanged as clear-text components under strict controls.

**PCI Requirements:**
- Minimum 2 components (3 recommended), each held by separate custodian
- Dual control during loading — no single person sees full key
- Components via separate secure channels; tamper-evident packaging

**Risks:** Higher PCI audit burden, operational risk, human error potential. Not recommended long-term.

### Migration Strategy

```
Phase 1 : Clear-text components (strict dual control)
Phase 2 : Bridge HSM established
Phase 3 : Partner adopts TR-31/TR-34
Phase 4 : Direct APC-to-partner key exchange
```

---

## Summary

| Capability | APC API | Key Type |
|-----------|---------|----------|
| PIN Generation | `GeneratePinData` | TR31_V2_VISA_PIN_VERIFICATION_KEY |
| PIN Verification | `VerifyPinData` | TR31_V2_VISA_PIN_VERIFICATION_KEY |
| CVV Generation | `GenerateCardValidationData` | TR31_C0_CARD_VERIFICATION_KEY |
| CVV Verification | `VerifyCardValidationData` | TR31_C0_CARD_VERIFICATION_KEY |
| ARQC Verification | `VerifyAuthRequestCryptogram` | TR31_E0_EMV_MKEY_APP_CRYPTOGRAMS |
| ARPC Generation | `GenerateAuthResponseCryptogram` | TR31_E0_EMV_MKEY_APP_CRYPTOGRAMS |
| PIN Translation | `TranslatePinData` | TR31_P0_PIN_ENCRYPTION_KEY |
| ECDH Key Agreement | `CreateKey` / `GetPublicKeyCertificate` (key setup), `TranslatePinData` (PIN block translation) | TR31_K3_ASYMMETRIC_KEY_FOR_KEY_AGREEMENT |

---
