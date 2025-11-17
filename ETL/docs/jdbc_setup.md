# JDBC Setup Guide for BI Tools and ML Pipelines

This document provides JDBC connection details for connecting BI dashboards and ML pipelines to the PostgreSQL/TimescaleDB data warehouse.

## Quick Reference

**JDBC Connection String Format:**
```
jdbc:postgresql://<host>:<port>/<database>?ssl=true
```

**Default Values:**
- Host: `localhost` (or your Render/cloud hostname)
- Port: `5432`
- Database: `ecommerce` (or configured database name)

---

## 1. PostgreSQL/TimescaleDB JDBC Driver

### Download JDBC Driver

**Latest Version:** PostgreSQL JDBC Driver 42.7.x

**Download Link:** https://jdbc.postgresql.org/download/

**Maven Dependency:**
```xml
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
    <version>42.7.1</version>
</dependency>
```

**Gradle:**
```gradle
implementation 'org.postgresql:postgresql:42.7.1'
```

---

## 2. Connection Details

### Local Development

```properties
jdbc.url=jdbc:postgresql://localhost:5432/ecommerce
jdbc.username=your_username
jdbc.password=your_password
jdbc.driver=org.postgresql.Driver
```

### Production (Render or Cloud)

```properties
jdbc.url=jdbc:postgresql://<your-db-host>.render.com:5432/<database>?ssl=true&sslmode=require
jdbc.username=<your_username>
jdbc.password=<your_password>
jdbc.driver=org.postgresql.Driver
```

**Environment Variable (Recommended):**
```bash
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

Convert to JDBC format:
```
jdbc:postgresql://host:5432/dbname?user=username&password=password&ssl=true
```

---

## 3. BI Tool Configuration

### Tableau

1. **Open Tableau Desktop**
2. **Connect to Data** → **PostgreSQL**
3. **Enter Connection Details:**
   - Server: `your-db-host.render.com` (or `localhost`)
   - Port: `5432`
   - Database: `ecommerce`
   - Authentication: Username and Password
   - Check "Require SSL" for production

4. **Advanced Options:**
   - Initial SQL: `SET search_path TO public;`

**Example Connection String:**
```
Server=dpg-abc123xyz.render.com
Port=5432
Database=ecommerce
Username=etl_user
SSL Mode=require
```

---

### Power BI

1. **Get Data** → **Database** → **PostgreSQL database**
2. **Enter Server and Database:**
   - Server: `your-db-host.render.com:5432`
   - Database: `ecommerce`

3. **Data Connectivity Mode:** Import or DirectQuery
4. **Authentication:** Database (username/password)

**Connection String:**
```
Host=your-db-host.render.com;Port=5432;Database=ecommerce;SSL Mode=Require;Trust Server Certificate=true
```

**M Query (Advanced Editor):**
```m
let
    Source = PostgreSQL.Database("your-db-host.render.com:5432", "ecommerce", [
        CreateNavigationProperties = false,
        UseSSL = true
    ])
in
    Source
```

---

### Metabase

1. **Add Database** → **PostgreSQL**
2. **Connection Settings:**
   - Name: `E-commerce Warehouse`
   - Host: `your-db-host.render.com`
   - Port: `5432`
   - Database name: `ecommerce`
   - Username: `etl_user`
   - Password: `********`
   - Use SSL: ✓ Yes

3. **Additional Options:**
   - Use a secure connection (SSL): `required`
   - Connection timeout: `30` seconds

---

### Apache Superset

**Database Connection String:**
```
postgresql+psycopg2://username:password@host:5432/ecommerce?sslmode=require
```

**Configuration:**
1. **Data** → **Databases** → **+ Database**
2. **Select PostgreSQL**
3. **SQLAlchemy URI:**
   ```
   postgresql+psycopg2://etl_user:password@your-db-host.render.com:5432/ecommerce?sslmode=require
   ```

---

### Looker

**Connection Settings:**
```yaml
connection: ecommerce_db
  host: your-db-host.render.com
  port: 5432
  database: ecommerce
  username: etl_user
  password: ${LOOKER_DB_PASSWORD}
  ssl: true
  dialect_name: postgresql
```

---

## 4. Python ML Pipeline Integration

### Using SQLAlchemy

```python
from sqlalchemy import create_engine
import pandas as pd

# Connection string
DATABASE_URL = "postgresql://user:password@host:5432/ecommerce"

# Create engine
engine = create_engine(DATABASE_URL)

# Read data
df = pd.read_sql_query("SELECT * FROM orders WHERE invoice_date > '2024-01-01'", engine)

# Or use TimescaleDB continuous aggregates
df_daily = pd.read_sql_query("SELECT * FROM daily_sales_summary", engine)
```

### Using psycopg2 (Direct)

```python
import psycopg2
import pandas as pd

conn = psycopg2.connect(
    host="your-db-host.render.com",
    port=5432,
    database="ecommerce",
    user="etl_user",
    password="your_password",
    sslmode="require"
)

query = "SELECT * FROM orders LIMIT 1000"
df = pd.read_sql_query(query, conn)
conn.close()
```

---

## 5. R Integration

### Using RPostgreSQL

```r
library(RPostgreSQL)

# Create driver
drv <- dbDriver("PostgreSQL")

# Connect
con <- dbConnect(drv,
                 host = "your-db-host.render.com",
                 port = 5432,
                 dbname = "ecommerce",
                 user = "etl_user",
                 password = "your_password")

# Query data
df <- dbGetQuery(con, "SELECT * FROM orders")

# Close connection
dbDisconnect(con)
```

---

## 6. Spark Integration

### PySpark

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("EcommerceETL") \
    .config("spark.jars", "postgresql-42.7.1.jar") \
    .getOrCreate()

jdbc_url = "jdbc:postgresql://your-db-host.render.com:5432/ecommerce"
properties = {
    "user": "etl_user",
    "password": "your_password",
    "driver": "org.postgresql.Driver",
    "ssl": "true"
}

df = spark.read.jdbc(
    url=jdbc_url,
    table="orders",
    properties=properties
)

df.show()
```

---

## 7. Security Best Practices

### SSL/TLS Configuration

**Always use SSL in production:**
```
jdbc:postgresql://host:5432/dbname?ssl=true&sslmode=require
```

**SSL Modes:**
- `disable`: No SSL (not recommended for production)
- `require`: Enforce SSL
- `verify-ca`: Verify CA certificate
- `verify-full`: Verify CA and hostname

### Credential Management

**DO NOT hardcode credentials!**

**Use environment variables:**
```bash
export DB_HOST="your-db-host.render.com"
export DB_PORT="5432"
export DB_NAME="ecommerce"
export DB_USER="etl_user"
export DB_PASSWORD="secure_password"
```

**Or use secrets managers:**
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- GitHub Secrets (for CI/CD)

---

## 8. Connection Pooling (Recommended for Production)

### HikariCP (Java)

```java
HikariConfig config = new HikariConfig();
config.setJdbcUrl("jdbc:postgresql://host:5432/ecommerce");
config.setUsername("etl_user");
config.setPassword("password");
config.setMaximumPoolSize(10);
config.setMinimumIdle(2);
config.setConnectionTimeout(30000);

HikariDataSource ds = new HikariDataSource(config);
```

### SQLAlchemy (Python)

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://user:pass@host:5432/ecommerce",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

---

## 9. TimescaleDB-Specific Features

### Using Continuous Aggregates

```sql
-- Query pre-computed daily summaries (fast)
SELECT * FROM daily_sales_summary
WHERE day >= NOW() - INTERVAL '30 days'
ORDER BY day DESC;

-- Query hourly data for dashboards
SELECT * FROM hourly_sales_summary
WHERE hour >= NOW() - INTERVAL '24 hours';
```

### Time-Series Queries

```sql
-- Use time_bucket for custom aggregations
SELECT 
    time_bucket('1 hour', invoice_date) AS hour,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue
FROM orders
WHERE invoice_date >= NOW() - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour DESC;
```

---

## 10. Testing Connection

### Command Line Test

```bash
# Using psql
psql -h your-db-host.render.com -p 5432 -U etl_user -d ecommerce

# Test query
SELECT version();
SELECT * FROM timescaledb_information.hypertables;
```

### Python Test Script

```python
import psycopg2

try:
    conn = psycopg2.connect(
        host="your-db-host.render.com",
        port=5432,
        database="ecommerce",
        user="etl_user",
        password="your_password",
        sslmode="require"
    )
    
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print(f"Connected successfully! PostgreSQL version: {version[0]}")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
```

---

## 11. Troubleshooting

### Common Issues

**1. Connection Timeout**
```
Solution: Check firewall rules, security groups, and network connectivity
Increase connection timeout in JDBC URL: ?connectTimeout=30
```

**2. SSL Required**
```
Error: "FATAL: SSL connection is required"
Solution: Add ssl=true&sslmode=require to connection string
```

**3. Authentication Failed**
```
Error: "FATAL: password authentication failed"
Solution: Verify username/password, check pg_hba.conf settings
```

**4. Database Does Not Exist**
```
Solution: Verify database name, run TimescaleDB setup script first
```

---

## 12. Performance Optimization

### For BI Tools

**Use Views for Complex Queries:**
```sql
CREATE VIEW sales_overview AS
SELECT 
    DATE_TRUNC('day', invoice_date) AS date,
    COUNT(*) AS orders,
    SUM(total_amount) AS revenue
FROM orders
GROUP BY date;
```

**Create Indexes:**
```sql
CREATE INDEX idx_orders_date ON orders (invoice_date DESC);
CREATE INDEX idx_customer_metrics ON customer_metrics (customer_id, metric_date);
```

### For ML Pipelines

**Use Chunked Reading:**
```python
# Read large tables in chunks
chunksize = 10000
for chunk in pd.read_sql_query(query, engine, chunksize=chunksize):
    # Process each chunk
    process_data(chunk)
```

---

## Contact & Support

For issues or questions:
- **Database Admin:** Set up appropriate user permissions
- **BI Team:** Configure read-only user for dashboards
- **ML Team:** Use connection pooling for model training

**Recommended Database User Permissions:**
```sql
-- Read-only user for BI tools
CREATE USER bi_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE ecommerce TO bi_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO bi_user;
GRANT SELECT ON ALL TABLES IN SCHEMA _timescaledb_internal TO bi_user;
```

---

**Last Updated:** November 2025
