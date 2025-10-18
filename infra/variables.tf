variable "project" {
  description = "Proyecto"
  type        = string
  default     = "medisupply"
}

variable "env" {
  description = "Entorno"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "Región AWS"
  type        = string
  default     = "us-east-1"
}

# Para tu task de ORDERS ya existente
variable "app_port" {
  description = "Puerto del contenedor orders"
  type        = number
  default     = 3000
}

variable "ecr_image" {
  description = "Imagen ECR de orders (incluye repo y tag, p.ej. 123456789012.dkr.ecr.us-east-1.amazonaws.com/orders:latest)"
  type        = string
}

# ============================================================
# VARIABLES PARA CATALOGO-SERVICE
# ============================================================
variable "catalogo_app_port" {
  description = "Puerto del contenedor catalogo-service"
  type        = number
  default     = 8080
}

variable "catalogo_ecr_image" {
  description = "Imagen ECR de catalogo-service (incluye repo y tag)"
  type        = string
  default     = "838693051133.dkr.ecr.us-east-1.amazonaws.com/medisupply-dev-catalogo-service:latest"
}
