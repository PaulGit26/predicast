variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Must be development, staging, or production."
  }
}

variable "project_name" {
  description = "Project name used as prefix for all resources"
  type        = string
  default     = "predicast"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "eks_node_instance_type" {
  description = "EC2 instance type for EKS worker nodes"
  type        = string
  default     = "t3.medium"
}

variable "eks_node_desired_size" {
  type    = number
  default = 2
}

variable "eks_node_min_size" {
  type    = number
  default = 1
}

variable "eks_node_max_size" {
  type    = number
  default = 6
}

variable "eks_cluster_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.29"
}

variable "rds_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "rds_allocated_storage" {
  type    = number
  default = 20
}

variable "rds_db_name" {
  type    = string
  default = "predicast"
}

variable "rds_username" {
  description = "PostgreSQL master username (store in tfvars, never commit)"
  type        = string
  sensitive   = true
}

variable "rds_password" {
  description = "PostgreSQL master password (store in tfvars, never commit)"
  type        = string
  sensitive   = true
}

variable "elasticache_node_type" {
  type    = string
  default = "cache.t3.micro"
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
