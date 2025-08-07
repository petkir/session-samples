#!/bin/bash

# Deployment script for PDF Upload to Azure AI Search
# This script helps set up and deploy the application

set -e

echo "🚀 PDF Upload to Azure AI Search - Deployment Script"
echo "===================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $python_version is installed, but Python $required_version or higher is required."
    exit 1
fi

echo "✅ Python $python_version is installed"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing requirements..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file from template..."
    cp .env.example .env
    echo "🔧 Please edit .env file with your Azure credentials before running the application"
else
    echo "✅ .env file already exists"
fi

# Create pdfs directory if it doesn't exist
if [ ! -d "pdfs" ]; then
    echo "📁 Creating pdfs directory..."
    mkdir -p pdfs
    echo "📄 Please place your PDF files in the 'pdfs' directory"
else
    echo "✅ pdfs directory already exists"
fi

# Run tests
echo "🧪 Running tests..."
python test_implementation.py

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your Azure credentials"
    echo "2. Place PDF files in the 'pdfs' directory"
    echo "3. Run the application:"
    echo "   source venv/bin/activate"
    echo "   python main.py"
    echo ""
    echo "Optional commands:"
    echo "   python main.py --help                    # Show help"
    echo "   python main.py --stats                   # Show index statistics"
    echo "   python main.py --search 'query'          # Test search"
    echo "   python main.py --delete-index            # Delete index"
    echo "   python example_usage.py                  # Run examples"
else
    echo "❌ Tests failed. Please check the implementation."
    exit 1
fi
