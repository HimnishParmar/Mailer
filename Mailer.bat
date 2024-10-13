@echo off
echo Current Directory: %cd%

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
