@echo off
REM NEMT Simulator - Build Go binaries for Windows
REM This script builds Go services for inclusion in the Electron package

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "DIST_DIR=%PROJECT_ROOT%\dist"
set "GATEWAY_DIR=%DIST_DIR%\gateway"

echo ==========================================
echo Building Go binaries for NEMT Simulator
echo ==========================================

REM Create output directory
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"
if not exist "%GATEWAY_DIR%" mkdir "%GATEWAY_DIR%"

set "OUTPUT_DIR=%GATEWAY_DIR%"

echo Platform: Windows x64
echo Output: %OUTPUT_DIR%

REM Check if Go is available
where go >nul 2>&1
if errorlevel 1 (
    echo ERROR: Go is not installed or not in PATH
    exit /b 1
)

REM Get version info
for /f "delims=" %%v in ('git describe --tags --always 2^>nul') do set "VERSION=%%v"
if not defined VERSION set "VERSION=dev"

for /f "delims=" %%t in ('powershell -Command "Get-Date -Format u"') do set "BUILD_TIME=%%t"

REM Build gateway
echo.
echo Building gateway for Windows/amd64...

cd /d "%PROJECT_ROOT%\src\gateway"

set "CGO_ENABLED=0"
set "GOOS=windows"
set "GOARCH=amd64"

go build -ldflags "-s -w -X main.version=%VERSION% -X main.buildTime=%BUILD_TIME%" -o "%OUTPUT_DIR%\gateway.exe" .\cmd\gateway

if errorlevel 1 (
    echo ERROR: Build failed
    exit /b 1
)

echo Built: %OUTPUT_DIR%\gateway.exe

REM Build for Linux (cross-compile)
echo.
echo Building gateway for Linux/amd64 (cross-compile)...

set "GOOS=linux"

go build -ldflags "-s -w -X main.version=%VERSION% -X main.buildTime=%BUILD_TIME%" -o "%OUTPUT_DIR%\gateway" .\cmd\gateway

if errorlevel 1 (
    echo WARNING: Linux cross-compile failed
) else (
    echo Built: %OUTPUT_DIR%\gateway
)

REM Build for macOS (cross-compile)
echo.
echo Building gateway for macOS (cross-compile)...

set "GOOS=darwin"

REM macOS amd64
go build -ldflags "-s -w -X main.version=%VERSION% -X main.buildTime=%BUILD_TIME%" -o "%OUTPUT_DIR%\gateway-darwin-amd64" .\cmd\gateway

REM macOS arm64
set "GOARCH=arm64"
go build -ldflags "-s -w -X main.version=%VERSION% -X main.buildTime=%BUILD_TIME%" -o "%OUTPUT_DIR%\gateway-darwin-arm64" .\cmd\gateway

echo ==========================================
echo Build complete!
echo Output directory: %OUTPUT_DIR%
echo ==========================================

REM List built files
dir /b "%OUTPUT_DIR%\gateway*" 2>nul || echo No gateway binaries found

endlocal
