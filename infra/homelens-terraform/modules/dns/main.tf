locals {
  name_prefix = "${var.project_name}-${var.environment}"

  # prod: api.ourhomelens.com / dev|staging: api-dev.ourhomelens.com
  api_subdomain = var.environment == "prod" ? "api.${var.hosted_zone_name}" : "api-${var.environment}.${var.hosted_zone_name}"

  # prod: origin.ourhomelens.com / dev|staging: origin-dev.ourhomelens.com
  origin_subdomain = var.environment == "prod" ? "origin.${var.hosted_zone_name}" : "origin-${var.environment}.${var.hosted_zone_name}"

  # prod: ourhomelens.com / dev|staging: dev.ourhomelens.com
  cdn_domain = var.environment == "prod" ? var.hosted_zone_name : "${var.environment}.${var.hosted_zone_name}"
}

# Route53 도메인 등록 시 생성된 기존 hosted zone 참조 (신규 생성 아님)
data "aws_route53_zone" "main" {
  name         = var.hosted_zone_name
  private_zone = false
}

# api.ourhomelens.com (prod) / api-dev.ourhomelens.com (dev) → ALB
resource "aws_route53_record" "api_a" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = local.api_subdomain
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# origin.ourhomelens.com (prod) / origin-dev.ourhomelens.com (dev) → ALB
# CloudFront가 이 도메인으로 ALB에 HTTPS 연결 — ACM 인증서 도메인과 일치해야 함
resource "aws_route53_record" "origin_a" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = local.origin_subdomain
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# ourhomelens.com (prod) / dev.ourhomelens.com (dev) → CloudFront
# zone apex(루트 도메인)는 CNAME 사용 불가 — A alias 사용
resource "aws_route53_record" "cdn_a" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = local.cdn_domain
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = "Z2FDTNDATAQYW2" # CloudFront 고정 zone ID
    evaluate_target_health = false
  }
}
