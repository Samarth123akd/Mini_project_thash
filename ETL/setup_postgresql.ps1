# PostgreSQL Integration Script for ETL Project
# Run this in PowerShell to set up and test PostgreSQL connection

Write-Host "=== PostgreSQL Integration Setup ===" -ForegroundColor Cyan
Write-Host ""

# Configuration
$DB_HOST = "localhost"
$DB_PORT = "5432"
$DB_NAME = "etl_db"
$DB_USER = "etl_user"
$DB_PASSWORD = "etl_password_123"  # CHANGE THIS!

# Build connection string
$CONNECTION_STRING = "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

Write-Host "Step 1: Checking if PostgreSQL is running..." -ForegroundColor Yellow
$pgService = Get-Service -Name "postgresql*" -ErrorAction SilentlyContinue
if ($pgService) {
    if ($pgService.Status -eq "Running") {
        Write-Host "✅ PostgreSQL service is running" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Starting PostgreSQL service..." -ForegroundColor Yellow
        Start-Service $pgService.Name
        Write-Host "✅ PostgreSQL service started" -ForegroundColor Green
    }
} else {
    Write-Host "⚠️  PostgreSQL service not found. It might be installed but not as a service." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 2: Setting up database and user..." -ForegroundColor Yellow
Write-Host "Please follow these steps in pgAdmin:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Option A - Using pgAdmin (Recommended):" -ForegroundColor White
Write-Host "1. Open pgAdmin and connect to PostgreSQL 18" -ForegroundColor Gray
Write-Host "2. Right-click 'Databases' → Create → Database" -ForegroundColor Gray
Write-Host "   - Name: etl_db" -ForegroundColor Gray
Write-Host "   - Click Save" -ForegroundColor Gray
Write-Host "3. Right-click 'Login/Group Roles' → Create → Login/Group Role" -ForegroundColor Gray
Write-Host "   - Name: etl_user" -ForegroundColor Gray
Write-Host "   - Definition tab → Password: etl_password_123" -ForegroundColor Gray
Write-Host "   - Privileges tab → Check 'Can login?'" -ForegroundColor Gray
Write-Host "   - Click Save" -ForegroundColor Gray
Write-Host "4. Click on etl_db → Tools → Query Tool" -ForegroundColor Gray
Write-Host "5. Copy and run the SQL from 'setup_database.sql' (Step 5 only)" -ForegroundColor Gray
Write-Host ""
Write-Host "Option B - Using psql command line:" -ForegroundColor White
Write-Host "Run this command and enter your postgres password when prompted:" -ForegroundColor Gray
Write-Host "psql -U postgres -f setup_database.sql" -ForegroundColor Yellow
Write-Host ""

$response = Read-Host "Have you completed the database setup? (y/n)"
if ($response -ne 'y') {
    Write-Host "Please complete the setup and run this script again." -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "Step 3: Testing database connection..." -ForegroundColor Yellow

# Test connection using Python
try {
    $testResult = python -c @"
from sqlalchemy import create_engine
import sys
try:
    engine = create_engine('$CONNECTION_STRING')
    conn = engine.connect()
    print('SUCCESS')
    conn.close()
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"@
    
    if ($testResult -match "SUCCESS") {
        Write-Host "✅ Database connection successful!" -ForegroundColor Green
    } else {
        Write-Host "❌ Connection failed: $testResult" -ForegroundColor Red
        Write-Host ""
        Write-Host "Troubleshooting tips:" -ForegroundColor Yellow
        Write-Host "1. Make sure etl_db database exists in pgAdmin" -ForegroundColor Gray
        Write-Host "2. Make sure etl_user login role exists" -ForegroundColor Gray
        Write-Host "3. Check password is correct: etl_password_123" -ForegroundColor Gray
        Write-Host "4. Verify PostgreSQL is listening on port 5432" -ForegroundColor Gray
        exit 1
    }
} catch {
    Write-Host "❌ Python test failed. Make sure Python and sqlalchemy are installed." -ForegroundColor Red
    Write-Host "Run: pip install sqlalchemy psycopg2-binary" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Step 4: Setting environment variable..." -ForegroundColor Yellow
$env:DATABASE_URL = $CONNECTION_STRING
Write-Host "✅ DATABASE_URL set for current session" -ForegroundColor Green

# Create .env file
$envContent = @"
DATABASE_URL=$CONNECTION_STRING
AIRFLOW_CONN_POSTGRES_DEFAULT=$CONNECTION_STRING
"@
$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Host "✅ Created .env file with connection string" -ForegroundColor Green

Write-Host ""
Write-Host "Step 5: Creating database tables..." -ForegroundColor Yellow

if (Test-Path "sql\schema.sql") {
    try {
        # Try using psql
        $schemaResult = psql $CONNECTION_STRING -f "sql\schema.sql" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Database schema created successfully" -ForegroundColor Green
        } else {
            Write-Host "⚠️  psql command failed. Creating tables via pgAdmin..." -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Please do this manually in pgAdmin:" -ForegroundColor Cyan
            Write-Host "1. Click on etl_db database" -ForegroundColor Gray
            Write-Host "2. Tools → Query Tool" -ForegroundColor Gray
            Write-Host "3. Open sql\schema.sql file" -ForegroundColor Gray
            Write-Host "4. Click Execute (F5)" -ForegroundColor Gray
            Write-Host ""
            Read-Host "Press Enter after you've created the tables..."
        }
    } catch {
        Write-Host "⚠️  Using pgAdmin method..." -ForegroundColor Yellow
        Write-Host "Please open pgAdmin and run sql\schema.sql in Query Tool" -ForegroundColor Cyan
        Read-Host "Press Enter after you've created the tables..."
    }
} else {
    Write-Host "❌ schema.sql not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Step 6: Verifying tables..." -ForegroundColor Yellow

$verifyQuery = @"
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
"@

try {
    $tables = python -c @"
from sqlalchemy import create_engine, text
engine = create_engine('$CONNECTION_STRING')
conn = engine.connect()
result = conn.execute(text(\"\"\"$verifyQuery\"\"\"))
tables = [row[0] for row in result]
for table in tables:
    print(table)
conn.close()
"@
    
    if ($tables) {
        Write-Host "✅ Found tables:" -ForegroundColor Green
        $tables | ForEach-Object { Write-Host "   - $_" -ForegroundColor Gray }
    } else {
        Write-Host "⚠️  No tables found. Please create tables manually using pgAdmin." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not verify tables. Check pgAdmin manually." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run ETL pipeline:" -ForegroundColor White
Write-Host "   python scripts\run_etl.py" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Or load data manually:" -ForegroundColor White
Write-Host "   python -c `"from etl.transform import transform_csv; transform_csv('data/staging/olist_orders_dataset.csv', 'data/staging/clean/orders_clean.csv')`"" -ForegroundColor Gray
Write-Host "   python scripts\load_to_db.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Launch dashboard:" -ForegroundColor White
Write-Host "   streamlit run dashboard\streamlit_app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "Connection string saved to .env file" -ForegroundColor Green
Write-Host "DATABASE_URL=$CONNECTION_STRING" -ForegroundColor Gray
