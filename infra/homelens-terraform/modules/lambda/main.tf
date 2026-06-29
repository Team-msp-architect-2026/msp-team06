locals {
  # VPC 밖 배치 — 외부 API(네이버, 국토부, 카카오) 직접 호출
  non_vpc_functions = {
    "news-collector"          = { memory = 512,  timeout = 180 }
    "news-summarizer-trigger" = { memory = 1024, timeout = 180 }
    "molit-price-ingest"      = { memory = 1024, timeout = 900 }
  }

  # VPC 안 배치 — RDS private subnet 접근 필요
  vpc_functions = {
    "pipeline-step"        = { memory = 1024, timeout = 300 }
    "normalize-price-data" = { memory = 1024, timeout = 300 }
    "detect-data-update"   = { memory = 512,  timeout = 180 }
    "region-normalizer"    = { memory = 512,  timeout = 180 }
    "summarize-news"       = { memory = 1024, timeout = 180 }
    "apt-complex-ingest"   = { memory = 1024, timeout = 300 }
  }

  common_env_vars = {
    ENV                  = var.env
    SQS_PRICE_INGEST_URL = var.price_ingest_queue_url
    SQS_NEWS_SUMMARY_URL = var.news_summary_queue_url
    SQS_REPORT_GEN_URL   = var.report_queue_url
    RAW_DATA_BUCKET      = var.raw_data_bucket_name
    REDIS_HOST           = var.redis_host
    REDIS_PORT           = tostring(var.redis_port)
  }
}

resource "aws_lambda_function" "non_vpc" {
  for_each = local.non_vpc_functions

  function_name = "${var.project_name}-${var.env}-${each.key}"
  role          = aws_iam_role.lambda_exec.arn

  package_type = "Zip"
  runtime      = "python3.12"
  handler      = "handler.lambda_handler"
  filename     = "${path.module}/placeholder.zip"

  memory_size = each.value.memory
  timeout     = each.value.timeout

  environment {
    variables = local.common_env_vars
  }

  tags = { Env = var.env }
}

resource "aws_lambda_function" "vpc" {
  for_each = local.vpc_functions

  function_name = "${var.project_name}-${var.env}-${each.key}"
  role          = aws_iam_role.lambda_exec.arn

  package_type = "Zip"
  runtime      = "python3.12"
  handler      = "handler.lambda_handler"
  filename     = "${path.module}/placeholder.zip"

  memory_size = each.value.memory
  timeout     = each.value.timeout

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_sg_id]
  }

  environment {
    variables = local.common_env_vars
  }

  tags = { Env = var.env }
}
