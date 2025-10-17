variable "project" { type = string }
variable "env" { type = string }
variable "aws_region" { type = string }
variable "vpc_id" { type = string }
variable "private_subnets" { type = list(string) }
variable "use_haproxy" { type = bool }
variable "bff_alb_dns_name" { type = string }
variable "ecs_cluster_arn" {
  description = "ECS Cluster ARN"
  type        = string
}