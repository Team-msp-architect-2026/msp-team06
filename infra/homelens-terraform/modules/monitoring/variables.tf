variable "project_name" {
  type    = string
  default = "homelens"
}

variable "env" {
  type        = string
  description = "dev | staging | prod"
}

variable "alb_arn_suffix" {
  type        = string
  description = "ALB ARN suffix — networking 모듈에서 받음"
}

variable "aws_region" {
  type        = string
  description = "AWS region"
  default     = "eu-west-3"
}

variable "eks_cluster_name" {
  type        = string
  description = "EKS 클러스터 이름 - kube-prometheus-stack 설치 및 scrape설정에 필요"
}

variable "prometheus_stack_version" {
  type        = string
  description = "kube-prometheus-stack Helm chart 버전"
  default     = "58.2.2"
}

variable "grafana_admin_password" {
  type        = string
  sensitive   = true
  description = "Grafana admin 비밀번호 (terraform.tfvars또는 환경변수로 주입)"
  default     = "Homelens@2026!"
}