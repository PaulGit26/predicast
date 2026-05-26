variable "cluster_name" { type = string }
variable "oidc_provider_arn" { type = string }
variable "oidc_provider_url" { type = string }
variable "s3_bucket_data_arn" { type = string }
variable "s3_bucket_models_arn" { type = string }

locals {
  oidc_sub = replace(var.oidc_provider_url, "https://", "")
}

# ── Backend ServiceAccount role (IRSA) ────────────────────────────────────────

resource "aws_iam_role" "backend_sa" {
  name = "${var.cluster_name}-backend-sa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Federated = var.oidc_provider_arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${local.oidc_sub}:sub" = "system:serviceaccount:predicast:predicast-backend-sa"
          "${local.oidc_sub}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "backend_s3" {
  name = "predicast-backend-s3"
  role = aws_iam_role.backend_sa.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = [var.s3_bucket_data_arn, "${var.s3_bucket_data_arn}/*",
                    var.s3_bucket_models_arn, "${var.s3_bucket_models_arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = ["arn:aws:secretsmanager:*:*:secret:predicast/*"]
      }
    ]
  })
}

# ── Pipeline ServiceAccount role (IRSA) ───────────────────────────────────────

resource "aws_iam_role" "pipeline_sa" {
  name = "${var.cluster_name}-pipeline-sa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Federated = var.oidc_provider_arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${local.oidc_sub}:sub" = "system:serviceaccount:predicast:predicast-pipeline-sa"
          "${local.oidc_sub}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "pipeline_s3" {
  name = "predicast-pipeline-s3"
  role = aws_iam_role.pipeline_sa.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
      Resource = [var.s3_bucket_data_arn, "${var.s3_bucket_data_arn}/*",
                  var.s3_bucket_models_arn, "${var.s3_bucket_models_arn}/*"]
    }]
  })
}

# ── ServiceAccount K8s manifests ─────────────────────────────────────────────

output "backend_sa_role_arn"  { value = aws_iam_role.backend_sa.arn }
output "pipeline_sa_role_arn" { value = aws_iam_role.pipeline_sa.arn }
