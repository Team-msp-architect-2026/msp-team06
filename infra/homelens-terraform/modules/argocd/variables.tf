variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "eks_cluster_name" {
  type        = string
  description = "EKS 클러스터 이름 (kubeconfig 업데이트용)"
}

variable "repo_url" {
  type        = string
  description = "GitHub repo HTTPS URL"
  default     = "https://github.com/Team-msp-architect-2026/msp-team06"
}

variable "git_revision" {
  type        = string
  description = "ArgoCD가 추적할 Git 브랜치 또는 태그"
  default     = "dev"
}

variable "k8s_manifests_path" {
  type        = string
  description = "레포 내 k8s 매니페스트 디렉토리 경로"
  default     = "infra/k8s"
}

variable "github_token" {
  type        = string
  sensitive   = true
  description = "Private repo 접근용 GitHub PAT (public repo면 빈 문자열)"
  default     = ""
}
