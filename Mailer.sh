#!/bin/bash

# Navigate to the directory containing the virtual environment
cd .venv/bin
# Activate the virtual environment
source activate
# Navigate back to the root folder
cd ../..
# Run the Python app
python start_app.py
