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
  # Configure the AWS Provider - region can be set via AWS_REGION env var
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Locals
# locals {
#   source_files            = fileset("${path.module}/source-files", "**/*")
#   source_bucket_name      = "${var.source_bucket_name}-${data.aws_caller_identity.current.account_id}"
#   destination_bucket_name = "${var.destination_bucket_name}-${data.aws_caller_identity.current.account_id}"
# }

# Source S3 bucket
resource "aws_s3_bucket" "source" {
  # Append the AWS Account at the end
  bucket = "${var.source_bucket_name}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "source" {
  bucket = aws_s3_bucket.source.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "source" {
  bucket = aws_s3_bucket.source.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Destination S3 bucket
resource "aws_s3_bucket" "destination" {
  bucket = "${var.destination_bucket_name}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "destination" {
  bucket = aws_s3_bucket.destination.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "destination" {
  bucket = aws_s3_bucket.destination.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Iterate over the files in source-files directory and add them to source s3 bucket
# resource "aws_s3_object" "source_files" {
#   for_each = fileset("${path.module}/source-files/", "*")
#   bucket   = aws_s3_bucket.source.id
#   key      = each.value
#   source   = "${path.module}/source-files/${each.value}"
#   etag     = filemd5("${path.module}/source-files/${each.value}")
# }

# Upload files to source bucket
resource "aws_s3_object" "source_files" {
  for_each = fileset("${path.module}/source-files/", "*")

  bucket = aws_s3_bucket.source.id
  key    = "src/${each.value}"
  source = "${path.module}/source-files/${each.value}"

  # Calculate ETag for each file to detect changes
  etag = filemd5("${path.module}/source-files/${each.value}")

  # # Automatically detect content type
  # content_type = lookup(local.mime_types, regex("\\.[^.]+$", each.value), null)
}

# IAM Role for DataSync
resource "aws_iam_role" "datasync" {
  name = "datasync-s3-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "datasync.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Attach AWS managed policy called AWSDataSyncFullAccess
resource "aws_iam_role_policy_attachment" "datasync" {
  role       = aws_iam_role.datasync.name
  policy_arn = "arn:aws:iam::aws:policy/AWSDataSyncFullAccess"
}


# Custom policy for S3 access
resource "aws_iam_role_policy" "s3_access" {
  name = "datasync-s3-bucket-access"
  role = aws_iam_role.datasync.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads"
        ]
        Resource = [
          aws_s3_bucket.source.arn,
          aws_s3_bucket.destination.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:AbortMultipartUpload",
          "s3:DeleteObject",
          "s3:GetObject",
          "s3:ListMultipartUploadParts",
          "s3:PutObject",
          "s3:GetObjectTagging",
          "s3:GetObjectAttributes",
          "s3:ReplicateObject"
        ]
        Resource = [
          "${aws_s3_bucket.source.arn}/*",
          "${aws_s3_bucket.destination.arn}/*"
        ]
      }
    ]
  })
}

# Outputs
output "source_bucket_name" {
  description = "Name of the source S3 bucket"
  value       = aws_s3_bucket.source.id
}

output "source_bucket_arn" {
  description = "ARN of the source S3 bucket"
  value       = aws_s3_bucket.source.arn
}

output "destination_bucket_name" {
  description = "Name of the destination S3 bucket"
  value       = aws_s3_bucket.destination.id
}

output "destination_bucket_arn" {
  description = "ARN of the destination S3 bucket"
  value       = aws_s3_bucket.destination.arn
}

output "datasync_role_arn" {
  description = "ARN of the IAM role for DataSync"
  value       = aws_iam_role.datasync.arn
}
