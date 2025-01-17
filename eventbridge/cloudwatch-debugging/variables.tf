
variable "region" {
  description = "AWS region for resource creation"
  type        = string
  default     = "us-east-1"
}

variable "aws_account" {
  description = "AWS account ID for resource tagging"
  type        = string
}

variable "environment" {
  description = "Environment name for resource tagging"
  type        = string
  default     = "dev"
}
