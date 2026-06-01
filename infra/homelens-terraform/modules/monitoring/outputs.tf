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
  description = "CloudWatch 성능 대시보드명"
}

output "grafana_access" {
  description = "Grafana 접근 방법 — terraform apply 후 이 명령어로 포트포워딩"
  value       = "kubectl port-forward svc/kube-prometheus-stack-grafana 3000:80 -n monitoring"
}

output "grafana_admin_user" {
  description = "Grafana 로그인 계정"
  value       = "admin"
}

output "kube_prometheus_stack_namespace" {
  description = "kube-prometheus-stack 설치 네임스페이스"
  value       = "monitoring"
}