variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev / staging / prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "cluster_version" {
  description = "EKS Kubernetes version"
  type        = string
  default     = "1.35"
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for EKS node groups"
  type        = list(string)
}

variable "eks_node_sg_id" {
  description = "Security group ID for EKS nodes"
  type        = string
}

variable "alb_sg_id" {
  description = "ALB security group ID — cluster SG ingress 규칙에 사용"
  type        = string
}

variable "ami_type" {
  description = "AMI type for EKS managed node groups"
  type        = string
  default     = "AL2023_x86_64_STANDARD"
}

# api node group
variable "api_node_instance_type" {
  description = "EC2 instance type for api node group"
  type        = string
}

variable "api_node_min_size" {
  description = "Minimum node count for api node group"
  type        = number
}

variable "api_node_desired_size" {
  description = "Desired node count for api node group"
  type        = number
}

variable "api_node_max_size" {
  description = "Maximum node count for api node group"
  type        = number
}

# worker node group
variable "worker_node_instance_type" {
  description = "EC2 instance type for worker node group"
  type        = string
}

variable "worker_node_min_size" {
  description = "Minimum node count for worker node group"
  type        = number
}

variable "worker_node_desired_size" {
  description = "Desired node count for worker node group"
  type        = number
}

variable "worker_node_max_size" {
  description = "Maximum node count for worker node group"
  type        = number
}
