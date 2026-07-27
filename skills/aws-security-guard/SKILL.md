---
name: aws-security-guard
description: >
  Pre-execution security guard for AWS operations. Detects security risks before executing
  AWS CLI commands, IaC code (CloudFormation/Terraform/CDK), or AWS resource creation/modification/deletion,
  and presents warnings with reasons and alternatives.
  Trigger keywords: "AWS resource creation", "AWS CLI", "CloudFormation", "Terraform", "CDK",
  "S3 bucket", "security group", "IAM policy", "RDS", "EC2",
  "AWSリソース作成", "セキュリティグループ", "IAMポリシー".
license: MIT No Attribution
compatibility: No external dependencies. Works with prompt logic only.
metadata:
  author: aws-jp-fsi-sa
  version: "1.0"
---

# AWS Security Guard

## When to use this skill

Use this skill when the user requests:
- AWS resource creation, modification, or deletion
- AWS CLI command execution
- IaC code generation or application (CloudFormation/Terraform/CDK)

## Workflow

### Step 1: Analyze the operation intent

Identify from the user's request:
- Target AWS service
- Operation type (create/modify/delete)
- Scope of affected resources
- Data sensitivity level (PII, payment data, confidential data)

### Step 2: Evaluate security risks

Evaluate risks across the following categories:

**1. Network Exposure** [Critical/High]
- Public access (0.0.0.0/0 inbound, internet-facing)
- Default SG with all ports open, overly permissive NACLs
- Unrestricted VPC peering/Transit Gateway routing
- Direct SSH/RDP exposure (no bastion/SSM)
- Auto-assign public IP on EC2/ECS/EKS
- Subnet auto-assign public IP enabled
- IMDSv2 not enforced (IMDSv1 allowed)

**2. IAM & Authentication** [Critical]
- AdministratorAccess/PowerUserAccess grants
- Wildcard (*) resource policies
- Console access without MFA
- Root account access key creation/usage
- Cross-account AssumeRole without external ID
- IAM policies attached directly to users (not via groups/roles)
- Policies allowing decryption actions on all KMS keys

**3. Encryption & Key Management** [High]
- No encryption at rest (EBS/RDS/S3/EFS/DynamoDB/Kinesis/SQS/OpenSearch/Redshift)
- No encryption in transit (SSL/TLS not enforced)
- KMS key rotation disabled
- Wildcard/public access in KMS key policies
- Plaintext secret management without Secrets Manager
- Secret auto-rotation not configured

**4. Data Protection & Sharing** [Critical]
- S3 bucket public access (Block Public Access disabled)
- Wildcard Principal in S3 bucket policies
- Public EBS snapshots/AMIs
- Public RDS/DocumentDB/Neptune snapshots
- Versioning disabled, MFA Delete not set
- SSM documents shared publicly
- SNS/SQS policies allowing public access

**5. Logging & Audit** [High]
- CloudTrail disabled/deleted
- Multi-region CloudTrail not configured
- CloudTrail log file integrity validation disabled
- S3 server access logging not configured
- VPC Flow Logs disabled
- ALB/CLB access logging not configured
- API Gateway execution logging not configured
- RDS/Aurora audit logs not sent to CloudWatch

**6. Availability & Resilience** [Medium/High]
- Single-AZ in production
- No backup/insufficient retention
- Deletion protection disabled
- Auto Scaling with single instance type/single AZ
- CloudFormation stack termination protection disabled

**7. Container & Serverless** [High]
- ECR image scanning not configured
- ECR tag immutability not configured
- Plaintext secrets in Lambda environment variables (Secrets Manager not used)
- Excessive ECS task role permissions
- ECS containers running as root/privileged mode
- ECS container root filesystem writable
- ECS task definition sharing host process namespace
- Public Lambda function URL without authentication
- Lambda function using unsupported runtime

**8. Database** [High/Critical]
- RDS/Aurora public access enabled
- RDS SSL/TLS not enforced
- RDS using default port
- RDS using default administrator username
- RDS IAM authentication not configured
- RDS placed in public subnet (with IGW route)
- DynamoDB point-in-time recovery disabled
- ElastiCache without authentication/encryption/using default subnet group
- OpenSearch/Elasticsearch public access, fine-grained access control not enabled
- Redshift using default admin username, Enhanced VPC routing not enabled

**9. API & Endpoints** [High]
- API Gateway endpoints without authentication
- API Gateway cache data not encrypted
- CloudFront allowing HTTP (HTTPS not enforced)
- CloudFront not using OAC (using OAI or direct S3 access)
- CloudFront using deprecated TLS policy/SSL protocols
- Public API/CloudFront without WAF
- ALB not redirecting HTTP to HTTPS
- Wildcard CORS origin
- Transfer Family using FTP protocol (not SFTP/FTPS)



### Step 3: Output format

Severity levels:
- **Critical**: Immediate serious incident risk (data leak, global exposure, root account operations)
- **High**: Exploitable by attackers (missing encryption, excessive permissions, lost audit trail)
- **Medium**: Operational issues (availability risk, cost explosion, best practice deviation)
- **Low**: Differences from recommended settings, optimization opportunities

When risks are detected:

```
⚠️ Security Risk Detected

【Risk】[One-line risk summary]
【Reason】[Why this is dangerous, with reference to best practices]
【Impact】[Worst-case scenario if executed as-is]
【Severity】Critical / High / Medium / Low

✅ Alternative
[Propose an alternative that achieves the user's goal while maintaining security]

Proceed?
1. Execute with the alternative
2. Execute original operation acknowledging the risk
3. Cancel
```

When no risks are detected:
```
✅ Security check passed. No risks detected. Proceeding.
```

### Step 4: Respect user decisions

- If the user chooses "execute acknowledging risk", append the following log to `security-guard.log` then proceed:
- Never force-block. Provide information and support decision-making.
- Create the log file if it does not exist.

Log format:
```
[RISK ACCEPTED] [timestamp] | Severity: [Critical/High/Medium/Low] | Risk: [risk summary] | Operation: [summary of executed operation]
```




