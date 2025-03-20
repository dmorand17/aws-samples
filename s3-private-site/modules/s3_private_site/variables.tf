variable "bucket_name" {
  description = "The name of the S3 bucket."
  type        = string
}

variable "private_hosted_zone_name" {
  description = "The name of the Route 53 private hosted zone."
  type        = string
}

variable "vpc_id" {
  description = "The ID of the VPC where the resources will be created."
  type        = string
}

variable "region" {
  description = "The AWS region."
  type        = string
}

variable "subnet_ids" {
  description = "The list of subnet IDs for the ALB."
  type        = list(string)
}
