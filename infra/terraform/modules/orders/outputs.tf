output "service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.orders.name
}

output "service_arn" {
  description = "ECS service ARN"
  value       = aws_ecs_service.orders.id
}

output "task_definition_arn" {
  description = "Task definition ARN"
  value       = aws_ecs_task_definition.orders.arn
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.orders.name
}