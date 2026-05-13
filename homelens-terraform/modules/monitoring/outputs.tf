output "prometheus_workspace_id" {
  value       = aws_prometheus_workspace.main.id
  description = "Prometheus 워크스페이스 ID"
}

output "prometheus_workspace_endpoint" {
  value       = aws_prometheus_workspace.main.prometheus_endpoint
  description = "Prometheus 엔드포인트"
}

output "xray_group_arn" {
  value       = aws_xray_group.main.arn
  description = "X-Ray 그룹 ARN"
}

output "dashboard_name" {
  value       = aws_cloudwatch_dashboard.main.dashboard_name
  description = "Grafana 성능 대시보드명"
}