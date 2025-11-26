#!/bin/bash
set -euo pipefail

# Check if Python is installed
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version)
echo "Python version: $PYTHON_VERSION"
echo

# Set virtual environment name
VENV_NAME="venv"

# Check if virtual environment exists
if [[ -d "$VENV_NAME" ]]; then
    echo "Virtual environment found. Activating..."
    source "$VENV_NAME/bin/activate"
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to activate virtual environment"
        echo "Removing corrupted virtual environment..."
        rm -rf "$VENV_NAME"
    else
        echo "Virtual environment activated successfully!"
    fi
fi

# Create virtual environment if it doesn't exist
if [[ ! -d "$VENV_NAME" ]]; then
    echo "Virtual environment not found. Creating new one..."
    python3 -m venv "$VENV_NAME"
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to create virtual environment"
        echo "Please check your Python installation."
        exit 1
    fi
    
    echo "Activating virtual environment..."
    source "$VENV_NAME/bin/activate"
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to activate virtual environment"
        exit 1
    fi
    echo "Virtual environment created and activated successfully!"
fi

echo

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip
if [[ $? -ne 0 ]]; then
    echo "Warning: Failed to upgrade pip, continuing anyway..."
fi

# Install/Update requirements
echo "Installing/Updating requirements..."
if [[ -f "requirements.txt" ]]; then
    pip install -r requirements.txt
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to install requirements"
        echo "Please check your requirements.txt file and internet connection."
        exit 1
    fi
    echo "Requirements installed successfully!"
else
    echo "Error: requirements.txt not found"
    echo "Please ensure requirements.txt exists in the project root."
    exit 1
fi

echo