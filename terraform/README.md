# AI Usage Log - Terraform Configuration

This directory contains Terraform configurations for deploying the AI Usage Log application on AWS Fargate.

## Architecture

The infrastructure includes:

- **ECS Fargate** for running containerized applications
- **Application Load Balancer** for distributing traffic
- **Amazon EFS** for persistent SQLite database/CSV storage
- **AWS Secrets Manager** for environment variables
- **EventBridge** for scheduling the weekly digest email
- **Route 53 Hosted Zone** for DNS management within AWS
- **ACM Certificate** for SSL/TLS encryption
- **Cloudflare NS Records** for subdomain delegation to Route 53

## Prerequisites

- AWS CLI configured with appropriate credentials
- OpenTofu/Terraform installed
- Docker image pushed to GHCR (e.g. ghcr.io/suhailskhan/ai-usage-log:latest)
- Domain with DNS zone hosted on Cloudflare nameservers
- Cloudflare API token with Zone:Edit permissions

## Configuration

1. Copy and configure the terraform.tfvars file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Update terraform.tfvars with your values:
   ```hcl
   aws_region = "us-east-1"
   environment = "dev"
   domain_name = "suhailskhan.com"        # Your root domain
   subdomain   = "ai-usage-log"           # The subdomain to use for the app
   cloudflare_api_token = "your-cloudflare-api-token"
   cloudflare_zone_id = "your-cloudflare-zone-id"
   ```

- The full app URL will be constructed as: `https://${subdomain}.${domain_name}` and used for ACM, Route 53, Cloudflare, and the app environment.

## DNS and Domain Configuration

This setup uses a hybrid DNS approach combining Amazon Route 53 and Cloudflare:

### Route 53
- Creates a hosted zone for the subdomain (e.g., `ai-usage-log.suhailskhan.com`)
- Manages DNS records within AWS for ALB integration
- Provides seamless integration with ACM for SSL certificate validation

### Cloudflare
- Manages the root domain DNS (e.g., `suhailskhan.com`)
- Creates NS records pointing the subdomain to Amazon Route 53 nameservers
- Delegates DNS control of the subdomain to Amazon Route 53

### SSL/TLS Configuration
- ACM certificate is automatically provisioned for the subdomain
- Certificate validation occurs via DNS validation in Route 53
- ALB listener is configured for HTTPS on port 443
- HTTP traffic on port 80 is redirected to HTTPS

### Getting Cloudflare Credentials

1. **API Token**: Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
   - Create a new token with Zone:Edit permissions for your domain
   - The token needs permissions to edit DNS records
   
2. **Zone ID**: Found in the Cloudflare dashboard for your domain
   - Go to your domain overview page and copy the Zone ID from the right sidebar

### Understanding the DNS Flow

1. **Cloudflare** manages your root domain (e.g., `suhailskhan.com`)
2. **Terraform** creates a Route 53 hosted zone for your subdomain (e.g., `ai-usage-log.suhailskhan.com`)
3. **Terraform** automatically creates NS records in Cloudflare pointing the subdomain to AWS nameservers
4. **Route 53** takes full control of DNS for the subdomain and integrates with the ALB
5. **ACM** validates the SSL certificate using DNS validation in Route 53
6. **Traffic flows directly** from users → Route 53 → ALB

## Deployment Steps

1. Initialize Terraform:
   ```
   terraform init
   ```

2. Review the plan:
   ```
   terraform plan
   ```

3. Apply the configuration:
   ```
   terraform apply
   ```

4. Store environment variables in AWS Secrets Manager:
   ```
   aws secretsmanager put-secret-value \
     --secret-id ai-usage-log-env \
     --secret-string '{
       "MANAGER_CHOICES": "Manager 1,Manager 2",
       "TOOL_CHOICES": "ChatGPT,GitHub Copilot",
       "PURPOSE_CHOICES": "Development,Writing,Other",
       "STORAGE_TYPE": "SQLite",
       "SMTP_SERVER": "smtp.example.com",
       "SMTP_PORT": "465",
       "SMTP_USERNAME": "your_email@example.com",
       "SMTP_PASSWORD": "your_password",
       "RECIPIENTS": "recipient1@example.com,recipient2@example.com"
     }'
   ```

5. Access the application using your custom domain once DNS propagation is complete

## DNS Verification

After deployment, you can verify the DNS configuration:

```bash
# Check Route 53 nameservers for your subdomain
dig NS ai-usage-log.suhailskhan.com

# Verify the A record points to your ALB
dig ai-usage-log.suhailskhan.com

# Check SSL certificate
curl -I https://ai-usage-log.suhailskhan.com
```

## Important Notes

- The SQLite database/CSV is stored on EFS for persistence and shared access
- The container expects the database/CSV to be in `/app/data`
- The application will be accessible via HTTPS at your custom domain (e.g., `https://ai-usage-log.suhailskhan.com`)
- SSL certificate is automatically provisioned and renewed via ACM
- Traffic goes directly to AWS ALB
- Route 53 handles subdomain DNS resolution and ALB integration

## Cleanup

To destroy all created resources:
```
terraform destroy
```
