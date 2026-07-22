# main.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}



provider "aws" {
  region = var.aws_region

  # Add default tags to all resources
  default_tags {
    tags = var.tags
  }
}

data "aws_caller_identity" "current" {}

# SNS Topic for budget alerts
resource "aws_sns_topic" "budget_alerts" {
  name = "budget-alerts-topic"
}

resource "aws_sns_topic_policy" "budget_alerts_policy" {
  arn = aws_sns_topic.budget_alerts.arn
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        "Sid"  = "AllowBudgetServiceToPublish",
        Effect = "Allow",
        Principal = {
          Service = "budgets.amazonaws.com"
        },
        Action   = "SNS:Publish",
        Resource = aws_sns_topic.budget_alerts.arn,
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:budgets::${data.aws_caller_identity.current.account_id}:*"
          }
        }
      }
    ]
  })
}

# Budget definition
resource "aws_budgets_budget" "monthly_budget" {
  name         = var.budget_name
  budget_type  = "COST"
  limit_amount = var.budget_limit
  limit_unit   = "USD"

  # Budget is monthly and resets each month
  time_unit = "MONTHLY"

  # Start from the first day of the current month
  time_period_start = formatdate("YYYY-MM-01_00:00", timestamp())

  # No end date (ongoing budget)
  time_period_end = "2087-06-15_00:00"

  # Cost types configuration
  cost_types {
    include_credit             = false
    include_discount           = true
    include_other_subscription = true
    include_recurring          = true
    include_refund             = false
    include_subscription       = true
    include_support            = true
    include_tax                = true
    include_upfront            = true
    use_amortized              = false
    use_blended                = false
  }

  # Alert at 100% of actual spend
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    notification_type          = "ACTUAL"
    threshold_type             = "PERCENTAGE"
    subscriber_email_addresses = [var.notification_email]
  }

  # Alert when forecasted spend exceeds 100%
  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 75
    notification_type         = "FORECASTED"
    threshold_type            = "PERCENTAGE"
    subscriber_sns_topic_arns = [aws_sns_topic.budget_alerts.arn]
  }
}

# SNS Topic subscription for email notifications
resource "aws_sns_topic_subscription" "budget_email_subscription" {
  topic_arn = aws_sns_topic.budget_alerts.arn
  protocol  = "email"
  endpoint  = var.notification_email
}
