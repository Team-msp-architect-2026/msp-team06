resource "aws_prometheus_workspace" "main" {
    alias = "${var.project_name}-${var.env}"

    tags = { Env = var.env}
}

resource "aws_xray_group" "main" {
    group_name      = "${var.project_name}-${var.env}"
    filter_expression = "service(\"${var.project_name}-${var.env}\")"

    tags = { Env = var.env}
}


resource "aws_xray_sampling_rule" "pipeline" {
    rule_name    = "${var.project_name}-${var.env}-pipeline"
    priority     = 1000
    version      = 1
    reservoir_size = 5
    fixed_rate   = 0.05
    url_path     = "*"
    host         = "*"
    http_method  = "*"
    service_type = "*"
    service_name = "${var.project_name}-${var.env}-*"
    resource_arn = "*"

    tags = { Env = var.env }

}

resource "aws_cloudwatch_metric_alarm" "sqs_depth" {
    alarm_name        = "${var.project_name}-${var.env}-sqs-depth"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods = 2
    metric_name = "ApproximateNumberOfMessagesVisible"
    namespace   = "AWS/SQS"
    period      = 60
    statistic   = "Average"
    threshold = 100
    alarm_description = "SQS 큐 적체량 100개 초과"

    dimensions  = {
        QueueName = "${var.project_name}-${var.env}-report-generation"
    
    }
    
    tags = { Env = var.env }
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
    alarm_name          = "${var.project_name}-${var.env}-lambda-errors"
    comparison_operator = "GreaterThanThreshold"
    evaluation_periods = 2
    metric_name = "Errors"
    namespace = "AWS/Lambda"
    period    = 60
    statistic = "Sum"
    threshold = 5
    alarm_description = "Lambda 에러 5회 초과"

    tags = { Env = var.env }
}
  
resource "aws_cloudwatch_metric_alarm" "rds_latency"{
  alarm_name           = "${var.project_name}-${var.env}-rds-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods   = 2
  metric_name          = "ReadLatency"
  namespace            = "AWS/RDS"
  period               = 60
  statistic            = "Average"
  threshold            = 0.002
  alarm_description    = "RDS 읽기 지연 2ms 초과"
  
  dimensions = {
    DBInstanceIdentifier = "${var.project_name}-${var.env}-postgre"
  }


  tags = { Env = var.env }
} 

