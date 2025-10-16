terraform {
  backend "s3" {
    bucket         = "miso-tfstate-838693051133"
    key            = "infra.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "miso-tf-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

# ============================================================
# VPC / NETWORKING
# ============================================================
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.5.1"

  name = "miso-vpc"
  cidr = "10.20.0.0/16"
  azs  = ["us-east-1a", "us-east-1b"]

  public_subnets  = ["10.20.1.0/24", "10.20.2.0/24"]
  private_subnets = ["10.20.11.0/24", "10.20.12.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true

  tags = { Project = var.project, Env = var.env }
}

# ============================================================
# SECURITY GROUPS
# ============================================================
# ECS Service SG (solo egress)
resource "aws_security_group" "ecs_sg" {
  name        = "orders-ecs-sg"
  description = "Security group for Orders ECS Service"
  vpc_id      = module.vpc.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "orders-ecs-sg", Project = var.project, Env = var.env }
}

# RDS PostgreSQL SG:
#  - permite 5432 desde ECS
#  - (TEMP) 5432 abierto a Internet para pruebas (eliminar luego)
resource "aws_security_group" "postgres_sg" {
  name        = "orders-postgres-sg"
  description = "Security group for Orders PostgreSQL RDS"
  vpc_id      = module.vpc.vpc_id

  # Acceso desde ECS
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_sg.id]
    description     = "Allow PostgreSQL from Orders ECS"
  }

  # ⚠️ TEMP: acceso abierto a Internet (quitar cuando termines)
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "TEMP: Allow PostgreSQL from anywhere"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "orders-postgres-sg", Project = var.project, Env = var.env }
}

# ============================================================
# RDS POSTGRESQL
# ============================================================
resource "random_password" "db_password" {
  length           = 24
  special          = true
  override_special = "-_."
}

resource "aws_db_subnet_group" "postgres_private" {
  name       = "orders-postgres-subnets"
  subnet_ids = module.vpc.private_subnets
  tags       = { Name = "orders-postgres-subnets", Project = var.project, Env = var.env }
}

resource "aws_db_subnet_group" "postgres_public" {
  name       = "orders-postgres-subnets-public"
  subnet_ids = module.vpc.public_subnets
  tags       = { Name = "orders-postgres-subnets-public", Project = var.project, Env = var.env }
}

resource "aws_db_parameter_group" "postgres" {
  family = "postgres15"
  name   = "orders-postgres-params"

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
  name = "orders-rds-monitoring"
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
  identifier = "orders-postgres"

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

  publicly_accessible  = true
  apply_immediately    = true
  db_subnet_group_name = aws_db_subnet_group.postgres_public.name

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
    Project    = var.project
    Env        = var.env
    ManagedBy  = "Terraform"
    Purpose    = "School Project - Production Simulation"
    CostCenter = "Education"
  }
}

# ============================================================
# SECRETS MANAGER
# ============================================================
resource "aws_secretsmanager_secret" "db_url" {
  name                    = "orders/DB_URL"
  description             = "Database connection URL for Orders service"
  recovery_window_in_days = 7
  lifecycle { prevent_destroy = true }
  tags = { Project = var.project, Env = var.env }
}

resource "aws_secretsmanager_secret_version" "db_url_v" {
  secret_id     = aws_secretsmanager_secret.db_url.id
  secret_string = "postgresql+asyncpg://${aws_db_instance.postgres.username}:${urlencode(random_password.db_password.result)}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
}

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "orders/DB_PASSWORD"
  description             = "PostgreSQL master password"
  recovery_window_in_days = 7
  lifecycle { prevent_destroy = true }
  tags = { Project = var.project, Env = var.env }
}

resource "aws_secretsmanager_secret_version" "db_password_v" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

# ============================================================
# CLOUDWATCH ALARMS (opcional)
# ============================================================
resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  alarm_name          = "orders-db-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Database CPU over 80%"
  dimensions          = { DBInstanceIdentifier = aws_db_instance.postgres.id }
  tags                = { Project = var.project, Env = var.env }
}

resource "aws_cloudwatch_metric_alarm" "database_storage" {
  alarm_name          = "orders-db-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 5368709120
  alarm_description   = "Database storage under 5GB"
  dimensions          = { DBInstanceIdentifier = aws_db_instance.postgres.id }
  tags                = { Project = var.project, Env = var.env }
}

resource "aws_cloudwatch_metric_alarm" "database_connections" {
  alarm_name          = "orders-db-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Database connections over 80"
  dimensions          = { DBInstanceIdentifier = aws_db_instance.postgres.id }
  tags                = { Project = var.project, Env = var.env }
}

# ============================================================
# ECS CLUSTER (orders)
# ============================================================
resource "aws_ecs_cluster" "orders" {
  name = "orders-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = { Project = var.project, Env = var.env }
}

# ============================================================
# IAM ROLES para ORDERS
# ============================================================
data "aws_iam_policy_document" "task_exec_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task_exec_role" {
  name               = "orders-task-exec"
  assume_role_policy = data.aws_iam_policy_document.task_exec_assume.json
  tags               = { Project = var.project, Env = var.env }
}

resource "aws_iam_role_policy_attachment" "exec_ecr" {
  role       = aws_iam_role.task_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy_attachment" "exec_secrets" {
  role       = aws_iam_role.task_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
}

data "aws_iam_policy_document" "task_app_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task_app_role" {
  name               = "orders-task-app"
  assume_role_policy = data.aws_iam_policy_document.task_app_assume.json
  tags               = { Project = var.project, Env = var.env }
}

# ============================================================
# CLOUDWATCH LOGS de ORDERS
# ============================================================
resource "aws_cloudwatch_log_group" "orders" {
  name              = "/ecs/orders"
  retention_in_days = 7
  tags              = { Project = var.project, Env = var.env }
}

# ============================================================
# ECS TASK DEFINITION de ORDERS (tu servicio ya existente)
# ============================================================
resource "aws_ecs_task_definition" "orders" {
  family                   = "orders"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.task_exec_role.arn
  task_role_arn            = aws_iam_role.task_app_role.arn

  container_definitions = jsonencode([
    {
      name      = "orders",
      image     = var.ecr_image,
      essential = true,
      portMappings = [
        { containerPort = var.app_port, hostPort = var.app_port, protocol = "tcp" }
      ],
      environment = [
        { name = "ENV", value = var.env },
        { name = "PORT", value = tostring(var.app_port) },
        { name = "RUN_DDL_ON_STARTUP", value = "false" },
        { name = "WEB_CONCURRENCY", value = "2" }
      ],
      secrets = [
        { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.db_url.arn }
      ],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.orders.name,
          "awslogs-region"        = var.aws_region,
          "awslogs-stream-prefix" = "orders"
        }
      },
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.app_port}/health || exit 1"],
        interval    = 30,
        timeout     = 5,
        retries     = 3,
        startPeriod = 60
      }
    }
  ])

  tags = { Project = var.project, Env = var.env }
}

# ============================================================
# ECS SERVICE de ORDERS (SIN LB)
# ============================================================
resource "aws_ecs_service" "orders" {
  name            = "orders-svc"
  cluster         = aws_ecs_cluster.orders.id
  task_definition = aws_ecs_task_definition.orders.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = false
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  tags = { Project = var.project, Env = var.env }
}

# ============================================================
# HAPROXY + CONSUMER (SQS)
# ============================================================

# Descubre los repos existentes en ECR (evitas variables para imágenes):
#data "aws_ecr_repository" "haproxy" { name = "haproxy-consumer" }
#data "aws_ecr_repository" "worker" { name = "orders-consumer" }

# creacion recursos
resource "aws_ecr_repository" "haproxy" {
  name = "${var.project}-${var.env}-haproxy-consumer"
  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }
  lifecycle { prevent_destroy = true }
  tags = { Project = var.project, Env = var.env }
}

resource "aws_ecr_repository" "worker" {
  name = "${var.project}-${var.env}-orders-consumer"
  image_scanning_configuration { scan_on_push = true }
  encryption_configuration { encryption_type = "AES256" }
  lifecycle { prevent_destroy = true }
  tags = { Project = var.project, Env = var.env }
}

# SQS FIFO + DLQ
resource "aws_sqs_queue" "haproxy_consumer_orders_events_dlq" {
  name                        = "${var.project}-${var.env}-orders-events-dlq.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  message_retention_seconds   = 1209600
  receive_wait_time_seconds   = 20
  tags                        = { Project = var.project, Env = var.env, Component = "haproxy-consumer" }
}

resource "aws_sqs_queue" "haproxy_consumer_orders_events_fifo" {
  name                        = "${var.project}-${var.env}-orders-events.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  visibility_timeout_seconds  = 60
  message_retention_seconds   = 1209600
  receive_wait_time_seconds   = 20
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.haproxy_consumer_orders_events_dlq.arn
    maxReceiveCount     = 5
  })
  tags = { Project = var.project, Env = var.env, Component = "haproxy-consumer" }
}

# IAM para la Task del consumer
data "aws_iam_policy_document" "haproxy_consumer_ecs_tasks_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "haproxy_consumer_task_role" {
  name               = "${var.project}-${var.env}-haproxy-consumer-task-role"
  assume_role_policy = data.aws_iam_policy_document.haproxy_consumer_ecs_tasks_assume.json
  tags               = { Project = var.project, Env = var.env }
}

data "aws_iam_policy_document" "haproxy_consumer_sqs_consumer" {
  statement {
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:ChangeMessageVisibility",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl"
    ]
    resources = [
      aws_sqs_queue.haproxy_consumer_orders_events_fifo.arn,
      aws_sqs_queue.haproxy_consumer_orders_events_dlq.arn
    ]
  }
}

resource "aws_iam_policy" "haproxy_consumer_sqs_consumer" {
  name   = "${var.project}-${var.env}-sqs-consumer-policy"
  policy = data.aws_iam_policy_document.haproxy_consumer_sqs_consumer.json
}

resource "aws_iam_role_policy_attachment" "haproxy_consumer_attach_sqs" {
  role       = aws_iam_role.haproxy_consumer_task_role.name
  policy_arn = aws_iam_policy.haproxy_consumer_sqs_consumer.arn
}

resource "aws_iam_role" "haproxy_consumer_exec_role" {
  name               = "${var.project}-${var.env}-haproxy-consumer-exec-role"
  assume_role_policy = data.aws_iam_policy_document.haproxy_consumer_ecs_tasks_assume.json
  tags               = { Project = var.project, Env = var.env }
}

resource "aws_iam_role_policy_attachment" "haproxy_consumer_exec_attach" {
  role       = aws_iam_role.haproxy_consumer_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Logs del componente
resource "aws_cloudwatch_log_group" "haproxy_consumer_lg" {
  name              = "/ecs/${var.project}-${var.env}-haproxy-consumer"
  retention_in_days = 14
  tags              = { Project = var.project, Env = var.env }
}

# SG del componente
resource "aws_security_group" "haproxy_consumer_sg" {
  name        = "${var.project}-${var.env}-haproxy-consumer-sg"
  description = "SG for HAProxy front + egress to Orders"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all egress"
  }

  tags = { Project = var.project, Env = var.env }
}

# Task Definition: HAProxy + Worker (usando ECR existentes)
resource "aws_ecs_task_definition" "haproxy_consumer_td" {
  family                   = "${var.project}-${var.env}-haproxy-consumer"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  task_role_arn            = aws_iam_role.haproxy_consumer_task_role.arn
  execution_role_arn       = aws_iam_role.haproxy_consumer_exec_role.arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name         = "haproxy",
      image        = "${aws_ecr_repository.haproxy.repository_url}:latest",
      essential    = true,
      portMappings = [{ containerPort = 80, hostPort = 80, protocol = "tcp" }],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          awslogs-group         = aws_cloudwatch_log_group.haproxy_consumer_lg.name,
          awslogs-region        = var.aws_region,
          awslogs-stream-prefix = "haproxy"
        }
      },
      environment = [
        { "name" : "AWS_REGION", "value" : var.aws_region }
      ]
    },
    {
      name      = "worker",
      image     = "${aws_ecr_repository.worker.repository_url}:latest",
      essential = true,
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          awslogs-group         = aws_cloudwatch_log_group.haproxy_consumer_lg.name,
          awslogs-region        = var.aws_region,
          awslogs-stream-prefix = "worker"
        }
      },
      environment = [
        { "name" : "AWS_REGION", "value" : var.aws_region },
        { "name" : "SQS_QUEUE_URL", "value" : aws_sqs_queue.haproxy_consumer_orders_events_fifo.url },
        { "name" : "LB_TARGET_URL", "value" : "http://127.0.0.1/orders" },
        { "name" : "SQS_WAIT", "value" : "20" },
        { "name" : "SQS_BATCH", "value" : "10" },
        { "name" : "SQS_VISIBILITY", "value" : "60" },
        { "name" : "HTTP_TIMEOUT", "value" : "30" }
      ]
    }
  ])

  tags = { Project = var.project, Env = var.env }
}

# Service del componente (en el cluster orders)
resource "aws_ecs_service" "haproxy_consumer_svc" {
  name            = "${var.project}-${var.env}-haproxy-consumer-svc"
  cluster         = aws_ecs_cluster.orders.id
  task_definition = aws_ecs_task_definition.haproxy_consumer_td.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = module.vpc.private_subnets
    security_groups  = [aws_security_group.haproxy_consumer_sg.id]
    assign_public_ip = false
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  tags = { Project = var.project, Env = var.env }

  depends_on = [
    aws_sqs_queue.haproxy_consumer_orders_events_fifo,
    aws_cloudwatch_log_group.haproxy_consumer_lg
  ]
}
