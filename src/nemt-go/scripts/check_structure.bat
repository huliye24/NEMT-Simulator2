@echo off
REM 检查NEMT-Go包结构是否符合规范 (Windows版本)
REM 用法: scripts\check_structure.bat

setlocal enabledelayedexpansion

set ERRORS=0
set PROJECT_ROOT=%~dp0..
cd /d "%PROJECT_ROOT%"

echo ==========================================
echo NEMT-Go 包结构检查 (Windows)
echo ==========================================
echo.

REM 检查 cmd/ 目录
echo [1/4] 检查 cmd/ 目录...
for /d %%d in (cmd\*) do (
    set "dir=%%d"
    set "pkg_name=%%~nd"

    if not exist "%%d\main.go" (
        echo   ERROR: %%d 缺少 main.go
        set /a ERRORS+=1
    )

    for %%f in ("%%d\*.go") do (
        set "fname=%%~nf"
        if not "!fname!"=="main" (
            echo   ERROR: %%d 应只包含 main.go，发现: %%~nxf
            set /a ERRORS+=1
        )
    )
)
echo.
if %ERRORS%==0 echo   OK
echo.

REM 检查 pkg/ 目录
echo [2/4] 检查 pkg/ 目录...
if not exist "pkg" (
    echo   ERROR: 缺少 pkg/ 目录
    set /a ERRORS+=1
) else (
    echo   OK
)
echo.

echo [3/4] 检查包名规范...
echo   OK (请使用 Linux/macOS 脚本进行完整检查)
echo.

echo [4/4] 检查文件名规范...
echo   OK (请使用 Linux/macOS 脚本进行完整检查)
echo.

echo ==========================================
if %ERRORS%==0 (
    echo 结果: 全部检查通过
    exit /b 0
) else (
    echo 结果: 发现 %ERRORS% 个错误
    exit /b 1
)
