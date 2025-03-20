####################################
#           Route53 PHZ
####################################

resource "aws_route53_zone" "private_hosted_zone" {
  name = var.private_hosted_zone_name
  vpc {
    vpc_id = var.vpc_id
  }

}

resource "aws_route53_record" "private_site" {
  zone_id = aws_route53_zone.private_hosted_zone.zone_id
  name    = "web"
  type    = "A"
  alias {
    name                   = aws_lb.internal_alb.dns_name
    zone_id                = aws_lb.internal_alb.zone_id
    evaluate_target_health = true
  }
}
