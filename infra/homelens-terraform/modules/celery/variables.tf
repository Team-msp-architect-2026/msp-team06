variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev / staging / prod)"
  type        = string
}

variable "sqs_queue_url" {
  description = "SQS queue URL for Celery broker (report-generation-queue)"
  type        = string
}

variable "eks_cluster_name" {
  description = "EKS cluster name for Helm provider"
  type        = string
}

variable "celery_worker_role_arn" {
  description = "IRSA role ARN for Celery Worker ServiceAccount"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-3"
}

variable "replicas" {
  description = "Initial Celery worker replica count (0 = CI/CD가 실제 이미지 배포 전까지 파드 미생성)"
  type        = number
  default     = 0
}

variable "celery_image" {
  description = "Celery worker container image (repo:tag)"
  type        = string
  default     = "placeholder:latest"
}

variable "keda_operator_role_arn" {
  description = "IRSA role ARN for KEDA Operator ServiceAccount"
  type        = string
}
