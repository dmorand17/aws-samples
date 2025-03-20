output "s3_bucket_name" {
  description = "The name of the S3 bucket."
  value       = module.s3_private_site.s3_bucket_name
}

# output "s3_endpoint_private_ips" {
#   description = "The private IP addresses of the VPC endpoint."
#   value       = module.s3_private_site.vpc_endpoint_private_ips
# }

output "s3_endpoint_id" {
  description = "The ID of the VPC endpoint."
  value       = module.s3_private_site.vpc_endpoint_id
}

output "vpc_endpoint_private_ips" {
  description = "The private IP addresses of the VPC endpoint."
  value       = module.s3_private_site.vpc_endpoint_private_ips
}

# output "alb_dns_name" {
#   description = "The DNS name of the internal ALB."
#   value       = module.s3_private_site.alb_dns_name
# }

# output "route53_record_name" {
#   description = "The Route 53 record name for the private site."
#   value       = module.s3_private_site.route53_record_name
# }

# output "private_hosted_zone_id" {
#   description = "The ID of the Route 53 private hosted zone."
#   value       = module.s3_private_site.private_hosted_zone_id
# }

