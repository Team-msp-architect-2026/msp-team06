variable "aws_region" {
  description = "AWS region for bootstrap resources"
  type        = string
  default     = "eu-west-3"
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "homelens"
}

variable "environments" {
  description = "List of environments to create tfstate buckets for"
  type        = list(string)
  default     = ["dev", "staging", "prod"]
}
