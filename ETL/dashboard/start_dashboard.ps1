# Start E-Commerce Dashboard
# This script starts the Flask backend server for the dashboard

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "  E-Commerce Analytics Dashboard Startup" -ForegroundColor Yellow
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host ""

# Set DATABASE_URL
$env:DATABASE_URL = "postgresql://etl_user:etl_password_123@localhost:5432/ETL_DB"

Write-Host "📊 Database: " -NoNewline -ForegroundColor Green
Write-Host "ETL_DB"

Write-Host "🌐 Server: " -NoNewline -ForegroundColor Green
Write-Host "http://localhost:5000"

Write-Host ""
Write-Host "Starting Flask server..." -ForegroundColor Yellow
Write-Host ""

# Navigate to dashboard directory
cd "$PSScriptRoot"

# Start the Flask app
python backend_api.py
