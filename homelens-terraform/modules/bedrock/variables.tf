variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev / staging / prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region where Bedrock is available"
  type        = string
  default     = "eu-west-3"
}
