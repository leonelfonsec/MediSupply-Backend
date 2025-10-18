variable "project" { type = string }
variable "env" { type = string }
variable "aws_region" { type = string }
variable "vpc_id" { type = string }
variable "private_subnets" { type = list(string) }
variable "ecr_image" { type = string }
variable "app_port" { type = number }
variable "db_url_secret_arn" { type = string }
variable "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  type        = string
}