# Load Brazilian E-commerce Data to PostgreSQL

## Quick Start (3 Steps)

### Step 1: Set Database URL
```powershell
$env:DATABASE_URL = "postgresql://etl_user:etl_password_123@localhost:5432/etl_db"
```

**Update** the username, password, and database name to match your PostgreSQL setup.

### Step 2: Create Tables (if not already done)
```powershell
psql $env:DATABASE_URL -f sql/schema.sql
```

### Step 3: Load Brazilian Dataset
```powershell
python scripts/load_brazilian_data.py
```

---

## What the Script Does

1. **Finds your Brazilian dataset** folder automatically
2. **Loads dimension tables** first:
   - `dim_customers` - 99,441 customers
   - `dim_products` - 32,951 products
3. **Loads fact tables**:
   - `fact_orders` - 99,441 orders
   - `fact_order_items` - 112,650 line items
   - `fact_payments` - 103,886 payments
4. **Updates order totals** from order items
5. **Creates audit record** in `ingest_audit` table
6. **Verifies data** with row counts

---

## Troubleshooting

### ❌ "DATABASE_URL not set"
Set the environment variable:
```powershell
$env:DATABASE_URL = "postgresql://user:pass@localhost:5432/etl_db"
```

### ❌ "Could not find 'brazilian dataset' folder"
The script looks in these locations:
- `brazilian dataset/` (current folder)
- `../brazilian dataset/` (parent folder)
- `../../brazilian dataset/` (grandparent folder)

Make sure your folder is named exactly `brazilian dataset` with a space.

### ❌ "Database connection failed"
Check:
1. PostgreSQL is running: `Get-Service postgresql*`
2. Database exists: `psql -U postgres -l`
3. Create database if missing:
   ```powershell
   psql -U postgres
   CREATE DATABASE etl_db;
   \q
   ```

### ❌ "Table does not exist"
Create tables first:
```powershell
psql $env:DATABASE_URL -f sql/schema.sql
```

---

## Verify Data

After loading, check the data:

```powershell
# Connect to database
psql $env:DATABASE_URL

# Check row counts
SELECT 'customers' AS table_name, COUNT(*) FROM dim_customers
UNION ALL
SELECT 'products', COUNT(*) FROM dim_products
UNION ALL
SELECT 'orders', COUNT(*) FROM fact_orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM fact_order_items
UNION ALL
SELECT 'payments', COUNT(*) FROM fact_payments;

# View sample orders
SELECT 
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_total_cents / 100.0 AS total_brl,
    o.order_item_count
FROM fact_orders o
ORDER BY o.order_purchase_timestamp DESC
LIMIT 10;
```

---

## Next Steps

After loading the data:

### 1. Launch Dashboard
```powershell
# Streamlit (interactive)
streamlit run dashboard/streamlit_app.py

# Flask (production)
gunicorn wsgi:app -b 0.0.0.0:8000
```

### 2. Train ML Model
The notebook will now read from PostgreSQL:
```powershell
jupyter notebook ml/train_example.ipynb
```

### 3. Run Airflow Pipeline
```powershell
airflow dags trigger etl_pipeline
```

---

## Performance

Expected loading time:
- **Small dataset** (<100K rows): ~30 seconds
- **Medium dataset** (100K-1M rows): ~2-5 minutes
- **Large dataset** (>1M rows): ~10-15 minutes

The script uses efficient bulk loading with temporary staging tables.

---

## Script Features

✅ **Automatic detection** of Brazilian dataset folder  
✅ **Upsert logic** - safe to run multiple times  
✅ **Transaction safety** - rollback on errors  
✅ **Audit logging** - tracks every load  
✅ **Data validation** - verifies row counts  
✅ **Currency conversion** - BRL to cents for precision  
✅ **Progress tracking** - see what's loading  

---

## Alternative: Manual Load

If you prefer manual control:

```python
import pandas as pd
from sqlalchemy import create_engine
import os

# Connect
engine = create_engine(os.environ['DATABASE_URL'])

# Load customers
df = pd.read_csv('brazilian dataset/olist_customers_dataset.csv')
df.to_sql('dim_customers', engine, if_exists='append', index=False)

# Load products
df = pd.read_csv('brazilian dataset/olist_products_dataset.csv')
df.to_sql('dim_products', engine, if_exists='append', index=False)

# ... etc
```

---

**Created**: November 15, 2025  
**Script**: `scripts/load_brazilian_data.py`
