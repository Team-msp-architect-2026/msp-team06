output "log_group_name" {
  description = "CloudWatch log group name for Bedrock invocation logs"
  value       = aws_cloudwatch_log_group.bedrock.name
}

output "log_group_arn" {
  description = "CloudWatch log group ARN for Bedrock invocation logs"
  value       = aws_cloudwatch_log_group.bedrock.arn
}

output "bedrock_logging_role_arn" {
  description = "IAM role ARN used by Bedrock to write invocation logs"
  value       = aws_iam_role.bedrock_logging.arn
}

output "bedrock_config_secret_arn" {
  description = "Secrets Manager ARN for Bedrock model config"
  value       = data.aws_secretsmanager_secret.bedrock_config.arn
}
