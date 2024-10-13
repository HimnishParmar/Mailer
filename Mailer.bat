@echo off
echo Current Directory: %cd%



REM Step 0: Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed.
    echo Downloading Python installer...

    REM Download Python installer from the official site
    powershell -Command "(New-Object System.Net.WebClient).DownloadFile('https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe', 'python_installer.exe')"

    echo Installing Python...
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

    REM Clean up by removing the installer file
    del python_installer.exe

    REM Recheck if Python is installed
    python --version >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        echo Python installation failed. Please install Python manually from https://www.python.org.
        pause
        exit /b
    )
) ELSE (
    echo Python is installed.
)



REM Step 1: Check if virtual environment exists
IF NOT EXIST ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
) ELSE (
    echo Virtual environment already exists.
)

REM Step 2: Activate the virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate

REM Step 3: Check if requirements.txt exists and install the dependencies
IF EXIST "requirements.txt" (
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
) ELSE (
    echo requirements.txt not found. Skipping installation.
)

REM Step 4: Run the Tkinter application
echo Running start_app.py...
python start_app.py

REM Prevent the terminal from closing
pause
