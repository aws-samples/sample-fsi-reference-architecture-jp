---
name: fsi-genai-platform
description: >-
  Reference architecture for building a Generative AI (生成AI) workload for
  financial institutions on AWS, based on the closed-network edition of the
  AWS Samples "Generative AI Use Cases (GenU)" application with financial-grade
  security customizations. Use this skill when designing, reviewing, or
  explaining a financial-services generative AI platform on AWS: RAG-based
  internal knowledge search, document drafting, customer-support assistance,
  chat/summarization/translation, image/video generation, closed-network
  (閉域) deployment, Amazon Bedrock, Amazon Bedrock Guardrails, Amazon Cognito
  authentication, CloudWatch monitoring dashboards, KMS encryption, and FISC
  (金融情報システムセンター) compliance mapping for the "BLEA for FSI /
  金融リファレンスアーキテクチャ日本版" v1.6 GenAI asset.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI Reference Architecture — Generative AI (生成AI)

## Workload Overview

This skill packages the **Generative AI (生成AI)** reference architecture from
the "金融リファレンスアーキテクチャ日本版 (BLEA for FSI)" v1.6 initiative. It is a
sample implementation for adopting generative AI inside financial institutions.

The implementation is based on the **closed-network (閉域版) edition** of the
AWS Samples application **Generative AI Use Cases (GenU)**
(https://github.com/aws-samples/generative-ai-use-cases), with additional
customizations that address the security requirements financial institutions
typically demand (encryption, audit logging, Guardrail hardening).

GenU is an open-source application that delivers a wide range of generative AI
use cases — chat, text generation, summarization, translation, RAG, image
generation, and video generation. This reference architecture provides:

- An organized set of financial-institution use cases achievable with GenU.
- An explanation of the main features of the GenU closed-network edition and how
  to use them.
- The security-hardening customizations applied for financial requirements
  (encryption, audit logs, Guardrail settings).
- The FISC Safety Standards compliance status (see the FISC compliance summary
  below and `references/fisc-mapping.md`).

**Financial use cases addressed** include: internal knowledge search & retrieval
via RAG (searching regulations, manuals, past approval documents, and product
materials in natural language), document drafting support (approval documents,
reports, customer-facing materials, internal email), customer-support assistance
(summarizing inquiries, drafting replies, searching similar past cases), data
analysis support (trend analysis of sales/market data, report summarization,
insight extraction), and internal-communication efficiency (automatic meeting
minutes from audio, multi-language translation, material summarization). Image
generation, video generation, and diagram generation extend these to
presentation material, internal training content, and business-flow
visualization.

**Prerequisites & positioning.** The closed-network configuration is one option
that matches an organization's network policy. The standard (non-closed) edition
of GenU already offers sufficient security features and may be selected depending
on requirements. The design supports staged security hardening: an organization
may start with the standard edition and later add Guardrails, migrate to the
closed-network configuration, or enforce MFA as risk assessment dictates.

## Best Practices and Key Components

### Best Practices

- SHOULD: Confine client-to-system communication to a closed network (閉域) when
  data confidentiality or network-security policy requires it; use the GenU
  closed-network mode so traffic does not traverse the internet.
- SHOULD: Serve the web static frontend via Application Load Balancer + Amazon ECS
  Fargate (instead of Amazon CloudFront) when running in the closed-network
  configuration.
- MUST: Route all AWS Lambda communication to other AWS services (Amazon DynamoDB,
  Amazon S3, Amazon Bedrock, etc.) through VPC endpoints so it completes inside the
  VPC in the closed-network configuration.
- SHOULD: Proxy Amazon Cognito authentication through an Amazon API Gateway Private
  API in the closed-network configuration so authentication requests reach the
  Cognito User Pool from the isolated environment.
- MUST: Authenticate and authorize users with Amazon Cognito; verify JWT token
  validity with a Lambda Authorizer so only properly authorized requests reach
  backend services.
- SHOULD: Consider stricter password policies (minimum length, complexity), MFA
  enforcement, and appropriate session-timeout settings on Amazon Cognito
  according to organizational requirements.
- SHOULD: Provide a CloudWatch monitoring dashboard that visualizes Amazon Bedrock
  token usage (input/output tokens), API call status (request count, error rate,
  response time), recent prompt history, and user activity patterns.
- MUST: Record all operation logs to CloudWatch Logs with appropriate retention
  periods and access control for audit and incident investigation.
- MUST: Enable Amazon Bedrock Guardrails to filter model input and output; block
  sensitive information such as credit card numbers, international bank account
  numbers, AWS access keys, email addresses, phone numbers, and passwords.
- SHOULD: Customize Guardrails to the organization's policy — e.g., add
  Japanese-language support and finance-oriented topic filters (insider trading,
  money laundering, regulatory violation, customer confidential information) and
  restrict investment-advice or law-violating responses.
- WILL: Guardrails are configured independently of the model, so a common policy
  can be applied across multiple models.
- MUST: Encrypt data at rest (Amazon S3, Amazon DynamoDB, OpenSearch, Guardrails)
  with AWS KMS customer-managed keys, and manage KMS key policies and key rotation.
- MUST: Enable point-in-time recovery (PITR) on Amazon DynamoDB tables.
- PREFER: Serverless managed services (AWS Lambda, Amazon API Gateway, Amazon
  DynamoDB, Amazon Bedrock) to reduce operational burden, gain usage-based
  auto-scaling, and obtain high availability by default.
- WILL: Amazon Bedrock is designed not to use customer data for model training, so
  input-data confidentiality is protected.
- MUST: Manage the infrastructure as code with AWS CDK so environments are
  reproducible across development, verification, and production, and configuration
  history is version-controlled for auditability.
- MAY: Use the standard (non-closed) edition of GenU instead when full feature
  coverage is required, since the closed-network edition does not support external
  IdP SAML federation, Voice Chat, or AgentCore Chat, and requires the deploy
  region and the model region to be identical.
- MUST NOT: Assume the closed-network edition supports SAML federation with an
  external IdP, Voice Chat, or AgentCore Chat — these are currently out of scope
  for that configuration.

### Key Components

#### Frontend Web Application

- **Component Overview**: Serves the GenU web UI. In the closed-network edition the
  static files are distributed by a load balancer and container tasks inside an
  isolated subnet instead of a CDN, keeping traffic within the VPC.
- **Assumed AWS Services**: Application Load Balancer, Amazon ECS Fargate, Amazon VPC
  (isolated subnet).

#### Authentication & Authorization

- **Component Overview**: Manages user sign-up, sign-in, and request authorization.
  In the closed environment a dedicated API Gateway proxy relays authentication
  requests to the Cognito User Pool, and a Lambda Authorizer validates JWT tokens.
- **Assumed AWS Services**: Amazon Cognito, Amazon API Gateway (Private API), AWS
  Lambda (Lambda Authorizer).

#### Backend API & Application Logic

- **Component Overview**: Hosts the business logic for chat, generation,
  summarization, and related use cases, invoked from the frontend and interacting
  with data stores and Amazon Bedrock via VPC endpoints.
- **Assumed AWS Services**: Amazon API Gateway, AWS Lambda (VPC-attached).

#### Generative AI Inference & RAG

- **Component Overview**: Provides foundation-model inference and retrieval-augmented
  generation for knowledge search, plus speech and knowledge services used by GenU
  use cases. Access from Lambda is through VPC endpoints.
- **Assumed AWS Services**: Amazon Bedrock, Amazon Bedrock Knowledge Bases, Amazon
  Bedrock Agents, Amazon Kendra, Amazon Transcribe.

#### Output Control (Guardrails)

- **Component Overview**: Filters model input and output, blocking sensitive
  information and finance-specific denied topics; the hardened configuration adds
  Japanese support and finance topic filters.
- **Assumed AWS Services**: Amazon Bedrock Guardrails.

#### Data Persistence

- **Component Overview**: Stores chat history, system contexts, and generated
  artifacts; encrypted with KMS customer-managed keys and protected with PITR on
  DynamoDB tables.
- **Assumed AWS Services**: Amazon DynamoDB, Amazon S3, AWS KMS.

#### Speech & Media Services (frontend direct access)

- **Component Overview**: Supports speech-to-text and text-to-speech and media
  generation features accessible directly from the frontend through VPC endpoints.
- **Assumed AWS Services**: Amazon Transcribe, Amazon Polly, AWS Lambda (VPC-attached).

#### Network Connectivity

- **Component Overview**: Provides in-VPC name resolution and private connectivity to
  AWS services so the closed-network edition avoids internet egress.
- **Assumed AWS Services**: Amazon VPC, Route 53 Resolver endpoint, Interface VPC
  endpoints, Gateway VPC endpoints.

#### Monitoring & Audit

- **Component Overview**: Visualizes usage and cost and records operation and model
  invocation logs for audit; a dashboard surfaces token usage, invocation counts,
  sign-ins, and prompt logs.
- **Assumed AWS Services**: Amazon CloudWatch (dashboard, Logs), AWS CloudTrail, VPC
  Flow Logs.

## FISC Compliance Summary

This asset is mapped against the **FISC Safety Standards (第13版, 13th edition)**
practical standards (実務基準). The mapping table records, per standard number,
the controls provided by the common governance-base template, the controls
provided by this GenAI workload template, and additional considerations for the
user. Only measures addressed by BLEA for FSI are listed; overall system safety
must also consider the user application implementation and operational/development
processes.

Representative GenAI-side controls include: user protection via Amazon Cognito
(実1); restriction of client communication to a closed network (実2, 実4, 実34);
IAM-based access control plus AWS KMS encryption for S3/DynamoDB (実3, 実13, 実30);
CloudWatch Logs and VPC Flow Logs (実10, 実72); CDK-managed configuration with
DynamoDB PITR enabled (実39, 実42); Amazon Bedrock Guardrails for content
filtering (実69, 実152); and CloudWatch dashboard monitoring plus CloudTrail
auditing for AI-usage governance (実151, 実152). Several standards are marked out
of scope because they concern financial-transaction services, management/operation
processes, development processes, or are already handled on the AWS cloud side.

The complete, unabridged table (every 実N entry) is preserved in
`references/fisc-mapping.md`.

## Reference Architecture

The closed-network architecture runs entirely inside an Amazon VPC. A browser in
an isolated subnet reaches the frontend (Application Load Balancer + Amazon ECS
Fargate); AWS Lambda functions and the frontend reach AWS services (Amazon
DynamoDB and Amazon S3 via Gateway VPC endpoints; Amazon Bedrock, Amazon
Transcribe, Amazon Polly, Amazon Cognito, Amazon Kendra, and others via Interface
VPC endpoints); authentication is proxied through an Amazon API Gateway Private
API to Amazon Cognito; and a Route 53 Resolver endpoint provides in-VPC name
resolution.

See `assets/images/arch.png` for the diagram and `references/architecture.md` for
the full technical detail (features, security hardening, architectural
characteristics, and closed-network feature limitations).

## CDK Sample Overview

No CDK sample is provided for this asset in BLEA for FSI v1.6; this asset is
documentation only.

The BLEA for FSI repository does not contain a CDK application for this workload.
Instead, the sample is realized by cloning the external AWS Samples GenU
repository at a specific commit and applying a customization patch
(`changes.diff`) shipped in the source documentation. The deployment procedure
(clone/patch/build/deploy of the external GenU project, Bedrock model-invocation
logging setup, and verification) is captured, for reference, in
`references/deployment.md`. The actual CDK code being deployed lives in the
external GenU repository, not in this asset.
