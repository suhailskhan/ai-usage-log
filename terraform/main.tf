terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
  
  backend "s3" {
    bucket = "ai-usage-state"
    key    = "ai-usage-log/terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

locals {
  full_domain_name = "${var.subdomain}.${var.domain_name}"
}

# Network resources
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "ai-usage-log-vpc"
  }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true

  tags = {
    Name = "ai-usage-log-public-a"
  }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true

  tags = {
    Name = "ai-usage-log-public-b"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "ai-usage-log-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "ai-usage-log-public-rt"
  }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

# Security groups
resource "aws_security_group" "alb" {
  name        = "ai-usage-log-alb-sg"
  description = "Security group for the ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "fargate" {
  name        = "ai-usage-log-fargate-sg"
  description = "Security group for Fargate containers"
  vpc_id      = aws_vpc.main.id

  ingress {
    protocol        = "tcp"
    from_port       = 8501
    to_port         = 8501
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "efs" {
  name        = "ai-usage-log-efs-sg"
  description = "Security group for EFS"
  vpc_id      = aws_vpc.main.id

  ingress {
    protocol        = "tcp"
    from_port       = 2049
    to_port         = 2049
    security_groups = [aws_security_group.fargate.id]
  }

  egress {
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EFS for shared database storage
resource "aws_efs_file_system" "ai_usage_log" {
  creation_token = "ai-usage-log-efs"
  
  tags = {
    Name = "ai-usage-log-efs"
  }
}

resource "aws_efs_mount_target" "efs_mt_a" {
  file_system_id = aws_efs_file_system.ai_usage_log.id
  subnet_id      = aws_subnet.public_a.id
  security_groups = [aws_security_group.efs.id]
}

resource "aws_efs_mount_target" "efs_mt_b" {
  file_system_id = aws_efs_file_system.ai_usage_log.id
  subnet_id      = aws_subnet.public_b.id
  security_groups = [aws_security_group.efs.id]
}

# IAM roles for ECS tasks
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "ai-usage-log-execution-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Add permissions to access Secrets Manager
resource "aws_iam_policy" "secrets_access" {
  name        = "ai-usage-log-secrets-access"
  description = "Allow ECS tasks to access Secrets Manager"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          aws_secretsmanager_secret.app_env.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "secrets_access_attachment" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = aws_iam_policy.secrets_access.arn
}

# Secrets Manager to store environment variables
resource "aws_secretsmanager_secret" "app_env" {
  name = "ai-usage-log-env"
  recovery_window_in_days = 0  # Makes the secret immediately deletable
}

# Note: In production, set this separately after deployment
# resource "aws_secretsmanager_secret_version" "app_env_values" {
#   secret_id = aws_secretsmanager_secret.app_env.id
#   secret_string = jsonencode({
#     MANAGER_CHOICES = "Manager 1,Manager 2"
#     TOOL_CHOICES = "ChatGPT,GitHub Copilot"
#     PURPOSE_CHOICES = "Development,Writing,Other"
#     STORAGE_TYPE = "SQLite"
#     SMTP_SERVER = "placeholder"
#     SMTP_PORT = "465"
#     SMTP_USERNAME = "placeholder"
#     SMTP_PASSWORD = "placeholder"
#     RECIPIENTS = "placeholder@example.com"
#     STREAMLIT_APP_URL = "https://your-streamlit-app-url"
#   })
# }

# Load balancer
resource "aws_lb" "main" {
  name               = "ai-usage-log-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]
  
  tags = {
    Name = "ai-usage-log-alb"
  }
}

resource "aws_lb_target_group" "app" {
  name        = "ai-usage-log-tg"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
  
  health_check {
    enabled             = true
    interval            = 30
    path                = "/"
    port                = "traffic-port"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    matcher             = "200"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

resource "aws_acm_certificate" "ai_usage_log" {
  domain_name       = local.full_domain_name
  validation_method = "DNS"
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "acm_validation" {
  for_each = {
    for dvo in aws_acm_certificate.ai_usage_log.domain_validation_options : dvo.domain_name => dvo
  }
  zone_id = aws_route53_zone.ai_usage_log.id
  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  records = [each.value.resource_record_value]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "ai_usage_log" {
  certificate_arn         = aws_acm_certificate.ai_usage_log.arn
  validation_record_fqdns = [for record in aws_route53_record.acm_validation : record.fqdn]
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = aws_acm_certificate_validation.ai_usage_log.certificate_arn
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
  depends_on = [aws_acm_certificate_validation.ai_usage_log]
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "ai-usage-log-cluster"
}

# ECS Task Definition for Streamlit App
resource "aws_ecs_task_definition" "app" {
  family                   = "ai-usage-log-app"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_execution_role.arn
  
  container_definitions = jsonencode([
    {
      name      = "ai-usage-log-app"
      image     = "ghcr.io/suhailskhan/ai-usage-log:latest"
      essential = true
      
      portMappings = [
        {
          containerPort = 8501
          hostPort      = 8501
          protocol      = "tcp"
        }
      ]
      
      environment = [
        {
          name  = "STREAMLIT_SERVER_ADDRESS",
          value = "0.0.0.0"
        },
        {
          name  = "STREAMLIT_SERVER_PORT",
          value = "8501"
        },
        {
          name  = "STREAMLIT_SERVER_HEADLESS",
          value = "true"
        },
        {
          name  = "STREAMLIT_APP_URL",
          value = "https://${local.full_domain_name}"
        }
      ]
      
      secrets = [
        {
          name      = "MANAGER_CHOICES",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:MANAGER_CHOICES::"
        },
        {
          name      = "TOOL_CHOICES",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:TOOL_CHOICES::"
        },
        {
          name      = "PURPOSE_CHOICES",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:PURPOSE_CHOICES::"
        },
        {
          name      = "STORAGE_TYPE",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:STORAGE_TYPE::"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ai-usage-log"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "app"
        }
      }
      
      mountPoints = [
        {
          sourceVolume  = "efs-data"
          containerPath = "/app/data"
          readOnly      = false
        }
      ]
    }
  ])
  
  volume {
    name = "efs-data"
    
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.ai_usage_log.id
      root_directory = "/"
    }
  }
}

# ECS Service for Streamlit App
resource "aws_ecs_service" "app" {
  name             = "ai-usage-log-service"
  cluster          = aws_ecs_cluster.main.id
  task_definition  = aws_ecs_task_definition.app.arn
  desired_count    = 1
  launch_type      = "FARGATE"
  platform_version = "LATEST"
  
  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.fargate.id]
    assign_public_ip = true
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "ai-usage-log-app"
    container_port   = 8501
  }
  
  depends_on = [
    aws_lb_listener.http
  ]
}

# ECS Task Definition for Weekly Digest
resource "aws_ecs_task_definition" "digest" {
  family                   = "ai-usage-log-digest"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_execution_role.arn
  
  container_definitions = jsonencode([
    {
      name      = "ai-usage-log-digest"
      image     = "ghcr.io/suhailskhan/ai-usage-log:latest"
      essential = true
      command   = ["python", "send_weekly_digest.py"]
      
      secrets = [
        {
          name      = "MANAGER_CHOICES",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:MANAGER_CHOICES::"
        },
        {
          name      = "TOOL_CHOICES",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:TOOL_CHOICES::"
        },
        {
          name      = "PURPOSE_CHOICES",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:PURPOSE_CHOICES::"
        },
        {
          name      = "STORAGE_TYPE",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:STORAGE_TYPE::"
        },
        {
          name      = "SMTP_SERVER",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:SMTP_SERVER::"
        },
        {
          name      = "SMTP_PORT",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:SMTP_PORT::"
        },
        {
          name      = "SMTP_USERNAME",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:SMTP_USERNAME::"
        },
        {
          name      = "SMTP_PASSWORD",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:SMTP_PASSWORD::"
        },
        {
          name      = "RECIPIENTS",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:RECIPIENTS::"
        }
      ]
      
      environment = [
        {
          name  = "STREAMLIT_APP_URL",
          value = "https://${local.full_domain_name}"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ai-usage-log"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "digest"
        }
      }
      
      mountPoints = [
        {
          sourceVolume  = "efs-data"
          containerPath = "/app/data"
          readOnly      = false
        }
      ]
    }
  ])
  
  volume {
    name = "efs-data"
    
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.ai_usage_log.id
      root_directory = "/"
    }
  }
}

# ECS Task Definition for Manual DB Seeding
resource "aws_ecs_task_definition" "seed_db" {
  family                   = "ai-usage-log-seed-db"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_execution_role.arn
  
  container_definitions = jsonencode([
    {
      name      = "ai-usage-log-seed-db"
      image     = "ghcr.io/suhailskhan/ai-usage-log:latest"
      essential = true
      command   = ["python", "seed_db.py"]
      
      secrets = [
        {
          name      = "MANAGER_CHOICES",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:MANAGER_CHOICES::"
        },
        {
          name      = "TOOL_CHOICES",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:TOOL_CHOICES::"
        },
        {
          name      = "PURPOSE_CHOICES",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:PURPOSE_CHOICES::"
        },
        {
          name      = "STORAGE_TYPE",
          valueFrom = "${aws_secretsmanager_secret.app_env.arn}:STORAGE_TYPE::"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/ai-usage-log"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "seed-db"
        }
      }
      
      mountPoints = [
        {
          sourceVolume  = "efs-data"
          containerPath = "/app/data"
          readOnly      = false
        }
      ]
    }
  ])
  
  volume {
    name = "efs-data"
    
    efs_volume_configuration {
      file_system_id = aws_efs_file_system.ai_usage_log.id
      root_directory = "/"
    }
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/ai-usage-log"
  retention_in_days = 30
}

# EventBridge rule to run weekly digest
resource "aws_cloudwatch_event_rule" "weekly_digest" {
  name                = "ai-usage-log-weekly-digest"
  description         = "Trigger weekly AI usage digest email"
#   schedule_expression = "cron(0 8 ? * MON *)"  # Run at 8 AM UTC every Monday
  schedule_expression = "rate(3 hours)"  # For demo's sake, temporarily run every 3 hours
}

resource "aws_cloudwatch_event_target" "weekly_digest_target" {
  rule      = aws_cloudwatch_event_rule.weekly_digest.name
  target_id = "ai-usage-log-digest"
  arn       = aws_ecs_cluster.main.arn
  role_arn  = aws_iam_role.events_role.arn
  
  ecs_target {
    task_count          = 1
    task_definition_arn = aws_ecs_task_definition.digest.arn
    launch_type         = "FARGATE"
    platform_version    = "LATEST"
    
    network_configuration {
      subnets          = [aws_subnet.public_a.id]
      security_groups  = [aws_security_group.fargate.id]
      assign_public_ip = true
    }
  }
}

# IAM role for EventBridge to run ECS tasks
resource "aws_iam_role" "events_role" {
  name = "ai-usage-log-events-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "events_policy" {
  name        = "ai-usage-log-events-policy"
  description = "Allow EventBridge to run ECS tasks"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "ecs:RunTask"
        Resource = aws_ecs_task_definition.digest.arn
        Condition = {
          StringLike = {
            "ecs:cluster" = aws_ecs_cluster.main.arn
          }
        }
      },
      {
        Effect = "Allow"
        Action = "iam:PassRole"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "events_policy_attachment" {
  role       = aws_iam_role.events_role.name
  policy_arn = aws_iam_policy.events_policy.arn
}

# Route53 Hosted Zone
resource "aws_route53_zone" "ai_usage_log" {
  name = local.full_domain_name
}

resource "aws_route53_record" "alb_alias" {
  zone_id = aws_route53_zone.ai_usage_log.id
  name    = local.full_domain_name
  type    = "A"
  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# Cloudflare NS records for delegating ai-usage-log subdomain to Route53
resource "cloudflare_record" "ai_usage_log_ns_1" {
  zone_id = var.cloudflare_zone_id
  name    = var.subdomain
  content = aws_route53_zone.ai_usage_log.name_servers[0]
  type    = "NS"
  ttl     = 300
}

resource "cloudflare_record" "ai_usage_log_ns_2" {
  zone_id = var.cloudflare_zone_id
  name    = var.subdomain
  content = aws_route53_zone.ai_usage_log.name_servers[1]
  type    = "NS"
  ttl     = 300
}

resource "cloudflare_record" "ai_usage_log_ns_3" {
  zone_id = var.cloudflare_zone_id
  name    = var.subdomain
  content = aws_route53_zone.ai_usage_log.name_servers[2]
  type    = "NS"
  ttl     = 300
}

resource "cloudflare_record" "ai_usage_log_ns_4" {
  zone_id = var.cloudflare_zone_id
  name    = var.subdomain
  content = aws_route53_zone.ai_usage_log.name_servers[3]
  type    = "NS"
  ttl     = 300
}
