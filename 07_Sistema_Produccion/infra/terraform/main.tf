terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "terraform"
    }
  }
}

data "aws_availability_zones" "available" { state = "available" }
data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  name       = var.project_name
}

# ── VPC (public only — no NAT gateway needed for single EC2) ──────────────────

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags                 = { Name = "${local.name}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name}-igw" }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, 0)
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
  tags                    = { Name = "${local.name}-public" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = { Name = "${local.name}-public-rt" }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# ── Security Group for EC2 ────────────────────────────────────────────────────

resource "aws_security_group" "ec2" {
  name        = "${local.name}-ec2"
  description = "Predicast server - HTTP/S + SSH"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ── Modules ───────────────────────────────────────────────────────────────────

module "ecr" {
  source        = "./modules/ecr"
  backend_repo  = var.ecr_backend_repo
  frontend_repo = var.ecr_frontend_repo
  pipeline_repo = var.ecr_pipeline_repo
}

module "s3" {
  source             = "./modules/s3"
  bucket_data_name   = "${var.s3_bucket_data}-${local.account_id}"
  bucket_models_name = "${var.s3_bucket_models}-${local.account_id}"
  environment        = "production"
}

module "ec2" {
  source               = "./modules/ec2"
  name_prefix          = local.name
  instance_type        = var.ec2_instance_type
  subnet_id            = aws_subnet.public.id
  security_group_id    = aws_security_group.ec2.id
  s3_bucket_data_arn   = module.s3.bucket_data_arn
  s3_bucket_models_arn = module.s3.bucket_models_arn
}
