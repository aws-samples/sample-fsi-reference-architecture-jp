---
name: aws-payment-cryptography-guide
description: >
  Covers AWS Payment Cryptography (APC) adoption, design, and migration support
  for issuers, acquirers, PSPs, and network processors. Provides architectural
  guidance on HSM migration, PIN verification, PIN translation, key management,
  card issuance, merchant acquiring, and payment gateway integration. Includes
  PCI compliance considerations, cryptographic protocol references (DUKPT, TR-31,
  TR-34, ECDH), and decision frameworks for selecting APC capabilities. Trigger
  keywords: "Payment Cryptography", "HSM migration", "PIN verification",
  "PIN translation", "DUKPT", "TR-31", "TR-34", "ARQC", "CVV", "P2PE",
  "Select PIN", "ECDH", "card issuance", "merchant acquiring", "payment gateway"
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# AWS Payment Cryptography Guide — Agent Skill

## Purpose

This skill equips customers with comprehensive guidance for adopting, designing, and migrating to **AWS Payment Cryptography (APC)**.
It covers the full spectrum of payment processing roles—card issuers, merchant acquirers, payment service providers (PSPs), and network processors—providing architecture patterns, migration strategies, and operational best practices.

---

## Workflow

Follow these steps when handling a user query:

### Step 1 — Identify Business Type

Determine the user's business role from context:

| Business Type | Indicators |
|---|---|
| **Issuer** | Card issuance, PIN generation, ARQC validation, Select PIN, card personalization |
| **Acquirer** | Merchant acquiring, POS terminal management, PIN translation, P2PE |
| **PSP** | Payment gateway, multi-acquirer routing, tokenization, payment facilitation |
| **Network Processor** | Switch operations, network-level PIN translation, stand-in processing |
| **Unknown** | Insufficient context to classify — proceed to Step 4 |

### Step 2 — Load Role-Specific Reference

Once the business type is identified, load the corresponding reference file:

| Business Type | Reference File |
|---|---|
| Issuer | `references/issuer.md` |
| Acquirer | `references/acquirer.md` |
| PSP | `references/psp.md` |
| Network Processor | `references/network-processor.md` |

Use this file as the primary context for answering the user's question.

### Step 3 — Load Cross-Cutting Topics (as needed)

If the query involves topics that span multiple business types, additionally
load the relevant shared reference:

| Topic | Reference File |
|---|---|
| Key management, TR-31, TR-34, ECDH key exchange | `references/key-management.md` |
| PCI DSS / PCI PIN / PCI P2PE compliance | `references/pci-compliance.md` |
| Migration from on-premises HSMs to APC | `references/migration-guide.md` |
| External resources (documentation, blogs, samples) | `references/external-resources.md` |

### Step 4 — Initial Exploration / Overview

If the user's business type is unknown or the question is exploratory:

1. Load `references/faq.md` — covers common questions and概要
2. Load `references/decision-tree.md` — provides a structured decision framework
   for selecting APC capabilities based on use case

Guide the user through clarifying questions to identify their business type
and specific needs.

### Step 5 — Compliance Disclaimer

**Always** include the following disclaimer when providing guidance related to
PCI compliance, security controls, or certification scope:

> ⚠️ **Disclaimer**: The guidance provided here is for informational and
> architectural planning purposes only. PCI DSS, PCI PIN, and PCI P2PE
> compliance requirements must be validated with a Qualified Security Assessor
> (QSA) or Payment Card Industry Forensic Investigator (PFI) as appropriate.
> AWS Payment Cryptography is a PCI-certified service, but your overall
> compliance posture depends on your specific implementation.

---

## File References

### references/

| File | Description |
|---|---|
| `issuer.md` | Card issuer patterns — PIN generation, ARQC/ARPC, card personalization |
| `acquirer.md` | Merchant acquirer patterns — PIN translation, P2PE, terminal integration |
| `psp.md` | PSP/gateway patterns — multi-acquirer routing, tokenization |
| `network-processor.md` | Network processor patterns — switch integration, stand-in processing |
| `key-management.md` | Key lifecycle management — TR-31, TR-34, ECDH, key hierarchy design |
| `pci-compliance.md` | PCI compliance mapping — DSS, PIN, P2PE scope reduction with APC |
| `migration-guide.md` | Migration strategies — phased migration from on-premises HSMs |
| `external-resources.md` | Curated links — official docs, blog posts, sample code, pricing |
| `faq.md` | Frequently asked questions — overview, pricing model, regional availability |
| `decision-tree.md` | Decision framework for selecting APC capabilities by use case |

---

## Response Guidelines

1. **Be specific to the user's role** — Tailor recommendations to their
   business type rather than providing generic guidance.
2. **Reference AWS documentation** — Link to official AWS docs when available.
3. **Provide code examples** — Include AWS CLI or SDK snippets where helpful.
4. **Highlight regional considerations** — Note APC regional availability
   when relevant to architecture decisions.
5. **Security-first** — Always prioritize security best practices; never
   suggest shortcuts that compromise key security or compliance posture.
6. **Migration pragmatism** — Acknowledge that migration is incremental;
   support hybrid architectures during transition periods.

---

## Notes

- **Language**: This skill operates in **English only**. The agent loads the
  English `.md` reference files. The `*_ja.md` files are standalone Japanese
  reference translations for human readers; they are **not** loaded or routed to
  by this skill and are not guaranteed to track the English files.
- **Verify volatile facts before quoting**: pricing, throughput quotas, SLA
  figures, certified Regions, and API/CLI details change over time. Do not
  present hardcoded numbers from the reference files as current fact — confirm
  against the latest AWS documentation, pricing page, Service Quotas, and AWS
  Artifact before relying on them in a decision.
- This skill does not replace AWS documentation or AWS Support. For service
  limits, SLA details, or account-specific issues, direct users to the
  appropriate AWS channels.
- APC features and availability evolve; always verify current capabilities
  against the latest AWS documentation.
