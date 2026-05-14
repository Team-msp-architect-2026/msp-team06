output "namespace" {
  description = "Kubernetes namespace for HomeLens workloads"
  value       = kubernetes_namespace.homelens.metadata[0].name
}

output "deployment_name" {
  description = "Celery worker Deployment name"
  value       = kubernetes_deployment.celery_worker.metadata[0].name
}

output "service_account_name" {
  description = "Celery worker ServiceAccount name"
  value       = kubernetes_service_account.celery_worker.metadata[0].name
}
