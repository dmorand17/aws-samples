# S3 Private Site Module

This Terraform module creates an S3 private site with the following components:

- An S3 bucket with a private ACL and a bucket policy restricting access via a VPC endpoint.
- An internal Application Load Balancer (ALB) to serve as the entry point for the site.
- A VPC endpoint for S3 to enable private connectivity.
- A Route 53 private hosted zone created dynamically and a record pointing to the ALB.
- A default `index.html` file for testing the setup.

## Usage

```hcl
module "s3_private_site" {
  source = "./modules/s3-private-site"

  bucket_name            = "my-private-site-bucket"
  private_hosted_zone_name = "example.com"
  vpc_id                 = "vpc-12345678"
  region                 = "us-east-1"
  alb_security_group_id  = "sg-12345678"
  subnet_ids             = ["subnet-12345678", "subnet-87654321"]
  vpc_endpoint_security_group_id = "sg-87654321"
}
```

## Inputs

| Name                             | Description                                            | Type           | Required |
| -------------------------------- | ------------------------------------------------------ | -------------- | -------- |
| `bucket_name`                    | The name of the S3 bucket.                             | `string`       | Yes      |
| `private_hosted_zone_name`       | The name of the Route 53 private hosted zone.          | `string`       | Yes      |
| `vpc_id`                         | The ID of the VPC where the resources will be created. | `string`       | Yes      |
| `region`                         | The AWS region.                                        | `string`       | Yes      |
| `alb_security_group_id`          | The security group ID for the ALB.                     | `string`       | Yes      |
| `subnet_ids`                     | The list of subnet IDs for the ALB.                    | `list(string)` | Yes      |
| `vpc_endpoint_security_group_id` | The security group ID for the VPC interface endpoint.  | `string`       | Yes      |

## Outputs

| Name                     | Description                                    |
| ------------------------ | ---------------------------------------------- |
| `s3_bucket_name`         | The name of the S3 bucket.                     |
| `alb_dns_name`           | The DNS name of the internal ALB.              |
| `route53_record_name`    | The Route 53 record name for the private site. |
| `private_hosted_zone_id` | The ID of the Route 53 private hosted zone.    |

## Deployment

1. Create an S3 bucket with versioning enabled for Terraform state management:

   ```sh
   BUCKET_NAME=tfstate-$(aws sts get-caller-identity --query Account --output text)
   aws s3api create-bucket \
    --bucket $BUCKET_NAME \
    --region $AWS_REGION || true
   aws s3api put-bucket-versioning --bucket $BUCKET_NAME --versioning-configuration Status=Enabled
   ```

2. Create a `terraform.tfvars` file inside the `environments/<env>` directory to specify your variables:

   ```hcl
   aws_region         = "us-east-1"
   budget_limit       = 3000
   notification_email = "your-email@example.com"
   create_sns_topic   = true

   tags = {
     environment = "<env>"
     project     = "budget-notification"
     managed-by  = "terraform"
     cost-center = "<env>-cost-center"
   }
   ...
   ```

3. Create a `backend.config` file inside the `environments/<env>` directory to configure the backend:

   ```hcl
   bucket         = "your-s3-bucket-name"
   key            = "<project>/terraform.tfstate"
   region         = "us-east-1"
   encrypt        = true
   use_lockfile   = true
   ```

## Usage

1. Initialize Terraform with the backend configuration:

   ```sh
   terraform init -backend-config=environments/<env>/backend.config
   ```

2. Apply the configuration:

   ```sh
   terraform apply -var-file=environments/<env>/terraform.tfvars
   ```

3. Confirm the apply step with `yes`.

## How to deploy files to s3 bucket

Example of how to copy files to the s3 bucket using terraform outputs

## Testing

Once the module is applied, you can test the setup by:

1. Accessing the ALB DNS name or the Route 53 record name from within the VPC.
2. You should see the default `index.html` content: "Welcome to the S3 Private Site".

## Notes

- Ensure that the ALB security group allows inbound traffic on port 80 from the appropriate sources.
- The S3 bucket policy restricts access to the bucket via the specified VPC endpoint only.

## License

This project is licensed under the MIT License.
