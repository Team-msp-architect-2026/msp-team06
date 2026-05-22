locals {
  lambda_functions = {
    "news-collector"          = { memory = 512,  timeout = 180 }
    "news-summarizer-trigger" = { memory = 1024, timeout = 180 }
    "molit-price-ingest"      = { memory = 1024, timeout = 900 }
    "region-normalizer"       = { memory = 512,  timeout = 180 }
    "pipeline-step"           = { memory = 1024, timeout = 300 }
    "normalize-price-data"    = { memory = 1024, timeout = 300 }
    "detect-data-update"      = { memory = 512,  timeout = 180 }
    "summarize-news"          = { memory = 1024, timeout = 180 }
    "apt-complex-ingest"      = { memory = 1024, timeout = 300 }
  }
}

resource "aws_lambda_function" "main" {
  for_each = local.lambda_functions

  function_name = "${var.project_name}-${var.env}-${each.key}"
  role          = aws_iam_role.lambda_exec.arn

  package_type = "Zip"
  runtime      = "python3.12"
  handler      = "handler.lambda_handler"
  filename     = "${path.module}/placeholder.zip"

  memory_size = each.value.memory
  timeout     = each.value.timeout

  # VPC 밖 배치 확정 — vpc_config 블록 없음

  environment {
    variables = {
      ENV                  = var.env
      SQS_PRICE_INGEST_URL = var.price_ingest_queue_url
      SQS_NEWS_SUMMARY_URL = var.news_summary_queue_url
      SQS_REPORT_GEN_URL   = var.report_queue_url
      RAW_DATA_BUCKET      = var.raw_data_bucket_name
    }
  }

  tags = { Env = var.env }
}