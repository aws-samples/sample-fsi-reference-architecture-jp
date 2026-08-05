---
name: fsi-insurance-analytics
description: >-
  Reference architecture case study for an insurance (保険 / 保険業) data analytics
  platform on AWS, based on real-world insurers (New York Life, Sun Life). Covers
  a lake house built on Amazon S3 and Amazon Redshift, a metadata-driven ingestion
  framework using Amazon Aurora and AWS Glue, Redshift Data Sharing for compute
  separation, and a micro-account strategy for PII/PHI isolation. Use this skill
  when designing or reviewing an insurance data platform, analytics workload, or
  multi-account data pipeline on AWS, or when answering questions about 保険ワークロード
  のデータ分析基盤, データレイク, レイクハウス, PII/PHI 保護, or マルチアカウント戦略 in the FSI reference
  architecture.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# Insurance Workload: Data Analytics Platform

## Workload Overview

This case study describes a reference architecture for an **insurance data
analytics platform** on AWS. It is modeled on the architecture of a data
analytics platform currently operated by real insurance companies, referencing
the data-processing and security requirements typical of insurance workloads.
Published examples of insurers running insurance-workload data analytics
platforms include **New York Life** and **Sun Life**.

**Purpose.** The architecture builds a data platform that realizes the data
processing required for insurance operations efficiently and economically. It
provides an analytics foundation that supports the delivery of diverse services
to agents and policyholders.

**Current challenges (business drivers).** The insurer's existing on-premises
data platform faces insufficient processing capacity and escalating cost due to a
rapid increase in data volume. Functional constraints of the legacy system make it
unable to respond to increasingly diverse user needs. Security boundaries are
ambiguous, making it difficult to satisfy compliance requirements, and failures or
changes at each processing stage risk impacting other systems.

**What the architecture aims to achieve.** Four goals:

- **Cost-efficient scalability** — automatically scale resources up and down in
  response to data-volume fluctuation, realizing a pay-as-you-go model that pays
  only for what is needed when it is needed.
- **High-performance data processing** — provide processing capacity that handles
  high-speed processing of large data volumes and concurrent access from multiple
  users.
- **High availability** — achieve redundancy so business can continue even during
  system failures.
- **Strengthened security and governance** — clarify security boundaries, address
  compliance requirements, strengthen separation of duties and governance, and
  ensure operational independence so that failures or changes at each processing
  stage do not affect others, with appropriate access control and privilege
  management by role (data engineers, analysts, security teams, etc.).

## Best Practices and Key Components

### Best Practices

- SHOULD: Center the data platform on an integrated data lake so that ingestion
  through analytics of policyholder information, health information, and financial
  data for insurance operations is systematized on the cloud.
- SHOULD: Adopt managed services with auto-scaling and a pay-as-you-go model tied
  to data-volume fluctuation to achieve cost-efficient scalability and resolve the
  fixed-cost and over-provisioning problems of on-premises environments.
- SHOULD: Combine a data lake and data warehouse into an integrated processing
  foundation to handle high-speed processing of large data volumes and concurrent
  access from multiple users; run automated ETL/ELT pipelines with parallel
  execution of data transformation.
- SHOULD: Achieve redundancy for business continuity through automatic replication
  of the data lake, multi-node cluster configuration, and automatic job retry.
- MUST: Introduce a multi-account strategy so that ingestion, data lake,
  transformation, data warehouse, and analytics are each executed in separated
  accounts, incorporating PII/PHI tokenization, account isolation, and
  least-privilege access control to satisfy insurance-industry data privacy and
  regulatory requirements.
- SHOULD: Use an Amazon Aurora metadata repository together with an AWS Glue
  framework so that Glue jobs are auto-generated according to the pattern of the
  data source, eliminating point-to-point per-source ingestion solutions and
  enabling efficient ingestion from 100+ heterogeneous sources.
- SHOULD: Use Amazon Redshift Data Sharing to fully separate ETL/ELT processing
  from analytics processing, providing data scientists a serverless cluster with
  safe access to production data while avoiding performance contention.
- MUST: Land data in the landing bucket in exactly the same state as the source
  system and perform no transformation there; run standardization and PII/PHI
  tokenization only in the unified pipeline afterward.
- MUST: Store only changed, standardized, and tokenized data in the Raw bucket of
  the ingestion account before applying changes to the data lake account.
- SHOULD: Grant least-privilege, role-specific permissions — the data-acquisition
  layer gets write-only access to the landing bucket and the processing layer gets
  read-only access — and use trust-policy-based cross-account access to enable
  rapid isolation on compromise.
- MUST: Apply least-privilege IAM role-based cross-account access so that resources
  are accessible only from specific accounts with an established trust relationship.
- SHOULD: Store sensitive information encrypted in AWS Secrets Manager and AWS
  Systems Manager Parameter Store (SecureString), with key management by AWS KMS.
- SHOULD: Audit all API calls with AWS CloudTrail and track resource configuration
  changes with AWS Config.
- MAY: Use the Detect PII transform in an AWS Glue Studio visual ETL job to
  automatically detect personal information (configuring detection patterns,
  thresholds, and sampling rate) and mask sensitive data; combine with AWS Glue
  DataBrew recipes for date-format conversion, and use AWS Glue regex to create
  Japanese-capable sensitive-data detection entities.
- MAY: Build a generic ingestion framework for structured and unstructured data
  from sources such as Salesforce, Adobe, and SharePoint.
- SHOULD: Migrate eligible tables from Parquet to Apache Iceberg where it yields
  benefits (identified for 1,200–1,400 of roughly 4,000 tables).
- WILL: Converting about 500 tables to Iceberg achieved a 25–40% performance
  improvement for update and write processing.
- MAY: Defer building a full disaster-recovery (DR) environment for analytics and
  reporting workloads when several hours of downtime is acceptable, relying on S3
  durability and Multi-AZ placement, and implement DR incrementally later as
  business requirements change.

### Key Components

#### Data Lake

- **Component Overview**: The central store of the lake house. Ingests data from
  roughly 100 heterogeneous sources and provides 99.999999999% (11 nines)
  durability and virtually unlimited scalability, suited to the 30–40 year
  long-term data retention required in insurance. The data lake account is the
  first layer where end users consume data, maintaining 30–40 years of
  policyholder history as Type 2 (history-retaining) slowly changing dimensions.
- **Assumed AWS Services**: Amazon S3, AWS Lake Formation.

#### Metadata Repository and Ingestion Framework

- **Component Overview**: A unified, metadata-driven ingestion framework. The main
  metadata repository stores source patterns; loading metadata auto-generates
  Glue jobs, eliminating point-to-point ingestion and enabling efficient ingestion
  from 100+ sources (SFTP, DMS, CDC, message-based, etc.).
- **Assumed AWS Services**: Amazon Aurora, AWS Glue, AWS Lambda.

#### ETL/ELT and Transformation

- **Component Overview**: Automated transformation pipelines. In the unified
  pipeline: (1) proprietary delta detection, (2) standardization (datetime format,
  address doctor calls), and (3) PII/PHI tokenization via a 3rd-party service.
  Optional PII detection and masking can use the AWS Glue Studio Detect PII
  transform and AWS Glue DataBrew recipes.
- **Assumed AWS Services**: AWS Glue (jobs, Studio, DataBrew), AWS Lambda, AWS Step
  Functions, 3rd-party tokenization service.

#### Data Warehouse

- **Component Overview**: Compute-separated warehouse using Redshift Data Sharing.
  The main provisioned cluster runs ETL/ELT processing and shares production data
  with serverless clusters for data scientists and analysts, avoiding performance
  contention. Permission management is implemented with AWS Lake Formation and
  Redshift external tables.
- **Assumed AWS Services**: Amazon Redshift (provisioned + serverless), Amazon
  Redshift Data Sharing, Amazon Redshift Spectrum, AWS Lake Formation.

#### Analytics and Reporting

- **Component Overview**: Analytics layer consuming shared production data for
  reporting and data-science use, isolated from ETL/ELT compute.
- **Assumed AWS Services**: Amazon Athena, Amazon QuickSight, Amazon Redshift
  (serverless).

#### Multi-Account Security and Governance

- **Component Overview**: A Well-Architected micro-account strategy that separates
  every data-pipeline stage into dedicated accounts, achieving complete PII/PHI
  isolation. Role-specific permissions (write-only for acquisition, read-only for
  processing) and trust-policy cross-account access enable rapid isolation on
  compromise. Sensitive information is encrypted and audited.
- **Assumed AWS Services**: AWS IAM (roles, trust policies, cross-account access),
  AWS Secrets Manager, AWS Systems Manager Parameter Store, AWS KMS, AWS
  CloudTrail, AWS Config, AWS Organizations.

## FISC Compliance Summary

No dedicated FISC mapping file is provided for this case study, and the source
document does not include an explicit mapping to specific FISC Security Guideline
control numbers. The source addresses regulatory and compliance concerns only at
the level of general requirements for the insurance industry:

- Insurance-industry-specific data privacy requirements and regulatory compliance
  are cited as the reason for the multi-account strategy, PII/PHI tokenization,
  account isolation, and least-privilege access control.
- Clarifying ambiguous security boundaries, strengthening separation of duties and
  governance, and ensuring operational independence are stated compliance-oriented
  drivers.
- No specific FISC control numbers, laws, or named standards beyond these general
  statements appear in the source. Do not infer further FISC mappings.

## Reference Architecture

The architecture migrates to a lake house built on an Amazon S3 data lake and
Amazon Redshift, ingesting data from roughly 100 heterogeneous sources and using
managed services (AWS Glue, AWS Lambda, Amazon Redshift, etc.). It is organized
around a metadata-driven ingestion framework, compute separation via Redshift Data
Sharing, and a security-focused multi-account (micro-account) structure that fully
isolates PII/PHI across the pipeline.

See `references/architecture.md` for full technical detail, including the ingestion
flow (landing → Raw → data lake), data-consumption layers, table/Iceberg figures,
permission and sensitive-data management, the "what was not implemented" (full DR)
decision, the FAQ, and the SCD Type reference. Architecture diagrams are in
`assets/images/` (`overview.png`, `reference-architecture.png`).

## CDK Sample Overview

No CDK sample is provided for this case study.
