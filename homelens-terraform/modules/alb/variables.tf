variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev / staging / prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for ALB target group"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for ALB"
  type        = list(string)
}

variable "alb_sg_id" {
  description = "Security group ID for ALB"
  type        = string
}

variable "alb_controller_role_arn" {
  description = "IRSA role ARN for ALB Ingress Controller ServiceAccount"
  type        = string
}

variable "eks_cluster_name" {
  description = "EKS cluster name (used by ALB controller Helm values)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-3"
}

variable "acm_certificate_arn" {
  description = "ACM 인증서 ARN — eu-west-3 발급 (ALB HTTPS 리스너용)"
  type        = string
  default     = "arn:aws:acm:eu-west-3:611058323802:certificate/cbf76714-d305-4f44-a7ee-c0d347ccd808"
}
