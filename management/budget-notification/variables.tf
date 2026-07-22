variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "budget_limit" {
  description = "The budget limit in USD"
  type        = number
  default     = 3000
}

variable "budget_name" {
  description = "The name of the budget"
  type        = string
  default     = "monthly-budget"
}

variable "notification_email" {
  description = "Email address for budget notifications"
  type        = string
}

variable "create_sns_topic" {
  description = "Whether to create an SNS topic for budget alerts"
  type        = bool
  default     = true
}

variable "tags" {
  description = "A map of tags to assign to the resources"
  type        = map(string)
  default = {
    environment = "dev"
    project     = "budget-notification"
    managed-by  = "terraform"
    cost-center = "default-cost-center"
  }
}
