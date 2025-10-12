variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project name"
  type        = string
  default     = "MediSupply"
}

variable "env" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "app_port" {
  description = "Port for Orders service"
  type        = number
  default     = 8000
}

variable "ecr_image" {
  description = "ECR image URI for Orders service"
  type        = string
  # Ejemplo: 838693051133.dkr.ecr.us-east-1.amazonaws.com/orders-service:latest
}