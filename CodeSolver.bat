@echo off
setlocal
set "APP_ROOT=%~dp0"
cd /d "%APP_ROOT%"
set PYTHONUTF8=1
set PYTHONDONTWRITEBYTECODE=1
title CodeSolver Offline
chcp 65001 >nul
if not exist "%APP_ROOT%runtime\python\python.exe" (
  echo ERROR: falta runtime\python\python.exe. Ejecuta tools\fetch_deps.py en la maquina de desarrollo.
  pause
  exit /b 1
)
if "%~1"=="solve" (
  shift
  "%APP_ROOT%runtime\python\python.exe" -X utf8 "%APP_ROOT%app\cli.py" %1 %2 %3 %4 %5 %6
  exit /b %errorlevel%
)
"%APP_ROOT%runtime\python\python.exe" -X utf8 "%APP_ROOT%app\launcher.py" %*
if errorlevel 1 (
  echo.
  echo CodeSolver termino con error %errorlevel%. Revisa la carpeta logs\.
  pause
)
endlocal
