variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-3"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "homelens"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

# EKS
variable "cluster_version" {
  description = "EKS cluster version"
  type        = string
  default     = "1.35"
}

variable "api_node_instance_type" {
  description = "EC2 instance type for api node group"
  type        = string
}

variable "api_node_min_size" {
  description = "Minimum node count for api node group"
  type        = number
}

variable "api_node_desired_size" {
  description = "Desired node count for api node group"
  type        = number
}

variable "api_node_max_size" {
  description = "Maximum node count for api node group"
  type        = number
}

variable "worker_node_instance_type" {
  description = "EC2 instance type for worker node group"
  type        = string
}

variable "worker_node_min_size" {
  description = "Minimum node count for worker node group"
  type        = number
}

variable "worker_node_desired_size" {
  description = "Desired node count for worker node group"
  type        = number
}

variable "worker_node_max_size" {
  description = "Maximum node count for worker node group"
  type        = number
}

# RDS
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
}

variable "rds_multi_az" {
  description = "Enable RDS Multi-AZ"
  type        = bool
}

variable "rds_allocated_storage" {
  description = "RDS initial allocated storage (GB)"
  type        = number
}

variable "rds_max_allocated_storage" {
  description = "RDS max allocated storage for autoscaling (GB)"
  type        = number
}

# ElastiCache
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
}

# Secrets — 외부 API 키 (secrets.auto.tfvars에서 주입, 절대 커밋 금지)
variable "kakao_rest_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "kakao_js_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "naver_client_id" {
  type      = string
  sensitive = true
  default   = ""
}

variable "naver_client_secret" {
  type      = string
  sensitive = true
  default   = ""
}

variable "molit_service_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "mois_service_key" {
  type      = string
  sensitive = true
  default   = ""
}

