provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_ca_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name, "--region", var.aws_region]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_ca_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name, "--region", var.aws_region]
    }
  }
}

module "networking" {
  source       = "../../modules/networking"
  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
}

module "eks" {
  source       = "../../modules/eks"
  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  cluster_version           = var.cluster_version
  private_subnet_ids        = module.networking.private_subnet_ids
  eks_node_sg_id            = module.networking.eks_node_sg_id
  alb_sg_id                 = module.networking.alb_sg_id
  rds_sg_id                 = module.networking.rds_sg_id
  redis_sg_id               = module.networking.redis_sg_id

  api_node_instance_type    = var.api_node_instance_type
  api_node_min_size         = var.api_node_min_size
  api_node_desired_size     = var.api_node_desired_size
  api_node_max_size         = var.api_node_max_size

  worker_node_instance_type = var.worker_node_instance_type
  worker_node_min_size      = var.worker_node_min_size
  worker_node_desired_size  = var.worker_node_desired_size
  worker_node_max_size      = var.worker_node_max_size
}

module "rds" {
  source       = "../../modules/rds"
  project_name = var.project_name
  env          = var.environment

  db_subnet_ids         = module.networking.db_subnet_ids
  rds_sg_id             = module.networking.rds_sg_id
  instance_class        = var.rds_instance_class
  multi_az              = var.rds_multi_az
  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
}

module "elasticache" {
  source       = "../../modules/elasticache"
  project_name = var.project_name
  env          = var.environment

  db_subnet_ids = module.networking.db_subnet_ids
  redis_sg_id   = module.networking.redis_sg_id
  node_type     = var.redis_node_type
}

module "sqs" {
  source       = "../../modules/sqs"
  project_name = var.project_name
  env          = var.environment
}

module "secrets" {
  source       = "../../modules/secrets"
  project_name = var.project_name
  env          = var.environment

  kakao_rest_api_key  = var.kakao_rest_api_key
  kakao_js_api_key    = var.kakao_js_api_key
  naver_client_id     = var.naver_client_id
  naver_client_secret = var.naver_client_secret
  molit_service_key   = var.molit_service_key
  mois_service_key    = var.mois_service_key

  rds_endpoint   = module.rds.rds_endpoint
  rds_secret_arn = module.rds.rds_secret_arn
  redis_endpoint = module.elasticache.redis_primary_endpoint
}

module "s3" {
  source       = "../../modules/s3"
  project_name = var.project_name
  env          = var.environment
}

module "alb" {
  source       = "../../modules/alb"
  project_name = var.project_name
  environment  = var.environment

  public_subnet_ids       = module.networking.public_subnet_ids
  alb_sg_id               = module.networking.alb_sg_id
  vpc_id                  = module.networking.vpc_id
  alb_controller_role_arn = module.eks.alb_controller_role_arn
  eks_cluster_name        = module.eks.cluster_name
  aws_region              = var.aws_region
  acm_certificate_arn     = "arn:aws:acm:eu-west-3:611058323802:certificate/cbf76714-d305-4f44-a7ee-c0d347ccd808"
}

module "lambda" {
  source       = "../../modules/lambda"
  project_name = var.project_name
  env          = var.environment

  report_queue_url       = module.sqs.report_queue_url
  report_queue_arn       = module.sqs.report_queue_arn
  news_summary_queue_url = module.sqs.news_summary_queue_url
  news_summary_queue_arn = module.sqs.news_summary_queue_arn
  price_ingest_queue_url = module.sqs.price_ingest_queue_url
  price_ingest_queue_arn = module.sqs.price_ingest_queue_arn
  raw_data_bucket_name   = module.s3.raw_data_bucket_name
  raw_data_bucket_arn    = module.s3.raw_data_bucket_arn

  private_subnet_ids = module.networking.private_subnet_ids
  lambda_sg_id       = module.networking.eks_node_sg_id
  redis_host         = module.elasticache.redis_primary_endpoint
}

module "step_functions" {
  source       = "../../modules/step-functions"
  project_name = var.project_name
  env          = var.environment

  news_collector_arn          = module.lambda.news_collector_arn
  news_summarizer_trigger_arn = module.lambda.news_summarizer_trigger_arn
  molit_price_ingest_arn      = module.lambda.molit_price_ingest_arn
  region_normalizer_arn       = module.lambda.region_normalizer_arn
}

module "eventbridge" {
  source       = "../../modules/eventbridge"
  project_name = var.project_name
  env          = var.environment

  news_pipeline_arn  = module.step_functions.news_pipeline_arn
  price_pipeline_arn = module.step_functions.price_pipeline_arn
}

module "waf_cdn" {
  source       = "../../modules/waf-cdn"
  project_name = var.project_name
  environment  = var.environment
  domain_name  = "ourhomelens.com"
  acm_certificate_arn = "arn:aws:acm:us-east-1:611058323802:certificate/6be544e8-d753-4c2b-aec5-53a041884db9"

  providers = {
    aws.us_east_1 = aws.us_east_1
  }
}

module "dns" {
  source       = "../../modules/dns"
  project_name = var.project_name
  environment  = var.environment

  alb_dns_name           = module.alb.alb_dns_name
  alb_zone_id            = module.alb.alb_zone_id
  cloudfront_domain_name = module.waf_cdn.cloudfront_domain_name
}

module "monitoring" {
  source       = "../../modules/monitoring"
  project_name = var.project_name
  env          = var.environment
  aws_region   = var.aws_region

  alb_arn_suffix = module.alb.alb_arn_suffix
}

module "bedrock" {
  source       = "../../modules/bedrock"
  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  depends_on = [module.secrets]
}

module "celery" {
  source       = "../../modules/celery"
  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  eks_cluster_name       = module.eks.cluster_name
  celery_worker_role_arn = module.eks.celery_worker_role_arn
  keda_operator_role_arn = module.eks.keda_operator_role_arn
  sqs_queue_url          = module.sqs.report_queue_url

  depends_on = [module.eks, module.sqs]
}

module "argocd" {
  source       = "../../modules/argocd"
  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region

  eks_cluster_name   = module.eks.cluster_name
  repo_url           = "https://github.com/Team-msp-architect-2026/msp-team06"
  git_revision       = "dev"
  k8s_manifests_path = "infra/k8s"
  github_token       = var.github_token

  depends_on = [module.eks, module.alb, module.celery]
}
