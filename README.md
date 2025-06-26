# AWS Samples Repository

A comprehensive collection of AWS service samples, infrastructure templates, and deployment examples across various AWS services. This repository serves as a practical reference for implementing common AWS patterns and solutions.

## 🚀 Quick Start

Each sample directory contains its own README with specific deployment instructions. Browse the sections below to find the AWS service you're interested in.

## 📁 Repository Structure

### 🤖 AI/ML Services

#### [Amazon Q](./amazon-q/)

- **S3 for Q - Multiple Buckets**: CDK-based solution for enabling Amazon Q Business access to multiple S3 buckets with CloudFront distribution and metadata generation
- **S3 for Q - Single Bucket**: CloudFormation template for single bucket Amazon Q integration

#### [Amazon Bedrock](./bedrock/)

- **DeepSeek R1 8B**: Deployment example for DeepSeek R1 model on AWS Bedrock

#### [Amazon SageMaker](./cloudformation/sagemaker/)

- **Notebook Templates**: CloudFormation templates for SageMaker notebook instances

### 🏗️ Infrastructure & Compute

#### [Amazon EKS](./cloudformation/eks-setup/)

- **Complete EKS Setup**: Step-by-step CloudFormation templates for EKS cluster deployment
- **EKS Examples**: Additional EKS deployment examples and configurations

#### [AWS ParallelCluster](./parallelcluster/)

- **Open OnDemand Integration**: Scripts and configurations for AWS ParallelCluster with Open OnDemand integration
- **Munge Key Generation**: Automated Munge key creation for Slurm authentication

#### [Application Load Balancer](./alb-maintenance/)

- **Maintenance Window Management**: Automation scripts for ALB maintenance windows

#### [Network Load Balancer](./nlb/)

- **Encrypted Access Logs**: NLB configuration with encrypted access logging

### 🗄️ Storage & Data

#### [Amazon S3](./cloudformation/s3/)

- **Deployment Templates**: CloudFormation templates for S3 bucket deployment
- **Sample Templates**: Various S3 configuration examples

#### [Amazon DynamoDB](./dynamodb/)

- **Product Catalog**: Sample product catalog implementation with data loading scripts

#### [AWS DataSync](./datasync/)

- **Sync by Modification Time**: Terraform and CloudFormation examples for DataSync with modification time filtering

### 🔐 Security & Identity

#### [Keycloak](./cloudformation/keycloak/)

- **EC2 Deployment**: Keycloak deployment on EC2 instances
- **ECS Deployment**: Containerized Keycloak deployment
- **Infrastructure Setup**: Complete Keycloak infrastructure templates

#### [IAM](./cloudformation/iam/)

- **Role Creation Examples**: Sample IAM role creation templates

### 🔍 Search & Analytics

#### [Amazon OpenSearch](./cloudformation/opensearch/)

- **OpenSearch Examples**: Deployment templates and Terraform configurations

#### [Amazon Kendra](./cloudformation/kendra-index/)

- **GenAI Kendra Index**: CloudFormation template for Kendra index setup

### 📡 Networking

#### [VPC](./cloudformation/vpc/)

- **Network Templates**: VPC configuration examples
- **Default Security Groups**: Security group management templates

#### [Transit Gateway](./cloudformation/transit-gateway/)

- **TGW Configuration**: Transit Gateway setup templates

### 🔔 Event-Driven Architecture

#### [Amazon EventBridge](./eventbridge/)

- **CloudWatch Debugging**: Terraform setup for EventBridge with CloudWatch integration
- **SageMaker Canvas Events**: EventBridge integration with SageMaker Canvas

### 💰 Cost Management

#### [Budget Notifications](./budget-notification/)

- **Terraform Budget Setup**: Automated budget notification system with SNS integration

### 🛠️ Development Tools

#### [Custom Resources](./cloudformation/custom-resource/)

- **Q S3 Access**: Custom CloudFormation resource for Amazon Q S3 access

#### [Lambda](./cloudformation/translate-lambda-stack/)

- **Translation Service**: Lambda-based translation service with CloudFormation

### 🏷️ Resource Management

#### [Resource Tag Sync](./resource-tag-sync/)

- **Tag Synchronization**: Automated resource tagging solutions

## 🛠️ Infrastructure as Code

This repository includes examples using multiple IaC tools:

- **CloudFormation**: YAML and JSON templates
- **Terraform**: HCL configurations with S3 backend
- **AWS CDK**: TypeScript/Python infrastructure code
- **Shell Scripts**: Deployment and automation scripts

## 📋 Prerequisites

Most samples require:

- AWS CLI configured with appropriate credentials
- Python 3.x (for CDK and Python scripts)
- Terraform (for Terraform examples)
- Docker (for containerized solutions)

## 🚀 Getting Started

1. **Choose a sample** from the directory structure above
2. **Navigate to the sample directory** and read its README
3. **Follow the deployment instructions** specific to that sample
4. **Customize the configuration** for your environment

## 🔧 Common Patterns

### Environment Management

Many samples include environment-specific configurations:

- `environments/` directories for Terraform projects
- Environment-specific backend configurations
- Variable files for different deployment stages

### Security Best Practices

- IAM roles with least privilege
- Encrypted storage and communications
- Secrets management with AWS Secrets Manager
- Security group configurations

### Monitoring & Logging

- CloudWatch integration
- SNS notifications
- Structured logging
- Cost monitoring

## 🤝 Contributing

Contributions are welcome! Please:

1. Follow the existing directory structure
2. Include comprehensive README files
3. Add appropriate license headers
4. Test deployments before submitting

## 📄 License

This project is licensed under the MIT License - see individual sample directories for specific licensing information.

## 🆘 Support

For issues or questions:

1. Check the specific sample's README
2. Review AWS documentation for the service
3. Create an issue in this repository

---

**Note**: These samples are for educational and reference purposes. Always review and customize configurations for production use, following AWS best practices and your organization's security requirements.
