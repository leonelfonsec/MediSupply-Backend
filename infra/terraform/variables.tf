variable "project" {
  type        = string
  description = "Nombre del proyecto"
  default     = "medisupply"
}

variable "env" {
  type        = string
  description = "Entorno (dev/stg/prod)"
  default     = "dev"
}

variable "aws_region" {
  type        = string
  description = "Región AWS"
  default     = "us-east-1"
}

# Imagen del micro de Orders (ECR) para ECS
variable "orders_ecr_image" {
  type        = string
  description = "URI de la imagen de orders en ECR (repository:tag)"
}

variable "orders_app_port" {
  type        = number
  description = "Puerto del contenedor Orders"
  default     = 3000
}

# BFF Venta
variable "bff_name" {
  type        = string
  description = "Nombre lógico del BFF"
  default     = "bff-venta"
}

variable "bff_repo_name" {
  type        = string
  description = "Nombre del repo ECR para el BFF"
  default     = "medisupply-dev-bff-venta"
}

variable "bff_app_port" {
  type        = number
  description = "Puerto del contenedor BFF"
  default     = 8000
}

variable "bff_env" {
  type        = map(string)
  description = "Variables de entorno adicionales para BFF"
  default     = {}
}

# Flag para elegir destino del consumer (HAProxy local vs ALB)
variable "use_haproxy" {
  type        = bool
  description = "true: target http://127.0.0.1/orders, false: target ALB BFF"
  default     = true
}

variable "ecr_image" {
  description = "Imagen ECR de orders"
  type        = string
}

variable "app_port" {
  description = "Puerto del contenedor orders"
  type        = number
  default     = 3000
}