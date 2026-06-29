variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev / staging / prod)"
  type        = string
}

variable "hosted_zone_name" {
  description = "Route 53 hosted zone name"
  type        = string
  default     = "ourhomelens.com"
}

variable "alb_dns_name" {
  description = "ALB DNS name for A-record alias"
  type        = string
}

variable "alb_zone_id" {
  description = "ALB hosted zone ID for alias record"
  type        = string
}

variable "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  type        = string
}
