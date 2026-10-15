# PSP (Payment Service Providers / Payment Gateways / Payment Facilitators)

## Overview

Payment Service Providers (PSPs), payment gateways, and payment facilitators operate as intermediaries between merchants and the broader payment ecosystem. These organizations process transactions on behalf of multiple merchants, requiring robust multi-tenant architectures that ensure cryptographic isolation while maintaining operational efficiency at scale.

AWS Payment Cryptography (APC) provides PSPs with a cloud-native HSM-backed platform that eliminates the operational burden of managing physical HSM fleets while supporting the complex key management hierarchies required for multi-merchant, multi-acquirer environments.

---

## Multi-Tenant Key Management

### Key Isolation Per Merchant

PSPs must ensure strict cryptographic isolation between merchants. APC supports this through IAM policies, key aliases, and tag-based access control.

#### IAM Policy-Based Isolation

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "payment-cryptography:Encrypt*",
        "payment-cryptography:Decrypt*"
      ],
      "Resource": "arn:aws:payment-cryptography:*:*:key/*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/MerchantId": "${aws:PrincipalTag/MerchantId}"
        }
      }
    }
  ]
}
```

#### Key Alias Strategy

```
alias/psp/merchant-{merchant_id}/zone-{zone_key_type}
alias/psp/merchant-{merchant_id}/bdk-{terminal_group}
alias/psp/merchant-{merchant_id}/pin-{acquirer_id}
```

#### Tag-Based Access Control

| Tag Key | Example Value | Purpose |
|---------|---------------|---------|
| `MerchantId` | `MERCH-00142` | Tenant isolation |
| `Environment` | `production` | Env separation |
| `KeyPurpose` | `pin-encryption` | Functional classification |
| `AcquirerLink` | `ACQ-A-JP` | Acquirer association |
| `ComplianceScope` | `pci-dss-4.0` | Audit classification |

### Organizational Key Hierarchy Design

```
Platform Master KEK (APC-managed)
├── Merchant-A KEK
│   ├── Working Key: PEK (PIN Encryption)
│   ├── Working Key: MAC Key (Transaction Auth)
│   └── Working Key: DEK (Data Encryption)
├── Merchant-B KEK
│   ├── Working Key: PEK
│   ├── Working Key: MAC Key
│   └── Working Key: DEK
└── Shared Services KEK
    ├── Tokenization Master Key
    └── 3DS Crypto Key
```

**Key rotation strategy**: Rotate working keys per-merchant (typically 24-hour or transaction-count-based) while KEKs rotate quarterly.

---

## Tokenization Integration

### PAN Encryption/Decryption Flows

```
┌─────────┐    PAN     ┌──────────┐   Encrypt   ┌─────┐
│ Merchant│───────────▶│  PSP GW  │────────────▶│ APC │
└─────────┘            └──────────┘              └─────┘
                             │                       │
                             │ Token                  │ Ciphertext
                             ▼                       ▼
                       ┌──────────┐           ┌──────────┐
                       │Token Vault│◀──────────│Key Store │
                       └──────────┘           └──────────┘
```

### Integration Patterns

1. **Encrypt-then-tokenize**: PAN encrypted via APC before token generation. Token vault stores encrypted PAN; detokenization requires APC decryption.

2. **Tokenize-with-APC-keys**: The tokenization service keeps the data encryption keys that protect PANs in its vault in APC (`TR31_D0_SYMMETRIC_DATA_ENCRYPTION_KEY`) and calls `EncryptData`/`DecryptData`, ensuring HSM-grade key protection without dedicated hardware. Token generation itself is implemented in the tokenization service; APC does not generate tokens.

### Format-Preserving Encryption Considerations

- **APC does not provide format-preserving encryption (FPE).** `EncryptData`/`DecryptData` support TDES/AES block cipher modes (such as CBC and ECB), RSA, DUKPT, and EMV schemes, but not NIST SP 800-38G modes such as FF1. The output is not format-preserving.
- If FPE is required, implement it outside APC (for example, in the tokenization service using a library or HSM that supports FF1), and design the protection of the FPE key separately. APC keys cannot be used for FPE computation inside APC.
- Ensure the implementation meets NIST SP 800-38G (FF1) requirements, and confirm the current status of FF3-1 in the latest revision of NIST SP 800-38G
- Balance format preservation needs against cryptographic strength

---

## 3-D Secure

### APC's Role in 3DS Cryptographic Operations

3-D Secure 2.x requires cryptographic operations for:

- **ACS**: Authentication value (Visa CAVV / Mastercard AAV) generation — supported by APC
- **DS / 3DS Server / 3DS SDK**: Message-level signing and encryption between participants (JWS/JWE as defined in the EMVCo 3DS specification) — not provided by APC; implement these in the 3DS component (for example, using AWS KMS or AWS CloudHSM)

APC can manage the keys used to generate and verify authentication values in the ACS:

```
Cardholder → Merchant → 3DS Server → Directory Server → ACS
                                                          │
                                                          ▼
                                                   ┌────────────┐
                                                   │    APC     │
                                                   │(CAVV/AAV   │
                                                   │   Key)     │
                                                   └────────────┘
```

### 3DS Integration Points (ACS)

| Operation | APC API | Key Type |
|-----------|---------|----------|
| Visa CAVV V7 generation/verification | `GenerateCardValidationData` / `VerifyCardValidationData` (`CardVerificationValue1` with repurposed inputs) | `TR31_C0_CARD_VERIFICATION_KEY` |
| Mastercard SPA2 AAV (IAV component) generation/verification | `GenerateMac` / `VerifyMac` (`Algorithm`: `HMAC`) | `TR31_M7_HMAC_KEY` |

> Consult the card network specifications for how to build the input data. APC does not provide 3DS message signing/encryption (JWS/JWE) or 3DS certificate management.

---

## Multiple Acquirer Connectivity

### Managing Key Pairs per Acquirer/Network

Each acquirer connection requires its own cryptographic key set:

```
PSP Platform
├── Acquirer A
│   ├── ZPK-A (Zone PIN Key)
│   ├── ZMK-A (Zone Master Key)
│   └── MAC-A (Message Auth Key)
├── Acquirer B
│   ├── ZPK-B, ZMK-B, MAC-B
└── Acquirer C (Domestic)
    ├── ZPK-C, ZMK-C, MAC-C
```

### PIN Translation Across Acquirer Boundaries

```python
# Decrypt PIN block under inbound key, re-encrypt under outbound acquirer key
response = client.translate_pin_data(
    IncomingKeyIdentifier="alias/psp/merchant-142/pek-inbound",
    OutgoingKeyIdentifier="alias/psp/acquirer-a/zpk-outbound",
    IncomingTranslationAttributes={
        "IsoFormat0": {"PrimaryAccountNumber": pan}  # full PAN (12-19 digits)
    },
    OutgoingTranslationAttributes={
        "IsoFormat4": {"PrimaryAccountNumber": pan}
    },
    EncryptedPinBlock=incoming_pin_block
)
```

> **Note**: For ISO format 4, APC builds the PIN block using the legacy PAN length (the rightmost 12 digits excluding the check digit). Confirm that the counterparty uses the same convention.

### Routing-Based Key Selection

| Routing Factor | Key Selection Logic |
|----------------|-------------------|
| Card BIN range | Select acquirer key by BIN-to-acquirer mapping |
| Transaction currency | Route to regional acquirer with matching settlement |
| Merchant preference | Honor merchant-specific routing rules |
| Failover | Automatic key switch on connectivity failure |
| Cost optimization | Route to lowest-cost acquirer, select corresponding keys |

---

## P2PE as a Service

### Offering P2PE to Merchants Using APC

```
┌────────────┐        ┌───────────────┐        ┌─────────────┐
│  Merchant  │  P2PE  │     PSP       │  APC   │   AWS APC   │
│  Terminal  │───────▶│  Decryption   │───────▶│   (HSM)     │
│  (POI)     │ cipher │  Environment  │  API   │             │
└────────────┘        └───────────────┘        └─────────────┘
```

#### Key Management for P2PE Service

- **Base Derivation Keys (BDK)**: Stored in APC, never exposed in clear
- **IPEK derivation**: Performed within APC for terminal injection
- **Decryption**: All transaction decryption via APC API calls
- **Key injection**: Terminal injection process references APC-managed BDKs

### Component Listing Considerations

1. **Decryption environment**: APC operates within AWS's PCI-validated infrastructure
2. **Key management documentation**: Document APC key lifecycle in P2PE component listing
3. **Shared responsibility**: Delineate AWS vs. PSP responsibilities in the P2PE Implementation Manual (PIM)
4. **Terminal management**: Ensure POI device management aligns with P2PE requirements

---

## Scaling Considerations

### High-TPS Design for Gateway Workloads

| Pattern | Description | Benefit |
|---------|-------------|---------|
| Connection pooling | Persistent HTTPS connections to APC | Reduce TLS overhead |
| Request batching | Group related operations | Reduce per-call overhead |
| Async processing | Non-blocking API calls | Improve throughput |
| Regional routing | Route to nearest APC endpoint | Minimize latency |
| Caching (non-sensitive) | Cache key metadata/aliases (never key material) | Reduce API calls |

### Service Quota Management

- **Default TPS limits**: Request increases ahead of traffic growth
- **CloudWatch monitoring**: Alarms at 70% quota utilization
- **Burst handling**: Quota-aware backoff during traffic spikes
- **Per-key limits**: Distribute load across multiple key aliases

### Multi-Region Deployment

```
┌─────────────────────────────────────────────────┐
│              Global PSP Platform                  │
├──────────────┬──────────────┬───────────────────┤
│  US Region   │  EU Region   │  APAC Region      │
│  us-east-1   │  eu-west-1   │  ap-northeast-1   │
│  ┌────────┐  │  ┌────────┐  │  ┌────────┐      │
│  │  APC   │  │  │  APC   │  │  │  APC   │      │
│  └────────┘  │  └────────┘  │  └────────┘      │
└──────────────┴──────────────┴───────────────────┘
```

**Cross-region considerations**: Key synchronization via Multi-Region key replication (`AddKeyReplicationRegions`, same account and partition; keys must be exportable, and replica keys are read-only) or TR-31 export/import, data residency compliance, active-passive/active-active failover, sub-100ms latency routing.

---

## Japan-Specific Considerations

### PCI DSS Outsourcing Scope Definition

| Component | Scope Owner | Justification |
|-----------|------------|---------------|
| APC HSM infrastructure | AWS (out of scope) | AWS PCI DSS AOC covers |
| Key management procedures | PSP (in scope) | PSP defines key lifecycle |
| API calls to APC | PSP (in scope) | Application responsibility |
| Network connectivity | PSP (in scope) | VPC and network design |
| Physical HSM security | AWS (out of scope) | AWS facility controls |

---

## Summary

PSPs leveraging AWS Payment Cryptography benefit from:

1. **Reduced operational burden**: No physical HSM fleet management
2. **Elastic scalability**: Scale crypto operations with transaction volume
3. **Multi-tenant isolation**: IAM and tag-based controls for merchant separation
4. **Global reach**: Multi-region deployment for international operations
5. **Compliance alignment**: PCI DSS, FISC, and Payment Services Act support
6. **Cost efficiency**: Pay-per-use model vs. fixed HSM infrastructure costs

---
