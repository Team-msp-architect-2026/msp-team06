output "news_schedule_arn" {
  value = aws_scheduler_schedule.news_daily.arn
}

output "price_schedule_arn" {
  value = aws_scheduler_schedule.price_monthly.arn
}