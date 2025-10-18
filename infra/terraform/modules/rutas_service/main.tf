terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

locals {
  service_id = "${var.project}-${var.env}-${var.service_name}"
}

# ============================================================
# ECR REPOSITORY
# ============================================================
resource "aws_ecr_repository" "this" {
  name                 = "${var.project}-${var.env}-${var.service_name}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

# ============================================================
# CLOUDWATCH LOGS
# ============================================================
resource "aws_cloudwatch_log_group" "this" {
  name              = "/ecs/${local.service_id}"
  retention_in_days = 7

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

# ============================================================
# IAM ROLES
# ============================================================
data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# Execution Role (para pull de ECR y logs)
resource "aws_iam_role" "execution_role" {
  name               = "${local.service_id}-exec-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

resource "aws_iam_role_policy_attachment" "execution_role_policy" {
  role       = aws_iam_role.execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Política adicional para leer Secrets Manager
data "aws_iam_policy_document" "secrets_policy" {
  statement {
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [var.db_url_secret_arn]
  }
}

resource "aws_iam_policy" "secrets_policy" {
  name   = "${local.service_id}-secrets-policy"
  policy = data.aws_iam_policy_document.secrets_policy.json
}

resource "aws_iam_role_policy_attachment" "secrets_attach" {
  role       = aws_iam_role.execution_role.name
  policy_arn = aws_iam_policy.secrets_policy.arn
}

# Task Role (permisos de la aplicación)
resource "aws_iam_role" "task_role" {
  name               = "${local.service_id}-task-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

# ============================================================
# SECURITY GROUPS
# ============================================================
resource "aws_security_group" "alb" {
  name        = "${local.service_id}-alb-sg"
  description = "ALB interno para ${var.service_name}"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP desde VPC"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["10.20.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

resource "aws_security_group" "svc" {
  name        = "${local.service_id}-svc-sg"
  description = "SG del servicio ${var.service_name}"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Trafico desde ALB"
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

# ============================================================
# APPLICATION LOAD BALANCER (INTERNAL)
# ============================================================
resource "aws_lb" "this" {
  name               = "${substr(local.service_id, 0, 26)}-alb"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.private_subnets

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

resource "aws_lb_target_group" "this" {
  name        = "${substr(local.service_id, 0, 28)}-tg"
  port        = var.app_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    enabled             = true
    path                = var.health_check_path
    protocol            = "HTTP"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

# ============================================================
# ECS TASK DEFINITION
# ============================================================
resource "aws_ecs_task_definition" "this" {
  family                   = local.service_id
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = aws_iam_role.execution_role.arn
  task_role_arn            = aws_iam_role.task_role.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = var.service_name
      image     = "${aws_ecr_repository.this.repository_url}:${var.image_tag}"
      essential = true

      portMappings = [
        {
          containerPort = var.app_port
          hostPort      = var.app_port
          protocol      = "tcp"
        }
      ]

      environment = [
        { name = "ENV", value = var.env },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "PORT", value = tostring(var.app_port) }
      ]

      secrets = [
        {
          name      = "DATABASE_URL"
          valueFrom = var.db_url_secret_arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.this.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = var.service_name
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.app_port}${var.health_check_path} || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}

# ============================================================
# ECS SERVICE
# ============================================================
resource "aws_ecs_service" "this" {
  name            = "${local.service_id}-svc"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.svc.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = var.service_name
    container_port   = var.app_port
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  depends_on = [aws_lb_listener.http]

  tags = {
    Project = var.project
    Env     = var.env
    Service = var.service_name
  }
}