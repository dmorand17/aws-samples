module "s3_private_site" {
  source = "./modules/s3_private_site"

  bucket_name              = var.bucket_name
  private_hosted_zone_name = var.private_hosted_zone_name
  vpc_id                   = var.vpc_id
  region                   = var.aws_region
  subnet_ids               = var.private_subnets
}

# Upload files to S3 bucket from www folder
resource "aws_s3_object" "object-upload-html" {
  bucket   = module.s3_private_site.s3_bucket_name
  for_each = fileset("www/", "*.html")

  key    = each.value
  source = "www/${each.value}"
}

resource "aws_s3_object" "object-upload-txt" {
  bucket   = module.s3_private_site.s3_bucket_name
  for_each = fileset("www/", "*.txt")

  key    = each.value
  source = "www/${each.value}"
}
