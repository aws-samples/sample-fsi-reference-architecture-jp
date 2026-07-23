---
name: fsi-genai-usecases
description: >-
  Case study of generative AI (生成AI) use cases for financial institutions from the
  BLEA for FSI (金融リファレンスアーキテクチャ日本版) reference architecture. Covers four
  concrete Amazon Bedrock-centered ユースケース: document/content review (RAPID),
  AI sales roleplay training, a multi-agent contract-assistant, and ATM fraud
  detection with Amazon Nova. Use this skill when designing, explaining, or
  implementing GenAI workloads for banks/insurers on AWS — e.g. Bedrock agents,
  multi-agent collaboration, Human-in-the-Loop document審査, compliance guardrails,
  or multimodal video analysis. Triggers: 生成AI, ユースケース, Bedrock, Nova,
  マルチエージェント, ロールプレイ, 文書審査, 不正検知, 契約書アシスタント.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI Generative AI Use Cases

## Workload Overview

This case study presents concrete use cases for applying generative AI in financial
institutions (banks, insurers, securities firms). All examples are built around
**Amazon Bedrock** and supporting AWS services, and each ships with a public sample
implementation. The case study collects four use cases, each addressing a distinct
business problem in financial services:

1. **Document / Content Review (RAPID)** — automates the large volume of document
   review work in financial institutions using a Human-in-the-Loop model. Guideline
   documents are turned into checklists automatically, target documents are reviewed
   against them by generative AI, and a human makes the final decision.
2. **AI Sales Roleplay** — a training system where a sales representative practices
   financial-product sales skills by conversing (via voice) with an AI-played customer.
   It evaluates emotion, compliance, video (facial expression / eye contact), and
   reference accuracy in real time.
3. **Contract Assistant Agent** — an AI assistant that comprehensively supports
   contract-related work (new contract drafting, existing-contract lookup, and
   answering contract questions) through a supervisor + specialist multi-agent
   configuration on Amazon Bedrock.
4. **ATM Fraud Detection (elderly phone use)** — analyzes surveillance-camera video
   with Amazon Nova (multimodal) to automatically detect behavior patterns that may
   indicate fraud (e.g. an elderly person operating an ATM while on a phone call), to
   prevent bank-transfer (振り込め) and special fraud damage before it occurs.

**Purpose / significance in financial services.** These use cases target recurring
pain points in the sector: heavy manual document审查 burden, the need for consistent
sales quality and compliance adherence (e.g. suitability principle, explanation
obligations under financial instruments regulations), efficient handling of
contract operations, and protecting customers — especially the elderly — from fraud.
Common business drivers across all four are operational efficiency (24-hour
operation, automation of routine work), quality standardization (removing per-person
variation), cost reduction (labor savings), and transparency / accountability (AI
decision rationale is made explicit, supporting explainability and audit response).

## Best Practices and Key Components

### Best Practices

- MUST: Keep a human in the loop for final judgment in document review — AI performs
  the first-pass review and a human makes the final decision and approval (RAPID's
  Human-in-the-Loop model).
- MUST: Make the AI's decision rationale explicit, so that the reason for a pass/fail
  judgment can be shown and accountability (説明責任) is preserved.
- MUST: Enforce compliance guardrails on generative AI output in customer-facing /
  sales-training scenarios — FinanceCompliance and GeneralCompliance guardrails are
  recommended for financial institutions, checking against financial instruments and
  banking regulations.
- MUST: Cover the legally required explanation items in sales roleplay (risk
  explanation, fee explanation, suitability confirmation) and prevent omission, to
  reduce legal risk from breach of the explanation obligation.
- MUST: Set required goals (必須ゴール) with explicit判定基準 for compliance-related
  and legally-required items in roleplay scenarios (assign priority 5 for compliance
  / legal requirements).
- SHOULD: Use a supervisor + specialist multi-agent configuration (Amazon Bedrock
  multi-agent collaboration) so a single interface can route diverse contract
  requests to the most suitable specialist agent automatically.
- SHOULD: Use direct browser-to-S3 upload via a time-limited presigned URL (5-minute
  expiry) to keep uploads secure and to avoid API Gateway payload limits for large
  video files.
- SHOULD: Apply S3 lifecycle policies to surveillance video and DynamoDB TTL to
  automatically delete old / unneeded data, for both cost and data management.
- SHOULD: Minimize false positives by correctly identifying normal customer behavior
  (short calls, calm demeanor, smooth operation) so business efficiency and customer
  experience are maintained.
- PREFER: A serverless architecture (API Gateway + Lambda + Amazon Bedrock + S3 +
  DynamoDB) for these GenAI workloads to balance scalability and operational
  efficiency through loosely-coupled layers.
- PREFER: Deploying via AWS CloudShell (no prerequisites) for the AI sales roleplay
  sample, running the provided `bin.sh` deploy script.
- MAY: Restrict self-sign-up and choose a specific Bedrock region for the roleplay
  sample via deploy options (`--disable-self-register`, `--bedrock-region`).
- MAY: Define custom guardrails (e.g. a 金融商取法 guardrail: no assertive judgments,
  material-fact explanation, suitability principle, no exaggerated advertising) when
  organization-specific compliance requirements exist.
- WILL: Detection of high-risk fraud immediately notifies store staff so they can
  speak to the customer and prevent damage before it occurs.
- WILL: The ATM fraud-detection Amazon Nova analysis performs integrated multimodal
  analysis of both video and audio to identify fraud patterns.
- WILL: The contract-assistant generated draft contracts are stored in S3 and
  provided to the user; sample templates include purchase, franchise, and
  time-and-material contracts.

### Key Components

#### Amazon Bedrock (Generative AI Foundation)

- **Component Overview**: The central generative-AI engine across all four use cases.
  Hosts the LLMs used for document analysis and review (RAPID), roleplay dialogue and
  compliance checking (via Anthropic Claude), multi-agent contract processing, and
  multimodal video analysis (via Amazon Nova). Also provides multi-agent
  collaboration and guardrail capabilities.
- **Assumed AWS Services**: Amazon Bedrock, Amazon Nova, Anthropic Claude (on Bedrock),
  Bedrock Agents, Bedrock multi-agent collaboration, Bedrock Guardrails.

#### Multi-Agent Orchestration (Contract Assistant)

- **Component Overview**: A supervisor agent (Contract Agent) receives user contract
  inquiries, analyzes intent, and routes to the optimal specialist among three
  sub-agents — contract-drafting, existing-contract-lookup, and contract-question
  answering — then composes the final answer. Implemented with Amazon Bedrock
  multi-agent collaboration.
- **Assumed AWS Services**: Amazon Bedrock (Agents, multi-agent collaboration),
  AWS Lambda (existing-contract lookup), Amazon S3 (generated contracts / templates),
  Amazon OpenSearch Service (knowledge base for contract Q&A).

#### Serverless Processing Layer

- **Component Overview**: Event-driven, serverless compute that handles presigned-URL
  generation, analysis triggering, status checks, and general application logic across
  the use cases. In ATM fraud detection this is three Lambda functions
  (presigned-URL, auto-analysis, status). Loosely-coupled layers (frontend, API,
  processing, AI analysis, data) enable flexible scaling and maintenance.
- **Assumed AWS Services**: AWS Lambda, Amazon API Gateway.

#### Data & Storage Layer

- **Component Overview**: Stores documents, videos, scenario data, evaluation results,
  checklists, and analysis metadata. S3 holds documents (RAPID), generated contracts
  and templates (contract assistant), video files (fraud detection), and scenario /
  evaluation data (roleplay). DynamoDB manages checklists and review results (RAPID),
  analysis results / metadata (fraud detection), and user info / progress (roleplay).
- **Assumed AWS Services**: Amazon S3, Amazon DynamoDB.

#### Web Delivery & API Layer

- **Component Overview**: Delivers the browser-based UIs and REST APIs. CloudFront
  provides low-latency delivery of the web applications; API Gateway exposes REST API
  endpoints and manages authentication/authorization and rate limiting. The ATM
  fraud-detection API exposes a presigned-URL endpoint (`GET /presigned-url`) and a
  status endpoint (`GET /status/{videoId}`).
- **Assumed AWS Services**: Amazon CloudFront, Amazon API Gateway.

#### Multimodal & Media Analysis Services

- **Component Overview**: Services that process non-text modalities. Amazon Nova (on
  Bedrock) analyzes ATM surveillance video and audio for fraud patterns. In AI sales
  roleplay, Amazon Transcribe converts speech to text and Amazon Rekognition analyzes
  video for non-verbal communication (facial expression, eye contact, gestures).
- **Assumed AWS Services**: Amazon Nova (on Amazon Bedrock), Amazon Transcribe,
  Amazon Rekognition.

#### Operations & Monitoring

- **Component Overview**: Observability for the workloads (documented in detail for the
  ATM fraud-detection use case). CloudWatch Metrics/Logs collect metrics and aggregate
  logs; CloudWatch Alarms detect anomalies and notify the operations team via SNS,
  visualized through an integrated dashboard. Monitored items include Lambda duration
  and error rate, API Gateway latency/errors, DynamoDB read/write capacity, S3 storage
  usage, and Bedrock API call count and errors.
- **Assumed AWS Services**: Amazon CloudWatch (Metrics, Logs, Alarms), Amazon SNS.

## FISC Compliance Summary

There is **no dedicated FISC mapping file** for this case study, and the source
documents do not contain an explicit FISC safety-standards mapping. Therefore no
`references/fisc-mapping.md` is created.

The source documents do, however, address financial regulatory / compliance concerns
qualitatively, which are relevant to FISC-aligned governance:

- Compliance guardrails based on the Financial Instruments and Exchange Act
  (金融商取法) and Banking Act (FinanceCompliance / GeneralCompliance), including
  prohibition of assertive judgments, the material-fact explanation obligation,
  the suitability principle (適合性原則), and prohibition of exaggerated advertising.
- Explanation-obligation adherence and customer protection in sales activities (risk
  explanation, fee explanation, suitability confirmation).
- Transparency and accountability: making AI decision rationale explicit to support
  explainability and audit response; systematic management of detection history and
  response records for audits (ATM fraud detection).
- Document review against laws/regulatory guidelines (e.g. FSA supervisory guidelines,
  industry self-regulatory rules), internal compliance rules, and information-security
  policies (RAPID review-criteria categories).

No further FISC control mapping should be inferred beyond these source-stated points.

## Reference Architecture

Each use case has its own architecture and workflow. Details, including diagrams and
per-use-case flows, are in the Japanese reference files:

- [references/architecture.md](references/architecture.md) — case-study overview and
  cross-cutting architecture.
- [references/contract-assistant-agent.md](references/contract-assistant-agent.md) —
  multi-agent contract assistant.
- [references/document-review.md](references/document-review.md) — RAPID document /
  content review.
- [references/cctv-fraud-detection.md](references/cctv-fraud-detection.md) — ATM fraud
  detection with Amazon Nova.
- [references/ai-roleplay.md](references/ai-roleplay.md) — AI sales roleplay training.
- [references/ai-roleplay-scenario-guide.md](references/ai-roleplay-scenario-guide.md) —
  financial roleplay scenario creation guide (6 steps).

## CDK Sample Overview

No CDK sample is provided for this case study. The individual use cases are deployed
from their own public sample repositories (referenced in the Japanese reference files),
for example via AWS CloudShell and a provided deploy script (`bin.sh`) for the AI sales
roleplay sample. This case study asset itself contains no CDK code.
