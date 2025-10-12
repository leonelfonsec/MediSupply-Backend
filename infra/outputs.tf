# ============================================================
# DATABASE OUTPUTS
# ============================================================
output "db_endpoint" {
  description = "RDS PostgreSQL endpoint (host:port)"
  value       = aws_db_instance.postgres.endpoint
}

output "db_address" {
  description = "RDS PostgreSQL address (without port)"
  value       = aws_db_instance.postgres.address
}

output "db_port" {
  description = "RDS PostgreSQL port"
  value       = aws_db_instance.postgres.port
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.postgres.db_name
}

output "db_username" {
  description = "Database master username"
  value       = aws_db_instance.postgres.username
  sensitive   = true
}

output "db_instance_id" {
  description = "RDS instance identifier"
  value       = aws_db_instance.postgres.id
}

# Secret con la DATABASE_URL (cadena completa)
output "db_url_secret_arn" {
  description = "Secrets Manager ARN for DATABASE_URL secret (orders/DB_URL)"
  value       = aws_secretsmanager_secret.db_url.arn
}

# Secret con la contraseña (si lo necesitas para psql local/CI)
output "db_password_secret_arn" {
  description = "Secrets Manager ARN for DB password (orders/DB_PASSWORD)"
  value       = aws_secretsmanager_secret.db_password.arn
}

# ============================================================
# NETWORK OUTPUTS
# ============================================================
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

# ============================================================
# ECS OUTPUTS
# ============================================================
output "ecs_cluster_name" {
  description = "ECS Cluster name"
  value       = aws_ecs_cluster.orders.name
}

output "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  value       = aws_ecs_cluster.orders.arn
}

output "ecs_service_name" {
  description = "ECS Service name"
  value       = aws_ecs_service.orders.name
}

output "ecs_security_group_id" {
  description = "Security group ID for ECS service"
  value       = aws_security_group.ecs_sg.id
}

# ============================================================
# MONITORING OUTPUTS
# ============================================================
output "cloudwatch_log_group" {
  description = "CloudWatch Log Group name"
  value       = aws_cloudwatch_log_group.orders.name
}

output "performance_insights_enabled" {
  description = "Whether Performance Insights is enabled"
  value       = aws_db_instance.postgres.performance_insights_enabled
}

# ============================================================
# QUICK ACCESS COMMANDS (sin ALB)
# ============================================================
# Nota: para conectar desde CLI, usa el secret de password.
# Bash:
#   export PGPASSWORD=$(aws secretsmanager get-secret-value --secret-id orders/DB_PASSWORD --query SecretString --output text)
#   psql -h $(terraform output -raw db_address) -U $(terraform output -raw db_username) -d $(terraform output -raw db_name)
#
# PowerShell:
#   $env:PGPASSWORD = (aws secretsmanager get-secret-value --secret-id orders/DB_PASSWORD --query SecretString --output text)
#   psql -h (terraform output -raw db_address) -U (terraform output -raw db_username) -d (terraform output -raw db_name)

output "view_logs" {
  description = "Command to view ECS logs"
  value       = "aws logs tail ${aws_cloudwatch_log_group.orders.name} --follow"
}

output "stop_database" {
  description = "Command to stop database (save costs)"
  value       = "aws rds stop-db-instance --db-instance-identifier ${aws_db_instance.postgres.id}"
}

output "start_database" {
  description = "Command to start database"
  value       = "aws rds start-db-instance --db-instance-identifier ${aws_db_instance.postgres.id}"
}
