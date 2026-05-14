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
