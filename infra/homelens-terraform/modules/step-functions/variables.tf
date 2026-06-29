variable "project_name" {
  type    = string
  default = "homelens"
}

variable "env" {
  type        = string
  description = "dev | staging | prod"
}

# ── Lambda ARN (lambda 모듈에서 받음) ─────────────
variable "news_collector_arn" {
  type = string
}

variable "news_summarizer_trigger_arn" {
  type = string
}

variable "molit_price_ingest_arn" {
  type = string
}

variable "region_normalizer_arn" {
  type = string
}