output "vpc_id" {
  value = module.networking.vpc_id
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  value     = module.rds.rds_endpoint
  sensitive = true
}

output "redis_endpoint" {
  value     = module.elasticache.redis_primary_endpoint
  sensitive = true
}

output "alb_dns_name" {
  value = module.alb.alb_dns_name
}

output "cloudfront_domain_name" {
  value = module.waf_cdn.cloudfront_domain_name
}

output "report_queue_url" {
  value       = module.sqs.report_queue_url
  description = "Celery AI 리포트 요청 큐 URL"
}
