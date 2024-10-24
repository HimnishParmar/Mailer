#!/bin/bash

echo "Current Directory: $(pwd)"

# Step 1: Check if Python is installed and meets the required version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

install_python() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Installing Python $REQUIRED_VERSION on Linux..."
        sudo apt update
        sudo apt install -y python3 python3-venv python3-pip
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Installing Python $REQUIRED_VERSION on macOS using Homebrew..."
        if ! command -v brew &> /dev/null; then
            echo "Homebrew not found. Installing Homebrew first..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew update
        brew install python@3.11
        echo "Please ensure your PATH is updated with the Python Homebrew location if needed."
    else
        echo "Unsupported OS. Please install Python $REQUIRED_VERSION manually."
        exit 1
    fi
}

if ! command -v python3 &> /dev/null; then
    echo "Python is not installed."
    read -p "Do you want to install Python $REQUIRED_VERSION? (y/n): " install_py
    if [[ "$install_py" == "y" || "$install_py" == "Y" ]]; then
        install_python
    else
        echo "Python is required. Exiting."
        exit 1
    fi
else
    if [[ $(echo -e "$PYTHON_VERSION\n$REQUIRED_VERSION" | sort -V | head -n1) != "$REQUIRED_VERSION" ]]; then
        echo "Python version must be $REQUIRED_VERSION or higher. Found: $PYTHON_VERSION."
        read -p "Do you want to install Python $REQUIRED_VERSION? (y/n): " install_py
        if [[ "$install_py" == "y" || "$install_py" == "Y" ]]; then
            install_python
        else
            echo "Python version mismatch. Exiting."
            exit 1
        fi
    else
        echo "Python version is sufficient: $PYTHON_VERSION."
    fi
fi


# Create virtual environment if not found
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."

    # Check for ensurepip and install python3-venv if needed
    if ! python3 -m venv .venv &> /dev/null; then
        echo "Virtual environment creation failed. Missing python3-venv or ensurepip."
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if ! dpkg -l | grep python3-venv &> /dev/null; then
                echo "python3-venv is not installed. Installing now..."
                sudo apt install -y python3-venv
            fi
        fi
        echo "Retrying virtual environment creation..."
        if ! python3 -m venv .venv; then
            echo "Failed to create virtual environment after retry. Exiting."
            exit 1
        fi
    else
        echo "Virtual environment created successfully."
    fi
else
    echo "Virtual environment already exists."
fi

# Check if virtual environment was created by verifying the existence of the activation script
if [ ! -f ".venv/bin/activate" ]; then
    echo "Error: Virtual environment activation script not found. Exiting."
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment activated successfully."
else
    echo "Error: Failed to activate virtual environment. Exiting."
    exit 1
fi

# Step 4: Check if Tkinter is available
if python3 -c "import tkinter" &> /dev/null; then
    echo "Tkinter is available."
else
    echo "Tkinter is not available."
    read -p "Do you want to install Tkinter? (y/n): " answer
    if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo "Installing Tkinter..."
            sudo apt update
            sudo apt install python3-tk
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            echo "On macOS, Tkinter should be included with Python installed via Homebrew."
            echo "Please ensure Python is installed via Homebrew or download from python.org."
        else
            echo "Unsupported OS. Please install Tkinter manually."
            exit 1
        fi
    else
        echo "Skipping Tkinter installation."
        exit 1
    fi
fi

# Step 5: Check if requirements.txt exists and install the dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Skipping installation."
fi

# Step 6: Run the Tkinter application
echo "Running start_app.py..."
python start_app.py
