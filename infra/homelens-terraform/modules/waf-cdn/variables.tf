variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev / staging / prod)"
  type        = string
}

variable "domain_name" {
  description = "Route 53 도메인 (e.g. ourhomelens.com)"
  type        = string
  default     = "ourhomelens.com"
}

variable "acm_certificate_arn" {
  description = "ACM 인증서 ARN — us-east-1 발급 (CloudFront 필수)"
  type        = string
  default     = "arn:aws:acm:us-east-1:611058323802:certificate/6be544e8-d753-4c2b-aec5-53a041884db9"
}

variable "default_ttl" {
  description = "CloudFront default TTL in seconds"
  type        = number
  default     = 60
}

variable "max_ttl" {
  description = "CloudFront max TTL in seconds"
  type        = number
  default     = 300
}

variable "min_ttl" {
  description = "CloudFront min TTL in seconds"
  type        = number
  default     = 0
}
