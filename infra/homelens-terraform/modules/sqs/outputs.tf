output "report_queue_url" {
  value       = aws_sqs_queue.main["report-generation"].url
  description = "FastAPI → Celery AI 리포트 요청 큐"
}

output "report_queue_arn" {
  value = aws_sqs_queue.main["report-generation"].arn
}

output "news_summary_queue_url" {
  value       = aws_sqs_queue.main["news-summary"].url
  description = "뉴스 AI 요약 작업 큐"
}

output "news_summary_queue_arn" {
  value = aws_sqs_queue.main["news-summary"].arn
}

output "price_ingest_queue_url" {
  value       = aws_sqs_queue.main["price-ingest"].url
  description = "가격 데이터 수집 큐"
}

output "price_ingest_queue_arn" {
  value = aws_sqs_queue.main["price-ingest"].arn
}

output "external_api_retry_queue_url" {
  value       = aws_sqs_queue.main["external-api-retry"].url
  description = "외부 API 실패 재시도 큐"
}
