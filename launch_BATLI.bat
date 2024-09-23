@echo off
REM BATLI Launcher Script
REM This script installs (if necessary) and runs the BATLI Flask application on Windows.
REM Prerequisites:
REM - Windows operating system
REM Usage:
REM Double-click to run the script.

REM Set script to exit on errors
SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
SET ERRORLEVEL=0

REM Determine script directory
SET SCRIPT_DIR=%~dp0
ECHO Script directory is %SCRIPT_DIR%

REM Set BATLI directory relative to script directory
SET BATLI_DIR=%SCRIPT_DIR%BATLI

REM Check if Python is installed
where python >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Python is not installed.
    ECHO Please install Python 3.7 or higher from:
    ECHO https://www.python.org/downloads/windows/
    PAUSE
    EXIT /B 1
) ELSE (
    ECHO Python is installed.
)

REM Check if Git is installed
where git >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Git is not installed.
    ECHO Please install Git for Windows from:
    ECHO https://git-scm.com/download/win
    PAUSE
    EXIT /B 1
) ELSE (
    ECHO Git is installed.
)

REM Check if BATLI repository exists
IF EXIST "%BATLI_DIR%" (
    ECHO BATLI repository found at %BATLI_DIR%. Updating repository...
    CD /D "%BATLI_DIR%"
    git pull origin main
) ELSE (
    ECHO Cloning the BATLI GitHub repository into %BATLI_DIR%...
    git clone https://github.com/pescoll/BATLI.git "%BATLI_DIR%"
    CD /D "%BATLI_DIR%"
)

REM Set up virtual environment if not already set up
IF NOT EXIST "venv" (
    ECHO Setting up virtual environment...
    python -m venv venv
)

REM Activate the virtual environment
CALL venv\Scripts\activate.bat

REM Upgrade pip
ECHO Upgrading pip...
python -m pip install --upgrade pip

REM Install required Python packages if necessary
IF NOT EXIST "venv_installed.flag" (
    IF EXIST "requirements.txt" (
        ECHO Installing required Python packages from requirements.txt...
        pip install -r requirements.txt
    ) ELSE (
        ECHO requirements.txt not found. Installing packages manually...
        pip install flask pandas seaborn matplotlib numpy werkzeug
    )
    REM Create a flag file to indicate installation is complete
    type nul > venv_installed.flag
) ELSE (
    ECHO Required Python packages already installed.
)

REM Kill any process using port 5001
ECHO Checking for processes using port 5001...
FOR /F "tokens=5" %%A IN ('netstat -a -n -o ^| findstr :5001 ^| findstr LISTENING') DO (
    ECHO Port 5001 is in use by PID %%A. Attempting to terminate the process...
    taskkill /PID %%A /F >nul 2>&1
    IF %ERRORLEVEL% EQU 0 (
        ECHO Process terminated.
    ) ELSE (
        ECHO Failed to terminate process PID %%A.
    )
)

REM Start the Flask application in the background
ECHO Starting BATLI...

REM Set environment variables
SET FLASK_APP=app.py
SET FLASK_ENV=development

REM Run Flask app in a new command window
start "BATLI" cmd /k "flask run --port=5001"

REM Give the Flask app time to start
TIMEOUT /T 2 /NOBREAK >nul

REM Open the web browser to the Flask app URL
ECHO Opening the web browser to http://localhost:5001
start http://localhost:5001

REM Wait for the user to close the Flask app
ECHO.
ECHO Press any key to stop the BATLI application...
PAUSE >nul

REM Close the Flask app
taskkill /FI "WINDOWTITLE eq BATLI" /F >nul 2>&1

REM Deactivate the virtual environment
CALL venv\Scripts\deactivate.bat

ECHO BATLI has been stopped.

ENDLOCAL
