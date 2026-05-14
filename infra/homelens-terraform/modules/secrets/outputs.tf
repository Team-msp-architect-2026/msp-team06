output "kakao_map_secret_arn" {
  value       = aws_secretsmanager_secret.kakao_map.arn
  description = "카카오맵 API 시크릿 ARN"
}

output "naver_news_secret_arn" {
  value       = aws_secretsmanager_secret.naver_news.arn
  description = "네이버 뉴스 API 시크릿 ARN"
}

output "molit_secret_arn" {
  value       = aws_secretsmanager_secret.molit.arn
  description = "국토부 API 시크릿 ARN"
}

output "rds_secret_arn" {
  value       = aws_secretsmanager_secret.rds.arn
  description = "RDS 접속 정보 시크릿 ARN"
}

output "redis_secret_arn" {
  value       = aws_secretsmanager_secret.redis.arn
  description = "Redis auth token 시크릿 ARN"
}

output "bedrock_secret_arn" {
  value       = aws_secretsmanager_secret.bedrock.arn
  description = "Bedrock 설정 시크릿 ARN"
}