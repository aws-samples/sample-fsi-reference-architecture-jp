# AWS Payment Cryptography — Frequently Asked Questions

## 1. Overview

### Q1: What is AWS Payment Cryptography (APC)?

AWS Payment Cryptography is a fully managed service that provides payment HSM (Hardware Security Module) functionality without the need to provision, manage, or maintain dedicated payment HSM hardware. It handles card issuing operations (PIN generation, CVV creation, ARQC verification), acquiring operations (PIN translation, MAC verification), and key management—all through API calls with the same cryptographic algorithms used by on-premises payment HSMs.

> 📖 [AWS Payment Cryptography Documentation](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/what-is.html)

---

### Q2: How does APC differ from AWS CloudHSM and AWS KMS?

| Aspect | APC | CloudHSM | KMS |
|--------|-----|----------|-----|
| **Purpose** | Payment-specific cryptographic operations (PIN, CVV, ARQC, MAC) | General-purpose HSM (PKCS#11, JCE, CNG) | General-purpose envelope encryption & key management |
| **Compliance** | PCI PIN, PCI P2PE, PCI DSS | FIPS 140-3 Level 3 (hsm2m.medium, FIPS mode clusters) | FIPS 140-3 Level 3 validated HSMs |
| **Key Types** | TDES, AES, RSA, ECC (payment-specific formats) | Broad algorithm support | Symmetric & asymmetric (AES, RSA, ECC) |
| **Management** | Fully managed (no hardware provisioning) | Customer-managed cluster | Fully managed |
| **Use Case** | Card payments, POS transactions | Custom crypto apps, TLS offload, PKI | Application-level encryption, S3/EBS/RDS |

APC is specifically designed for the payment industry and implements payment-standard operations (ISO 9564, ISO 16609, EMV) that KMS and CloudHSM do not natively support.

---

### Q3: What cryptographic algorithms and operations does APC support?

**Symmetric algorithms:**
- TDES (2-key and 3-key) — PIN blocks, MAC, legacy key exchange
- AES-128, AES-192, AES-256 — PIN blocks (ISO format 4), CMAC, key wrapping

**Asymmetric algorithms:**
- RSA 2048/3072/4096 — TR-34 key exchange, key wrapping
- ECC (NIST P-256, P-384, P-521) — ECDH key agreement for Select PIN flows

**Operations:**
- PIN generation, verification, translation (ISO formats 0–4)
- CVV/CVV2/iCVV generation and verification
- ARQC/ARPC (EMV) generation and verification
- MAC generation and verification (ISO 9797, CMAC)
- Card data verification (AMEX CSC, Discover CID)

---

## 2. Cost

### Q5: What is the pricing model for APC?

APC pricing has two components:

**1. API Call Charges (tiered):**
| Volume (monthly) | Price per 10,000 API calls |
|---|---|
| First 20 million calls [0 - 20,000,000] | $2.00 |
| Next 200 Million requests [20,000,001 - 220,000,000] | $0.75 |
| Next 300 Million requests [220,000,001 - 520,000,000] | $0.25 |
| Additional requests [520,000,001+] | $0.10 |

**2. Active Key Charges:**
- $1.00 per key per month (prorated daily)

| Key resources | Price per active key |
|---|---|
| First 500 keys [0-500] | $1.00 |
| Next 500 Keys [501-1000] | $0.10 |
| Next 50 Thousand Keys [1001-51,000] | $0.01 |
| Additional keys [51,001+] | $0.001 |


There are no upfront costs, no minimum commitments, and no hardware provisioning fees.

> 📖 [AWS Payment Cryptography Pricing](https://aws.amazon.com/payment-cryptography/pricing/)

---

## 3. Availability & Performance

### Q8: What is the SLA for AWS Payment Cryptography?

AWS Payment Cryptography offers a **99.99% availability SLA**. The service is deployed across multiple Availability Zones within each region, providing automatic failover. If the monthly uptime percentage falls below the SLA commitment, customers are eligible for service credits.

> 📖 [AWS Payment Cryptography SLA](https://aws.amazon.com/payment-cryptography/sla/)

---

### Q9: What are the default throughput limits (TPS)?

| Operation Type | Default TPS | Notes |
|---|---|---|
| Data plane operations with a symmetric key (PIN, CVV, MAC, ARQC) | 500 TPS | Per account per region, combined across all such operations |
| Data plane operations with an asymmetric key (RSA, ECDH) | 20 TPS | Per account per region, combined across all such operations |
| Control plane operations (CreateKey, ImportKey, etc.) | 5 TPS | Per account per region, combined across all control plane operations |

These are **default quotas**. Check the latest values in the [quotas page](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/quotas.html).

---

### Q10: Can I increase the TPS quotas?

Yes. All APC quotas are adjustable via AWS Service Quotas. To request an increase:

1. Navigate to **Service Quotas** → **AWS Payment Cryptography**
2. Select the relevant quota (e.g., "Combined rate of data plane requests (symmetric)")
3. Click "Request increase" and specify your desired limit

Processing time is typically 1–3 business days. For production workloads expecting high transaction volumes (e.g., holiday peaks), request increases proactively.

> 📖 [APC Service Quotas](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/quotas.html)

---

### Q11: Does APC support Multi-Region Keys?

Yes. APC provides native **Multi-Region key replication**. A key created in a
Primary Region (PRK) can be replicated to one or more Replica Regions (RRK)
within the same AWS partition and account. Replicated keys keep the **same key
ID** across Regions — only the Region portion of the ARN changes — and both the
PRK and RRK can perform cryptographic operations in their respective Regions.

Key points:
- Manage replication with `AddKeyReplicationRegions`, `RemoveKeyReplicationRegions`,
  `EnableDefaultKeyReplicationRegions`, and `GetDefaultKeyReplicationRegions`.
- The primary Region key (`MultiRegionKeyType: PRIMARY`) remains authoritative for
  key management; replicas are marked `MultiRegionKeyType: REPLICA`.
- Replication is asynchronous, and deletion cascades from the primary to replicas.

This enables low-latency multi-Region processing and disaster recovery without
manual key export/import. Manual TR-31/TR-34 exchange is still used for keys
shared with *external* systems outside your AWS account/partition.

> 📖 [Replicating AWS Payment Cryptography keys](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/keys-multi-region-replication.html)

---

## 4. Issuer Use Cases

### Q12: How does the Select PIN flow work with ECDH in APC?

The Select PIN flow allows cardholders to choose their own PIN during card activation (rather than receiving a mailer). APC implements this using **Elliptic Curve Diffie-Hellman (ECDH)** key agreement:

**Flow:**
1. **Certificate Setup** — Use AWS Private CA to issue short-lived ECC certificates (P-256/P-384) for both the mobile app and APC
2. **Key Agreement** — The mobile app and APC each generate an ephemeral ECC key pair. ECDH derives a shared secret without transmitting any secret material
3. **PIN Encryption** — The cardholder's selected PIN is encrypted under the ECDH-derived key on the mobile device
4. **PIN Block Processing** — APC receives the encrypted PIN block, unwraps it using the shared secret, re-encrypts it under the issuer's PIN Encryption Key (PEK), and generates the PIN verification value (PVV/PIN offset)

**Key benefits:**
- No pre-shared symmetric keys needed with the mobile device
- Short-lived certificates limit exposure window
- Forward secrecy from ephemeral key pairs

> 📖 [ECDH Select PIN Sample Code](https://github.com/aws-samples/samples-for-payment-cryptography-service/blob/main/python_sdk_example/ecdh_flows/README.md)

---

### Q13: Why use AWS Private CA for short-lived certificates in the ECDH flow?

AWS Private CA provides:

- **Short-lived certificates** (hours to days) that minimize the risk window if a mobile device is compromised
- **Automated issuance** — no manual certificate management needed per cardholder session
- **Cost efficiency** — short-lived certificate mode is priced lower ($50/month for subordinate CA)
- **Integration** — native AWS service-to-service authentication without external PKI dependencies

The mobile banking app requests a short-lived ECC certificate for each PIN-selection session, ensuring that even if intercepted, the certificate (and derived key material) expires rapidly.

---

### Q14: Can APC handle PIN Reset, PIN Set, and PIN Reveal operations?

Yes. APC supports the complete PIN lifecycle:

| Operation | API | Description |
|-----------|-----|-------------|
| **PIN Set** (Select PIN) | `GeneratePinData` | Cardholder chooses a new PIN; APC generates PVV/offset |
| **PIN Reset** | `GeneratePinData` | Same as Set, typically triggered from customer service flow |
| **PIN Reveal** | `TranslatePinData` | Re-encrypt existing PIN under session key for secure display to cardholder |
| **PIN Verify** | `VerifyPinData` | Validate cardholder-entered PIN against stored PVV/offset |

All operations support ISO PIN Block formats 0–4 and can use ECDH-derived keys for end-to-end encryption with mobile/web clients.

---

### Q15: How does ARQC verification work in APC?

ARQC (Authorization Request Cryptogram) is an EMV chip-card authentication mechanism. When a cardholder taps or inserts their chip card:

1. The card generates an ARQC using the card's Unique Derivation Key (UDK) and transaction data
2. The issuer receives the ARQC in the authorization request
3. APC's `VerifyAuthRequestCryptogram` API derives the session key from the Issuer Master Key (IMK) and verifies the cryptogram, optionally generating an ARPC (Authorization Response Cryptogram) in the response

**Supported derivation methods:**
- Visa (CVN 10, 18)
- Mastercard (CSK, Session Key)
- EMV Common Session Key derivation
- TDES and AES-based ARQC

---

### Q16: How does CVV/CVV2 generation work?

APC generates and verifies card verification values using the `GenerateCardValidationData` and `VerifyCardValidationData` APIs:

- **CVV** (magnetic stripe) — 3-digit value derived from PAN, expiry, service code, and CVK pair
- **CVV2** (card-not-present) — derived similarly but with different data inputs
- **iCVV** (chip transactions) — dynamic CVV for EMV chip
- **dCVV** (contactless) — dynamic CVV for contactless payments

The issuer's Card Verification Key (CVK) is stored in APC and used for both generation (during card personalization) and verification (during authorization).

---

## 5. Key Exchange

### Q17: What if my external partner (e.g., card personalization bureau) does NOT support TR-31 or TR-34 import?

This is a common challenge during migration. There are several workarounds in order of preference:

**Option 1: Bridge HSM Approach**
- Maintain a traditional HSM (e.g., Thales payShield) as a "bridge"
- Import keys from the partner into the bridge HSM using their supported method (e.g., clear components under dual control)
- Export from the bridge HSM as TR-31 key blocks
- Import the TR-31 key blocks into APC
- Decommission the bridge HSM once all keys are migrated

**Option 2: Request Partner Adoption**
- Engage your partner to adopt TR-31/TR-34 — most modern HSM firmware supports it
- TR-34 (RSA-based) is particularly easy for vendors to implement
- Provide the [ASC X9 TR-31](https://x9.org/) and [TR-34](https://x9.org/) specifications

**Option 3: Clear-Text Components via Your Own HSM (Last Resort — NOT Recommended)**
- APC does not directly support loading clear-text key components. `ImportKey` accepts only wrapped key material (`Tr31KeyBlock`, `Tr34KeyBlock`, `KeyCryptogram`, `DiffieHellmanTr31KeyBlock`, `As2805KeyCryptogram`) or public key certificates (`RootCertificatePublicKey`, `TrustedCertificatePublicKey`)
- Load the components into your own HSM in a key ceremony under dual control and split knowledge, then export the key to APC as a TR-31/TR-34 key block, or as a key cryptogram wrapped with the APC wrapping certificate obtained from `GetParametersForImport`
- Verify the imported key with its key check value (KCV)
- Higher risk — only use when no other option exists and with additional compensating controls

> ⚠️ Always consult your QSA (Qualified Security Assessor) before choosing a key exchange method to ensure PCI compliance.

---

### Q18: What key exchange standards does APC natively support?

| Standard | Direction | Use Case |
|----------|-----------|----------|
| **TR-31** | Import & Export | Symmetric key block exchange (industry standard) |
| **TR-34** | Import & Export | Asymmetric (RSA) key distribution for initial key loading |
| **RSA Wrap/Unwrap** | Import & Export | Key wrapping with RSA public key |
| **ECDH Key Agreement** | Derive | Session key establishment for Select PIN |

TR-31 is the preferred method for ongoing key exchange between APC and external systems. TR-34 is typically used for initial key loading or when no prior shared key exists.

> 📖 [Importing Keys](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/keys-import.html)

---

## 6. Acquirer Use Cases

### Q19: How does PIN Translation work for acquirers?

PIN Translation converts a PIN block encrypted under one key (e.g., the terminal's PIN Encryption Key) to encryption under a different key (e.g., the network/issuer's zone key) without ever exposing the clear PIN.

**API:** `TranslatePinData`

**Typical flow:**
1. POS terminal encrypts cardholder PIN under Terminal PEK → PIN block (Format 0/ISO 9564)
2. Acquirer sends PIN block to APC
3. APC decrypts under Terminal PEK, re-encrypts under Network Zone Key
4. Translated PIN block is forwarded to the card network/issuer

**Supported translations:**
- Format 0 ↔ Format 0 (TDES to TDES)
- Format 0 → Format 4 (TDES to AES)
- Format 4 ↔ Format 4 (AES to AES)
- Any combination of source/destination key types

---

### Q20: Can APC handle P2PE (Point-to-Point Encryption) decryption?

Yes. APC supports decryption of P2PE-encrypted transaction data from payment terminals:

1. **DUKPT key management** — APC stores the Base Derivation Key (BDK) and derives per-transaction keys using the terminal's Key Serial Number (KSN)
2. **Decryption** — `DecryptData` API decrypts the payment data encrypted at the terminal
3. **Re-encryption** — Optionally re-encrypt sensitive data under a different key for downstream processing

Supports both TDES-DUKPT and AES-DUKPT derivation methods.

---

### Q21: What MAC operations does APC support for acquirers?

APC supports MAC (Message Authentication Code) operations critical for transaction integrity:

**API:** `GenerateMac` / `VerifyMac`

| Algorithm | Key Type | Use Case |
|-----------|----------|----------|
| ISO 9797 Algorithm 1 | TDES | Legacy terminal MAC |
| ISO 9797 Algorithm 3 | TDES | Retail MAC (most common) |
| CMAC | AES | Modern terminal/network MAC |
| HMAC | AES/TDES | Application-layer integrity |

Acquirers typically verify MACs on incoming authorization messages and generate MACs on outgoing response messages to ensure message integrity across the payment network.

---

## 7. Compliance

### Q22: What PCI certifications does APC hold?

AWS Payment Cryptography maintains the following PCI compliance certifications:

| Certification | Scope |
|---------------|-------|
| **PCI PIN** | PIN processing, key management, and PIN translation operations |
| **PCI P2PE** | Decryption Management Component Provider (DMCP), Key Management Component Provider (KMCP), Key Loading Component Provider (KLCP) |
| **PCI DSS** | Level 1 Service Provider (as part of AWS's overall PCI DSS certification) |

These certifications mean customers can inherit APC's PCI compliance for the cryptographic operations layer, significantly reducing their own audit scope.

> 📖 [AWS PCI Compliance](https://aws.amazon.com/compliance/pci-dss-level-1-faqs/)

---

### Q23: What is the shared responsibility model for payment compliance with APC?

| Responsibility | AWS (APC) | Customer |
|---------------|-----------|----------|
| HSM hardware security | ✅ | |
| Physical key storage | ✅ | |
| Cryptographic algorithm implementation | ✅ | |
| PCI PIN/P2PE device certification | ✅ | |
| Key access policies (IAM) | | ✅ |
| Application-level security | | ✅ |
| Key rotation procedures | | ✅ |
| Transaction data handling | | ✅ |
| PCI DSS for cardholder data environment | | ✅ |
| Network security to/from APC | Shared | Shared |

AWS manages the cryptographic infrastructure; customers are responsible for how they invoke the service, manage access, and handle data before/after cryptographic operations.

---

### Q24: How do I access APC's compliance documentation?

Compliance artifacts are available through **AWS Artifact**:

1. Sign in to the AWS Console
2. Navigate to **AWS Artifact** → **Reports**
3. Search for "Payment Cryptography" or "PCI PIN"
4. Download the relevant attestation documents (AOC, ROC)

Available documents include:
- PCI PIN Attestation of Compliance (AOC)
- PCI P2PE Component Listing
- PCI DSS Attestation of Compliance
- SOC 2 Type II Report (covering APC)

> 📖 [AWS Artifact](https://aws.amazon.com/artifact/)

---

## 8. Migration

### Q25: How do I migrate keys from a Thales payShield HSM to APC?

**Step-by-step process:**

1. **Establish Key Encryption Key (KEK)** — Create a shared KEK between payShield and APC using TR-34 protocol
2. **Export from payShield** — Use the payShield console/API to export working keys as TR-31 key blocks wrapped under the KEK (firmware 3.x+ supports TR-31 natively)
3. **Import to APC** — Use `ImportKey` API with the TR-31 key block and the KEK reference
4. **Verify** — Perform test cryptographic operations with known test vectors to confirm key material matches
5. **Parallel run** — Run both systems simultaneously until confidence is established

> 📖 [AWS Blog: Synchronize keys automatically from payment HSMs to AWS Payment Cryptography](https://aws.amazon.com/blogs/industries/synchronize-keys-automatically-from-payment-hsms-to-aws-payment-cryptography/)

---

### Q26: Can I migrate from Atalla or Futurex HSMs?

Yes, though the approach varies by platform:

**Atalla (Utimaco):**
- Atalla supports TR-31 key block export (firmware dependent)
- If TR-31 is unavailable, use the bridge HSM approach
- Atalla variant key derivation methods must be mapped to APC equivalents

**Futurex:**
- Futurex Vectera Plus and KMES Series 3 support TR-31 natively
- Export keys as TR-31, establish KEK via TR-34, import to APC
- Futurex Guardian can serve as an intermediary for older models

For all migrations, create a **key inventory** first:
- Catalog all keys (type, usage, algorithm, expiry)
- Map each key to the equivalent APC key type and usage attributes
- Identify keys shared with external partners (these require coordinated exchange)

---

### Q27: What is the recommended hybrid operation approach during migration?

A hybrid (parallel-run) approach minimizes risk during migration:

**Phase 1: Preparation (2–4 weeks)**
- Deploy APC in your target region
- Import/synchronize all keys
- Build and test application integration

**Phase 2: Shadow Mode (2–4 weeks)**
- Route production traffic to existing HSM (primary)
- Mirror requests to APC (shadow)
- Compare cryptographic outputs to verify correctness
- Monitor latency and error rates

**Phase 3: Gradual Cutover (2–8 weeks)**
- Route a percentage of traffic to APC (start at 5–10%)
- Increase gradually as confidence builds
- Keep on-premises HSM as fallback

**Phase 4: Decommission (2–4 weeks)**
- Route 100% traffic to APC
- Maintain on-premises HSM in standby for 30–90 days
- Decommission hardware after stability period

**Key considerations:**
- Keep keys synchronized during the hybrid period (any key rotation must update both systems)
- Implement circuit-breaker patterns for automatic fallback
- Ensure monitoring covers both paths during parallel run

> 📖 [AWS Payment Cryptography Workshop](https://catalog.workshops.aws/payment-cryptography/en-US)

---

### Q28: How do I handle key synchronization during hybrid operation?

During hybrid operation, keys must remain identical in both the legacy HSM and APC:

1. **Initial sync** — Import all active keys from the legacy HSM into APC
2. **Rotation coordination** — When a key is rotated:
   - Generate the new key in one system
   - Export as TR-31 and import to the other
   - Update both systems' key references atomically in your application
3. **New key creation** — Create new keys in APC (future primary), then export to legacy HSM if needed for fallback
4. **Audit trail** — Log all key operations in both systems; reconcile daily

Use APC's key aliases and tags to maintain mapping between legacy HSM key labels and APC key ARNs.

---

## Additional Resources

- [AWS Payment Cryptography User Guide](https://docs.aws.amazon.com/payment-cryptography/latest/userguide/)
- [AWS Payment Cryptography API Reference](https://docs.aws.amazon.com/payment-cryptography/latest/APIReference/)
- [Sample Code Repository](https://github.com/aws-samples/samples-for-payment-cryptography-service)
- [AWS Payment Cryptography Workshop](https://catalog.workshops.aws/payment-cryptography/en-US)
- [AWS Blog: Synchronize keys automatically from payment HSMs to AWS Payment Cryptography](https://aws.amazon.com/blogs/industries/synchronize-keys-automatically-from-payment-hsms-to-aws-payment-cryptography/)
- [AWS Security Blog: Multi-Region keys: A new approach to key replication in AWS Payment Cryptography](https://aws.amazon.com/blogs/security/multi-region-keys-a-new-approach-to-key-replication-in-aws-payment-cryptography/)
- [AWS re:Invent Payment Cryptography Sessions](https://www.youtube.com/results?search_query=aws+reinvent+payment+cryptography)

---

*Last updated: 2026-07-08*
