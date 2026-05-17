terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.4.0"
}

provider "aws" {
  region = var.aws_region
}

# Minimal S3 bucket for data/models
resource "aws_s3_bucket" "predicast_data" {
  bucket = var.s3_bucket_data
  acl    = "private"
  tags = {
    Name = "predicast-data"
    Environment = var.environment
  }
}

# Placeholders for RDS / ElastiCache / EKS - add modules or resources per project needs

output "s3_bucket_name" {
  value = aws_s3_bucket.predicast_data.id
}
