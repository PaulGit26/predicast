variable "identifier" { type = string }
variable "instance_class" { type = string }
variable "allocated_storage" { type = number }
variable "db_name" { type = string }
variable "username" {
  type      = string
  sensitive = true
}
variable "password" {
  type      = string
  sensitive = true
}
variable "subnet_ids" { type = list(string) }
variable "security_group_id" { type = string }

resource "aws_db_subnet_group" "main" {
  name       = "${var.identifier}-subnet-group"
  subnet_ids = var.subnet_ids
}

resource "aws_db_instance" "main" {
  identifier             = var.identifier
  engine                 = "postgres"
  engine_version         = "16.4"
  instance_class         = var.instance_class
  allocated_storage      = var.allocated_storage
  storage_type           = "gp3"
  storage_encrypted      = true
  db_name                = var.db_name
  username               = var.username
  password               = var.password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.security_group_id]
  skip_final_snapshot    = false
  final_snapshot_identifier = "${var.identifier}-final"
  backup_retention_period = 0
  deletion_protection    = true
  multi_az               = false   # set true for production HA
  publicly_accessible    = false

  tags = { Name = var.identifier }
}

output "endpoint" { value = aws_db_instance.main.endpoint }
output "db_name"  { value = aws_db_instance.main.db_name }
