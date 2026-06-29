variable "aws_region" {
  type    = string
  default = "eu-west-3"
}

variable "project_name" {
  type    = string
  default = "homelens"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "cluster_version" {
  type    = string
  default = "1.35"
}

variable "api_node_instance_type" { type = string }
variable "api_node_min_size"      { type = number }
variable "api_node_desired_size"  { type = number }
variable "api_node_max_size"      { type = number }

variable "worker_node_instance_type" { type = string }
variable "worker_node_min_size"      { type = number }
variable "worker_node_desired_size"  { type = number }
variable "worker_node_max_size"      { type = number }

variable "rds_instance_class"        { type = string }
variable "rds_multi_az"              { type = bool }
variable "rds_allocated_storage"     { type = number }
variable "rds_max_allocated_storage" { type = number }

variable "redis_node_type" { type = string }

variable "redis_auth_token" {
  description = "Redis AUTH token (prod 필수 — CI/CD에서 TF_VAR_redis_auth_token으로 주입, tfvars에 기입 금지)"
  type        = string
  sensitive   = true
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

variable "github_token" {
  type        = string
  sensitive   = true
  description = "ArgoCD용 GitHub PAT (private repo 접근). public repo면 빈 문자열"
  default     = ""
}
