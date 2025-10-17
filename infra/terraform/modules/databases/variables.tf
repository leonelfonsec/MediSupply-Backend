variable "project" { type = string }
variable "env" { type = string }
variable "aws_region" { type = string }
variable "vpc_id" { type = string }
variable "public_subnets" { type = list(string) }
variable "private_subnets" { type = list(string) }
