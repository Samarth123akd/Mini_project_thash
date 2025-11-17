# Airflow Setup Guide

This guide walks you through configuring Apache Airflow connections and variables for the ETL pipeline.

---

## Prerequisites

- Airflow installed and initialized (`airflow db init`)
- Airflow webserver running (`airflow webserver --port 8080`)
- Airflow scheduler running (`airflow scheduler`)
- Admin user created

---

## 1. Access Airflow UI

Open your browser and navigate to:
```
http://localhost:8080
```

Login with your admin credentials.

---

## 2. Configure PostgreSQL Connection

### Steps:

1. Click **Admin** → **Connections** in the top menu
2. Click the **+** button to add a new connection
3. Fill in the following fields:

| Field | Value | Notes |
|-------|-------|-------|
| **Connection Id** | `postgres_default` | Used by DAG tasks |
| **Connection Type** | `Postgres` | Select from dropdown |
| **Host** | `localhost` | Or remote host IP/domain |
| **Schema** | `etl_db` | Your database name |
| **Login** | `postgres` | Database username |
| **Password** | `your_password` | Database password |
| **Port** | `5432` | Default PostgreSQL port |

4. Click **Test** to verify connection
5. Click **Save**

### Example Connection String Format:
```
postgresql://postgres:password@localhost:5432/etl_db
```

### Using Environment Variable (Alternative):

Instead of storing credentials in Airflow, you can use environment variables:

```powershell
# Set in your terminal or .env file
$env:AIRFLOW_CONN_POSTGRES_DEFAULT = "postgresql://user:pass@host:5432/etl_db"
```

Then use `postgres_default` as the connection ID in your DAG.

---

## 3. Configure API Connections

### 3.1 Shopify API Connection

1. Click **Admin** → **Connections** → **+**
2. Fill in:

| Field | Value |
|-------|-------|
| **Connection Id** | `shopify_api` |
| **Connection Type** | `HTTP` |
| **Host** | `https://yourstore.myshopify.com` |
| **Extra** | `{"api_key": "your_api_key", "api_version": "2024-01"}` |

3. Click **Save**

### 3.2 Stripe API Connection

1. Click **Admin** → **Connections** → **+**
2. Fill in:

| Field | Value |
|-------|-------|
| **Connection Id** | `stripe_api` |
| **Connection Type** | `HTTP` |
| **Host** | `https://api.stripe.com` |
| **Extra** | `{"api_key": "sk_test_your_secret_key"}` |

3. Click **Save**

### 3.3 Generic REST API Connection

For any other REST API:

| Field | Value |
|-------|-------|
| **Connection Id** | `custom_api` |
| **Connection Type** | `HTTP` |
| **Host** | `https://api.example.com` |
| **Login** | `username` (if using Basic Auth) |
| **Password** | `password` |
| **Extra** | `{"Authorization": "Bearer your_token"}` |

---

## 4. Configure Airflow Variables

Variables store configuration values used by DAGs.

### Steps:

1. Click **Admin** → **Variables**
2. Click **+** to add a new variable
3. Add the following variables:

| Key | Value | Description |
|-----|-------|-------------|
| `etl_data_dir` | `c:\Users\samar\Desktop\prjct_thash\ETL\data` | Base data directory |
| `etl_staging_raw` | `data/staging/raw` | Raw data staging path |
| `etl_staging_clean` | `data/staging/clean` | Cleaned data path |
| `etl_archive_dir` | `data/archive` | Archive directory |
| `etl_quality_threshold` | `80` | Minimum quality score % |
| `etl_null_threshold` | `20` | Maximum null percentage |
| `etl_duplicate_threshold` | `5` | Maximum duplicate percentage |
| `shopify_shop_url` | `yourstore.myshopify.com` | Shopify store URL |
| `stripe_api_version` | `2024-01` | Stripe API version |
| `alert_email` | `data-team@company.com` | Email for failure alerts |

### Using Variables in DAG:

```python
from airflow.models import Variable

# Get variable value
data_dir = Variable.get('etl_data_dir')
quality_threshold = Variable.get('etl_quality_threshold', default_var=80)

# Get as JSON
api_config = Variable.get('api_config', deserialize_json=True)
```

---

## 5. Configure Email Alerts

### SMTP Settings

Edit `airflow.cfg` or set environment variables:

```ini
[smtp]
smtp_host = smtp.gmail.com
smtp_starttls = True
smtp_ssl = False
smtp_user = your_email@gmail.com
smtp_password = your_app_password
smtp_port = 587
smtp_mail_from = airflow@company.com
```

**For Gmail**:
1. Enable 2-Factor Authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use app password instead of account password

### Environment Variable Method:

```powershell
$env:AIRFLOW__SMTP__SMTP_HOST = "smtp.gmail.com"
$env:AIRFLOW__SMTP__SMTP_USER = "your_email@gmail.com"
$env:AIRFLOW__SMTP__SMTP_PASSWORD = "your_app_password"
$env:AIRFLOW__SMTP__SMTP_PORT = "587"
$env:AIRFLOW__SMTP__SMTP_MAIL_FROM = "airflow@company.com"
```

---

## 6. Configure Slack Alerts (Optional)

### Create Slack Webhook:

1. Go to https://api.slack.com/apps
2. Create new app → Choose workspace
3. Enable **Incoming Webhooks**
4. Create webhook for channel (e.g., `#data-alerts`)
5. Copy webhook URL

### Add to Airflow Variables:

| Key | Value |
|-----|-------|
| `slack_webhook_url` | `https://hooks.slack.com/services/YOUR/WEBHOOK/URL` |

### Use in DAG:

```python
from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator
from airflow.models import Variable

slack_webhook_token = Variable.get('slack_webhook_url')

notify_slack = SlackWebhookOperator(
    task_id='notify_slack',
    http_conn_id='slack_webhook',
    webhook_token=slack_webhook_token,
    message='ETL Pipeline Failed! Check logs.',
    trigger_rule='one_failed'
)
```

---

## 7. Test Connections

### Test PostgreSQL:

```python
from airflow.providers.postgres.hooks.postgres import PostgresHook

hook = PostgresHook(postgres_conn_id='postgres_default')
conn = hook.get_conn()
cursor = conn.cursor()
cursor.execute("SELECT version();")
print(cursor.fetchone())
```

### Test API:

```python
from airflow.providers.http.hooks.http import HttpHook

hook = HttpHook(method='GET', http_conn_id='shopify_api')
response = hook.run('/admin/api/2024-01/orders.json')
print(response.status_code)
```

---

## 8. Verify Setup

### Checklist:

- [ ] Airflow webserver running on http://localhost:8080
- [ ] Airflow scheduler running
- [ ] PostgreSQL connection `postgres_default` configured and tested
- [ ] API connections configured (Shopify, Stripe, etc.)
- [ ] Variables added (paths, thresholds, emails)
- [ ] SMTP configured for email alerts
- [ ] (Optional) Slack webhook configured
- [ ] All connections show green status in UI

### Quick Verification Script:

```powershell
# Run from Airflow home directory
python -c "
from airflow.providers.postgres.hooks.postgres import PostgresHook
try:
    hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = hook.get_conn()
    print('✅ PostgreSQL connection successful')
except Exception as e:
    print('❌ PostgreSQL connection failed:', e)
"
```

---

## 9. Security Best Practices

### 1. Use Secrets Backend

Instead of storing passwords in Airflow, use a secrets backend:

**AWS Secrets Manager:**
```ini
[secrets]
backend = airflow.providers.amazon.aws.secrets.secrets_manager.SecretsManagerBackend
backend_kwargs = {"connections_prefix": "airflow/connections"}
```

**HashiCorp Vault:**
```ini
[secrets]
backend = airflow.providers.hashicorp.secrets.vault.VaultBackend
backend_kwargs = {"url": "http://vault:8200", "token": "your_token"}
```

### 2. Encrypt Fernet Key

Generate and set Fernet key for encrypting passwords:

```powershell
# Generate key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set in airflow.cfg or environment
$env:AIRFLOW__CORE__FERNET_KEY = "your_generated_key"
```

### 3. Use .env File

Create `.env` file for sensitive variables:

```ini
DATABASE_URL=postgresql://user:pass@localhost:5432/etl_db
SHOPIFY_API_KEY=your_api_key
STRIPE_API_KEY=sk_test_your_key
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
ALERT_EMAIL=alerts@company.com
```

Load with `python-dotenv`:

```python
from dotenv import load_dotenv
import os

load_dotenv()
db_url = os.getenv('DATABASE_URL')
```

---

## 10. Troubleshooting

### Connection Test Fails

**Issue**: "Connection refused" error

**Solution**:
- Verify PostgreSQL is running: `pg_ctl status`
- Check firewall rules
- Verify host and port are correct
- Check `pg_hba.conf` allows connections

### Import Error for Providers

**Issue**: `ModuleNotFoundError: No module named 'airflow.providers.postgres'`

**Solution**:
```powershell
pip install apache-airflow-providers-postgres
pip install apache-airflow-providers-http
pip install apache-airflow-providers-slack
```

### Variables Not Loading

**Issue**: `KeyError: 'Variable etl_data_dir does not exist'`

**Solution**:
- Verify variable exists in UI (Admin → Variables)
- Use default value: `Variable.get('key', default_var='fallback')`
- Check spelling and case sensitivity

### Email Alerts Not Sending

**Issue**: Emails not received on DAG failure

**Solution**:
- Verify SMTP settings in `airflow.cfg`
- Check spam folder
- Test SMTP connection manually
- Ensure `email_on_failure=True` in default_args

---

## 11. Next Steps

After completing Airflow setup:

1. **Run Test DAG**: Trigger `etl_pipeline` from UI
2. **Monitor Logs**: Check task logs for errors
3. **Verify Data**: Query PostgreSQL to confirm data loaded
4. **Set Schedule**: Enable DAG schedule if disabled
5. **Document Screenshots**: Capture DAG runs for submission

**Success Indicators**:
- ✅ DAG runs without errors
- ✅ Data appears in PostgreSQL tables
- ✅ Validation task passes quality checks
- ✅ Alerts sent on intentional failures

---

## Additional Resources

- **Airflow Documentation**: https://airflow.apache.org/docs/
- **PostgreSQL Hook**: https://airflow.apache.org/docs/apache-airflow-providers-postgres/
- **HTTP Provider**: https://airflow.apache.org/docs/apache-airflow-providers-http/
- **Slack Integration**: https://airflow.apache.org/docs/apache-airflow-providers-slack/

---

**Last Updated**: November 2025  
**Maintainer**: Data Engineering Team
