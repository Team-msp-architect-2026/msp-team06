resource "aws_sfn_state_machine" "news_pipeline" {
  name     = "${var.project_name}-${var.env}-news-pipeline"
  role_arn = aws_iam_role.step_functions_exec.arn

  definition = templatefile("${path.module}/definition_news.asl.json", {
    news_collector_arn          = var.news_collector_arn
    news_summarizer_trigger_arn = var.news_summarizer_trigger_arn
  })

  tags = { Env = var.env }
}

resource "aws_sfn_state_machine" "price_pipeline" {
  name     = "${var.project_name}-${var.env}-price-pipeline"
  role_arn = aws_iam_role.step_functions_exec.arn

  definition = templatefile("${path.module}/definition_price.asl.json", {
    molit_price_ingest_arn = var.molit_price_ingest_arn
    region_normalizer_arn  = var.region_normalizer_arn
  })

  tags = { Env = var.env }
}

resource "aws_iam_role" "step_functions_exec" {
  name = "${var.project_name}-${var.env}-step-functions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "states.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "step_functions_exec" {
  name = "${var.project_name}-${var.env}-step-functions-policy"
  role = aws_iam_role.step_functions_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["lambda:InvokeFunction"]
      Resource = [
        var.news_collector_arn,
        var.news_summarizer_trigger_arn,
        var.molit_price_ingest_arn,
        var.region_normalizer_arn
      ]
    }]
  })
}