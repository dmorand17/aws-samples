# AWS Budget Notification

This Terraform configuration sets up an AWS budget notification system. It creates an SNS topic for budget alerts and configures a budget with notifications for actual and forecasted spend.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) installed
- AWS account with appropriate permissions
- S3 bucket for Terraform state management

## Configuration

1. Clone the repository:

   ```sh
   git clone https://github.com/your-repo/aws-samples.git
   cd aws-samples/budget-notification
   ```

2. Create an S3 bucket with versioning enabled for Terraform state management:

   ```sh
   BUCKET_NAME=tfstate-$(aws sts get-caller-identity --query Account --output text)
   aws s3api create-bucket \
    --bucket $BUCKET_NAME \
    --region $AWS_REGION || true
   aws s3api put-bucket-versioning --bucket $BUCKET_NAME --versioning-configuration Status=Enabled
   ```

3. Create a `terraform.tfvars` file inside the `environments/<env>` directory to specify your variables:

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
   ```

4. Create a `backend.config` file inside the `environments/<env>` directory to configure the backend:

   ```hcl
   bucket         = "your-s3-bucket-name"
   key            = "terraform/state/budget-notification.tfstate"
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

## Resources Created

- **SNS Topic**: `budget-alerts-topic` (if `create_sns_topic` is true)
- **Budget**: `monthly-cost-budget`
- **SNS Topic Subscription**: Email subscription to the SNS topic (if `create_sns_topic` is true)

## Notifications

- **Actual Spend Notification**: Sent when actual spend exceeds 100% of the budget.
- **Forecasted Spend Notification**: Sent when forecasted spend exceeds 100% of the budget.

## Cleanup

To remove the resources created by this configuration, run:

```sh
terraform destroy -var-file=environments/<env>/terraform.tfvars
```

## License

This project is licensed under the MIT License.
