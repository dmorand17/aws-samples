# AWS Samples

A collection of self-contained AWS service samples, infrastructure templates, and
deployment examples spanning compute, storage, networking, security, AI/ML, and cost
management. Each sample is a practical, standalone reference for a common AWS pattern.

## 🚀 Quick start

Every sample lives in its own directory with its own README and deployment steps.

```bash
# 1. Pick a sample from the catalog below
cd security/ssm

# 2. Read its README, then deploy
aws cloudformation deploy \
  --template-file ssm-instance-profile.yaml \
  --stack-name ssm-instance-profile \
  --capabilities CAPABILITY_NAMED_IAM
```

## 📁 Samples

Samples are grouped by purpose into top-level category directories.

### AI / ML — [`ai-ml/`](./ai-ml/)

| Sample | Description | IaC |
|---|---|---|
| [amazon-q/s3-for-q-multiple-buckets](./ai-ml/amazon-q/s3-for-q-multiple-buckets/) | Amazon Q Business access to multiple S3 buckets with CloudFront and metadata generation | CDK (Python) |
| [amazon-q/s3-for-q-single-bucket](./ai-ml/amazon-q/s3-for-q-single-bucket/) | Single-bucket Amazon Q integration | CloudFormation |
| [bedrock/deepseek-r1-8B](./ai-ml/bedrock/deepseek-r1-8B/) | Import and test the DeepSeek R1 model on Amazon Bedrock | Python |
| [kendra-index](./ai-ml/kendra-index/) | GenAI Kendra index setup | CloudFormation |
| [sagemaker](./ai-ml/sagemaker/) | SageMaker notebook instance | CloudFormation |
| [translate-lambda-stack](./ai-ml/translate-lambda-stack/) | Lambda-based translation service | CloudFormation |

### Compute — [`compute/`](./compute/)

| Sample | Description | IaC |
|---|---|---|
| [eks-setup](./compute/eks-setup/) | Step-by-step EKS cluster (VPC, control plane, data plane) | CloudFormation + scripts |
| [eks-example](./compute/eks-example/) | Standalone EKS deployment example | CloudFormation |
| [macos](./compute/macos/) | macOS EC2 instance on a dedicated host | CloudFormation |
| [parallelcluster](./compute/parallelcluster/) | AWS ParallelCluster (Slurm) with Munge key generation; sample config wired to the basic-network VPC | Scripts + config |

### Networking — [`networking/`](./networking/)

| Sample | Description | IaC |
|---|---|---|
| [vpc](./networking/vpc/) | VPC with public/private subnets, regional NAT gateway, and gateway endpoints | CloudFormation |
| [transit-gateway](./networking/transit-gateway/) | Transit Gateway configuration | CloudFormation |
| [nlb](./networking/nlb/) | Network Load Balancer with encrypted access logs | CloudFormation |
| [alb-maintenance](./networking/alb-maintenance/) | ALB maintenance-window automation | Scripts |

### Storage & data — [`storage-data/`](./storage-data/)

| Sample | Description | IaC |
|---|---|---|
| [s3](./storage-data/s3/) | S3 bucket deployment templates | CloudFormation |
| [dynamodb/productcatalog](./storage-data/dynamodb/productcatalog/) | Product-catalog sample with data-loading scripts | Scripts + JSON |
| [datasync/sync-by-mtime](./storage-data/datasync/sync-by-mtime/) | DataSync filtered by modification time | Terraform + CloudFormation |

### Security & identity — [`security/`](./security/)

| Sample | Description | IaC |
|---|---|---|
| [keycloak](./security/keycloak/) | Keycloak on EC2 and ECS | CloudFormation |
| [iam](./security/iam/) | IAM role creation example | CloudFormation |
| [ssm](./security/ssm/) | IAM instance profile for Session Manager access (no SSH/bastion) | CloudFormation |

### Analytics — [`analytics/`](./analytics/)

| Sample | Description | IaC |
|---|---|---|
| [opensearch](./analytics/opensearch/) | OpenSearch domain example | CloudFormation |

### Messaging & events — [`messaging/`](./messaging/)

| Sample | Description | IaC |
|---|---|---|
| [eventbridge/cloudwatch-debugging](./messaging/eventbridge/cloudwatch-debugging/) | EventBridge to CloudWatch Logs debugging setup | Terraform |
| [eventbridge/sagemaker-canvas-events](./messaging/eventbridge/sagemaker-canvas-events/) | EventBridge integration with SageMaker Canvas | CloudFormation |

### Management & governance — [`management/`](./management/)

| Sample | Description | IaC |
|---|---|---|
| [budget-notification](./management/budget-notification/) | Budget notifications with SNS | Terraform |
| [custom-resource](./management/custom-resource/) | Custom resource enabling Amazon Q S3 access | CloudFormation |

## 📋 Prerequisites

- AWS CLI v2, configured with credentials for the target account
- Terraform (for Terraform samples)
- Python 3.12+ (for CDK and Python samples)
- Docker (for containerized samples)

## 📄 License

Licensed under the MIT License. Individual samples may include their own `LICENSE`
file — check the sample directory for specifics.

---

**Note:** These samples are for educational and reference purposes. Review and harden
configurations before production use, following AWS best practices and your
organization's security requirements.
