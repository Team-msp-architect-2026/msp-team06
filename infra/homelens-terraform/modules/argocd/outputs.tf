output "argocd_namespace" {
  description = "ArgoCD가 설치된 네임스페이스"
  value       = helm_release.argocd.namespace
}

output "argocd_chart_version" {
  description = "설치된 argo-cd Helm chart 버전"
  value       = helm_release.argocd.version
}

output "admin_password_command" {
  description = "초기 admin 비밀번호 조회 명령어"
  value       = "kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
}
