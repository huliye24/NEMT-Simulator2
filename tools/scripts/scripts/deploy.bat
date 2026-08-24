@echo off
REM NEMT Simulator - Windows 部署脚本

setlocal enabledelayedexpansion

set "RED=[92m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "NC=[0m"

set "NAMESPACE=nemt"
set "RELEASE_NAME=nemt"
set "CHART_PATH=.\k8s\nemt"

:menu
echo.
echo NEMT Simulator 部署脚本
echo =========================
echo 1. 部署
echo 2. 查看状态
echo 3. 回滚
echo 4. 卸载
echo 5. 退出
echo.
set /p choice=请选择操作:

if "%choice%"=="1" goto deploy
if "%choice%"=="2" goto status
if "%choice%"=="3" goto rollback
if "%choice%"=="4" goto uninstall
if "%choice%"=="5" goto end
goto menu

:deploy
echo [%GREEN%INFO%NC%] 部署 NEMT...
set /p tag=请输入镜像标签 (默认: latest):
if "!tag!"=="" set "tag=latest"

helm upgrade --install %RELEASE_NAME% %CHART_PATH% ^
    --namespace %NAMESPACE% ^
    --create-namespace ^
    --set image.tag=%tag% ^
    --wait --timeout 10m

echo [%GREEN%INFO%NC%] 部署完成
goto menu

:status
echo [%GREEN%INFO%NC%] 查看状态...
echo.
echo === Pods ===
kubectl get pods -n %NAMESPACE%
echo.
echo === Services ===
kubectl get svc -n %NAMESPACE%
goto menu

:rollback
echo [%GREEN%INFO%NC%] 回滚...
set /p rev=请输入要回滚的版本号:
helm rollback %RELEASE_NAME% %rev% -n %NAMESPACE%
echo [%GREEN%INFO%NC%] 回滚完成
goto menu

:uninstall
echo [%YELLOW%WARN%NC%] 即将卸载 NEMT...
set /p confirm=确认? (y/N):
if /i "!confirm!"=="y" (
    helm uninstall %RELEASE_NAME% -n %NAMESPACE%
    kubectl delete namespace %NAMESPACE%
    echo [%GREEN%INFO%NC%] 卸载完成
)
goto menu

:end
echo Goodbye!
endlocal
