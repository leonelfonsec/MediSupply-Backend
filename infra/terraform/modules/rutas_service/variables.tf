variable "project" {
  description = "Project name"
  type        = string
}

variable "env" {
  description = "Environment (dev/qa/prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "service_name" {
  description = "Service name"
  type        = string
  default     = "rutas"
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnets" {
  description = "Public subnet IDs"
  type        = list(string)
}

variable "private_subnets" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  type        = string
}

variable "db_url_secret_arn" {
  description = "Database URL secret ARN from Secrets Manager"
  type        = string
}

variable "app_port" {
  description = "Application port"
  type        = number
  default     = 8000
}

variable "ecr_image" {
  description = "ECR image (just the tag, repository is created by module)"
  type        = string
  default     = "latest"
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}

variable "desired_count" {
  description = "Number of tasks"
  type        = number
  default     = 1
}

variable "cpu" {
  description = "CPU units"
  type        = string
  default     = "512"
}

variable "memory" {
  description = "Memory in MB"
  type        = string
  default     = "1024"
}

variable "health_check_path" {
  description = "Health check endpoint"
  type        = string
  default     = "/health"
}