#!/bin/bash

echo "Current Directory: $(pwd)"

# Step 1: Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Step 2: Activate the virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Step 3: Check if requirements.txt exists and install the dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Skipping installation."
fi

# Step 4: Run the Tkinter application
echo "Running start_app.py..."
python start_app.py

# Prevent the terminal from closing
read -p "Press any key to exit..."
