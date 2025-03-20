# S3 Private HTTP Site

This Terraform module creates a private HTTP S3 site with the following components:

- An S3 bucket with a private ACL and a bucket policy restricting access via a VPC endpoint.
- An internal Application Load Balancer (ALB) to serve as the entry point for the site.
- A VPC endpoint for S3 to enable private connectivity.
- A Route 53 private hosted zone created dynamically and a record pointing to the ALB.
- A default `index.html` file for testing the setup.

## Usage

```hcl
module "s3_private_site" {
  source = "./modules/s3-private-site"

  bucket_name              = "my-private-site-bucket"
  private_hosted_zone_name = "example.com"
  vpc_id                   = "vpc-12345678"
  region                   = "us-east-1"
  subnet_ids               = ["subnet-12345678", "subnet-87654321"]
}
```

## Inputs

| Name                       | Description                                            | Type           | Required |
| -------------------------- | ------------------------------------------------------ | -------------- | -------- |
| `bucket_name`              | The name of the S3 bucket.                             | `string`       | Yes      |
| `private_hosted_zone_name` | The name of the Route 53 private hosted zone.          | `string`       | Yes      |
| `vpc_id`                   | The ID of the VPC where the resources will be created. | `string`       | Yes      |
| `region`                   | The AWS region.                                        | `string`       | Yes      |
| `subnet_ids`               | The list of subnet IDs for the ALB.                    | `list(string)` | Yes      |

## Outputs

| Name                       | Description                                   |
| -------------------------- | --------------------------------------------- |
| `s3_bucket_name`           | The name of the S3 bucket.                    |
| `s3_endpoint_id`           | The ID of the VPC endpoint.                   |
| `vpc_endpoint_private_ips` | The private IP addresses of the VPC endpoint. |

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
   bucket_name        = "my-private-site-bucket"
   private_hosted_zone_name = "example.com"
   vpc_id             = "vpc-12345678"
   subnet_ids         = ["subnet-12345678", "subnet-87654321"]
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

## Testing

Once the module is applied, you can test the setup by:

1. Accessing the ALB DNS name or the Route 53 record name from within the VPC.
2. You should see the default `index.html` content: "Welcome to the S3 Private Site".

## Notes

- Ensure that the ALB security group allows inbound traffic on port 80 from the appropriate sources.
- The S3 bucket policy restricts access to the bucket via the specified VPC endpoint only.

## License

This project is licensed under the MIT License.
