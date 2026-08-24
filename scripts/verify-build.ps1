# NEMT Simulator - Build Verification Script
# Run this to check if all components are in place

$BASE_DIR = "e:\NEMT Simulator"
Set-Location $BASE_DIR

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "NEMT Simulator - Build Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0

# Check directory structure
Write-Host "[1/8] Checking directory structure..." -ForegroundColor Yellow
$requiredDirs = @(
    "src/desktop/main",
    "src/desktop/preload",
    "src/desktop/shared",
    "src/web",
    "src/gateway",
    "src/collector",
    "src/scheduler",
    "src/gateway-pkg",
    "src/nemt-os",
    "configs",
    "build",
    "scripts"
)

foreach ($dir in $requiredDirs) {
    $path = Join-Path $BASE_DIR $dir
    if (Test-Path $path) {
        Write-Host "  [OK] $dir" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $dir" -ForegroundColor Red
        $errors++
    }
}
Write-Host ""

# Check key files
Write-Host "[2/8] Checking key files..." -ForegroundColor Yellow
$requiredFiles = @(
    "src/desktop/main/index.ts",
    "src/desktop/preload/index.ts",
    "src/desktop/shared/types.ts",
    "src/gateway/cmd/gateway/main.go",
    "src/nemt-os/grpc_server.py",
    "package.json",
    "Makefile"
)

foreach ($file in $requiredFiles) {
    $path = Join-Path $BASE_DIR $file
    if (Test-Path $path) {
        Write-Host "  [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $file" -ForegroundColor Red
        $errors++
    }
}
Write-Host ""

# Check Web files
Write-Host "[3/8] Checking Web frontend..." -ForegroundColor Yellow
$webFiles = @("src/web/package.json", "src/web/App.tsx")
foreach ($file in $webFiles) {
    $path = Join-Path $BASE_DIR $file
    if (Test-Path $path) {
        Write-Host "  [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $file" -ForegroundColor Red
        $errors++
    }
}
Write-Host ""

# Check Python files
Write-Host "[4/8] Checking Python engine..." -ForegroundColor Yellow
$pyFiles = @("src/nemt-os/nemt/__init__.py", "src/nemt-os/main.py")
foreach ($file in $pyFiles) {
    $path = Join-Path $BASE_DIR $file
    if (Test-Path $path) {
        Write-Host "  [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $file" -ForegroundColor Red
        $errors++
    }
}
Write-Host ""

# Check Go files
Write-Host "[5/8] Checking Go services..." -ForegroundColor Yellow
$goFiles = @("src/gateway/go.mod", "src/gateway/cmd/gateway/main.go")
foreach ($file in $goFiles) {
    $path = Join-Path $BASE_DIR $file
    if (Test-Path $path) {
        Write-Host "  [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $file" -ForegroundColor Red
        $errors++
    }
}
Write-Host ""

# Check configs
Write-Host "[6/8] Checking configuration files..." -ForegroundColor Yellow
$configFiles = @("configs/dev.yaml", "configs/prod.yaml")
foreach ($file in $configFiles) {
    $path = Join-Path $BASE_DIR $file
    if (Test-Path $path) {
        Write-Host "  [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $file" -ForegroundColor Red
        $errors++
    }
}
Write-Host ""

# Check npm dependencies
Write-Host "[7/8] Checking npm dependencies..." -ForegroundColor Yellow
if (Test-Path "package.json") {
    if (Test-Path "node_modules") {
        Write-Host "  [OK] node_modules exists" -ForegroundColor Green
    } else {
        Write-Host "  [INFO] Run 'npm install' to install dependencies" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [MISSING] package.json" -ForegroundColor Red
    $errors++
}
Write-Host ""

# Check Python dependencies
Write-Host "[8/8] Checking Python dependencies..." -ForegroundColor Yellow
if (Test-Path "src/nemt-os/requirements.txt") {
    Write-Host "  [OK] requirements.txt exists" -ForegroundColor Green
} else {
    Write-Host "  [INFO] Create requirements.txt if needed" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
if ($errors -eq 0) {
    Write-Host "Verification PASSED - All checks successful!" -ForegroundColor Green
} else {
    Write-Host "Verification FAILED - $errors error(s) found" -ForegroundColor Red
}
Write-Host "========================================" -ForegroundColor Cyan

exit $errors
