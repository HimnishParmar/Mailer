@echo off
echo Current Directory: %cd%
setlocal enabledelayedexpansion


REM Step 1: Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed.

    REM Ask the user for confirmation to download and install Python
    set /p install_python="Python is not installed. Do you want to download and install Python 3.12? (Y/N): "
    IF "!install_python!"=="Y" (
        echo Downloading Python installer...

         REM Download Python installer using bitsadmin
         bitsadmin /transfer "DownloadPython" https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe %cd%\python_installer.exe
    
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
        ) ELSE (
            echo Python installed successfully.
        )
    ) ELSE (
        echo Python installation skipped. Exiting...
        pause
        exit /b
    )
) ELSE (
    REM Check if Python version is 3.11.* or higher
    python --version 2>nul | findstr /r "^Python 3\.\(11\|[1-9][2-9]\)\.[0-9]+.*" >nul
    IF %ERRORLEVEL% NEQ 0 (
        echo Python 3.11 or higher is required. Current version is lower.

        REM Ask the user for confirmation to download and install Python 3.12
        set /p install_python="Do you want to download and install Python 3.12? (Y/N): "
        IF /I "%install_python%"=="Y" (
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
            ) ELSE (
                echo Python installed successfully.
            )
        ) ELSE (
            echo Python installation skipped. Exiting...
            pause
            exit /b
        )
    ) ELSE (
        echo Python version is 3.11 or higher.
    )
)

REM Step 2: Check for Tkinter availability
python -c "import tkinter" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Tkinter is not installed. Please reinstall Python with Tkinter support.
    pause
    exit /b
) ELSE (
    echo Tkinter is available.
)

REM Step 3: Check if virtual environment exists and activation script is present, if not, create/recreate it
IF NOT EXIST ".venv\Scripts\activate" (
    echo Virtual environment or activation script not found, creating or recreating it...
    REM Remove any existing .venv directory if it's corrupted
    IF EXIST ".venv" (
        rmdir /s /q ".venv"
        echo Removed existing virtual environment.
    )
    REM Create a new virtual environment
    python -m venv .venv
    IF %ERRORLEVEL% NEQ 0 (
        echo Failed to create virtual environment. Ensure Python and venv are correctly installed.
        pause
        exit /b
    ) ELSE (
        echo Virtual environment created successfully.
    )
) ELSE (
    echo Virtual environment and activation script found.
)

REM Step 4: Attempt to activate the virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate

REM Verify if virtual environment is activated
IF "%VIRTUAL_ENV%" == "" (
    echo Virtual environment activation failed. Recreating virtual environment...
    REM Remove the existing virtual environment if activation fails
    rmdir /s /q ".venv"
    REM Create a new virtual environment
    python -m venv .venv
    IF %ERRORLEVEL% NEQ 0 (
        echo Failed to recreate virtual environment. Ensure Python and venv are correctly installed.
        pause
        exit /b
    )
    REM Activate the virtual environment again
    echo Re-activating the virtual environment...
    call .venv\Scripts\activate
    IF "%VIRTUAL_ENV%" == "" (
        echo Virtual environment activation failed after reattempt. Exiting.
        pause
        exit /b
    ) ELSE (
        echo Virtual environment reactivated successfully.
    )
) ELSE (
    echo Virtual environment activated successfully.
)

REM Step 5: Check if requirements.txt exists and install the dependencies
IF EXIST "requirements.txt" (
    echo Installing dependencies from requirements.txt...
    pip install -r requirements.txt
    IF %ERRORLEVEL% NEQ 0 (
        echo Failed to install dependencies. Please check the requirements.txt file.
        pause
        exit /b
    )
) ELSE (
    echo requirements.txt not found. Skipping installation.
)

REM Step 6: Check if start_app.py exists and run the Tkinter application
IF EXIST "start_app.py" (
    echo Running start_app.py...
    python start_app.py
    IF %ERRORLEVEL% NEQ 0 (
        echo Failed to run start_app.py. Please check for errors in the script.
        pause
        exit /b
    )
) ELSE (
    echo start_app.py not found. Please ensure the script exists in the current directory.
    pause
    exit /b
)


pause
