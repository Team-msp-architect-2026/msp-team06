locals {
  oidc_issuer = replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")
}

# ---------------------------------------------------------------------------
# IRSA — ALB Ingress Controller
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "alb_controller_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:sub"
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }
  }
}

resource "aws_iam_role" "alb_controller" {
  name               = "${local.name_prefix}-alb-controller-role"
  assume_role_policy = data.aws_iam_policy_document.alb_controller_assume.json
}

resource "aws_iam_role_policy" "alb_controller" {
  name = "alb-controller-policy"
  role = aws_iam_role.alb_controller.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "elasticloadbalancing:*",
          "ec2:DescribeVpcs",
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeInstances",
          "ec2:DescribeInternetGateways",
          "ec2:DescribeAvailabilityZones",
          "ec2:CreateSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupIngress",
          "ec2:DeleteSecurityGroup",
          "ec2:CreateTags",
          "ec2:DeleteTags",
          "ec2:DescribeTags",
          "iam:CreateServiceLinkedRole",
          "cognito-idp:DescribeUserPoolClient",
          "acm:ListCertificates",
          "acm:DescribeCertificate",
          "waf-regional:*",
          "wafv2:*",
          "shield:*",
        ]
        Resource = "*"
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# IRSA — FastAPI ServiceAccount
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "fastapi_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:sub"
      values   = ["system:serviceaccount:homelens:fastapi"]
    }
  }
}

resource "aws_iam_role" "fastapi_api" {
  name               = "${local.name_prefix}-fastapi-api-role"
  assume_role_policy = data.aws_iam_policy_document.fastapi_assume.json
}

resource "aws_iam_role_policy" "fastapi_api" {
  name = "fastapi-api-policy"
  role = aws_iam_role.fastapi_api.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:homelens/${var.environment}/*",
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:rds!db-*"
        ]
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# IRSA — Celery Worker ServiceAccount
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "celery_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:sub"
      values   = ["system:serviceaccount:homelens:celery-worker"]
    }
  }
}

resource "aws_iam_role" "celery_worker" {
  name               = "${local.name_prefix}-celery-worker-role"
  assume_role_policy = data.aws_iam_policy_document.celery_assume.json
}

resource "aws_iam_role_policy" "celery_worker" {
  name = "celery-worker-policy"
  role = aws_iam_role.celery_worker.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:ChangeMessageVisibility",
          "sqs:GetQueueAttributes",
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject"]
        Resource = [
          "arn:aws:s3:::${var.project_name}-${var.environment}-raw-data/*",
          "arn:aws:s3:::${var.project_name}-${var.environment}-report-backup/*",
        ]
      },
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = [
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:homelens/${var.environment}/*",
          "arn:aws:secretsmanager:${var.aws_region}:*:secret:rds!db-*"
        ]
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# IRSA — KEDA Operator (SQS 큐 깊이 읽기 권한)
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "keda_operator_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:sub"
      values   = ["system:serviceaccount:keda:keda-operator"]
    }
  }
}

resource "aws_iam_role" "keda_operator" {
  name               = "${local.name_prefix}-keda-operator-role"
  assume_role_policy = data.aws_iam_policy_document.keda_operator_assume.json
}

resource "aws_iam_role_policy" "keda_operator" {
  name = "keda-operator-policy"
  role = aws_iam_role.keda_operator.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl",
          "sqs:ReceiveMessage",
        ]
        Resource = "*"
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# IRSA — Cluster Autoscaler
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "cluster_autoscaler_assume" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.eks.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:aud"
      values   = ["sts.amazonaws.com"]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer}:sub"
      values   = ["system:serviceaccount:kube-system:cluster-autoscaler"]
    }
  }
}

resource "aws_iam_role" "cluster_autoscaler" {
  name               = "${local.name_prefix}-cluster-autoscaler-role"
  assume_role_policy = data.aws_iam_policy_document.cluster_autoscaler_assume.json
}

resource "aws_iam_role_policy" "cluster_autoscaler" {
  name = "cluster-autoscaler-policy"
  role = aws_iam_role.cluster_autoscaler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeScalingActivities",
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup",
          "autoscaling:DescribeTags",
          "ec2:DescribeInstanceTypes",
          "ec2:DescribeLaunchTemplateVersions",
          "ec2:DescribeImages",
          "ec2:GetInstanceTypesFromInstanceRequirements",
          "eks:DescribeNodegroup",
        ]
        Resource = "*"
      }
    ]
  })
}
