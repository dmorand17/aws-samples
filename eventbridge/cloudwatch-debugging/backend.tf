terraform {
  backend "s3" {
    bucket       = "tfstate-lock"
    region       = "us-east-1"
    key          = "eventbridge-cloudwatch-debugging/terraform.tfstate"
    encrypt      = true
    use_lockfile = true
  }
}
