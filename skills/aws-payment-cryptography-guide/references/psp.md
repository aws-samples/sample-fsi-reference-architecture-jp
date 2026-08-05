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
| `AcquirerLink` | `ACQ-VISA-JP` | Acquirer association |
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

2. **Tokenize-with-APC-keys**: Tokenization service uses APC-managed keys for internal FPE operations, ensuring HSM-grade key protection without dedicated hardware.

### Format-Preserving Encryption Considerations

- APC supports AES-based operations suitable for FPE wrapper implementations
- Use `TR31_D0_SYMMETRIC_DATA_ENCRYPTION_KEY` for FPE working keys
- Ensure implementation meets NIST SP 800-38G (FF1/FF3-1) requirements
- Balance format preservation needs against cryptographic strength

---

## 3-D Secure

### APC's Role in 3DS Cryptographic Operations

3-D Secure 2.x requires cryptographic operations for:

- **ACS**: Authentication value (CAVV/AAV) generation
- **DS**: Message signing and encryption between participants
- **3DS Server**: Request/response signing for DS communication

```
Cardholder → Merchant → 3DS Server → Directory Server → ACS
                            │                              │
                            ▼                              ▼
                     ┌────────────┐                ┌────────────┐
                     │    APC     │                │    APC     │
                     │(Signing Key)│               │(CAVV Key)  │
                     └────────────┘                └────────────┘
```

### 3DS Server Integration Points

| Operation | APC Key Usage | Key Type |
|-----------|---------------|----------|
| AReq signing | Message authentication | `TR31_M3_ISO_9797_3_MAC_KEY` |
| CAVV generation | Cryptogram computation | `TR31_E0_EMV_MKEY_APP_CRYPTOGRAMS` |
| DS communication | Encryption/decryption | `TR31_D0_SYMMETRIC_DATA_ENCRYPTION_KEY` |
| Certificate key storage | Key pair management | RSA/ECC keys |

---

## Multiple Acquirer Connectivity

### Managing Key Pairs per Acquirer/Network

Each acquirer connection requires its own cryptographic key set:

```
PSP Platform
├── Acquirer A (Visa Direct)
│   ├── ZPK-A (Zone PIN Key)
│   ├── ZMK-A (Zone Master Key)
│   └── MAC-A (Message Auth Key)
├── Acquirer B (Mastercard Network)
│   ├── ZPK-B, ZMK-B, MAC-B
└── Acquirer C (Domestic - JCB)
    ├── ZPK-C, ZMK-C, MAC-C
```

### PIN Translation Across Acquirer Boundaries

```python
# Decrypt PIN block under inbound key, re-encrypt under outbound acquirer key
response = client.translate_pin_data(
    IncomingKeyIdentifier="alias/psp/merchant-142/pek-inbound",
    OutgoingKeyIdentifier="alias/psp/acquirer-visa/zpk-outbound",
    IncomingTranslationAttributes={
        "IsoFormat0": {"PrimaryAccountNumber": pan_12_digits}
    },
    OutgoingTranslationAttributes={
        "IsoFormat4": {"PrimaryAccountNumber": pan_12_digits}
    },
    EncryptedPinBlock=incoming_pin_block
)
```

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
| Caching (non-sensitive) | Cache key metadata/aliases | Reduce API calls |

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

**Cross-region considerations**: Key synchronization via TR-31 key blocks, data residency compliance, active-passive/active-active failover, sub-100ms latency routing.

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
