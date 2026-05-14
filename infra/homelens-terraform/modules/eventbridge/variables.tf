variable "project_name" {
  type    = string
  default = "homelens"
}

variable "env" {
  type        = string
  description = "dev | staging | prod"
}

# ── Step Functions (step-functions 모듈에서 받음) ──
variable "news_pipeline_arn" {
  type = string
}

variable "price_pipeline_arn" {
  type = string
}