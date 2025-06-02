# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.0.1-alpha.2] - 2025-06-02

### Added
- JWT-based authentication system with user login/logout functionality
  - Protected edit and delete operations behind authentication
- Personal "My Statistics" view for logged-in users to see their own usage data
- Authentication middleware for secure session management
- Entry management features in Raw Data tab:
  - Inline editing of existing entries with pre-filled forms
  - Entry duplication functionality for quick similar submissions
  - Entry deletion with confirmation dialogs
- Row selection capability in Raw Data tab
- Infrastructure destroy workflow for automated cleanup
- OpenTofu support as alternative to Terraform
- Environment-aware JWT configuration for deployment security
- AWS Secrets Manager integration for JWT secrets

### Enhanced
- Code organization with new utility modules:
  - `analytics_utils.py` for shared data processing functions
  - `form_utils.py` for survey form-related functionality
  - `visualization_utils.py` for data visualization components
  - `auth_middleware.py` for authentication handling
- Tab structure and navigation:
  - Renamed tabs for better clarity
  - "Past Submissions" tab now requires authentication
- Form validation and error handling across all features
- Seed scripts now automatically create data directory if missing
- Eliminated code duplication through shared utilities (~200 lines reduced)
- Import consolidation and code organization

### Security
- Secure cookie settings for production deployment
- JWT audience configuration with environment awareness
- Environment variable validation for deployed environments

### Infrastructure
- Moved from `terraform/` to `infra/` directory structure
- Added OpenTofu configuration files alongside Terraform
- Enhanced GitHub Actions workflow with OpenTofu support
- Infrastructure destroy automation with safety validations

### Dependencies
- Added PyJWT for JSON Web Token authentication

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

[v0.0.1-alpha.2]: https://github.com/suhailskhan/ai-usage-log/releases/tag/v0.0.1-alpha.2
[v0.0.1-alpha.1]: https://github.com/suhailskhan/ai-usage-log/releases/tag/v0.0.1-alpha.1
