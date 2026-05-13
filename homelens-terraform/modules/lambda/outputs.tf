output "news_collector_arn" {
  value = aws_lambda_function.main["news-collector"].arn
}

output "news_summarizer_trigger_arn" {
  value = aws_lambda_function.main["news-summarizer-trigger"].arn
}

output "molit_price_ingest_arn" {
  value = aws_lambda_function.main["molit-price-ingest"].arn
}

output "region_normalizer_arn" {
  value = aws_lambda_function.main["region-normalizer"].arn
}

output "pipeline_step_arn" {
  value = aws_lambda_function.main["pipeline-step"].arn
}