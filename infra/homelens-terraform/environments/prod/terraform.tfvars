aws_region   = "eu-west-3"
project_name = "homelens"
environment  = "prod"

# EKS — api node group
cluster_version        = "1.35"
api_node_instance_type = "t3.large"
api_node_min_size      = 2
api_node_desired_size  = 2
api_node_max_size      = 4

# EKS — worker node group
worker_node_instance_type = "t3.large"
worker_node_min_size      = 1
worker_node_desired_size  = 2
worker_node_max_size      = 5

# RDS
rds_instance_class        = "db.t4g.medium"
rds_multi_az              = true
rds_allocated_storage     = 100
rds_max_allocated_storage = 200

# ElastiCache Redis
redis_node_type       = "cache.t4g.medium"
