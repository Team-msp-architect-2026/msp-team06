locals {
  name_prefix = "${var.project_name}-${var.environment}"
}

# ---------------------------------------------------------------------------
# IAM — EKS Cluster Role
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "eks_cluster_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eks_cluster" {
  name               = "${local.name_prefix}-eks-cluster-role"
  assume_role_policy = data.aws_iam_policy_document.eks_cluster_assume.json
}

resource "aws_iam_role_policy_attachment" "eks_cluster" {
  role       = aws_iam_role.eks_cluster.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

# ---------------------------------------------------------------------------
# IAM — EKS Node Role
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "eks_node_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eks_node" {
  name               = "${local.name_prefix}-eks-node-role"
  assume_role_policy = data.aws_iam_policy_document.eks_node_assume.json
}

resource "aws_iam_role_policy_attachment" "eks_node_policies" {
  for_each = toset([
    "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy",
  ])

  role       = aws_iam_role.eks_node.name
  policy_arn = each.value
}

# ---------------------------------------------------------------------------
# EKS Cluster
# ---------------------------------------------------------------------------
resource "aws_eks_cluster" "main" {
  name     = "${local.name_prefix}-eks"
  version  = var.cluster_version
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids              = var.private_subnet_ids
    security_group_ids      = [var.eks_node_sg_id]
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator"]

  depends_on = [aws_iam_role_policy_attachment.eks_cluster]

  tags = { Name = "${local.name_prefix}-eks" }
}

# ---------------------------------------------------------------------------
# Node Group — api (FastAPI + 시스템 컴포넌트 통합)
# ---------------------------------------------------------------------------
resource "aws_eks_node_group" "api" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${local.name_prefix}-api"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = var.private_subnet_ids

  ami_type       = var.ami_type
  instance_types = [var.api_node_instance_type]

  scaling_config {
    min_size     = var.api_node_min_size
    desired_size = var.api_node_desired_size
    max_size     = var.api_node_max_size
  }

  update_config { max_unavailable = 1 }

  depends_on = [aws_iam_role_policy_attachment.eks_node_policies]

  tags = { Name = "${local.name_prefix}-api-node-group" }
}

# ---------------------------------------------------------------------------
# Node Group — worker (Celery — role=worker taint 적용)
# ---------------------------------------------------------------------------
resource "aws_eks_node_group" "worker" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${local.name_prefix}-worker"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = var.private_subnet_ids

  ami_type       = var.ami_type
  instance_types = [var.worker_node_instance_type]

  scaling_config {
    min_size     = var.worker_node_min_size
    desired_size = var.worker_node_desired_size
    max_size     = var.worker_node_max_size
  }

  update_config { max_unavailable = 1 }

  labels = { role = "worker" }

  taint {
    key    = "dedicated"
    value  = "worker"
    effect = "NO_SCHEDULE"
  }

  depends_on = [aws_iam_role_policy_attachment.eks_node_policies]

  tags = { Name = "${local.name_prefix}-worker-node-group" }
}

# ---------------------------------------------------------------------------
# OIDC Provider (IRSA용)
# ---------------------------------------------------------------------------
data "tls_certificate" "eks" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
}
