@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title IT Support Toolkit
mode con: cols=80 lines=30 >nul 2>&1

echo.
echo ============================================================================
echo  IT SUPPORT TOOLKIT
echo  Professional CLI Technician Console
echo ============================================================================
echo.
echo  Checking Python 3.11+...
set "PYEXE="
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if not errorlevel 1 for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)"') do set "PYEXE=%%P"
if not defined PYEXE (
  python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
  if not errorlevel 1 for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)"') do set "PYEXE=%%P"
)
if not defined PYEXE (
  echo  [FAIL] Python 3.11+ was not found.
  echo.
  echo  The finished EXE does not require Python.
  pause
  exit /b 1
)
for /f "delims=" %%V in ('"%PYEXE%" --version 2^>^&1') do echo  [OK] %%V
echo.
echo  Starting technician console...
echo.
"%PYEXE%" -m src.main
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo.
  echo  [FAIL] Application exited with code %RC%.
  pause
)
endlocal & exit /b %RC%
