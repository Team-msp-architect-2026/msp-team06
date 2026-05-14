output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.main.id
}

output "waf_arn" {
  description = "WAF WebACL ARN"
  value       = aws_wafv2_web_acl.cdn.arn
}
