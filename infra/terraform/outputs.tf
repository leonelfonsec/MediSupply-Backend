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
# ECS CLUSTER OUTPUTS
# ============================================================
output "ecs_cluster_name" {
  description = "ECS Cluster name"
  value       = aws_ecs_cluster.orders.name
}

output "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  value       = aws_ecs_cluster.orders.arn
}

# ============================================================
# DATABASE OUTPUTS (recursos directos en main.tf)
# ============================================================
output "db_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "db_address" {
  description = "RDS PostgreSQL address"
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
  description = "Database username"
  value       = aws_db_instance.postgres.username
  sensitive   = true
}

output "db_instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.postgres.id
}

output "db_url_secret_arn" {
  description = "Database URL secret ARN"
  value       = aws_secretsmanager_secret.db_url.arn
}

output "db_password_secret_arn" {
  description = "Database password secret ARN"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "postgres_security_group_id" {
  description = "PostgreSQL security group ID"
  value       = aws_security_group.postgres_sg.id
}

# ============================================================
# ORDERS SERVICE OUTPUTS
# ============================================================
output "orders_service_name" {
  description = "Orders service name"
  value       = module.orders.service_name
}

output "orders_log_group" {
  description = "Orders log group name"
  value       = module.orders.log_group_name
}

# ============================================================
# CONSUMER OUTPUTS
# ============================================================
output "haproxy_consumer_sqs_queue_url" {
  description = "SQS queue URL"
  value       = module.consumer.sqs_queue_url
}

output "haproxy_consumer_sqs_dlq_url" {
  description = "SQS DLQ URL"
  value       = module.consumer.sqs_dlq_url
}

# ============================================================
# BFF OUTPUTS
# ============================================================
output "bff_alb_dns" {
  description = "BFF ALB DNS name"
  value       = module.bff_venta.alb_dns_name
}

output "bff_alb_url" {
  description = "BFF URL"
  value       = "http://${module.bff_venta.alb_dns_name}"
}

output "bff_ecr_repo_url" {
  description = "BFF ECR repo URL"
  value       = module.bff_venta.ecr_repo_url
}

# ============================================================
# QUICK REFERENCE
# ============================================================
output "quick_reference" {
  description = "Quick reference commands"
  value = {
    bff_url       = "http://${module.bff_venta.alb_dns_name}"
    connect_to_db = "export PGPASSWORD=$(aws secretsmanager get-secret-value --secret-id ${aws_secretsmanager_secret.db_password.name} --query SecretString --output text) && psql -h ${aws_db_instance.postgres.address} -U ${aws_db_instance.postgres.username} -d ${aws_db_instance.postgres.db_name}"
    view_logs     = "aws logs tail /ecs/${var.project}-${var.env} --follow"
  }
}