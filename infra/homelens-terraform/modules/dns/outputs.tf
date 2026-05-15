output "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  value       = data.aws_route53_zone.main.zone_id
}

output "name_servers" {
  description = "Route53 hosted zone name servers"
  value       = data.aws_route53_zone.main.name_servers
}

output "api_fqdn" {
  description = "API subdomain FQDN"
  value       = aws_route53_record.api_a.fqdn
}
