@echo off
echo Current Directory: %cd%
REM Navigate to the directory containing your virtual environment
cd .venv/Scripts
echo Current Directory: %cd%
REM Activate the virtual environment
call activate
echo Activated: %cd%
REM Navigate to the directory containing your start_app.py
cd ../../
echo Current Directory: %cd%
REM Run the Tkinter application
python start_app.py
pause
