# AI Usage Log - Terraform Configuration

This directory contains Terraform configurations for deploying the AI Usage Log application on AWS Fargate.

## Architecture

The infrastructure includes:

- **ECS Fargate** for running containerized applications
- **Application Load Balancer** for distributing traffic
- **Amazon EFS** for persistent SQLite database storage
- **AWS Secrets Manager** for environment variables
- **EventBridge** for scheduling the weekly digest email

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform installed (version 1.0+)
- Docker image pushed to GHCR (ghcr.io/suhailskhan/ai-usage-log:latest)

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
       "RECIPIENTS": "recipient1@example.com,recipient2@example.com",
       "STREAMLIT_APP_URL": "http://your-alb-dns-name"
     }'
   ```

5. Access the application using the ALB DNS name:
   ```
   terraform output alb_dns_name
   ```

## Important Notes

- The SQLite database is stored on EFS for persistence and shared access
- The container expects the database to be in `/app/data/ai_usage_log.db`
- Make sure to update the `STREAMLIT_APP_URL` in Secrets Manager with the actual ALB DNS name
- Consider adding HTTPS/SSL by configuring an ACM certificate and updating the ALB listener

## Cleanup

To destroy all created resources:
```
terraform destroy
```
