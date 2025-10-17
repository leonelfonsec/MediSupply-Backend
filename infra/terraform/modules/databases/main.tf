resource "random_password" "db_password" {
  length           = 24
  special          = true
  override_special = "-_."
}

resource "aws_security_group" "postgres_sg" {
  name        = "${var.project}-${var.env}-postgres-sg"
  description = "SG for PostgreSQL RDS"
  vpc_id      = var.vpc_id

  # Acceso temporal abierto para pruebas
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "TEMP: open 5432"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Project = var.project, Env = var.env }
}

resource "aws_db_subnet_group" "postgres_public" {
  name       = "${var.project}-${var.env}-rds-public"
  subnet_ids = var.public_subnets
  tags       = { Project = var.project, Env = var.env }
}

resource "aws_db_parameter_group" "postgres" {
  family = "postgres15"
  name   = "${var.project}-${var.env}-pg-params"

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = { Project = var.project, Env = var.env }
}

resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project}-${var.env}-rds-monitoring"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = { Service = "monitoring.rds.amazonaws.com" }
    }]
  })
  tags = { Project = var.project, Env = var.env }
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

resource "aws_db_instance" "postgres" {
  identifier = "${var.project}-${var.env}-orders-postgres"

  engine         = "postgres"
  engine_version = "15.14"
  instance_class = "db.t4g.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true

  db_name  = "orders"
  username = "orders_user"
  password = random_password.db_password.result
  port     = 5432

  publicly_accessible    = true
  apply_immediately      = true
  db_subnet_group_name   = aws_db_subnet_group.postgres_public.name
  vpc_security_group_ids = [aws_security_group.postgres_sg.id]

  multi_az                = false
  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"
  copy_tags_to_snapshot   = true

  skip_final_snapshot      = true
  deletion_protection      = false
  delete_automated_backups = true

  enabled_cloudwatch_logs_exports       = ["postgresql", "upgrade"]
  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  monitoring_interval                   = 60
  monitoring_role_arn                   = aws_iam_role.rds_monitoring.arn

  auto_minor_version_upgrade = true
  parameter_group_name       = aws_db_parameter_group.postgres.name

  tags = {
    Project   = var.project
    Env       = var.env
    ManagedBy = "Terraform"
  }
}

# Secrets
resource "aws_secretsmanager_secret" "db_url" {
  name                    = "orders/DB_URL"
  description             = "DB URL for Orders"
  recovery_window_in_days = 7
  tags                    = { Project = var.project, Env = var.env }
}

resource "aws_secretsmanager_secret_version" "db_url_v" {
  secret_id     = aws_secretsmanager_secret.db_url.id
  secret_string = "postgresql+asyncpg://${aws_db_instance.postgres.username}:${urlencode(random_password.db_password.result)}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
}

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "orders/DB_PASSWORD"
  description             = "RDS master password"
  recovery_window_in_days = 7
  tags                    = { Project = var.project, Env = var.env }
}

resource "aws_secretsmanager_secret_version" "db_password_v" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}
