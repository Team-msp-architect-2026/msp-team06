variable "project_name" {
  type    = string
  default = "homelens"
}

variable "env" {
  type        = string
  description = "dev | staging | prod"
}

variable "alb_arn_suffix" {
  type        = string
  description = "ALB ARN suffix — networking 모듈에서 받음"
}

variable "aws_region" {
  type        = string
  description = "AWS region"
  default     = "eu-west-3"
}