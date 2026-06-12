output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "cluster_ca_data" {
  description = "EKS cluster certificate authority data"
  value       = aws_eks_cluster.main.certificate_authority[0].data
  sensitive   = true
}

output "oidc_provider_arn" {
  description = "EKS OIDC provider ARN (for IRSA)"
  value       = aws_iam_openid_connect_provider.eks.arn
}

output "alb_controller_role_arn" {
  description = "IRSA role ARN for ALB Ingress Controller"
  value       = aws_iam_role.alb_controller.arn
}

output "fastapi_role_arn" {
  description = "IRSA role ARN for FastAPI ServiceAccount"
  value       = aws_iam_role.fastapi_api.arn
}

output "celery_worker_role_arn" {
  description = "IRSA role ARN for Celery Worker ServiceAccount"
  value       = aws_iam_role.celery_worker.arn
}

output "keda_operator_role_arn" {
  description = "IRSA role ARN for KEDA Operator ServiceAccount"
  value       = aws_iam_role.keda_operator.arn
}

output "cluster_autoscaler_role_arn" {
  description = "IRSA role ARN for Cluster Autoscaler"
  value       = aws_iam_role.cluster_autoscaler.arn
}
