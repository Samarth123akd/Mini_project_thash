# Premium Analytics Dashboard Startup Script
# Launches the ML-powered dashboard with all features

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  🚀 Premium Analytics Dashboard - ML-Powered" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Set DATABASE_URL
$env:DATABASE_URL = "postgresql://etl_user:etl_password_123@localhost:5432/ETL_DB"

Write-Host "📊 Database: " -NoNewline -ForegroundColor Green
Write-Host "ETL_DB (PostgreSQL)"

Write-Host "🤖 ML Model: " -NoNewline -ForegroundColor Green
Write-Host "Order Total Prediction (RandomForest)"

Write-Host "🌐 Dashboard URL: " -NoNewline -ForegroundColor Green
Write-Host "http://localhost:5000"

Write-Host "🎨 Features: " -NoNewline -ForegroundColor Green
Write-Host "Revenue Forecast, CLV Analysis, ML Insights, Product Recommendations"

Write-Host ""
Write-Host "Starting enhanced Flask server..." -ForegroundColor Yellow
Write-Host ""

# Navigate to dashboard directory
cd "$PSScriptRoot"

# Start the ML-powered backend
python ml_backend.py
