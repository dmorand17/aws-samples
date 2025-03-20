output "s3_bucket_name" {
  description = "The name of the S3 bucket."
  value       = aws_s3_bucket.private_site.bucket
}

output "vpc_endpoint_security_group_id" {
  description = "The ID of the security group for the VPC Endpoint."
  value       = aws_security_group.vpc_endpoint_sg.id
}

output "vpc_endpoint_private_ips" {
  description = "The private IP addresses of the VPC endpoint."
  value       = [for eni in data.aws_network_interface.s3_vpc_endpoint_eni : eni.private_ip]
}

output "vpc_endpoint_id" {
  description = "The ID of the VPC endpoint."
  value       = aws_vpc_endpoint.s3_endpoint.id
}

# output "route53_record_name" {
#   description = "The Route 53 record name for the private site."
#   value       = aws_route53_record.private_site.name
# }

# output "private_hosted_zone_id" {
#   description = "The ID of the Route 53 private hosted zone."
#   value       = aws_route53_zone.private_hosted_zone.zone_id
# }

# output "acm_certificate_arn" {
#   description = "The ARN of the ACM certificate for the private hosted zone."
#   value       = aws_acm_certificate.private_site_cert.arn
# }

# output "alb_security_group_id" {
#   description = "The ID of the security group for the ALB."
#   value       = aws_security_group.alb_sg.id
# }

# output "alb_arn" {
#   description = "The ARN of the internal ALB."
#   value       = aws_lb.internal_alb.arn
# }


# output "alb_dns_name" {
#   description = "The DNS name of the internal ALB."
#   value       = aws_lb.internal_alb.dns_name
# }

