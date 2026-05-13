output "rds_endpoint" {
    value     = aws_db_instance.main.endpoint
    description = "FastAPI DB 연결용 엔드포인트"
}

output "rds_db_name" {
    value = aws_db_instance.main.db_name
}

output "rds_secret_arn" {
    value     = aws_db_instance.main.master_user_secret[0].secret_arn
    description = "Secrets Manager 자동 저장된 DB 비밀번호 ARN"
}

