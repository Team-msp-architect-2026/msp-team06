output "raw_data_bucket_name" {
    value     = aws_s3_bucket.raw_data.bucket
    description = "Lambda 수집 결과 저장 버킷"
}

output "raw_data_bucket_arn" {
    value = aws_s3_bucket.raw_data.arn
}

output "report_backup_bucket_name" {
    value     = aws_s3_bucket.report_backup.bucket
    description = "AI 리포트 백업 버킷"
}

output "report_backup_bucket_arn" {
    value = aws_s3_bucket.report_backup.arn
}
