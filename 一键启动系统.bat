@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

cd /d "%~dp0"
title Traffic System One-Click Start

set "ENV_NAME=dev"
set "INSTALL_DEPS=0"
set "OPEN_BROWSER=1"

if /I "%~1"=="dev" set "ENV_NAME=dev"
if /I "%~1"=="test" set "ENV_NAME=test"
if /I "%~1"=="prod" set "ENV_NAME=prod"

if /I "%~2"=="install" set "INSTALL_DEPS=1"
if /I "%~2"=="noopen" set "OPEN_BROWSER=0"
if /I "%~3"=="noopen" set "OPEN_BROWSER=0"

echo [INFO] Project Root: %cd%
echo [INFO] Env: %ENV_NAME%

where powershell >nul 2>&1
if errorlevel 1 (
  echo [ERROR] PowerShell not found.
  goto :fail
)

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found. Please install Python and add it to PATH.
  goto :fail
)

if not exist ".\ops\scripts\deploy_env.ps1" (
  echo [ERROR] Missing script: .\ops\scripts\deploy_env.ps1
  goto :fail
)

set "ENV_FILE=.\ops\environments\%ENV_NAME%.env"
if not exist "%ENV_FILE%" (
  echo [ERROR] Missing env file: %ENV_FILE%
  goto :fail
)

set "API_HOST=127.0.0.1"
set "API_PORT=8000"
set "FRONTEND_PORT=5500"

for /f "usebackq tokens=1,* delims==" %%A in ("%ENV_FILE%") do (
  if not "%%A"=="" (
    set "K=%%A"
    set "V=%%B"
    if not "!K:~0,1!"=="#" (
      if /I "!K!"=="API_HOST" set "API_HOST=!V!"
      if /I "!K!"=="API_PORT" set "API_PORT=!V!"
      if /I "!K!"=="FRONTEND_PORT" set "FRONTEND_PORT=!V!"
    )
  )
)

if /I "%API_HOST%"=="0.0.0.0" set "API_HOST=127.0.0.1"

set "PS_ARGS=-NoProfile -ExecutionPolicy Bypass -File .\ops\scripts\deploy_env.ps1 -EnvName %ENV_NAME%"
if "%INSTALL_DEPS%"=="0" set "PS_ARGS=%PS_ARGS% -NoInstall"

echo [INFO] Running: powershell %PS_ARGS%
powershell %PS_ARGS%
if errorlevel 1 (
  echo [ERROR] Startup failed. Check logs under ops\logs\%ENV_NAME%\
  goto :fail
)

set "API_URL=http://%API_HOST%:%API_PORT%"
set "FRONTEND_URL=http://127.0.0.1:%FRONTEND_PORT%"

echo.
echo ==========================================
echo [OK] System started successfully.
echo [OK] API: %API_URL%
echo [OK] Frontend: %FRONTEND_URL%
echo [OK] Stop cmd: powershell -ExecutionPolicy Bypass -File .\ops\scripts\stop_env.ps1 -EnvName %ENV_NAME%
echo ==========================================
echo.

if "%OPEN_BROWSER%"=="1" (
  start "" "%FRONTEND_URL%"
)

goto :end

:fail
echo.
echo [FAIL] One-click startup failed.
exit /b 1

:end
exit /b 0
