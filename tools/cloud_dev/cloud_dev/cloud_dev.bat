@echo off
chcp 65001 >nul
REM 云端开发环境管理脚本

echo.
echo ========================================
echo    Cloud Dev Environment Manager
echo ========================================
echo.

if "%1"=="" goto status
if "%1"=="status" goto status
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="logs" goto logs
if "%1"=="setup" goto setup

:usage
echo 用法:
echo   cloud_dev.bat           查看状态
echo   cloud_dev.bat status    查看状态
echo   cloud_dev.bat start     启动服务
echo   cloud_dev.bat stop      停止服务
echo   cloud_dev.bat restart   重启服务
echo   cloud_dev.bat logs      查看日志
echo   cloud_dev.bat setup     初始化配置
echo.
goto end

:status
python "%~dp0cloud_dev.py" status
goto end

:start
python "%~dp0cloud_dev.py" start
goto end

:stop
python "%~dp0cloud_dev.py" stop
goto end

:restart
python "%~dp0cloud_dev.py" restart
goto end

:logs
python "%~dp0cloud_dev.py" logs %2
goto end

:setup
python "%~dp0cloud_dev.py" setup
goto end

:end
