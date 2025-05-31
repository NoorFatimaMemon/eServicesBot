@echo off
setlocal

:: Check if Python is installed
where python >nul 2>&1
if %errorlevel% equ 0 (
    echo Python is already installed.
    goto install_requirements
) else (
    echo Python not found. Installing Python...
)

:: Set Python version
set PYTHON_VERSION=3.10.0
set PYTHON_INSTALLER=python-%PYTHON_VERSION%-amd64.exe
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_INSTALLER%

:: Download Python installer using curl or PowerShell as fallback
echo Downloading Python %PYTHON_VERSION%...

where curl >nul 2>&1
if %errorlevel% equ 0 (
    curl -o %PYTHON_INSTALLER% %PYTHON_URL%
) else (
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'"
)

if %errorlevel% neq 0 (
    echo ERROR: Failed to download Python!
    pause
    exit /b 1
)
echo Download complete.

:: Install Python silently
echo Installing Python...
start /wait %PYTHON_INSTALLER% /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
if %errorlevel% neq 0 (
    echo ERROR: Python installation failed!
    pause
    exit /b 1
)
echo Python installed successfully.

:: Refresh environment variables (for current session)
set "PATH=C:\Program Files\Python310;C:\Program Files\Python310\Scripts;%PATH%"

:: Ensure Python is recognized
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not recognized after installation!
    pause
    exit /b 1
)
echo Python is now recognized.

:: Install pip (if missing)
python -m ensurepip
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ERROR: Pip installation failed!
    pause
    exit /b 1
)
echo Pip installed successfully.

:install_requirements
:: Install dependencies from requirements.txt
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)
echo Requirements installed successfully.

echo Script finished successfully!
pause