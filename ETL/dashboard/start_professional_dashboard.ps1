# Professional Dashboard Startup Script
# Brazilian E-Commerce Analytics Dashboard

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  📊 Starting Professional E-Commerce Analytics Dashboard" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Navigate to dashboard directory
Set-Location -Path $PSScriptRoot

# Activate virtual environment and start dashboard
Write-Host "🚀 Starting Flask backend..." -ForegroundColor Green
$pythonPath = "C:/Users/samar/Desktop/prjct_thash/.venv/Scripts/python.exe"

Write-Host ""
Write-Host "✨ Dashboard will be available at:" -ForegroundColor Yellow
Write-Host "   http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "📊 Features:" -ForegroundColor Magenta
Write-Host "   • Real-time KPIs from 99,441+ orders" -ForegroundColor White
Write-Host "   • Interactive sales timeline charts" -ForegroundColor White
Write-Host "   • Top products & customer distribution" -ForegroundColor White
Write-Host "   • Payment methods & order status analysis" -ForegroundColor White
Write-Host "   • ML model performance metrics" -ForegroundColor White
Write-Host "   • Professional gradient UI with glassmorphism" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor DarkGray
Write-Host ""

& $pythonPath csv_dashboard.py
