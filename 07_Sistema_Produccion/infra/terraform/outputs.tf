output "ec2_public_ip" {
  description = "Server IP — add as GitHub secret EC2_HOST"
  value       = module.ec2.public_ip
}

output "ec2_ssh_private_key" {
  description = "SSH private key — add as GitHub secret EC2_SSH_KEY"
  value       = module.ec2.ssh_private_key
  sensitive   = true
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

output "s3_data_bucket" {
  value = module.s3.bucket_data_name
}

output "s3_models_bucket" {
  value = module.s3.bucket_models_name
}

output "deploy_command" {
  description = "Command to SSH into the server"
  value       = "ssh -i predicast.pem ec2-user@${module.ec2.public_ip}"
}
