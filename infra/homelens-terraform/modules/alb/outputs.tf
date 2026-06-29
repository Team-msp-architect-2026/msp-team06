output "alb_arn" {
  description = "ALB ARN"
  value       = aws_lb.main.arn
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "alb_zone_id" {
  description = "ALB hosted zone ID (for Route53 alias)"
  value       = aws_lb.main.zone_id
}

output "target_group_arn" {
  description = "API target group ARN"
  value       = aws_lb_target_group.api.arn
}

output "alb_arn_suffix" {
  description = "ALB ARN suffix (CloudWatch / Grafana 대시보드용)"
  value       = aws_lb.main.arn_suffix
}
