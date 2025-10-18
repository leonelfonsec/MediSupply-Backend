output "repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.this.repository_url
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.this.name
}

output "service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.this.name
}

output "service_arn" {
  description = "ECS service ARN"
  value       = aws_ecs_service.this.id
}

output "alb_dns_name" {
  description = "Internal ALB DNS name"
  value       = aws_lb.this.dns_name
}

output "alb_url" {
  description = "Internal ALB URL"
  value       = "http://${aws_lb.this.dns_name}"
}

output "target_group_arn" {
  description = "Target group ARN"
  value       = aws_lb_target_group.this.arn
}

output "alb_sg_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "service_sg_id" {
  description = "Service security group ID"
  value       = aws_security_group.svc.id
}