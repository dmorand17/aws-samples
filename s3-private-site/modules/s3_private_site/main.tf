# Fetch details of the existing VPC using its ID
data "aws_vpc" "vpc" {
  id = var.vpc_id
}

####################################
#             S3 Bucket            
####################################
resource "aws_s3_bucket" "private_site" {
  bucket = var.bucket_name
}

# Add bucket policy
resource "aws_s3_bucket_policy" "private_site" {
  bucket = aws_s3_bucket.private_site.id
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["s3:GetObject","s3:ListBucket"],
      "Resource": [
        "${aws_s3_bucket.private_site.arn}",
        "${aws_s3_bucket.private_site.arn}/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:sourceVpce": "${aws_vpc_endpoint.s3_endpoint.id}"
        }
      }
    }
  ]
}
EOF
}

####################################
# S3 Interface VPC Endpoint
####################################
resource "aws_security_group" "vpc_endpoint_sg" {
  name        = "vpc-endpoint-sg"
  description = "Security group for VPC Endpoint allowing access from ALB"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Allow HTTP traffic from ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  ingress {
    description     = "Allow HTTPS traffic from ALB"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_vpc_endpoint" "s3_endpoint" {
  vpc_id             = var.vpc_id
  service_name       = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type  = "Interface"
  security_group_ids = [aws_security_group.vpc_endpoint_sg.id]
  subnet_ids         = var.subnet_ids

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:*"
        Resource  = "*"
      }
    ]
  })
}

data "aws_vpc_endpoint" "s3_endpoint" {
  service_name = "com.amazonaws.${var.region}.s3"
  vpc_id       = var.vpc_id
}

data "aws_network_interface" "s3_vpc_endpoint_eni" {
  for_each = data.aws_vpc_endpoint.s3_endpoint.network_interface_ids
  id       = each.value
}

# Add endpoint policy to allow access to the S3 bucket
resource "aws_vpc_endpoint_policy" "s3_endpoint_policy" {
  vpc_endpoint_id = aws_vpc_endpoint.s3_endpoint.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:*"
        Resource  = [aws_s3_bucket.private_site.arn, "${aws_s3_bucket.private_site.arn}/*"]
      }
    ]
  })
}


####################################
#            Load Balancer
####################################

resource "aws_lb_target_group" "s3_http_target_group" {
  name        = "s3-private-site-target-group"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    protocol = "HTTP"
    path     = "/"
    port     = "80"
  }
}

resource "aws_lb_target_group_attachment" "s3_http_targets" {
  for_each         = data.aws_network_interface.s3_vpc_endpoint_eni
  target_group_arn = aws_lb_target_group.s3_http_target_group.arn
  target_id        = each.value.private_ip
  port             = 80
}

resource "aws_security_group" "alb_sg" {
  name        = "alb-sg"
  description = "Security group for ALB allowing access from VPC CIDR"
  vpc_id      = var.vpc_id

  ingress {
    description = "Allow HTTP traffic from VPC CIDR"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.vpc.cidr_block]
  }

  ingress {
    description = "Allow HTTPS traffic from VPC CIDR"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.vpc.cidr_block]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_lb" "internal_alb" {
  name               = "s3-internal-site-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = var.subnet_ids

}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.internal_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.s3_http_target_group.arn
  }
}
