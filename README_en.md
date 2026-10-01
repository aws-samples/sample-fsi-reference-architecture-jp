# FSI Reference Architecture JP

> \[[日本語 (JA)](README.md)\]

We provide best practices, knowledge, and tools related to the **security, availability, and compliance** required by financial systems, as assets centered on **Agent Skills**. This offering presents concrete guidance for designing, building, and operating financial workloads—such as banking, insurance, and cashless payments—on the AWS Cloud.

## What is the FSI Reference Architecture JP / Overview

The FSI Reference Architecture JP is a set of assets that help maintain and strengthen the "mission-critical domains that require high reliability" of financial systems. It consists of content that supports the work of engineers at Japanese financial institutions in areas such as ensuring security and governance, strengthening resiliency, accelerating modernization, and addressing compliance.

<p align="center">
  <img src="documents/images/root-readme/overview.png" alt="Overview of the FSI Reference Architecture JP" width="720">
</p>

### Intended Users

- **Engineers**, **architects**, and **developers** involved in business or IT systems in the financial domain
- The **AI agents** and **generative AI tools** used by them

### Intended Use Cases

- Architecting, designing, implementing, and operating systems that use AWS services
- Day-to-day information gathering related to the AWS Cloud

## Content Provided

### Agent Skills

Much of the content and knowledge provided by this asset is authored as **Agent Skills** (hereafter "Skills").
When AI agents use these Skills, they support the execution of tasks such as architecting financial workloads and gathering information. The Skills are organized by category, centered on financial workloads (business workloads / foundation & shared infrastructure / generative AI / security & resilience), and also include AWS service enablement, the AWS Well-Architected Framework FSI Lens for FISC, various information-gathering capabilities, business support, and general-purpose tools.

<p align="center">
  <img src="documents/images/root-readme/skills-overview.png" alt="Overview of the provided Skills" width="820">
</p>

For the list and overview of each Skill, please refer to the **[Skill Catalog (skills/README.md)](skills/README.md)**.

### AWS Well-Architected Framework FSI Lens for FISC

As an extension to the AWS Well-Architected (W-A) Framework Review, this is knowledge (a "**Lens**") that presents points to consider when designing and deploying workloads on AWS, centered on the practical standards of the "Security Guidelines on Computer Systems for Financial Institutions" published by the [FISC (The Center for Financial Industry Information Systems)](https://www.fisc.or.jp/).
This **Lens** is also authored as an Agent Skill and provided as knowledge that AI agents can use.

For details, please refer to [FSI Lens for FISC](skills/fsi-lens-for-fisc/SKILL_ja.md).

### GameDay Plan Generator

This is a tool that automatically generates a GameDay (failure response drill) execution plan from configuration information of an AWS Cloud environment (a CloudFormation template or an architecture diagram).

For details, please refer to the separate repository [GameDay Plan Generator](https://github.com/aws-samples/sample-fsi-reference-architecture-jp-gameday-plan-generator).

## Appendix: Types of Content and Their Contents

Each piece of content broadly provides one or more of the following types of content.

- **Agent Skills** (denoted as "Agent Skills" or simply "Skills")
  - Provides knowledge such as best practices and work steps as Agent Skills. This **extends the knowledge and capabilities** of users and their generative AI / AI agents, supporting the execution of their work and tasks.
    - Agent Skills is a format for providing agents with specific capabilities or expertise, and is an open standard.
    - Many AI agent tools, including [Kiro](https://kiro.dev/), support it.
    - For an overview and specification of Agent Skills, please refer to [https://agentskills.io/](https://agentskills.io/home).
- **Documents**
  - Some knowledge may be provided as documents rather than as "Agent Skills."
  - Examples: whitepapers, customer reference collections
- **Web Applications**
  - As content of the FSI Reference Architecture JP, we provide Web applications in addition to Agent Skills and documents.
  - These Web applications are provided in a repository separate from this GitHub repository.

## License

This library is licensed under the MIT-0 (MIT No Attribution) License. See the LICENSE file.
