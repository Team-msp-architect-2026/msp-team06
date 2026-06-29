locals {
  name_prefix = "${var.project_name}-${var.environment}"

  applicationset_hash = sha256(jsonencode({
    ignoreDifferences = [
      {
        group        = "apps"
        kind         = "ReplicaSet"
        jsonPointers = ["/status/terminatingReplicas"]
      }
    ]
    syncPolicy = {
      prune       = true
      selfHeal    = true
      syncOptions = ["CreateNamespace=true", "ServerSideApply=true", "ServerSideDiff=true"]
    }
  }))
}

# ---------------------------------------------------------------------------
# ArgoCD — Helm 설치
# terraform apply 시 자동 설치 → terraform destroy 후 재apply 시 자동 재설치
# server.insecure=true: TLS는 ALB에서 처리하므로 ArgoCD 자체 TLS 불필요
# ---------------------------------------------------------------------------
resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = "9.5.17"
  namespace        = "argocd"
  create_namespace = true
  timeout          = 900
  cleanup_on_fail  = true
  wait             = false

  set {
    name  = "configs.params.server\\.insecure"
    value = "true"
  }

  values = [yamlencode({
    configs = {
      cm = {
        "resource.exclusions" = "- apiGroups:\n  - apps\n  kinds:\n  - ReplicaSet\n  clusters:\n  - '*'\n"
      }
    }
  })]
}

# ---------------------------------------------------------------------------
# Private GitHub repo 접근 Secret
# github_token이 빈 문자열이면 생성 생략 (public repo인 경우)
# ---------------------------------------------------------------------------
resource "null_resource" "argocd_repo_secret" {
  count = var.github_token != "" ? 1 : 0

  triggers = {
    repo_url   = var.repo_url
    token_hash = sha256(var.github_token)
  }

  provisioner "local-exec" {
    command = <<-EOT
      aws eks update-kubeconfig --region ${var.aws_region} --name ${var.eks_cluster_name}
      kubectl apply -f - <<YAML
apiVersion: v1
kind: Secret
metadata:
  name: ${local.name_prefix}-github-repo
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repository
stringData:
  url: ${var.repo_url}
  username: git
  password: ${var.github_token}
YAML
    EOT
  }

  depends_on = [helm_release.argocd]
}

# ---------------------------------------------------------------------------
# ApplicationSet — List generator
#
# List generator를 선택한 이유:
#   - prod 추가 시 elements 배열에 원소 하나만 추가하면 됨
#   - 환경별 브랜치(revision)를 명시적으로 제어 가능
#   - 다중 클러스터로 확장 시 cluster 필드 추가만으로 대응
#
# prod 추가 예시 (elements에 추가):
#   - env: prod
#     namespace: homelens
#     revision: main
#
# selfHeal: true  → 누군가 kubectl로 직접 수정해도 git 상태로 자동 복원
# prune: true     → git에서 삭제된 리소스는 클러스터에서도 삭제
# ---------------------------------------------------------------------------
resource "null_resource" "argocd_applicationset" {
  triggers = {
    chart_version       = helm_release.argocd.version
    environment         = var.environment
    git_revision        = var.git_revision
    repo_url            = var.repo_url
    k8s_path            = var.k8s_manifests_path
    applicationset_hash = local.applicationset_hash
  }

  provisioner "local-exec" {
    command = <<-EOT
      aws eks update-kubeconfig --region ${var.aws_region} --name ${var.eks_cluster_name}
      kubectl wait --for=condition=established \
        crd/applicationsets.argoproj.io \
        --timeout=120s
      kubectl apply -f - <<YAML
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: homelens
  namespace: argocd
spec:
  generators:
  - list:
      elements:
      - env: ${var.environment}
        namespace: homelens
        revision: ${var.git_revision}
  template:
    metadata:
      name: 'homelens-{{env}}'
      finalizers:
        - resources-finalizer.argocd.argoproj.io
    spec:
      project: default
      source:
        repoURL: ${var.repo_url}
        targetRevision: '{{revision}}'
        path: ${var.k8s_manifests_path}
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
          - ServerSideApply=true
          - ServerSideDiff=true
      ignoreDifferences:
        - group: apps
          kind: ReplicaSet
          jsonPointers:
            - /status/terminatingReplicas
YAML
    EOT
  }

  depends_on = [
    helm_release.argocd,
    null_resource.argocd_repo_secret,
  ]
}
