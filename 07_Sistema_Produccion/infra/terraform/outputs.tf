output "eks_cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "elasticache_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.elasticache.endpoint
  sensitive   = true
}

output "s3_bucket_data" {
  value = module.s3.bucket_data_name
}

output "s3_bucket_models" {
  value = module.s3.bucket_models_name
}

output "ecr_backend_url" {
  value = module.ecr.backend_url
}

output "ecr_frontend_url" {
  value = module.ecr.frontend_url
}

output "ecr_pipeline_url" {
  value = module.ecr.pipeline_url
}

output "kubeconfig_command" {
  description = "Command to update local kubeconfig"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}
