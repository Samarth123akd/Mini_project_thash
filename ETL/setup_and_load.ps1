# Setup and Load Brazilian Dataset to PostgreSQL
# This script will guide you through the process

Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "  Brazilian E-commerce Dataset → PostgreSQL Setup" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Step 1: Get database credentials
Write-Host "Step 1: Database Configuration" -ForegroundColor Yellow
Write-Host "-------------------------------"
$DB_HOST = Read-Host "PostgreSQL host (default: localhost)"
if ([string]::IsNullOrWhiteSpace($DB_HOST)) { $DB_HOST = "localhost" }

$DB_PORT = Read-Host "PostgreSQL port (default: 5432)"
if ([string]::IsNullOrWhiteSpace($DB_PORT)) { $DB_PORT = "5432" }

$DB_NAME = Read-Host "Database name (default: ETL_DB)"
if ([string]::IsNullOrWhiteSpace($DB_NAME)) { $DB_NAME = "ETL_DB" }

$DB_USER = Read-Host "PostgreSQL username (default: postgres)"
if ([string]::IsNullOrWhiteSpace($DB_USER)) { $DB_USER = "postgres" }

$DB_PASS = Read-Host "PostgreSQL password" -AsSecureString
$DB_PASS_TEXT = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($DB_PASS)
)

Write-Host ""

# Build connection string
$CONNECTION_STRING = "postgresql://${DB_USER}:${DB_PASS_TEXT}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
$env:DATABASE_URL = $CONNECTION_STRING

Write-Host "✅ Database URL configured" -ForegroundColor Green
Write-Host ""

# Step 2: Test connection
Write-Host "Step 2: Testing Database Connection" -ForegroundColor Yellow
Write-Host "------------------------------------"

$testResult = python -c @"
from sqlalchemy import create_engine, text
import sys
try:
    engine = create_engine('$CONNECTION_STRING')
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"@

if ($testResult -match "SUCCESS") {
    Write-Host "✅ Database connection successful!" -ForegroundColor Green
} else {
    Write-Host "❌ Database connection failed:" -ForegroundColor Red
    Write-Host $testResult -ForegroundColor Red
    Write-Host ""
    Write-Host "Please check:" -ForegroundColor Yellow
    Write-Host "  1. PostgreSQL is running"
    Write-Host "  2. Username and password are correct"
    Write-Host "  3. Database 'ETL_DB' exists"
    Write-Host ""
    Write-Host "To create the database, run in pgAdmin Query Tool:" -ForegroundColor Cyan
    Write-Host '  CREATE DATABASE "ETL_DB";' -ForegroundColor Gray
    exit 1
}

Write-Host ""

# Step 3: Create tables
Write-Host "Step 3: Creating Database Tables" -ForegroundColor Yellow
Write-Host "---------------------------------"

$createTables = python -c @"
from sqlalchemy import create_engine, text
from pathlib import Path

engine = create_engine('$CONNECTION_STRING')

# Read schema
schema_file = Path('sql/schema.sql')
if not schema_file.exists():
    print('ERROR: sql/schema.sql not found')
    exit(1)

with open(schema_file, 'r') as f:
    schema_sql = f.read()

# Execute schema
with engine.connect() as conn:
    # Split by semicolon and execute
    statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
    for stmt in statements:
        if stmt:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                if 'already exists' not in str(e):
                    print(f'Warning: {e}')
    conn.commit()

print('SUCCESS')
"@

if ($createTables -match "SUCCESS") {
    Write-Host "✅ Database tables created" -ForegroundColor Green
} else {
    Write-Host "⚠️  Warning: Some tables may already exist" -ForegroundColor Yellow
}

Write-Host ""

# Step 4: Load data
Write-Host "Step 4: Loading Brazilian Dataset" -ForegroundColor Yellow
Write-Host "----------------------------------"
Write-Host "This will load all CSV files from 'brazilian dataset' folder..."
Write-Host ""

$loadResult = python scripts/load_brazilian_data.py

Write-Host ""
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host ""

# Step 5: Save connection for future use
Write-Host "Step 5: Saving Connection (Optional)" -ForegroundColor Yellow
Write-Host "-------------------------------------"
$saveConn = Read-Host "Save DATABASE_URL to .env file? (y/n)"

if ($saveConn -eq 'y') {
    $envContent = "DATABASE_URL=$CONNECTION_STRING`n"
    $envContent += "# Generated on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Saved to .env file" -ForegroundColor Green
    Write-Host ""
    Write-Host "To use in future sessions:" -ForegroundColor Cyan
    Write-Host '  Get-Content .env | ForEach-Object { if($_ -match "^([^=]+)=(.*)$") { $env:($matches[1]) = $matches[2] } }' -ForegroundColor Gray
}

Write-Host ""
Write-Host "🎉 Setup Complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Launch dashboard:" -ForegroundColor White
Write-Host "     streamlit run dashboard/streamlit_app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Train ML model:" -ForegroundColor White
Write-Host "     jupyter notebook ml/train_example.ipynb" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Run Airflow pipeline:" -ForegroundColor White
Write-Host "     airflow dags trigger etl_pipeline" -ForegroundColor Gray
Write-Host ""
