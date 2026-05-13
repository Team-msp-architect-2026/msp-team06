output "ecr_repository_urls" {
  description = "ECR repository URLs by name"
  value       = { for name, repo in aws_ecr_repository.repos : name => repo.repository_url }
}

output "github_actions_deploy_role_arn" {
  description = "IAM role ARN for GitHub Actions OIDC deploy"
  value       = aws_iam_role.github_actions_deploy.arn
}

output "github_oidc_provider_arn" {
  description = "GitHub Actions OIDC provider ARN"
  value       = aws_iam_openid_connect_provider.github_actions.arn
}
