output "sqs_queue_url" {
  description = "SQS FIFO queue URL"
  value       = aws_sqs_queue.fifo.url
}

output "sqs_dlq_url" {
  description = "SQS DLQ URL"
  value       = aws_sqs_queue.dlq.url
}

output "sqs_queue_arn" {
  description = "SQS FIFO queue ARN"
  value       = aws_sqs_queue.fifo.arn
}