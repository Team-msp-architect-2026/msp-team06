resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-${var.env}-redis"
  subnet_ids = var.db_subnet_ids
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "${var.project_name}-${var.env}-redis"
  description          = "HomeLens Redis ${var.env}"

  engine         = "redis"
  engine_version = "7.1"
  node_type      = var.node_type

  num_cache_clusters = var.env == "prod" ? 2 : 1

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [var.redis_sg_id]

  auth_token                 = var.env == "prod" ? var.redis_auth_token : null
  transit_encryption_enabled = var.env == "prod" ? true : false
  at_rest_encryption_enabled = true

  tags = { Env = var.env }
}
