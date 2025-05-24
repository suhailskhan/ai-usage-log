variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token with Zone:Edit permissions"
  type        = string
  sensitive   = true
}

variable "cloudflare_zone_id" {
  description = "Cloudflare Zone ID"
  type        = string
}

variable "domain_name" {
  description = "The main domain name (e.g., suhailskhan.com)"
  type        = string
  default     = "suhailskhan.com"
}

variable "subdomain" {
  description = "The subdomain to use for the app"
  type        = string
  default     = "ai-usage-log"
}
