#!/bin/bash

# setup.sh - Initializes virtual environment and installs dependencies

# Exit on any error
set -e

# Define environment directory name
ENV_DIR="venv"

echo "🔧 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install it and re-run this script."
    exit 1
fi

echo "📁 Checking if virtual environment exists..."
if [ ! -d "$ENV_DIR" ]; then
    echo "📦 Creating virtual environment in ./$ENV_DIR"
    python3 -m venv "$ENV_DIR"
else
    echo "✅ Virtual environment already exists."
fi

echo "⚙️ Activating virtual environment..."
source "$ENV_DIR/bin/activate"

echo "📋 Installing required packages..."
pip install --upgrade pip
pip install flask pandas matplotlib

echo "✅ Setup complete."
echo "💡 To start the app, run:"
echo "source $ENV_DIR/bin/activate && python app.py"
