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

# ---------- BFF (venta) ----------
variable "bff_name" {
  description = "Nombre lógico del BFF"
  type        = string
  default     = "bff-venta"
}

variable "bff_repo_name" {
  description = "Nombre del repo ECR de este BFF"
  type        = string
  default     = "medisupply-dev-bff-venta"
}

variable "bff_app_port" {
  description = "Puerto del contenedor para el BFF"
  type        = number
  default     = 8000
}

variable "bff_env" {
  description = "Variables de entorno adicionales para el BFF"
  type        = map(string)
  default = {
    AWS_REGION = "us-east-1"
    # agrega aquí lo que tu BFF necesite (URLs/ENV extra)
  }
}

variable "use_haproxy" {
  type        = bool
  default     = true
  description = "Si true, el worker apunta a HAProxy local (127.0.0.1/orders). Si false, apunta al ALB."
}



