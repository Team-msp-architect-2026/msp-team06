variable "project_name" {
  type    = string
  default = "homelens"
}

variable "env" {
  type        = string
  description = "dev | staging | prod"
}

variable "glacier_transition_days" {
  type    = number
  default = 90
  description = "molit/ 원본 데이터 Glacier 전환 일수"
}