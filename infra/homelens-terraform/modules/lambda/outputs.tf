output "news_collector_arn" {
  value = aws_lambda_function.non_vpc["news-collector"].arn
}

output "news_summarizer_trigger_arn" {
  value = aws_lambda_function.non_vpc["news-summarizer-trigger"].arn
}

output "molit_price_ingest_arn" {
  value = aws_lambda_function.non_vpc["molit-price-ingest"].arn
}

output "region_normalizer_arn" {
  value = aws_lambda_function.vpc["region-normalizer"].arn
}

output "pipeline_step_arn" {
  value = aws_lambda_function.vpc["pipeline-step"].arn
}

output "normalize_price_data_arn" {
  value = aws_lambda_function.vpc["normalize-price-data"].arn
}

output "detect_data_update_arn" {
  value = aws_lambda_function.vpc["detect-data-update"].arn
}

output "summarize_news_arn" {
  value = aws_lambda_function.vpc["summarize-news"].arn
}

output "apt_complex_ingest_arn" {
  value = aws_lambda_function.vpc["apt-complex-ingest"].arn
}
