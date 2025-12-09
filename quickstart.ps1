# ============================================================================
# Quick Start Script for Local Artisan E-Marketplace
# ============================================================================
# Purpose: Automated setup and verification script
# Usage: Run this after completing manual setup steps
# ============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Local Artisan E-Marketplace - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check PostgreSQL installation
Write-Host "[2/6] Checking PostgreSQL installation..." -ForegroundColor Yellow
try {
    $psqlVersion = psql --version 2>&1
    Write-Host "✓ $psqlVersion found" -ForegroundColor Green
} catch {
    Write-Host "✗ PostgreSQL not found. Please install PostgreSQL 14+" -ForegroundColor Red
    exit 1
}

# Check if virtual environment exists
Write-Host "[3/6] Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✓ Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "! Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[4/6] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "✓ Virtual environment activated" -ForegroundColor Green

# Install dependencies
Write-Host "[5/6] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Test database connection
Write-Host "[6/6] Testing database connection..." -ForegroundColor Yellow
Write-Host "Note: You may be prompted for PostgreSQL password" -ForegroundColor Cyan

$testQuery = "SELECT COUNT(*) FROM users;"
$result = psql -U postgres -d artisan_marketplace -t -c $testQuery 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Database connection successful" -ForegroundColor Green
    Write-Host "✓ Found $result users in database" -ForegroundColor Green
} else {
    Write-Host "✗ Database connection failed" -ForegroundColor Red
    Write-Host "Please ensure:" -ForegroundColor Yellow
    Write-Host "  1. PostgreSQL service is running" -ForegroundColor Yellow
    Write-Host "  2. Database 'artisan_marketplace' exists" -ForegroundColor Yellow
    Write-Host "  3. schema.sql has been loaded" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To fix:" -ForegroundColor Yellow
    Write-Host "  psql -U postgres -d artisan_marketplace -f schema.sql" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Start the backend server:" -ForegroundColor White
Write-Host "   python -m uvicorn main:app --reload" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Open the frontend:" -ForegroundColor White
Write-Host "   Open 'app.html' in your browser" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Test accounts:" -ForegroundColor White
Write-Host "   Artisan: artisan1 / password123" -ForegroundColor Cyan
Write-Host "   Buyer:   buyer1 / password123" -ForegroundColor Cyan
Write-Host "   Admin:   admin1 / password123" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. API Documentation:" -ForegroundColor White
Write-Host "   http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Happy testing! 🚀" -ForegroundColor Green
