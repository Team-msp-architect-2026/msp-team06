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

output "normalize_price_data_arn" {
  value = aws_lambda_function.main["normalize-price-data"].arn
}

output "detect_data_update_arn" {
  value = aws_lambda_function.main["detect-data-update"].arn
}

output "summarize_news_arn" {
  value = aws_lambda_function.main["summarize-news"].arn
}

output "apt_complex_ingest_arn" {
  value = aws_lambda_function.main["apt-complex-ingest"].arn
}