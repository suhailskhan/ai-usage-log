output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "efs_id" {
  description = "ID of the EFS file system"
  value       = aws_efs_file_system.ai_usage_log.id
}

output "secrets_manager_name" {
  description = "Name of the Secrets Manager secret"
  value       = aws_secretsmanager_secret.app_env.name
}

output "ai_usage_log_zone_name_servers" {
  description = "Route53 name servers for ai-usage-log.suhailskhan.com"
  value       = aws_route53_zone.ai_usage_log.name_servers
}
