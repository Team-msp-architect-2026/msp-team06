locals {
  queues = {
    "report-generation" = { visibility_timeout = 180, max_receive_count = 5 }
    "news-summary"      = { visibility_timeout = 120, max_receive_count = 5 }
    "price-ingest"      = { visibility_timeout = 300, max_receive_count = 3 }
    "external-api-retry"= { visibility_timeout = 300, max_receive_count = 5 }
  }
}

resource "aws_sqs_queue" "dlq" {
    for_each = local.queues

    name                    = "${var.project_name}-${var.env}-${each.key}-dlq"
    message_retention_seconds = 1209600

    tags = { Env = var.env, Type = "dlq" }
}

resource "aws_sqs_queue" "main" {
    for_each = local.queues
    
    name                     = "${var.project_name}-${var.env}-${each.key}"
    visibility_timeout_seconds = each.value.visibility_timeout
    message_retention_seconds = 86400

    redrive_policy = jsonencode({
        deadLetterTargetArn = aws_sqs_queue.dlq[each.key].arn
        maxReceiveCount     = each.value.max_receive_count
    })

    tags = { Env = var.env, Type = "main"}
}