# Configure AWS Provider
provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Environment = "sandbox"
      cost-center = "111111"
      ManagedBy   = "Terraform"
    }
  }
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # This sets the version constraint to a minimum of 1.10 for native state file locking support
  required_version = "~> 1.10"
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

module "tf-state" {
  source      = "./modules/tf-state"
  bucket_name = "cc-tf-state-backend-ci-cd"
}

# Create an EventBridge rule
resource "aws_cloudwatch_event_rule" "all_events" {
  name        = "capture-all-events"
  description = "Capture all AWS events and send to CloudWatch"

  # This event pattern captures all events
  event_pattern = jsonencode({
    "account" : ["${data.aws_caller_identity.current.account_id}"]
  })
}

# Create a CloudWatch log group
resource "aws_cloudwatch_log_group" "events_log_group" {
  name              = "/aws/events/eventbridge-logs"
  retention_in_days = 7 # Adjust retention period as needed
}

# Create an IAM role for EventBridge
resource "aws_iam_role" "eventbridge_role" {
  name = "eventbridge-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })
}

# Create an IAM policy for writing to CloudWatch Logs
resource "aws_iam_role_policy" "eventbridge_policy" {
  name = "eventbridge-cloudwatch-policy"
  role = aws_iam_role.eventbridge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.events_log_group.arn}:*"
      }
    ]
  })
}

# Create the EventBridge target
resource "aws_cloudwatch_event_target" "cloudwatch_logs" {
  rule      = aws_cloudwatch_event_rule.all_events.name
  target_id = "SendToCloudWatch"
  arn       = aws_cloudwatch_log_group.events_log_group.arn
  # role_arn  = aws_iam_role.eventbridge_role.arn
}
