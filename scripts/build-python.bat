@echo off
REM NEMT Simulator - Build Python environment for packaging
REM This script creates a Python virtual environment with all dependencies

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "DIST_DIR=%PROJECT_ROOT%\dist"
set "NEMT_OS_DIR=%PROJECT_ROOT%\src\nemt-os"
set "VENV_DIR=%DIST_DIR%\nemt-os-venv"

echo ==========================================
echo Building Python environment for NEMT Simulator
echo ==========================================

REM Create output directory
if not exist "%DIST_DIR%" mkdir "%DIST_DIR%"

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

echo Python found:
python --version

REM Create virtual environment
echo.
echo Creating virtual environment at %VENV_DIR%...

if exist "%VENV_DIR%" (
    echo Removing existing virtual environment...
    rmdir /s /q "%VENV_DIR%"
)

python -m venv "%VENV_DIR%"

if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    exit /b 1
)

REM Activate virtual environment
echo.
echo Activating virtual environment...

call "%VENV_DIR%\Scripts\activate.bat"

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo.
echo Installing Python dependencies...

if exist "%NEMT_OS_DIR%\requirements.txt" (
    pip install -r "%NEMT_OS_DIR%\requirements.txt"
) else (
    echo WARNING: requirements.txt not found, installing basic dependencies...
    pip install numpy scipy grpcio grpcio-tools
)

REM Install NEMT package in development mode
echo.
echo Installing NEMT package...
pip install -e "%NEMT_OS_DIR%"

REM Freeze dependencies
echo.
echo Freezing dependencies to %DIST_DIR%\requirements.txt...
pip freeze > "%DIST_DIR%\requirements.txt"

echo.
echo ==========================================
echo Python environment build complete!
echo Virtual environment: %VENV_DIR%
echo ==========================================

REM List installed packages
echo.
echo Installed packages:
pip list --format=freeze | findstr /v "pip setuptools"

endlocal
