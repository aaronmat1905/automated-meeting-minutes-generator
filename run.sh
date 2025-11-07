#!/bin/bash
# Quick start script for Mac/Linux

echo "============================================================"
echo "AI Meeting Minutes Generator - Starting..."
echo "============================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found! Creating one..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found!"
    echo "Please copy .env.simple to .env and add your GEMINI_API_KEY"
    echo ""
    read -p "Press enter to exit..."
    exit 1
fi

# Check if requirements are installed
echo "Checking dependencies..."
if ! python -c "import flask" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Run the application
echo "Starting application..."
echo ""
python start.py
