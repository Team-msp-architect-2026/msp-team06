output "redis_primary_endpoint" {
    value     = aws_elasticache_replication_group.main.primary_endpoint_address
    description = "FastAPI / Celery Redis 연결용"
}

output "redis_port" {
    value = 6379
}
