# Migration Guide: On-Premises Payment HSMs to AWS Payment Cryptography

## Table of Contents

- [Migration Overview](#migration-overview)
- [Source HSM Support](#source-hsm-support)
- [Key Synchronization Methods](#key-synchronization-methods)
- [Phased Migration Strategy](#phased-migration-strategy)
- [Hybrid Operation](#hybrid-operation)
- [3DES to AES Migration](#3des-to-aes-migration)
- [Testing Strategy](#testing-strategy)
- [Common Challenges](#common-challenges)
- [Rollback Plan](#rollback-plan)

---

## Migration Overview

### Why Migrate to AWS Payment Cryptography?

Organizations managing on-premises payment HSMs face increasing operational burden,
upfront hardware costs, and staffing challenges. AWS Payment Cryptography addresses these:

| Driver | Benefit |
|--------|---------|
| **TCO Reduction** | Eliminate HSM hardware procurement (~$50K–$150K per unit), maintenance contracts, physical security, and dedicated HSM administrator staffing |
| **Elasticity** | Scale cryptographic operations dynamically — no capacity planning for peak periods (holiday shopping, promotional events) |
| **Data Center Exit** | Remove one of the last dependencies keeping payment workloads in physical data centers |
| **API Simplification** | Replace proprietary HSM socket commands with RESTful APIs, AWS SDKs, and infrastructure-as-code |
| **Compliance Streamlining** | Leverage AWS's PCI PTS HSM and PCI PIN certifications rather than managing your own audit evidence |

### Typical Migration Timeline

A full migration typically spans **4–9 months** depending on organizational complexity:

```
Month 1-2:   Discovery & Planning (key inventory, dependency mapping)
Month 2-3:   Key Synchronization Setup (establish KEKs, sync working keys)
Month 3-4:   Integration Development (API translation, application changes)
Month 4-6:   Testing & Validation (shadow mode, certification testing)
Month 6-8:   Phased Traffic Migration (canary → gradual shift → cutover)
Month 8-9:   Decommissioning (legacy HSM removal, contract wind-down)
```

> **Note**: Simple organizations may complete in 3 months. Complex multi-acquirer,
> multi-region deployments may extend to 12+ months.

---

## Source HSM Support

### Thales payShield 10K

**Key Synchronization Approach:**
- Export Zone Master Keys (ZMKs) using TR-34 protocol via `EY` command family
- Establish TR-34 KEK between payShield and AWS Payment Cryptography
- Wrap working keys under the shared KEK using TR-31 key blocks

**Considerations:**
- Firmware version 1.4a+ recommended for full TR-34 support
- Variant LMK keys require re-encryption to key-block format before export
- Legacy key types (ZPK, ZMK under variant mode) need conversion to TR-31

### Utimaco/Atalla AT1000

**Key Synchronization Approach:**
- Use Master File Key (MFK) export ceremonies to extract Key Encrypting Keys
- Atalla supports TR-31 key block export natively
- Establish shared KEK via TR-34 or manual key ceremony

**Considerations:**
- Atalla key naming conventions differ from TR-31 key usage attributes
- AKB (Atalla Key Block) format keys must be converted to TR-31 before import

### Futurex GSP3000

**Key Synchronization Approach:**
- Futurex Excrypt Manager supports TR-34 key distribution
- ECDH key agreement available for direct AES-256 key establishment
- TR-31 export supported for working keys after KEK establishment

**Considerations:**
- FXKB (Futurex Key Block) format requires translation to ANSI TR-31
- Firmware must support ASC X9 TR-34-2019 (not just TR-34-2012)
- Multi-tenant key partitions each require separate migration sessions

---

## Key Synchronization Methods

### TR-34 (Preferred for KEKs)

TR-34 is the **recommended method** for establishing Key Encrypting Keys between
your on-premises HSM and AWS Payment Cryptography.

```
┌─────────────────┐         TR-34 Protocol          ┌──────────────────────┐
│  On-Prem HSM    │ ◄──── Certificate Exchange ────► │  AWS Payment         │
│  (KDH)          │ ────── Wrapped KEK ────────────► │  Cryptography (KRD)  │
└─────────────────┘                                  └──────────────────────┘
```

**Process:**
1. AWS Payment Cryptography generates an asymmetric key pair for key reception
2. Export the KRD certificate from APC; load into on-premises HSM
3. On-premises HSM wraps KEK using the KRD public key
4. Import the TR-34 wrapped KEK into AWS Payment Cryptography
5. Both sides now share the KEK for subsequent TR-31 key wrapping

**Advantages:** Asymmetric exchange (no pre-shared secret), mutual authentication
via X.509 certificates, audit trail, PCI PIN Annex A compliance.

### TR-31 (For Working Keys)

Once a KEK is established via TR-34, use TR-31 to synchronize all working keys.

**Supported Key Types:**
- `B0` — BDK (Base Derivation Key) for DUKPT
- `P0` — PIN Encryption Key
- `C0` — CVK (Card Verification Key)
- `M1`/`M3` — MAC keys (ISO 9797-1)
- `D0` — Symmetric Data Encryption Key
- `K0`/`K1` — Key Encrypting Keys

**Process:** Export from on-prem HSM in TR-31 key block format → import into APC
via `ImportKey` API → APC validates key block MAC and stores with appropriate attributes.

### ECDH (For AES-256 Keys)

Used when direct AES-256 key establishment is needed (TR-34 traditionally limited
to 2048-bit RSA wrapping):

1. Generate ECDH key pair on APC (P-256 or P-384 curve)
2. Exchange public keys between on-prem HSM and APC
3. Both sides derive shared secret; use KDF to derive AES-256 KEK
4. Wrap working keys under the derived KEK

### Automated Key Synchronization Tool

AWS provides an automated solution for ongoing key replication between on-premises
HSMs and AWS Payment Cryptography.

> **Reference**: [Synchronize keys automatically from payment HSMs to AWS Payment Cryptography](https://aws.amazon.com/blogs/industries/synchronize-keys-automatically-from-payment-hsms-to-aws-payment-cryptography/) (June 2025)

**Capabilities:**
- Continuous key monitoring and automatic synchronization
- Support for Thales payShield, Utimaco/Atalla, and Futurex source HSMs
- Key lifecycle event detection (creation, rotation, deletion)
- Bidirectional sync for hybrid operation periods
- CloudWatch metrics/alarms and EventBridge integration

---

## Phased Migration Strategy

### Phase 1: Key Synchronization (Parallel Operation) — 2–4 weeks

- Establish TR-34 KEK between on-prem HSM and APC
- Synchronize all working keys (PEKs, BDKs, CVKs, MAC keys)
- Validate key parity using known-answer tests (KATs)
- Set up automated key sync — both systems hold identical key material, no traffic moves

**Success Criteria:** All KCVs match, automated sync replicates within SLA, zero mismatches.

### Phase 2: Canary Traffic Routing — 1–2 weeks

- Route 1–5% of non-critical traffic to AWS Payment Cryptography
- Compare response codes, timing, and cryptographic outputs
- Monitor error rates, latency percentiles (p50, p95, p99)

**Success Criteria:** Error rate ≤ baseline, p99 latency <50ms, zero crypto mismatches.

### Phase 3: Gradual Traffic Shift — 2–4 weeks

- Increase traffic: 5% → 25% → 50% → 75% → 90%
- Each increment held 48+ hours before advancing
- Maintain rollback capability at each stage

**Routing Options:** Feature flags, BIN-range based, or transaction-type based routing.

### Phase 4: Full Cutover — 1 week

- Route 100% production traffic to APC
- Keep on-prem HSMs in standby (no active traffic)
- Monitor 5–7 days at full load; verify all edge cases and batch processing

### Phase 5: Decommission Legacy HSMs — 2–4 weeks

- Disable network routes; execute key destruction ceremonies (PCI PIN compliant)
- Document destruction with dual control and audit evidence
- Return/dispose hardware; terminate maintenance contracts

---

## Hybrid Operation

### Running Both Systems Simultaneously

```
                    ┌─────────────────────┐
                    │   Payment Gateway   │
                    │   / Routing Layer   │
                    └──────────┬──────────┘
                    ┌──────────┴──────────┐
          ┌────────▼────────┐  ┌─────────▼──────────┐
          │  On-Prem HSM    │  │  AWS Payment       │
          │  (Legacy)       │  │  Cryptography      │
          └─────────────────┘  └────────────────────┘
```

### Key Consistency

- **Automated Sync**: Both systems hold identical key material at all times
- **Rotation Coordination**: Propagate within < 5 minutes SLA
- **KCV Validation**: Regular Key Check Value comparison between systems
- **Version Tracking**: Key version registry to detect drift

### Failback Strategy

1. **Immediate Failback** (< 1 hour): Routing layer redirects to on-prem HSMs
2. **Key State Verification**: Confirm on-prem keys match current production state
3. **Root Cause Analysis**: Resolve issue in APC configuration
4. **Re-migration**: Restart from appropriate phase after resolution

---

## 3DES to AES Migration

### Industry Mandate

- **ANSI X9.24-3**: Defines AES-based DUKPT for PIN encryption
- **PCI SSC**: 3DES disallowed after Dec 31, 2023 for new implementations
- **Card Networks**: Visa/Mastercard mandating AES for new terminal deployments
- **NIST SP 800-131A Rev 2**: 3DES deprecated and disallowed after 2023

### APC's AES Support

Native support for AES-128/192/256, AES-DUKPT (X9.24-3-2017), AES-based MAC
(CMAC, ISO 9797-1 Alg 5), and AES key wrapping (NIST SP 800-38F).

### Migration Planning

**Approach 1 — Migrate As-Is, Then Upgrade:**
Sync existing 3DES keys → complete traffic migration → rotate to AES with counterparties

**Approach 2 — Upgrade During Migration (Recommended):**
Establish AES equivalents in APC → coordinate AES key exchange with counterparties →
run 3DES (on-prem) and AES (APC) in parallel → migrate endpoints as they become capable

> **Tip**: Combining HSM migration with 3DES→AES reduces project count but increases
> complexity. Evaluate your organization's change tolerance.

---

## Testing Strategy

### Shadow Mode (Dual-Process and Compare)

Process every transaction on BOTH systems and compare results:

```
Transaction ──┬──► On-Prem HSM ──► Response A ──┐
              └──► APC         ──► Response B ──┘──► Compare
```

**Compare:** PIN verification results, PIN translation outputs, CVV results,
MAC outputs (must be bit-identical), ARQC validation results.

**Considerations:** Adds latency (use async comparison), careful handling of
DUKPT counters, log all mismatches for root cause analysis.

### Test Card Ranges

- Dedicated test BIN ranges from card networks
- Isolated test PINs and test key sets
- All PIN block formats (ISO Format 0, 1, 3, 4)
- DUKPT counter edge cases (exhaustion, resync)

### Certification Testing

- **Visa**: VTS PIN security testing
- **Mastercard**: MIP testing
- **Others**: Discover, Amex, JCB, UnionPay requirements
- **Acquirer Testing**: End-to-end flow verification with each acquirer

---

## Common Challenges

### Socket-to-API Translation

| Legacy HSM Command | AWS Payment Cryptography API |
|---|---|
| Thales `BA`/`BC` (PIN verify) | `VerifyPinData` |
| Thales `JG`/`JI` (PIN translate) | `TranslatePinData` |
| Thales `CY`/`CZ` (CVV generate/verify) | `GenerateCardValidationData` / `VerifyCardValidationData` |
| Thales `MS`/`MU` (MAC generate/verify) | `GenerateMac` / `VerifyMac` |
| Atalla `31x` / `30x` | `VerifyPinData` / `TranslatePinData` |

**Recommendation**: Build an abstraction layer isolating your app from the crypto provider.

### Latency Differences

- On-prem: Sub-ms LAN + ~2-5ms processing
- APC: Network round-trip + ~10-30ms processing
- **Mitigation**: Connection pooling, regional endpoints, VPC endpoints, request batching

### Quota Planning for Peak Loads

- Review service quotas (TPS per operation); model peak volumes
- Request increases BEFORE migration (2-week lead time)
- Implement client-side retry with exponential backoff

### Staff Re-training

- HSM administrators → cloud security engineers
- Socket-command expertise → API/SDK proficiency
- Vendor tooling → AWS Console, CLI, CloudFormation/Terraform

---

## Rollback Plan

### Maintaining On-Prem HSM Capability

1. **Do NOT decommission** until Phase 5 success criteria fully met
2. **Maintain contracts** through migration + buffer period
3. **Keep keys synchronized** bidirectionally throughout all phases
4. **Preserve network connectivity** to on-prem HSMs
5. **Retain HSM staff** or expertise through completion

### Key Re-export Procedures

1. Export current keys from APC using `ExportKey` API
2. Use TR-31 key blocks with established KEK for transport
3. Import into on-premises HSM; verify KCVs match
4. Route traffic back; validate with test transactions before full revert

### Rollback Decision Criteria

Trigger rollback if ANY persist for > 1 hour:
- Cryptographic mismatch rate > 0.01%
- Decline rate increase > 0.5% above baseline
- API error rate > 1%
- P99 latency exceeds SLA thresholds
- Any data integrity concern (even suspected)

---

## References

- [AWS Payment Cryptography Documentation](https://docs.aws.amazon.com/payment-cryptography/)
- [Synchronize keys automatically from payment HSMs to AWS Payment Cryptography](https://aws.amazon.com/blogs/industries/synchronize-keys-automatically-from-payment-hsms-to-aws-payment-cryptography/) (June 2025)
- [ANSI X9 TR-34-2019](https://x9.org/) / [ANSI X9 TR-31](https://x9.org/)
- [PCI PIN Security Requirements v3.1](https://www.pcisecuritystandards.org/)
- [NIST SP 800-131A Rev 2](https://csrc.nist.gov/publications/detail/sp/800-131a/rev-2/final)
