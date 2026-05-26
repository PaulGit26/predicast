variable "bucket_data_name" { type = string }
variable "bucket_models_name" { type = string }
variable "environment" { type = string }

resource "aws_s3_bucket" "data" {
  bucket        = var.bucket_data_name
  force_destroy = false
  tags          = { Name = var.bucket_data_name, Purpose = "datasets" }
}

resource "aws_s3_bucket" "models" {
  bucket        = var.bucket_models_name
  force_destroy = false
  tags          = { Name = var.bucket_models_name, Purpose = "ml-models" }
}

resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "models" {
  bucket = aws_s3_bucket.models.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "models" {
  bucket                  = aws_s3_bucket.models.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "bucket_data_name"   { value = aws_s3_bucket.data.bucket }
output "bucket_models_name" { value = aws_s3_bucket.models.bucket }
output "bucket_data_arn"    { value = aws_s3_bucket.data.arn }
output "bucket_models_arn"  { value = aws_s3_bucket.models.arn }
