aws_region   = "eu-west-3"
project_name = "homelens"
environment  = "dev"

# EKS — api node group
cluster_version        = "1.35"
api_node_instance_type = "t3.medium"
api_node_min_size      = 1
api_node_desired_size  = 1
api_node_max_size      = 2

# EKS — worker node group
worker_node_instance_type = "t3.medium"
worker_node_min_size      = 0
worker_node_desired_size  = 1
worker_node_max_size      = 2

# RDS
rds_instance_class        = "db.t4g.small"
rds_multi_az              = false
rds_allocated_storage     = 20
rds_max_allocated_storage = 30

# ElastiCache Redis
redis_node_type       = "cache.t4g.micro"
