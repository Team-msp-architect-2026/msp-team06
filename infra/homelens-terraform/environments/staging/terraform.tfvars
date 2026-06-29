aws_region   = "eu-west-3"
project_name = "homelens"
environment  = "staging"

# EKS — api node group
cluster_version        = "1.35"
api_node_instance_type = "t3.medium"
api_node_min_size      = 1
api_node_desired_size  = 2
api_node_max_size      = 3

# EKS — worker node group
worker_node_instance_type = "t3.medium"
worker_node_min_size      = 0
worker_node_desired_size  = 1
worker_node_max_size      = 3

# RDS
rds_instance_class        = "db.t4g.medium"
rds_multi_az              = false
rds_allocated_storage     = 50
rds_max_allocated_storage = 50

# ElastiCache Redis
redis_node_type       = "cache.t4g.small"
