locals {
  bff_id = "${var.project}-${var.env}-${var.bff_name}"
}

resource "aws_ecr_repository" "bff" {
  name         = var.bff_repo_name
  force_delete = true
  image_scanning_configuration { scan_on_push = true }
  tags = { Project = var.project, Env = var.env, Component = var.bff_name }
}

resource "aws_cloudwatch_log_group" "bff" {
  name              = "/ecs/${local.bff_id}"
  retention_in_days = 14
  tags              = { Project = var.project, Env = var.env, Component = var.bff_name }
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "exec_role" {
  name               = "${local.bff_id}-exec-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = { Project = var.project, Env = var.env, Component = var.bff_name }
}

resource "aws_iam_role_policy_attachment" "exec_attach" {
  role       = aws_iam_role.exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "app_role" {
  name               = "${local.bff_id}-task-role"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags               = { Project = var.project, Env = var.env, Component = var.bff_name }
}

# arn de SQS desde URL:
locals {
  sqs_arn = replace(var.sqs_url, "https://sqs.${var.aws_region}.amazonaws.com/", "arn:aws:sqs:${var.aws_region}:")
}

# Si prefieres usar ARN correctamente:
data "aws_iam_policy_document" "sqs_producer" {
  statement {
    effect = "Allow"
    actions = [
      "sqs:SendMessage",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl"
    ]
    resources = [var.sqs_arn]
  }
}

resource "aws_iam_policy" "sqs_producer" {
  name   = "${local.bff_id}-sqs-producer"
  policy = data.aws_iam_policy_document.sqs_producer.json
}

resource "aws_iam_role_policy_attachment" "app_attach_sqs" {
  role       = aws_iam_role.app_role.name
  policy_arn = aws_iam_policy.sqs_producer.arn
}

resource "aws_security_group" "alb_sg" {
  name        = "${local.bff_id}-alb-sg"
  description = "ALB SG for ${var.bff_name}"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Project = var.project, Env = var.env, Component = var.bff_name }
}

resource "aws_security_group" "svc_sg" {
  name        = "${local.bff_id}-svc-sg"
  description = "Service SG for ${var.bff_name}"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = var.bff_app_port
    to_port         = var.bff_app_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Project = var.project, Env = var.env, Component = var.bff_name }
}

resource "aws_lb" "alb" {
  name               = "${local.bff_id}-alb"
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = var.public_subnets
  idle_timeout       = 60
  tags               = { Project = var.project, Env = var.env, Component = var.bff_name }
}

resource "aws_lb_target_group" "tg" {
  name        = "${local.bff_id}-tg"
  port        = var.bff_app_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = var.vpc_id

  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200-399"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }
  tags = { Project = var.project, Env = var.env, Component = var.bff_name }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg.arn
  }
}

resource "aws_ecs_task_definition" "td" {
  family                   = local.bff_id
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.exec_role.arn
  task_role_arn            = aws_iam_role.app_role.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name         = var.bff_name,
      image        = "${aws_ecr_repository.bff.repository_url}:latest",
      essential    = true,
      portMappings = [{ containerPort = var.bff_app_port, hostPort = var.bff_app_port, protocol = "tcp" }],
      logConfiguration = {
        logDriver = "awslogs",
        options = {
          awslogs-group         = aws_cloudwatch_log_group.bff.name,
          awslogs-region        = var.aws_region,
          awslogs-stream-prefix = var.bff_name
        }
      },
      environment = concat(
        [for k, v in var.bff_env : { name = k, value = v }],
        [{ name = "SQS_QUEUE_URL", value = var.sqs_url }]
      ),
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.bff_app_port}/health || exit 1"],
        interval    = 30,
        timeout     = 5,
        retries     = 3,
        startPeriod = 20
      }
    }
  ])

  tags = { Project = var.project, Env = var.env, Component = var.bff_name }
}

resource "aws_ecs_service" "svc" {
  name            = "${local.bff_id}-svc"
  cluster         = var.ecs_cluster_arn
  task_definition = aws_ecs_task_definition.td.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.svc_sg.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.tg.arn
    container_name   = var.bff_name
    container_port   = var.bff_app_port
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  depends_on = [aws_lb_listener.http]

  tags = { Project = var.project, Env = var.env, Component = var.bff_name }
}
