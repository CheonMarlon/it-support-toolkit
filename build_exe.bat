@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title IT Support Toolkit - Build
mode con: cols=80 lines=32 >nul 2>&1
echo.
echo ============================================================================
echo  IT SUPPORT TOOLKIT - PROFESSIONAL CLI EXE BUILDER
echo ============================================================================
echo.
echo  This creates a single portable CONSOLE EXE.
echo  It does NOT create a virtual environment.
echo.
set "PYEXE="
echo [1/6] Detecting Python 3.11+...
py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if not errorlevel 1 for /f "delims=" %%P in ('py -3 -c "import sys; print(sys.executable)"') do set "PYEXE=%%P"
if not defined PYEXE (
  python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
  if not errorlevel 1 for /f "delims=" %%P in ('python -c "import sys; print(sys.executable)"') do set "PYEXE=%%P"
)
if not defined PYEXE goto fail
for /f "delims=" %%V in ('"%PYEXE%" --version 2^>^&1') do echo [OK] %%V

echo [2/6] Checking pip...
"%PYEXE%" -m pip --version >nul 2>&1
if errorlevel 1 goto fail
echo [OK] pip is available.

echo [3/6] Checking PyInstaller...
"%PYEXE%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
  echo [INFO] Installing build-time PyInstaller...
  "%PYEXE%" -m pip install --disable-pip-version-check --no-input "pyinstaller>=6,<7"
  if errorlevel 1 goto fail
)
for /f "delims=" %%V in ('"%PYEXE%" -m PyInstaller --version 2^>^&1') do echo [OK] PyInstaller %%V

echo [4/6] Validating source...
"%PYEXE%" -m src.main --version
if errorlevel 1 goto fail
echo [OK] Source validation passed.

echo [5/6] Building console EXE...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "IT-Support-Toolkit.spec" del /q "IT-Support-Toolkit.spec"
set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"
"%PYEXE%" -m PyInstaller --noconfirm --clean --onefile --console --name "IT-Support-Toolkit" --paths "%HERE%" "%HERE%\src\main.py"
if errorlevel 1 goto fail

echo [6/6] Verifying output...
if not exist "dist\IT-Support-Toolkit.exe" goto fail
copy /y "dist\IT-Support-Toolkit.exe" "%~dp0IT-Support-Toolkit.exe" >nul
if errorlevel 1 goto fail
if not exist "%~dp0IT-Support-Toolkit.exe" goto fail

echo.
echo ============================================================================
echo  BUILD SUCCESSFUL
echo ============================================================================
echo  EXE: %~dp0IT-Support-Toolkit.exe
echo.
echo  This is a CONSOLE application by design.
echo  Copy the EXE, sessions and exports folders to your USB drive.
echo  The finished EXE does NOT require Python.
echo.
pause
endlocal
exit /b 0

:fail
echo.
echo ============================================================================
echo  BUILD FAILED - THE ERROR IS ABOVE
echo ============================================================================
echo.
pause
endlocal
exit /b 1
