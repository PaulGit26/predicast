variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "predicast"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "ec2_instance_type" {
  description = "EC2 instance type (t2.micro = free tier)"
  type        = string
  default     = "t3.micro"
}

variable "s3_bucket_data" {
  type    = string
  default = "predicast-data"
}

variable "s3_bucket_models" {
  type    = string
  default = "predicast-models"
}

variable "ecr_backend_repo" {
  type    = string
  default = "predicast-backend"
}

variable "ecr_frontend_repo" {
  type    = string
  default = "predicast-frontend"
}

variable "ecr_pipeline_repo" {
  type    = string
  default = "predicast-pipeline"
}
