# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.0.1-alpha.1] - 2025-05-23

### Added
- Initial Streamlit-based web application for AI tool usage tracking
- Data entry form with comprehensive fields:
  - Employee name and manager selection
  - AI tool selection (ChatGPT, GitHub Copilot, etc.)
  - Usage purpose categorization
  - Duration tracking and time-saved metrics
  - Task complexity and satisfaction ratings
  - Workflow impact assessment
- Analytics dashboard with multiple visualization features:
  - Purpose distribution pie chart
  - Time saved analysis with before/after comparison
  - Duration analysis by AI tool
  - Tool effectiveness benchmarking
  - Complexity vs impact analysis
  - Satisfaction vs efficiency scatter plot
  - Manager/team performance insights
  - Purpose-based use case table
  - Trend and seasonality analysis with time-series charts
- Weekly digest email functionality for automated reporting
- Flexible storage backend supporting:
  - SQLite database storage (default)
  - CSV file storage option
- Environment-based configuration system:
  - Configurable manager choices via `MANAGER_CHOICES` env var
  - Configurable tool choices via `TOOL_CHOICES` env var
  - Configurable purpose categories via `PURPOSE_CHOICES` env var
  - Storage type selection via `STORAGE_TYPE` env var
  - Digest email SMTP configuration via various env vars
- Sample data seeding utilities for testing and demonstration
- Containerization
- Terraform infrastructure configuration for AWS ECS Fargate deployment

### Dependencies
- Streamlit (v1.45.x) for web application framework
- Pandas (v2.2.x) for data manipulation
- Plotly (v6.1.x) for interactive visualizations
- Matplotlib (v3.10.x) and Seaborn (v0.13.x) for additional charting
- Python-dotenv (v1.1.x) for environment configuration
- Schedule (v1.2.x) for automated email scheduling
- Faker (v37.3.x) for sample data generation

### Infrastructure
- Containerized application with multi-stage build
- Terraform configuration for AWS deployment
- SQLite database/CSV
- Environment variable configuration system

[v0.0.1-alpha.1]: https://github.com/suhailskhan/ai-usage-log/releases/tag/v0.0.1-alpha.1
