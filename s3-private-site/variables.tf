variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
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

# Add missing variables for VPC
variable "vpc_id" {
  description = "Name of the VPC"
  type        = string
}

variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string

}

variable "private_hosted_zone_name" {
  description = "Name of the private hosted zone"
  type        = string
}

variable "private_subnets" {
  description = "Private subnet ids"
  type        = list(string)
}
