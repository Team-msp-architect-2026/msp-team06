resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-${var.env}-lambda-ingest-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

# 기존 통합 정책 — S3, SQS, CloudWatch Logs
resource "aws_iam_role_policy" "lambda_exec" {
  name = "${var.project_name}-${var.env}-lambda-ingest-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "${var.raw_data_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = ["sqs:SendMessage"]
        Resource = [
          var.report_queue_arn,
          var.price_ingest_queue_arn,
          var.news_summary_queue_arn,
        ]
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = "arn:aws:secretsmanager:eu-west-3:*:secret:homelens/${var.env}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "arn:aws:logs:eu-west-3:*:*"
      }
    ]
  })
}

# homelens-lambda-vpc-policy — VPC Lambda ENI 생성 권한
resource "aws_iam_role_policy" "lambda_vpc" {
  name = "${var.project_name}-lambda-vpc-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeVpcs"
      ]
      Resource = "*"
    }]
  })
}

# homelens-lambda-rds-secret-policy — RDS manage_master_user_password 시크릿 조회
resource "aws_iam_role_policy" "lambda_rds_secret" {
  name = "${var.project_name}-lambda-rds-secret-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "secretsmanager:GetSecretValue"
      Resource = "arn:aws:secretsmanager:eu-west-3:611058323802:secret:rds!db-*"
    }]
  })
}

# homelens-lambda-bedrock-policy — AI 요약 모델 호출
resource "aws_iam_role_policy" "lambda_bedrock" {
  name = "${var.project_name}-lambda-bedrock-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "bedrock:InvokeModel"
      Resource = "arn:aws:bedrock:eu-west-3::foundation-model/anthropic.claude-*"
    }]
  })
}
