output "tfstate_bucket_names" {
  description = "tfstate S3 bucket names by environment"
  value       = { for env, bucket in aws_s3_bucket.tfstate : env => bucket.id }
}

output "tfstate_bucket_arns" {
  description = "tfstate S3 bucket ARNs by environment"
  value       = { for env, bucket in aws_s3_bucket.tfstate : env => bucket.arn }
}

output "tfstate_lock_table_name" {
  description = "DynamoDB state lock table name"
  value       = aws_dynamodb_table.tfstate_lock.name
}

output "tfstate_lock_table_arn" {
  description = "DynamoDB state lock table ARN"
  value       = aws_dynamodb_table.tfstate_lock.arn
}
