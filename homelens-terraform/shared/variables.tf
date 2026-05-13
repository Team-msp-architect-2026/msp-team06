variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-3"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "homelens"
}

variable "github_org" {
  description = "GitHub organisation or user name (GitHub 계정 정상화 후 terraform.tfvars에 입력)"
  type        = string
  default     = ""
}

variable "github_repo" {
  description = "GitHub repository name (GitHub 계정 정상화 후 terraform.tfvars에 입력)"
  type        = string
  default     = ""
}
