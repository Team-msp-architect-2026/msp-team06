variable "aws_region" {
  type    = string
  default = "eu-west-3"
}

variable "project_name" {
  type    = string
  default = "homelens"
}

variable "environment" {
  type    = string
  default = "staging"
}

variable "cluster_version" {
  type    = string
  default = "1.35"
}

variable "api_node_instance_type" { type = string }
variable "api_node_min_size"      { type = number }
variable "api_node_desired_size"  { type = number }
variable "api_node_max_size"      { type = number }

variable "worker_node_instance_type" { type = string }
variable "worker_node_min_size"      { type = number }
variable "worker_node_desired_size"  { type = number }
variable "worker_node_max_size"      { type = number }

variable "rds_instance_class"        { type = string }
variable "rds_multi_az"              { type = bool }
variable "rds_allocated_storage"     { type = number }
variable "rds_max_allocated_storage" { type = number }

variable "redis_node_type"       { type = string }
