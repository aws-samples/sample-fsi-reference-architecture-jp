---
name: fsi-foundation-analytics-platform
description: >-
  Reference architecture for a financial-grade Analytics Platform (データ分析プラットフォーム)
  built as a Simple data lake on AWS. It centers on an Amazon S3 data lake with a
  three-layer (raw / normalized / analytics) data placement, serverless ETL with
  AWS Glue orchestrated by AWS Step Functions, querying via Amazon Athena, and
  visualization with Amazon QuickSight. Use this skill when designing, reviewing, or
  building a scalable, cost-optimized, FISC-aligned data analytics foundation for a
  Japanese financial institution — keywords: データ分析プラットフォーム, データレイク,
  data lake, Simple data lake, Glue, Athena, QuickSight, ETL, 3層構造, FISC.
license: MIT No Attribution
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# FSI Analytics Platform (Simple data lake)

## Workload Overview

In a business environment of rising uncertainty, data-driven decision making has
become critical, and the volume of data that enterprises handle is growing at an
unprecedented rate. AWS provides a broad range of analytics services that can be
combined to build a scalable data analytics foundation quickly.

This reference architecture presents a **Simple data lake** for building a
cost-optimized data analytics foundation that meets the security level required of
financial institutions while remaining flexible to future changes in requirements
and growth in usage scale. Its core is an **Amazon S3 data lake**, deliberately
separating the components that *store* data from the components that *process* data,
because the two follow different lifecycles: data on an analytics platform accrues
value over years, whereas the tools used to process data change as the internal and
external environment evolves.

The sample application models a fictional "AWS Bank": data from three core systems
(the account/ledger system, the customer system, and the internet banking system) is
ingested daily into the data lake, transformed through an ETL pipeline, and then made
available for analysis through a BI tool. The end-to-end flow can be observed all the
way to an internet-banking marketing dashboard in Amazon QuickSight.

Detail is progressively disclosed in `references/`. Start here, then load the
reference file relevant to your task.

## Best Practices and Key Components

### Best Practices

- MUST: Store the analytics platform's data on an Amazon S3 data lake, keeping the data-storage components separate from the data-processing components so that a consistent data repository can evolve independently of the processing tools.
- MUST: Place data in a three-layer structure — raw (original data), normalized (standardized data), and analytics (purpose-built data) — to preserve future usability, promote utilization, and establish clear governance/management boundaries between areas.
- MUST: Keep the raw layer as an unmodified copy of source-system data, accessible in principle only to analytics-platform administrators, so future changes in use cases can still be served.
- MUST: In the normalized layer, apply common preprocessing (name matching, date-format unification), partitioning for query efficiency, and masking of sensitive/personal information so the data can be broadly published to analytics-platform users after sanitization.
- MUST: Manage access to each layer's S3 bucket with IAM, and assign appropriate IAM permissions per persona (analytics-platform administrator, data analyst, business user) to secure the platform.
- MUST: Encrypt Amazon S3 data with AWS KMS customer managed keys (CMK), and encrypt Glue Data Catalog objects.
- MUST: Run Glue Jobs inside a VPC that has no Internet Gateway (isolated/private subnets), restricting the reachable network space, and reach S3 and other resources only via VPC Endpoints.
- MUST: Manage metadata (data source location, format, schema) in the AWS Glue Data Catalog so ETL processing and query engines have a simplified implementation and configuration when accessing data.
- MUST: Encrypt the Athena WorkGroup query results (SSE-KMS) and enforce the WorkGroup configuration so query output is protected.
- SHOULD: Use serverless distributed processing — AWS Glue Spark Jobs for ETL and Amazon Athena as the query engine — so terabyte-scale data is processed efficiently and resources are consumed only when needed, keeping cost optimal from small-start to long-term growth.
- SHOULD: Restrict the QuickSight-accessible user environment using QuickSight IP address restrictions, and authenticate QuickSight users via IAM (and SAML-federated IdP with password rules).
- SHOULD: Grant BI (QuickSight) users access only to standardized data in the data lake — the analytics layer is referenceable while the raw layer is not.
- SHOULD: Grant only least-privilege IAM permissions, and access resources using the temporary credentials of IAM roles.
- SHOULD: Use only the standard libraries provided by AWS Glue; if external libraries are used in a Glue Job, manage that library's version.
- SHOULD: Manage the Glue Job Python code on an S3 bucket, and consider CodeCommit if source-control is required.
- PREFER: Adopt the three layers as an initial proposal; for larger organizations or specific requirements, consider a more finely subdivided hierarchy.
- PREFER: For large-scale governance, use attribute-based access strategies such as resource-tag ABAC or AWS Lake Formation LF-Tags for more scalable control instead of purely resource-based IAM.
- MAY: To expose sensitive data to only a subset of users in the normalized/analytics layers, use dedicated tables plus access permissions, or Amazon Redshift dynamic data masking, or AWS Lake Formation row-/column-level access control.
- MAY: Consider backing up data to another Region depending on the necessity, in addition to S3-based data retention.
- WILL: The Step Functions state machine that orchestrates the Glue Jobs is scheduled by EventBridge to run daily; during a run some tasks may transiently fail (status `TaskFailed`) and are automatically retried so that all jobs eventually succeed.
- WILL: The architecture is resilient to AZ failure, but in a large-scale failure a decision is required on whether to wait for service recovery or fail over to a secondary Region.
- MUST: Apply cdk-nag's AwsSolutionsChecks (via Aspects) to every CDK stack built from this skill, and gate CI (jest etc.) on zero unsuppressed AwsSolutions-* findings; suppress exceptions only with an explicit reason via NagSuppressions (see references/cdk-nag.md).

### Key Components

#### Data Lake Storage (Amazon S3)

- **Component Overview**: The core of the platform. Separate S3 buckets hold each data placement layer (origin/raw, normalized, analytics) plus master data and the Athena query-result output. Buckets are encrypted with an SSE-KMS CMK (except the Athena query-result bucket, which is encrypted at the Athena WorkGroup level). Provides high durability, cost efficiency, and scalability for parallel access.
- **Assumed AWS Services**: Amazon S3, AWS Key Management Service (KMS).

#### ETL Pipeline (AWS Glue + AWS Step Functions)

- **Component Overview**: Serverless ETL that transforms data received in the origin/raw layer → normalized layer → analytics layer. Glue Spark Jobs implement the transformations; a Step Functions state machine (`glue-job-pipeline`) orchestrates them in parallel stages and retries failed tasks. The pipeline is triggered daily by an EventBridge Schedule and accepts an `import_date` input (`all` or `YYYYMMDD`) for full vs. incremental processing.
- **Assumed AWS Services**: AWS Glue (Spark Jobs), AWS Step Functions, Amazon EventBridge (Scheduler), Amazon CloudWatch (Logs, Alarms), Amazon SNS.

#### Metadata & Query Engine (Glue Data Catalog + Amazon Athena)

- **Component Overview**: The Glue Data Catalog manages metadata (source location, format, schema) across the origin/raw/normalized/analytics/master databases. Amazon Athena queries the data lake via an Athena WorkGroup whose query results are encrypted with SSE-KMS; both Glue and Athena scale out to process very large data sets efficiently and serverlessly.
- **Assumed AWS Services**: AWS Glue Data Catalog, Amazon Athena.

#### Network Isolation (Private VPC + VPC Endpoints)

- **Component Overview**: Glue Jobs run on a VPC with private/isolated subnets across 2 AZs, no Internet Gateway, and VPC Flow Logs enabled. Access to AWS services (Amazon S3, AWS KMS, AWS Glue) is via VPC Endpoints. A self-referencing security group is used for the Glue connection.
- **Assumed AWS Services**: Amazon VPC, VPC Endpoints (S3 Gateway, KMS, Glue), VPC Flow Logs, Security Groups.

#### Visualization / BI (Amazon QuickSight)

- **Component Overview**: A marketing dashboard for AWS Bank's internet banking, built on the normalized and analytics layers via an Athena data source. Data is imported into SPICE, and the QuickSight service role is granted access to Athena and the relevant S3 buckets. Access is controlled with IAM authentication and IP address restrictions.
- **Assumed AWS Services**: Amazon QuickSight (Enterprise edition, SPICE), Amazon Athena, IAM.

## FISC Compliance Summary

This reference architecture is mapped against the practical standards (実務基準) of the
FISC Security Guidelines (安全対策基準), 11th edition. Only measures covered by BLEA for
FSI are recorded; overall system safety must additionally be considered together with
the user application implementation and the operations/development processes.

Representative applicable measures include: protection of access users via QuickSight
authentication (実1); QuickSight IP-address restriction (実2); KMS encryption of S3
data and Glue Data Catalog objects, and IAM-based access control (実3); Glue Jobs in a
private subnet reached via VPC Endpoints (実4); access logging to CloudWatch Logs /
CloudTrail / S3 access logs / VPC Flow Logs, all timestamped in UTC (実10); protection
of the encryption key via KMS CMK (実13); least-privilege IAM and BI use of only
standardized data (実25); IaC backup of configuration via AWS CDK (実39, 実42); and use
of AWS managed services with AZ-failure resilience (実84). Many measures are marked
"out of scope" because they are handled by the governance base, the user application,
the management/operations process, or already covered on the AWS cloud side.

The full, entry-by-entry mapping table (実1–実148) is preserved in
`references/fisc-mapping.md`.

## Reference Architecture

The architecture centers on an Amazon S3 data lake with three-layer data placement,
serverless ETL (Glue + Step Functions), Glue Data Catalog for schema management,
Athena for querying, and QuickSight for visualization, with Glue Jobs running in a
closed (Internet-Gateway-less) VPC reached only via VPC Endpoints.

Full technical detail — layer definitions, personas & access control, data lifecycle,
closed-network execution, schema management, and scalability — is in
`references/architecture.md`. The sample application's data model, ETL processing, and
schemas are documented in `references/application-data.md`, and the sample data schema
is captured in `references/sample-data-schema.md`.

Architecture diagram (S3-core Simple data lake):

![Architecture](assets/images/analitics-app-data-fig030.PNG)

## CDK Sample Overview

A working AWS CDK (TypeScript) sample is provided under `assets/sample-cdk/`
(`usecases/guest-analytics-platform-sample`). It deploys the DataLake components:
VPC, S3 buckets, AWS Glue Jobs, Athena WorkGroup, Step Functions state machine, and an
EventBridge Schedule. It is deployed onto an account where the BLEA for FSI governance
base is already in place. After the stack deploys, a QuickSight sample application
(data source, data set, and analysis) is set up via AWS CLI, and Glue Jobs are run
through the Step Functions state machine to validate the pipeline end-to-end.

> **Sample app security notice**: this sample is a reference/functional demo, not
> production-ready. The Glue ETL scripts use `reverse()` for PII "masking" (CIF /
> account numbers), which is trivially reversible and propagates to the
> BI-readable normalized/analytics layers, and the ETL deletes S3 prefixes
> unconditionally. Replace `reverse()` with hashing/tokenization/Lake Formation
> and add target allow-listing plus S3 versioning/backup before running against
> real data. The same notice ships as `assets/sample-cdk/SECURITY_NOTICE.md` and
> is printed as a warning on every `cdk synth` / `cdk deploy`.

Detailed deployment and operational-validation steps, including QuickSight setup and
troubleshooting, are in `references/deployment.md`.

The copied `assets/sample-cdk/test/*.test.ts` is the authoritative source of the
cdk-nag enforcement pattern; the extracted suppression ledger is in
`references/cdk-nag.md`.
