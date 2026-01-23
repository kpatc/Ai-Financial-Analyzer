#!/bin/bash
# Financial Chatbot Startup Script
# Sets up environment, installs dependencies, and starts the server

set -e

echo "=================================================="
echo "Financial Chatbot - Startup Script"
echo "=================================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if financial data exists
if [ ! -f "../data/financial_data_raw.csv" ]; then
    echo "WARNING: Financial data file not found at ../data/financial_data_raw.csv"
    echo "Please ensure the financial_data_raw.csv file is in the data directory."
fi

# Create necessary directories
mkdir -p chroma_db
mkdir -p logs

echo "=================================================="
echo "Setup complete! Starting Financial Chatbot API..."
echo "=================================================="
echo ""
echo "Frontend: http://localhost:5000/frontend/index.html"
echo "API: http://localhost:5000/api"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask server
python3 api.py
