locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# ---------------------------------------------------------------------------
# CloudWatch — Bedrock 호출 로그 그룹
# ---------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "bedrock" {
  name              = "/homelens/${var.environment}/bedrock"
  retention_in_days = var.environment == "prod" ? 30 : 7

  tags = { Name = "${local.name_prefix}-bedrock-logs" }
}

# ---------------------------------------------------------------------------
# IAM — Bedrock → CloudWatch 로그 쓰기 역할
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "bedrock_logging_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "bedrock_logging" {
  name               = "${local.name_prefix}-bedrock-logging-role"
  assume_role_policy = data.aws_iam_policy_document.bedrock_logging_assume.json
}

resource "aws_iam_role_policy" "bedrock_logging" {
  name = "${local.name_prefix}-bedrock-logging-policy"
  role = aws_iam_role.bedrock_logging.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = "${aws_cloudwatch_log_group.bedrock.arn}:*"
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# Bedrock 호출 로깅 설정
# ---------------------------------------------------------------------------
resource "aws_bedrock_model_invocation_logging_configuration" "main" {
  logging_config {
    cloudwatch_config {
      log_group_name = aws_cloudwatch_log_group.bedrock.name
      role_arn       = aws_iam_role.bedrock_logging.arn
    }
    embedding_data_delivery_enabled = false
    image_data_delivery_enabled     = false
    text_data_delivery_enabled      = true
  }
}

# ---------------------------------------------------------------------------
# Secrets Manager — bedrock/config 버전 채우기
# modules/secrets 가 껍데기(secret)를 이미 생성하므로 version 만 추가
# ---------------------------------------------------------------------------
data "aws_secretsmanager_secret" "bedrock_config" {
  name = "homelens/${var.environment}/bedrock/config"
}

resource "aws_secretsmanager_secret_version" "bedrock_config" {
  secret_id = data.aws_secretsmanager_secret.bedrock_config.id

  secret_string = jsonencode({
    model_id   = "eu.anthropic.claude-sonnet-4-6"
    region     = var.aws_region
    max_tokens = 4096
  })

  # CI/CD 또는 수동으로 모델 ID를 교체할 수 있도록 drift 무시
  lifecycle {
    ignore_changes = [secret_string]
  }
}
