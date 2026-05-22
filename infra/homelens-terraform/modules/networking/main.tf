locals {
  name_prefix = "${var.project_name}-${var.environment}"

  # 서브넷 정의 — terraform_instructions.md §2-2
  public_subnets = [
    { az = "eu-west-3a", cidr = "10.0.10.0/24" },
    { az = "eu-west-3c", cidr = "10.0.110.0/24" },
  ]
  private_subnets = [
    { az = "eu-west-3a", cidr = "10.0.20.0/24" },
    { az = "eu-west-3c", cidr = "10.0.120.0/24" },
  ]
  db_subnets = [
    { az = "eu-west-3a", cidr = "10.0.30.0/24" },
    { az = "eu-west-3c", cidr = "10.0.130.0/24" },
  ]

  # dev/staging 공통 Interface Endpoint 서비스
  common_interface_endpoints = {
    ecr_api         = "com.amazonaws.${var.aws_region}.ecr.api"
    ecr_dkr         = "com.amazonaws.${var.aws_region}.ecr.dkr"
    sqs             = "com.amazonaws.${var.aws_region}.sqs"
    secretsmanager  = "com.amazonaws.${var.aws_region}.secretsmanager"
    sts             = "com.amazonaws.${var.aws_region}.sts"
    logs            = "com.amazonaws.${var.aws_region}.logs"
    bedrock_runtime = "com.amazonaws.${var.aws_region}.bedrock-runtime"
  }

  # prod 추가 Interface Endpoint 서비스
  prod_interface_endpoints = {
    eks             = "com.amazonaws.${var.aws_region}.eks"
    ec2             = "com.amazonaws.${var.aws_region}.ec2"
    elb             = "com.amazonaws.${var.aws_region}.elasticloadbalancing"
    monitoring      = "com.amazonaws.${var.aws_region}.monitoring"
    xray            = "com.amazonaws.${var.aws_region}.xray"
    states          = "com.amazonaws.${var.aws_region}.states"
    events          = "com.amazonaws.${var.aws_region}.events"
  }

  interface_endpoints = var.environment == "prod" ? merge(
    local.common_interface_endpoints,
    local.prod_interface_endpoints
  ) : local.common_interface_endpoints
}

# ---------------------------------------------------------------------------
# VPC
# ---------------------------------------------------------------------------
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${local.name_prefix}-vpc" }
}

# ---------------------------------------------------------------------------
# Internet Gateway
# ---------------------------------------------------------------------------
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name_prefix}-igw" }
}

# ---------------------------------------------------------------------------
# Public Subnets
# ---------------------------------------------------------------------------
resource "aws_subnet" "public" {
  count = length(local.public_subnets)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = local.public_subnets[count.index].cidr
  availability_zone       = local.public_subnets[count.index].az
  map_public_ip_on_launch = true

  tags = {
    Name                                                          = "${local.name_prefix}-public-${local.public_subnets[count.index].az}"
    "kubernetes.io/role/elb"                                      = "1"
    "kubernetes.io/cluster/${local.name_prefix}-eks"              = "shared"
  }
}

# ---------------------------------------------------------------------------
# Private Subnets (EKS 노드)
# ---------------------------------------------------------------------------
resource "aws_subnet" "private" {
  count = length(local.private_subnets)

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.private_subnets[count.index].cidr
  availability_zone = local.private_subnets[count.index].az

  tags = {
    Name                                                          = "${local.name_prefix}-private-${local.private_subnets[count.index].az}"
    "kubernetes.io/role/internal-elb"                             = "1"
    "kubernetes.io/cluster/${local.name_prefix}-eks"              = "shared"
  }
}

# ---------------------------------------------------------------------------
# DB Subnets (RDS / ElastiCache)
# ---------------------------------------------------------------------------
resource "aws_subnet" "db" {
  count = length(local.db_subnets)

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.db_subnets[count.index].cidr
  availability_zone = local.db_subnets[count.index].az

  tags = { Name = "${local.name_prefix}-db-${local.db_subnets[count.index].az}" }
}

# ---------------------------------------------------------------------------
# Elastic IPs for NAT Gateway
# ---------------------------------------------------------------------------
resource "aws_eip" "nat" {
  count  = 2
  domain = "vpc"
  tags   = { Name = "${local.name_prefix}-nat-eip-${count.index}" }
}

# ---------------------------------------------------------------------------
# NAT Gateways (az-a, az-c 각 1개)
# ---------------------------------------------------------------------------
resource "aws_nat_gateway" "main" {
  count = 2

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = { Name = "${local.name_prefix}-nat-${local.public_subnets[count.index].az}" }

  depends_on = [aws_internet_gateway.main]
}

# ---------------------------------------------------------------------------
# Route Tables — Public
# ---------------------------------------------------------------------------
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name_prefix}-rt-public" }
}

resource "aws_route" "public_igw" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ---------------------------------------------------------------------------
# Route Tables — Private (az-a → NAT 0, az-c → NAT 1)
# ---------------------------------------------------------------------------
resource "aws_route_table" "private" {
  count  = 2
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${local.name_prefix}-rt-private-${local.private_subnets[count.index].az}" }
}

resource "aws_route" "private_nat" {
  count = 2

  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[count.index].id
}

resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_route_table_association" "db" {
  count          = 2
  subnet_id      = aws_subnet.db[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# ---------------------------------------------------------------------------
# Security Groups
# ---------------------------------------------------------------------------

# ALB SG
resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "ALB inbound HTTPS/HTTP"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP (redirect)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-alb-sg" }
}

# EKS Node SG
resource "aws_security_group" "eks_node" {
  name        = "${local.name_prefix}-eks-node-sg"
  description = "EKS node group"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Node-to-node"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-eks-node-sg" }
}

# ALB egress → EKS — 순환 참조 방지를 위해 별도 리소스로 분리
# ingress 쪽(eks_from_alb)은 EKS cluster SG에서 관리 (eks 모듈 참고)
resource "aws_security_group_rule" "alb_to_eks" {
  type                     = "egress"
  description              = "ALB to EKS API port"
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
  security_group_id        = aws_security_group.alb.id
  source_security_group_id = aws_security_group.eks_node.id
}

# RDS SG
# ingress 규칙은 eks 모듈에서 aws_security_group_rule로 추가 (cluster SG 소스)
# eks_node_sg는 노드에 붙지 않으므로 소스로 사용 불가
resource "aws_security_group" "rds" {
  name        = "${local.name_prefix}-rds-sg"
  description = "RDS PostgreSQL"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "${local.name_prefix}-rds-sg" }
}

# Redis SG
# ingress 규칙은 eks 모듈에서 aws_security_group_rule로 추가 (cluster SG 소스)
resource "aws_security_group" "redis" {
  name        = "${local.name_prefix}-redis-sg"
  description = "ElastiCache Redis"
  vpc_id      = aws_vpc.main.id

  tags = { Name = "${local.name_prefix}-redis-sg" }
}

# VPC Endpoint SG
resource "aws_security_group" "vpc_endpoint" {
  name        = "${local.name_prefix}-vpc-endpoint-sg"
  description = "Interface VPC Endpoints"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS from private subnets (EKS cluster SG + eks_node_sg)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [for s in local.private_subnets : s.cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-vpc-endpoint-sg" }
}

# ---------------------------------------------------------------------------
# VPC Endpoint — S3 Gateway (Route table 연결)
# ---------------------------------------------------------------------------
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = concat(
    [aws_route_table.public.id],
    aws_route_table.private[*].id
  )

  tags = { Name = "${local.name_prefix}-vpce-s3" }
}

# ---------------------------------------------------------------------------
# VPC Endpoint — Interface (공통 + prod 추가)
# ---------------------------------------------------------------------------
resource "aws_vpc_endpoint" "interface" {
  for_each = local.interface_endpoints

  vpc_id              = aws_vpc.main.id
  service_name        = each.value
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true

  subnet_ids         = aws_subnet.private[*].id
  security_group_ids = [aws_security_group.vpc_endpoint.id]

  tags = { Name = "${local.name_prefix}-vpce-${each.key}" }
}
