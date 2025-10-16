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
