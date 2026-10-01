@echo off
REM BATLI Launcher Script
REM This script installs (if necessary) and runs the BATLI Flask application on Windows.
REM Prerequisites:
REM - Windows operating system
REM Usage:
REM Double-click to run the script.

REM Set script to exit on errors
SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

SET "REPO_URL=https://github.com/pescoll/BATLI.git"
SET "REPO_BRANCH=main"

REM Determine script directory
SET "SCRIPT_DIR=%~dp0"
ECHO Script directory is %SCRIPT_DIR%

REM Set BATLI directory relative to script directory
SET "BATLI_DIR=%SCRIPT_DIR%BATLI"

REM Check if Python is installed
where python >nul 2>&1
IF ERRORLEVEL 1 (
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
IF ERRORLEVEL 1 (
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
    IF EXIST "%BATLI_DIR%\.git" (
        ECHO BATLI repository found at %BATLI_DIR%. Updating repository...
        CD /D "%BATLI_DIR%"
        IF ERRORLEVEL 1 (
            ECHO Failed to enter BATLI directory.
            PAUSE
            EXIT /B 1
        )

        git remote get-url origin >nul 2>&1
        IF ERRORLEVEL 1 (
            git remote add origin "%REPO_URL%"
        ) ELSE (
            git remote set-url origin "%REPO_URL%"
        )

        git fetch --prune origin %REPO_BRANCH%
        IF ERRORLEVEL 1 (
            ECHO Failed to download BATLI updates from GitHub.
            PAUSE
            EXIT /B 1
        )

        git merge --ff-only FETCH_HEAD
        IF ERRORLEVEL 1 (
            ECHO The local BATLI code cannot be updated with a normal fast-forward.
            ECHO Saving a backup of tracked local code, then installing the GitHub version...
            CALL :BACKUP_CURRENT_CODE
            git reset --hard FETCH_HEAD
            IF ERRORLEVEL 1 (
                ECHO Failed to replace the local BATLI code with the GitHub version.
                PAUSE
                EXIT /B 1
            )
        )
    ) ELSE (
        ECHO A BATLI folder exists at %BATLI_DIR%, but it is not a Git repository.
        ECHO Moving it aside and cloning a fresh copy from GitHub...
        CALL :BACKUP_EXISTING_FOLDER
        IF ERRORLEVEL 1 (
            PAUSE
            EXIT /B 1
        )
        git clone "%REPO_URL%" "%BATLI_DIR%"
        IF ERRORLEVEL 1 (
            ECHO Failed to clone the BATLI GitHub repository.
            PAUSE
            EXIT /B 1
        )
        CD /D "%BATLI_DIR%"
    )
) ELSE (
    ECHO Cloning the BATLI GitHub repository into %BATLI_DIR%...
    git clone "%REPO_URL%" "%BATLI_DIR%"
    IF ERRORLEVEL 1 (
        ECHO Failed to clone the BATLI GitHub repository.
        PAUSE
        EXIT /B 1
    )
    CD /D "%BATLI_DIR%"
)

REM Set up virtual environment if not already set up
IF NOT EXIST "venv\Scripts\python.exe" (
    ECHO Setting up virtual environment...
    IF EXIST "venv" RMDIR /S /Q "venv"
    python -m venv venv
    IF ERRORLEVEL 1 (
        ECHO Failed to create the Python virtual environment.
        PAUSE
        EXIT /B 1
    )
)

REM Activate the virtual environment
CALL venv\Scripts\activate.bat
IF ERRORLEVEL 1 (
    ECHO Failed to activate the Python virtual environment.
    PAUSE
    EXIT /B 1
)

REM Repair pip if the virtual environment was created without a working pip entry point
python -m pip --version >nul 2>&1
IF ERRORLEVEL 1 (
    ECHO Pip is missing or broken. Repairing pip...
    python -m ensurepip --upgrade
)

python -m pip --version >nul 2>&1
IF ERRORLEVEL 1 (
    ECHO The virtual environment is damaged. Recreating it...
    CALL venv\Scripts\deactivate.bat >nul 2>&1
    RMDIR /S /Q "venv"
    DEL /Q "venv_installed.flag" >nul 2>&1
    python -m venv venv
    IF ERRORLEVEL 1 (
        ECHO Failed to recreate the Python virtual environment.
        PAUSE
        EXIT /B 1
    )
    CALL venv\Scripts\activate.bat
    IF ERRORLEVEL 1 (
        ECHO Failed to activate the recreated Python virtual environment.
        PAUSE
        EXIT /B 1
    )
    python -m ensurepip --upgrade
)

python -m pip --version >nul 2>&1
IF ERRORLEVEL 1 (
    ECHO Pip could not be repaired. Please reinstall Python with pip enabled.
    PAUSE
    EXIT /B 1
)

REM Upgrade pip
ECHO Upgrading pip...
python -m pip install --upgrade pip
IF ERRORLEVEL 1 (
    ECHO Pip upgrade failed. Continuing with the current pip version...
)

REM Install or update required Python packages
IF EXIST "requirements.txt" (
    ECHO Installing/updating required Python packages from requirements.txt...
    python -m pip install -r requirements.txt
) ELSE (
    ECHO requirements.txt not found. Installing packages manually...
    python -m pip install flask pandas seaborn matplotlib numpy werkzeug
)
IF ERRORLEVEL 1 (
    ECHO Failed to install required Python packages.
    PAUSE
    EXIT /B 1
)
type nul > venv_installed.flag

REM Kill any process using port 5001
ECHO Checking for processes using port 5001...
FOR /F "tokens=5" %%A IN ('netstat -a -n -o ^| findstr :5001 ^| findstr LISTENING') DO (
    ECHO Port 5001 is in use by PID %%A. Attempting to terminate the process...
    taskkill /PID %%A /F >nul 2>&1
    IF !ERRORLEVEL! EQU 0 (
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
start "BATLI" cmd /k "python -m flask run --port=5001"

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
EXIT /B 0

:BACKUP_CURRENT_CODE
FOR /F %%I IN ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') DO SET "BACKUP_STAMP=%%I"
IF NOT DEFINED BACKUP_STAMP SET "BACKUP_STAMP=manual"
SET "BACKUP_NAME=backup-before-update-!BACKUP_STAMP!-!RANDOM!"
git branch "!BACKUP_NAME!" >nul 2>&1
git diff --quiet
IF ERRORLEVEL 1 git stash push -m "!BACKUP_NAME!" >nul 2>&1
ECHO Backup branch/stash name: !BACKUP_NAME!
EXIT /B 0

:BACKUP_EXISTING_FOLDER
FOR /F %%I IN ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') DO SET "BACKUP_STAMP=%%I"
IF NOT DEFINED BACKUP_STAMP SET "BACKUP_STAMP=manual"
SET "BATLI_BACKUP_DIR=%SCRIPT_DIR%BATLI_backup_!BACKUP_STAMP!-!RANDOM!"
MOVE "%BATLI_DIR%" "!BATLI_BACKUP_DIR!" >nul
IF ERRORLEVEL 1 (
    ECHO Failed to move the existing BATLI folder to !BATLI_BACKUP_DIR!.
    EXIT /B 1
)
ECHO Existing BATLI folder moved to !BATLI_BACKUP_DIR!.
EXIT /B 0
