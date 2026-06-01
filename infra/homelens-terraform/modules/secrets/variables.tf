variable "project_name" {
  type    = string
  default = "homelens"
}

variable "env" {
  type        = string
  description = "dev | staging | prod"
}

# 외부 API 키 — secrets.auto.tfvars에서 주입, 절대 커밋 금지
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

# 인프라 파생값 — RDS / ElastiCache 모듈 output에서 전달
variable "rds_endpoint" {
  type    = string
  default = ""
}

variable "rds_secret_arn" {
  type    = string
  default = ""
}

variable "redis_endpoint" {
  type    = string
  default = ""
}

variable "redis_auth_token" {
  type      = string
  sensitive = true
  default   = null
}

# Bedrock 설정 — 민감정보 아님
variable "bedrock_model_id" {
  type    = string
  default = "eu.anthropic.claude-sonnet-4-6-20250514-v1:0"
}

variable "bedrock_region" {
  type    = string
  default = "eu-west-3"
}