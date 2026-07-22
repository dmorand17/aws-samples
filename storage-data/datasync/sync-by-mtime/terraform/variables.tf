# variables.tf
variable "source_bucket_name" {
  type        = string
  description = "Name for the source S3 bucket"
}

variable "destination_bucket_name" {
  type        = string
  description = "Name for the destination S3 bucket"
}

# Optional variables with defaults
variable "region" {
  type        = string
  description = "AWS region"
  default     = "us-east-1" # Default region if not specified
}

variable "environment" {
  type        = string
  description = "Environment name (e.g., dev, prod)"
  default     = "dev"
}
