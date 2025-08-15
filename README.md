# dbt + Airflow + GitHub Actions: Hybrid Data Pipeline

A modern data engineering architecture demonstrating **hybrid orchestration** where Airflow triggers GitHub Actions to run dbt transformations on Databricks. This pattern combines the orchestration power of Airflow with the CI/CD capabilities of GitHub Actions.

## 🏗️ Architecture Overview

```
┌─────────────────┐    API Call    ┌──────────────────┐    Execute    ┌─────────────┐
│  Apache Airflow │ ──────────────▶│  GitHub Actions  │ ────────────▶│ dbt Models  │
│   (Scheduler)   │                │   (CI/CD Runner) │               │ (Databricks)│
└─────────────────┘                └──────────────────┘               └─────────────┘
      ▲                                       │                              │
      │                                       ▼                              ▼
┌─────────────────┐                ┌──────────────────┐               ┌─────────────┐
│   Docker        │                │  Version Control │               │  Data       │
│  (Local Dev)    │                │   (Git Workflow) │               │ Warehouse   │
└─────────────────┘                └──────────────────┘               └─────────────┘
```

### Data Flow
1. **Airflow DAG** triggers on schedule (hourly/every 2 hours)
2. **HTTP Operator** calls GitHub repository dispatch API
3. **GitHub Actions** receives trigger and starts workflow
4. **dbt runs** transformations on Databricks
5. **Airflow monitors** status and reports results

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- GitHub account with repository access
- Databricks workspace and credentials
- GitHub Personal Access Token

### Setup Instructions

1. **Clone and Configure**
```bash
git clone https://github.com/xoniks/dbt-airflow-github_actions.git
cd dbt-airflow-github_actions
```

2. **Environment Setup**
```bash
# Create .env file
AIRFLOW_UID=50000
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=your_username/dbt-airflow-github_actions
```

3. **GitHub Secrets** (Repository Settings → Secrets and variables → Actions)
```
DATABRICKS_HOST=your_databricks_workspace_url
DATABRICKS_HTTP_PATH=your_sql_warehouse_http_path  
DATABRICKS_TOKEN=your_databricks_personal_access_token
```

4. **Start Services**
```bash
docker-compose up -d
```

5. **Configure Airflow** (http://localhost:8081, admin/admin)
   - **Variables**: `github_token`, `github_repo`
   - **Connection**: `github_api` (HTTP, https://api.github.com)

## 📋 Project Structure

```
├── airflow/
│   ├── dags/
│   │   ├── trigger_dbt_github_action.py      # Simple trigger DAG
│   │   └── trigger_and_monitor_dbt.py        # Advanced monitoring DAG
│   ├── logs/                                 # Airflow execution logs
│   └── plugins/                              # Custom operators
├── models/
│   ├── bronze/
│   │   ├── bronze_customers.sql              # Raw data staging
│   │   └── bronze_suppliers.sql              # Raw data staging
│   ├── silver/
│   │   ├── customers.sql                     # Cleaned customers
│   │   └── suppliers.sql                     # Cleaned suppliers
│   └── sources.yml                           # Source definitions
├── .github/workflows/
│   └── dbt-run.yml                           # CI/CD pipeline
├── docker-compose.yml                        # Local development setup
├── dbt_project.yml                           # dbt configuration
└── profiles.yml                              # Databricks connection
```

## 🔄 DAG Architecture: Two Approaches

We implement **two complementary DAGs** with different purposes:

### 1. `trigger_dbt_github_action.py` - Simple Trigger
**Purpose**: Lightweight, frequent executions
- **Schedule**: Every 1 hour
- **Tasks**: `start` → `trigger_dbt_run` → `end`
- **Monitoring**: None (fire-and-forget)
- **Use Case**: Regular data refreshes without blocking Airflow

### 2. `trigger_and_monitor_dbt.py` - Advanced Monitoring  
**Purpose**: Full lifecycle management with status tracking
- **Schedule**: Every 2 hours  
- **Tasks**: `start` → `trigger_dbt_run` → `monitor_dbt_status` → `end`
- **Monitoring**: Real-time GitHub Actions status checking
- **Use Case**: Critical jobs requiring success validation

### DAG Comparison

| Feature | Simple DAG | Monitoring DAG |
|---------|------------|----------------|
| **Execution Time** | ~2 seconds | ~3-5 minutes |
| **Resource Usage** | Minimal | Moderate |
| **Failure Detection** | Basic (HTTP response only) | Advanced (GitHub Actions status) |
| **Debugging** | Limited visibility | Full GitHub Actions integration |
| **Best For** | Frequent updates | Critical validations |

## 🎯 Trigger Methods

This pipeline supports **three trigger methods**:

1. **📅 Scheduled Execution** (Airflow DAGs)
   - Simple DAG: Every hour
   - Monitor DAG: Every 2 hours

2. **📝 Git Push Triggers** (`.github/workflows/dbt-run.yml`)
   - Triggers on push to `main` branch
   - Only when dbt files change (`models/**`, `dbt_project.yml`)

3. **🔘 Manual Execution**
   - Airflow UI: "Trigger DAG" button
   - GitHub Actions: "Run workflow" button

## 🏗️ dbt Model Architecture

### Bronze Layer (Raw Data)
```sql
-- bronze_customers.sql
SELECT id, name FROM {{ source('ecom', 'raw_customers') }}
```

### Silver Layer (Clean Data)  
```sql
-- customers.sql
SELECT 
  id AS customer_id,
  TRIM(name) AS customer_name
FROM {{ ref('bronze_customers') }}
WHERE id IS NOT NULL AND name IS NOT NULL
```

## 🎯 When to Use This Pattern

### ✅ Ideal Use Cases
- **Analytics Engineering Teams**: Need Git workflow for dbt models
- **Educational Projects**: Learning modern data stack patterns  
- **Hybrid Cloud**: Local development, cloud execution
- **CI/CD for Data**: Automated testing and validation
- **Cost Optimization**: Pay-per-use execution model

### ❌ When Not to Use
- **Real-time Processing**: Too much latency (30-60s overhead)
- **High-Frequency Jobs**: GitHub Actions rate limits
- **Simple ETL**: Over-engineered for basic transformations
- **Small Teams**: Complexity overhead not justified

## 📊 Monitoring & Operations

### Airflow UI (http://localhost:8081)
- DAG status and execution history
- Task logs and debugging information
- Manual trigger capabilities
- Variable and connection management

### GitHub Actions
- Workflow execution details
- dbt run results and logs
- Failure notifications and debugging
- Version control integration

### Key Monitoring Points
1. **Airflow Task Success**: HTTP API call succeeded
2. **GitHub Actions Status**: Workflow completion status
3. **dbt Run Results**: Model execution success/failure
4. **Data Quality**: Downstream validation and testing

## 🔧 Troubleshooting

### Common Issues

**Airflow Can't Trigger GitHub Actions**
- Check `github_token` variable in Airflow
- Verify `github_api` connection configuration
- Confirm repository name format: `username/repo-name`

**GitHub Actions Not Starting**
- Verify repository dispatch event type matches
- Check GitHub token permissions (repo scope required)
- Confirm workflow file is in `.github/workflows/`

**dbt Run Failures**
- Check Databricks credentials in GitHub Secrets
- Verify `profiles.yml` configuration
- Review dbt model syntax and dependencies

## 🔄 Alternative Architectures

### 1. **Pure GitHub Actions** (Simpler)
```yaml
schedule:
  - cron: '0 */6 * * *'
```
**Pros**: Single system, **Cons**: Limited orchestration

### 2. **Traditional Airflow + dbt** (Direct)
```python
dbt_run = BashOperator(bash_command='dbt run')
```
**Pros**: Direct control, **Cons**: No Git workflow benefits

### 3. **dbt Cloud** (Managed)
**Pros**: Fully managed, **Cons**: Vendor lock-in

## 🎓 Educational Value

This project demonstrates:
- **Modern Data Stack**: dbt, cloud data warehouses, orchestration
- **GitOps for Data**: Version-controlled transformations
- **API Integration**: Cross-system communication patterns
- **Hybrid Architecture**: Local development, cloud execution
- **DevOps for Analytics**: CI/CD, testing, monitoring

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Test changes locally with Docker setup
4. Submit pull request with clear description

## 📚 Next Steps

- Add data quality tests with dbt tests
- Implement notifications (Slack, email) on failures
- Add more complex transformation examples
- Deploy Airflow to production (AWS MWAA, Google Composer)
- Implement environment promotion (dev → staging → prod)

---

*This project serves as both a practical implementation and educational resource for modern data engineering patterns. Perfect for learning hybrid orchestration, GitOps workflows, and the modern data stack.*

