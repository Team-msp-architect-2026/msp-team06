terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = ">= 5.40.0"
      configuration_aliases = [aws.us_east_1]
    }
  }
}

locals {
  name_prefix   = "${var.project_name}-${var.environment}"
  # prod: origin.ourhomelens.com / dev|staging: origin-dev.ourhomelens.com
  origin_domain = var.environment == "prod" ? "origin.${var.domain_name}" : "origin-${var.environment}.${var.domain_name}"
}

# ---------------------------------------------------------------------------
# WAF — us-east-1 에서 생성 (CloudFront 연결 필수)
# ---------------------------------------------------------------------------
resource "aws_wafv2_web_acl" "cdn" {
  provider = aws.us_east_1

  name  = "${local.name_prefix}-cdn-waf"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-common-rules"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "RateLimitRule"
    priority = 2

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-rate-limit"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-cdn-waf"
    sampled_requests_enabled   = true
  }

  tags = { Name = "${local.name_prefix}-cdn-waf" }
}

# ---------------------------------------------------------------------------
# CloudFront Distribution
# ---------------------------------------------------------------------------
resource "aws_cloudfront_distribution" "main" {
  enabled         = true
  is_ipv6_enabled = true
  comment         = "${local.name_prefix} API distribution"
  price_class     = "PriceClass_100"
  aliases         = [var.domain_name, "*.${var.domain_name}"]

  web_acl_id = aws_wafv2_web_acl.cdn.arn

  origin {
    # origin.ourhomelens.com (prod) / origin-dev.ourhomelens.com (dev/staging)
    # Route53에서 이 도메인이 ALB를 가리켜야 CloudFront SSL 검증이 통과됨
    domain_name = local.origin_domain
    origin_id   = "alb-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "alb-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "X-API-KEY", "Origin", "Accept"]
      cookies { forward = "none" }
    }

    default_ttl = var.default_ttl
    min_ttl     = var.min_ttl
    max_ttl     = var.max_ttl

    compress = true
  }

  # 조회 API 전용 캐시 동작
  ordered_cache_behavior {
    path_pattern           = "/api/v1/news/*"
    target_origin_id       = "alb-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = true
      headers      = ["X-API-KEY"]
      cookies { forward = "none" }
    }

    default_ttl = 60
    min_ttl     = 0
    max_ttl     = 300
    compress    = true
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = { Name = "${local.name_prefix}-cdn" }
}
