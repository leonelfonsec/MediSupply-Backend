resource "aws_security_group" "ecs_sg" {
  name        = "${var.project}-${var.env}-orders-ecs-sg"
  description = "SG for Orders ECS"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Project = var.project, Env = var.env }
}

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
  name               = "${var.project}-${var.env}-orders-task-exec"
  assume_role_policy = data.aws_iam_policy_document.task_exec_assume.json
  tags               = { Project = var.project, Env = var.env }
}

resource "aws_iam_role_policy_attachment" "exec_ecr" {
  role       = aws_iam_role.task_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# App role (si necesitas permisos extra dentro del contenedor)
resource "aws_iam_role" "task_app_role" {
  name               = "${var.project}-${var.env}-orders-task-app"
  assume_role_policy = data.aws_iam_policy_document.task_exec_assume.json
  tags               = { Project = var.project, Env = var.env }
}

resource "aws_cloudwatch_log_group" "orders" {
  name              = "/ecs/orders"
  retention_in_days = 7
  tags              = { Project = var.project, Env = var.env }
}

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
      name         = "orders",
      image        = var.ecr_image,
      essential    = true,
      portMappings = [{ containerPort = var.app_port, hostPort = var.app_port, protocol = "tcp" }],
      environment = [
        { name = "ENV", value = var.env },
        { name = "PORT", value = tostring(var.app_port) },
        { name = "RUN_DDL_ON_STARTUP", value = "false" },
        { name = "WEB_CONCURRENCY", value = "2" }
      ],
      secrets = [
        { name = "DATABASE_URL", valueFrom = var.db_url_secret_arn }
      ],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          awslogs-group         = aws_cloudwatch_log_group.orders.name,
          awslogs-region        = var.aws_region,
          awslogs-stream-prefix = "orders"
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

resource "aws_ecs_service" "orders" {
  name            = "orders-svc"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.orders.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = false
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  tags = { Project = var.project, Env = var.env }
}
