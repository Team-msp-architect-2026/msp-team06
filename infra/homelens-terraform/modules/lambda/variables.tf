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

# ── VPC (networking 모듈에서 받음) ───────────────────
variable "private_subnet_ids" {
  description = "RDS 접근 Lambda용 private subnet IDs"
  type        = list(string)
}

variable "lambda_sg_id" {
  description = "RDS 접근 Lambda에 붙일 보안그룹 (eks-node-sg 재사용)"
  type        = string
}

# ── ElastiCache ───────────────────────────────────────
variable "redis_host" {
  description = "Redis primary endpoint"
  type        = string
}

variable "redis_port" {
  description = "Redis port"
  type        = number
  default     = 6379
}
