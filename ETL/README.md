# ecommerce-etl-dashboard

This repository is a production-ready ETL pipeline and analytics dashboard for the Brazilian e-commerce "Olist" dataset. It features modular ingestion from APIs and databases, data quality monitoring, efficient bulk loading with PostgreSQL COPY, TimescaleDB time-series optimizations, Apache Airflow orchestration, and dual dashboards (Flask + Streamlit).

## Features

- **Multi-source Ingestion**: REST APIs (Shopify, Stripe, etc.), databases (PostgreSQL, MySQL, MongoDB, SQLite, MSSQL), CSV/JSON files
- **Staging & Archiving**: Raw payloads saved to `data/staging/raw/{source}/{date}` with gzip compression before transformation
- **Data Quality**: 8-dimension quality scoring (completeness, validity, consistency, timeliness, uniqueness, accuracy, conformity, integrity)
- **Efficient Loading**: PostgreSQL COPY FROM STDIN (10-100x faster than INSERT), dimension upserts with ON CONFLICT
- **Monitoring**: Airflow validation task with quality thresholds (≥80% score, ≤20% nulls, ≤5% duplicates)
- **Parquet Support**: Output cleaned data in Parquet format for data lake integration
- **TimescaleDB**: Hypertables with compression for time-series analytics
- **Dual Dashboards**: Flask (production) + Streamlit (interactive analytics)
- **Audit Tracking**: `ingest_audit` table logs run_id, rows_ingested, errors, duration, metadata

## Directory Structure

```
data/
  staging/
    raw/          # Gzipped raw payloads by source and date
    clean/        # Cleaned data (CSV/Parquet) before loading
  processed/      # Final processed outputs
  archive/        # Historical archives
etl/
  ingest.py       # Multi-source data ingestion with archiving
  transform.py    # Cleaning, validation, normalization (CSV/Parquet)
  load.py         # Bulk loading with COPY, dimension upserts
  api_ingest.py   # API client with retry logic and rate limiting
  db_ingest.py    # Database connectors for 5+ database types
  data_quality.py # Quality scoring and HTML dashboard generation
dags/
  etl_pipeline.py # Airflow DAG with ingest→transform→load→validate→notify
dashboard/
  app.py          # Flask dashboard for production deployment
  streamlit_app.py # Streamlit dashboard for interactive analytics
sql/
  schema.sql      # Normalized schema (dim_customers, dim_products, fact_orders, etc.)
  timescaledb_setup.sql # Hypertables and continuous aggregates
tests/
  test_*.py       # Unit tests for all modules
```

## Dataset Setup

Download the Brazilian e-commerce "Olist" dataset from Kaggle:

### Option 1: Kaggle CLI (Recommended)
```powershell
# Install Kaggle CLI and place kaggle.json in ~/.kaggle/
pip install kaggle

# Download and unzip dataset
kaggle datasets download -d olistbr/brazilian-ecommerce -p data/staging --unzip
```

### Option 2: Manual Download
1. Visit https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
2. Download ZIP and extract to `data/staging/`

Expected files in `data/staging/`:
- `olist_orders_dataset.csv` (primary orders file)
- `olist_order_items_dataset.csv`
- `olist_customers_dataset.csv`
- `olist_products_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_geolocation_dataset.csv`
- `olist_order_reviews_dataset.csv`

## Quick Start

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure Database
Set your PostgreSQL connection string:
```powershell
$env:DATABASE_URL = "postgresql://user:pass@localhost:5432/etl_db"
```

### 3. Initialize Database Schema
```powershell
# Create tables
psql $env:DATABASE_URL -f sql/schema.sql

# (Optional) Enable TimescaleDB extensions
psql $env:DATABASE_URL -f sql/timescaledb_setup.sql
```

### 4. Run ETL Pipeline

#### Option A: Manual Execution
```powershell
# Ingest: Save raw data from source
python -c "from etl.ingest import save_raw, fetch_from_source; data = fetch_from_source('csv', 'data/staging/olist_orders_dataset.csv'); save_raw('csv', 'olist_orders', data)"

# Transform: Clean and validate (outputs to staging/clean/)
python -c "from etl.transform import transform_csv; transform_csv('data/staging/olist_orders_dataset.csv', 'data/staging/clean/orders_clean.csv', output_format='csv')"

# (Optional) Transform to Parquet for data lake
python -c "from etl.transform import transform_csv; transform_csv('data/staging/olist_orders_dataset.csv', 'data/staging/clean/orders_clean.parquet', output_format='parquet')"

# Load: Bulk insert with COPY FROM STDIN
python scripts/load_to_db.py
```

#### Option B: Airflow Orchestration (Recommended)
```powershell
# Start Airflow webserver and scheduler
airflow standalone

# Trigger DAG from UI at http://localhost:8080 or CLI:
airflow dags trigger etl_pipeline
```

The Airflow DAG runs:
1. **Ingest**: Fetch from sources, save raw payloads to `staging/raw/`
2. **Transform**: Clean, validate, compute metrics, output to `staging/clean/`
3. **Load**: Bulk load with COPY, upsert dimensions, log to `ingest_audit`
4. **Validate**: Run quality checks (≥80% score, ≤20% nulls, ≤5% duplicates)
5. **Notify**: Send alerts if validation fails

### 5. Launch Dashboards

#### Flask Dashboard (Production)
```powershell
# Development server
python dashboard/app.py

# Production with Gunicorn
gunicorn wsgi:app -b 0.0.0.0:8000 --workers 2
```
Access at http://localhost:5000 or http://localhost:8000

#### Streamlit Dashboard (Interactive Analytics)
```powershell
streamlit run dashboard/streamlit_app.py
```
Access at http://localhost:8501

Features:
- Sales trends over time (line chart)
- Top 10 products by revenue (bar chart)
- Customer segmentation (pie chart)
- Data quality metrics (KPI cards)
- Raw data viewer with filters

## Data Quality Monitoring

Run quality analysis on any CSV/Parquet file:
```powershell
python -c "from etl.data_quality import analyze_csv_quality; score, report = analyze_csv_quality('data/staging/clean/orders_clean.csv'); print(f'Quality Score: {score}%'); print(report)"
```

Quality dimensions:
- **Completeness**: % of non-null values
- **Validity**: % of values passing business rules
- **Consistency**: % of cross-field consistency checks
- **Timeliness**: % of recent data (< 90 days old)
- **Uniqueness**: % of unique records (no duplicates)
- **Accuracy**: % of valid data types and ranges
- **Conformity**: % matching expected formats (email, phone, etc.)
- **Integrity**: % of referential integrity maintained

HTML dashboard saved to `data/quality_reports/quality_report_{timestamp}.html`

## Advanced Features

### API Ingestion with Retry Logic
```python
from etl.api_ingest import APIIngestor

# Shopify orders
api = APIIngestor('https://yourstore.myshopify.com', api_key='YOUR_KEY')
orders = api.get_paginated('/admin/api/2024-01/orders.json', max_pages=5)

# Stripe payments
stripe_api = APIIngestor('https://api.stripe.com/v1', api_key='sk_test_...')
payments = stripe_api.get_paginated('/charges', max_pages=10)
```

Features:
- Exponential backoff with jitter (max 5 retries)
- Rate limiting (100 requests/minute default)
- Circuit breaker pattern (opens after 5 failures)
- Request/response logging

### Database Ingestion
```python
from etl.db_ingest import DatabaseIngestor

# PostgreSQL
db = DatabaseIngestor('postgresql', host='localhost', database='sourcedb', user='user', password='pass')
orders = db.fetch_data('SELECT * FROM orders WHERE created_at > %s', params=('2024-01-01',))

# MongoDB
mongo = DatabaseIngestor('mongodb', host='localhost', port=27017, database='ecommerce')
docs = mongo.fetch_data('orders', query={'status': 'completed'})
```

Supported databases: PostgreSQL, MySQL, MongoDB, SQLite, Microsoft SQL Server

### Parquet Output for Data Lakes
```powershell
# Transform to Parquet with PyArrow
python -c "from etl.transform import transform_csv; transform_csv('data/staging/olist_orders_dataset.csv', 'data/staging/clean/orders_clean.parquet', output_format='parquet')"
```

Benefits:
- 60-80% smaller file size vs CSV
- Column-oriented storage for analytics
- Integrated with Spark, Presto, Athena, BigQuery
- Preserves data types (no CSV string coercion)

### TimescaleDB Continuous Aggregates
```sql
-- Pre-aggregated hourly sales (refreshed every 15 minutes)
SELECT * FROM hourly_sales WHERE time > NOW() - INTERVAL '7 days';

-- Pre-aggregated daily customer metrics
SELECT * FROM daily_customer_metrics WHERE date > '2024-01-01';
```

See `sql/timescaledb_setup.sql` for setup instructions.

### Customer Lifetime Value (CLV)
```powershell
# Generate CLV predictions
python scripts/aggregate_orders.py
```

Output: `data/processed/customer_aggregates.csv` with:
- `customer_lifetime_value`: Total spent
- `order_count`: Number of orders
- `avg_order_value`: Average order size
- `days_since_last_order`: Recency

## Testing

Run all unit tests:
```powershell
pytest tests/ -v
```

Run specific test modules:
```powershell
pytest tests/test_ingest.py -v
pytest tests/test_transform.py -v
pytest tests/test_load.py -v
```

## Deploying to Render

### Quick Steps (Manual)

1. **Create PostgreSQL Database**
   - Go to https://render.com → New → PostgreSQL
   - Note the connection string: `postgresql://user:pass@host:5432/dbname`

2. **Create Web Service**
   - New → Web Service → Connect this Git repo
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:app -b 0.0.0.0:$PORT --workers 2`

3. **Set Environment Variables**
   - `DATABASE_URL`: Postgres connection string from step 1
   - `SECRET_KEY`: Random string for Flask sessions

4. **Initialize Database**
   - Use Render Shell or local psql:
   ```powershell
   psql $env:DATABASE_URL -f sql/schema.sql
   ```

### Infrastructure-as-Code (render.yaml)

For automated deployment, add this `render.yaml` to your repo:

```yaml
services:
  - type: web
    name: etl-dashboard
    env: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn wsgi:app -b 0.0.0.0:$PORT --workers 2
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: etl-db
          property: connectionString

databases:
  - name: etl-db
    plan: starter
```

Then import `render.yaml` in Render dashboard.

### Airflow on Render

For production Airflow:
1. Create separate Web Service with start command:
   ```
   airflow standalone
   ```
2. Set `AIRFLOW_HOME=/opt/render/project/src` environment variable
3. Mount persistent disk for DAGs and logs

Alternatively, use managed Airflow services (Astronomer, MWAA, Cloud Composer).

## ML Model Training

Train a scikit-learn model to predict `order_total`:

```powershell
# Install Jupyter
pip install -r requirements-dev.txt

# Launch notebook
jupyter notebook ml/train_example.ipynb
```

The notebook:
- Reads from `orders` table or falls back to CSV
- Engineers features (order_date, customer_id, product_count)
- Trains RandomForestRegressor
- Saves model to `models/order_total_model.pkl`
- Evaluates with MAE, RMSE, R²

## Performance Tips

### COPY Loading Benchmarks
- **INSERT**: 1,000 rows/sec
- **Bulk INSERT** (batch): 10,000 rows/sec
- **COPY FROM STDIN**: 50,000-100,000 rows/sec (10-100x faster)

Use `load_table_copy()` with `method='copy'` for datasets > 10,000 rows.

### Upsert Optimization
```sql
-- Efficient dimension upsert (handles updates without duplicates)
INSERT INTO dim_customers (customer_id, ...)
VALUES (...)
ON CONFLICT (customer_id) DO UPDATE SET ...;
```

Use `upsert_dimension()` for slowly changing dimensions.

### Parallel Ingestion
```python
from concurrent.futures import ThreadPoolExecutor

sources = ['orders', 'customers', 'products', 'payments']
with ThreadPoolExecutor(max_workers=4) as executor:
    executor.map(lambda s: fetch_from_source('csv', f'data/staging/{s}.csv'), sources)
```

## Troubleshooting

### Import Errors
```powershell
# Ensure all dependencies installed
pip install -r requirements.txt

# Verify imports
python -c "import streamlit, pyarrow, pandas, sqlalchemy; print('All imports OK')"
```

### Database Connection Issues
```powershell
# Test connection
python -c "from sqlalchemy import create_engine; import os; engine = create_engine(os.getenv('DATABASE_URL')); conn = engine.connect(); print('Connected'); conn.close()"
```

### Airflow DAG Not Showing
```powershell
# Refresh DAGs
airflow dags list

# Check logs
airflow tasks test etl_pipeline ingest 2024-01-01
```

### Data Quality Failing
```powershell
# Check quality report
python -c "from etl.data_quality import analyze_csv_quality; score, report = analyze_csv_quality('data/staging/clean/orders_clean.csv'); print(f'Score: {score}%'); print(report)"

# Lower threshold in DAG (edit dags/etl_pipeline.py):
# quality_threshold = 70  # Reduced from 80
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Add unit tests for new functionality
4. Run tests: `pytest tests/ -v`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open Pull Request

## License

MIT License - see LICENSE file for details

## Support

For issues or questions:
- Open GitHub Issue
- Check JDBC setup guide: `docs/jdbc_setup.md`
- Review implementation summary: `IMPLEMENTATION_SUMMARY.md`
