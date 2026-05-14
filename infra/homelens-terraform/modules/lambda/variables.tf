variable "project_name" {
  type    = string
  default = "homelens"
}

variable "env" {
  type        = string
  description = "dev | staging | prod"
}

# ── SQS (sqs 모듈에서 받음) ──────────────────────────
variable "report_queue_url" {
  type = string
}

variable "report_queue_arn" {
  type = string
}

variable "news_summary_queue_url" {
  type = string
}

variable "news_summary_queue_arn" {
  type = string
}

variable "price_ingest_queue_url" {
  type = string
}

variable "price_ingest_queue_arn" {
  type = string
}

# ── S3 (s3 모듈에서 받음) ────────────────────────────
variable "raw_data_bucket_name" {
  type = string
}

variable "raw_data_bucket_arn" {
  type = string
}
