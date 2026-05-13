# 뉴스 수집 — 매일 새벽 2시 KST (UTC 17:00)
resource "aws_scheduler_schedule" "news_daily" {
  name = "${var.project_name}-${var.env}-news-daily"

  flexible_time_window { mode = "OFF" }

  schedule_expression          = "cron(0 17 * * ? *)"
  schedule_expression_timezone = "UTC"

  target {
    arn      = var.news_pipeline_arn
    role_arn = aws_iam_role.eventbridge_exec.arn
    input    = jsonencode({ triggered_by = "scheduler", env = var.env })
  }

  # dev/staging은 수동 실행 — 불필요한 API 호출 방지
  state = var.env == "prod" ? "ENABLED" : "DISABLED"
}

# 국토부 가격 수집 — 매월 1일 오전 1시 KST (UTC 16:00)
resource "aws_scheduler_schedule" "price_monthly" {
  name = "${var.project_name}-${var.env}-price-monthly"

  flexible_time_window { mode = "OFF" }

  schedule_expression          = "cron(0 16 1 * ? *)"
  schedule_expression_timezone = "UTC"

  target {
    arn      = var.price_pipeline_arn
    role_arn = aws_iam_role.eventbridge_exec.arn
    input    = jsonencode({ triggered_by = "scheduler", env = var.env })
  }

  state = var.env == "prod" ? "ENABLED" : "DISABLED"
}

resource "aws_iam_role" "eventbridge_exec" {
  name = "${var.project_name}-${var.env}-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "scheduler.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "eventbridge_exec" {
  name = "${var.project_name}-${var.env}-eventbridge-policy"
  role = aws_iam_role.eventbridge_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["states:StartExecution"]
      Resource = [var.news_pipeline_arn, var.price_pipeline_arn]
    }]
  })
}