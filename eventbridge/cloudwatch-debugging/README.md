# Wait for Cloud Init Terraform Deployment

This README provides instructions for setting up and managing a Terraform project with an S3 backend configuration that includes state locking functionality.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform >= 1.0.0
- An AWS S3 bucket for storing state files
- An AWS DynamoDB table for state locking

## Backend Configuration Setup

1. First, create an S3 bucket for storing the Terraform state:

```bash
aws s3api create-bucket \
    --bucket tfstate-$(aws sts get-caller-identity --query Account --output text) \
    --region $AWS_REGION
```

2. Enable versioning on the S3 bucket:

```bash
aws s3api put-bucket-versioning \
    --bucket tfstate-$(aws sts get-caller-identity --query Account --output text) \
    --versioning-configuration Status=Enabled
```

## Backend Configuration

Create a `backend.tf` file with the following configuration:

```hcl
terraform {
  backend "s3" {
    bucket         = "your-terraform-state-bucket"
    key            = "terraform.tfstate"
    region         = "your-region"
    encrypt        = true
    use_lock_file  = true
  }
}
```

## Usage

1. Initialize Terraform:

```bash
terraform init

# OR

terraform init  -backend-config=./backend.config
```

2. Plan your changes:

```bash
terraform plan -out=tfplan
```

3. Apply the changes:

```bash
terraform apply tfplan
```

## Best Practices

1. Always use state locking to prevent concurrent modifications
2. Enable versioning on the S3 bucket for state file history
3. Use encryption for the state file
4. Implement appropriate IAM policies for the S3 bucket and DynamoDB table
5. Use workspaces for managing multiple environments

## IAM Policy Requirements

The following IAM permissions are required for the S3 backend:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket", "s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": ["arn:aws:s3:::your-terraform-state-bucket", "arn:aws:s3:::your-terraform-state-bucket/*"]
    }
  ]
}
```

## Troubleshooting

## Contributing

1. Create a new branch for your changes
2. Test your changes locally
3. Submit a pull request with a clear description of the changes

## Support

For issues or questions, please create an issue in the repository.
