# E-Commerce ETL Analytics Dashboard Startup Script

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  E-Commerce ETL Analytics Dashboard" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Set database URL
$env:DATABASE_URL = "postgresql://etl_user:etl_password_123@localhost:5432/ETL_DB"

# Navigate to dashboard directory
Set-Location "C:\Users\samar\Desktop\prjct_thash\ETL\dashboard"

Write-Host "Features:" -ForegroundColor Green
Write-Host "  - Complete Order Analytics" -ForegroundColor White
Write-Host "  - Customer Geography & Lifetime Value" -ForegroundColor White
Write-Host "  - Product Performance & Categories" -ForegroundColor White
Write-Host "  - Seller Performance & Distribution" -ForegroundColor White
Write-Host "  - Payment Methods & Installments" -ForegroundColor White
Write-Host "  - Geographic Revenue Analysis" -ForegroundColor White
Write-Host "  - ML Model Integration" -ForegroundColor White
Write-Host ""

Write-Host "Starting Flask Backend..." -ForegroundColor Yellow
Write-Host "Dashboard URL: http://localhost:5001" -ForegroundColor Green
Write-Host "API Base URL: http://localhost:5001/api" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Start the backend
python ecommerce_backend.py
