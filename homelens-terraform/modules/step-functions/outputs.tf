output "news_pipeline_arn"{
    value      = aws_sfn_state_machine.news_pipeline.arn
    description = "eventbridge 모듈에서 받음"

}

output "price_pipeline_arn" {
    value     = aws_sfn_state_machine.price_pipeline.arn
    description = "eventbridge 모듈에서 받음"
}