variable "name_prefix"          { type = string }
variable "instance_type"        { type = string }
variable "subnet_id"            { type = string }
variable "security_group_id"    { type = string }
variable "s3_bucket_data_arn"   { type = string }
variable "s3_bucket_models_arn" { type = string }

# ── SSH Key Pair ──────────────────────────────────────────────────────────────

resource "tls_private_key" "ec2" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "ec2" {
  key_name   = "${var.name_prefix}-key"
  public_key = tls_private_key.ec2.public_key_openssh
}

# ── IAM Role + Instance Profile ───────────────────────────────────────────────

resource "aws_iam_role" "ec2" {
  name = "${var.name_prefix}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "ec2_permissions" {
  name = "${var.name_prefix}-ec2-policy"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = [
          var.s3_bucket_data_arn, "${var.s3_bucket_data_arn}/*",
          var.s3_bucket_models_arn, "${var.s3_bucket_models_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.name_prefix}-ec2-profile"
  role = aws_iam_role.ec2.name
}

# ── AMI (Amazon Linux 2023) ───────────────────────────────────────────────────

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ── EC2 Instance ──────────────────────────────────────────────────────────────

resource "aws_instance" "main" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  iam_instance_profile   = aws_iam_instance_profile.ec2.name
  key_name               = aws_key_pair.ec2.key_name

  user_data = <<-USERDATA
    #!/bin/bash
    dnf update -y
    dnf install -y docker git
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ec2-user

    # Docker Compose v2
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

    # App directory
    mkdir -p /home/ec2-user/predicast
    chown ec2-user:ec2-user /home/ec2-user/predicast
  USERDATA

  root_block_device {
    volume_size = 30
    volume_type = "gp2"
    encrypted   = true
  }

  tags = { Name = "${var.name_prefix}-server" }
}

# ── Elastic IP ────────────────────────────────────────────────────────────────

resource "aws_eip" "main" {
  instance = aws_instance.main.id
  domain   = "vpc"
  tags     = { Name = "${var.name_prefix}-eip" }
}

# ── Outputs ───────────────────────────────────────────────────────────────────

output "public_ip"       { value = aws_eip.main.public_ip }
output "instance_id"     { value = aws_instance.main.id }
output "ssh_private_key" {
  value     = tls_private_key.ec2.private_key_pem
  sensitive = true
}
