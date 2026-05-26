variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "s3_bucket_data" {
  type    = string
  default = "predicast-data-placeholder"
}

variable "environment" {
  type    = string
  default = "staging"
}
