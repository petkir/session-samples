#!/bin/bash

# Enhanced PDF Upload with Image Extraction - Deployment Script
# This script sets up the environment and deploys the enhanced PDF processing system

set -e

echo "🚀 Enhanced PDF Upload with Image Extraction - Deployment Script"
echo "=============================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $python_version is installed, but Python $required_version or higher is required."
    echo "   Some packages in requirements.txt require Python 3.10+."
    echo "   Please upgrade your Python version or use a Python version manager like pyenv."
    exit 1
fi

echo "✅ Python $python_version is installed"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing Python packages..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << 'EOF'
# Azure AI Search Configuration
AZURE_SEARCH_SERVICE_NAME=your-search-service-name
AZURE_SEARCH_ADMIN_KEY=your-search-admin-key
AZURE_SEARCH_API_VERSION=2023-11-01

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_VISION_MODEL=gpt-4-vision-preview
AZURE_OPENAI_VISION_DEPLOYMENT=gpt-4-vision-preview

# PDF Processing Configuration
PDF_DIRECTORY_PATH=./pdfs
EXTRACTED_IMAGES_PATH=./extracted_images
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CONCURRENT_PDFS=5
MAX_CONCURRENT_CHUNKS=10
MAX_CONCURRENT_IMAGES=3

# Image Processing Configuration
EXTRACT_IMAGES=true
IMAGE_MIN_SIZE=100
IMAGE_MAX_SIZE=2048
IMAGE_QUALITY=85
SUPPORTED_IMAGE_FORMATS=JPEG,PNG,TIFF

# Vision Analysis Configuration
VISION_MAX_TOKENS=1000
VISION_TEMPERATURE=0.1
VISION_DETAIL_LEVEL=high

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Search Index Configuration
SEARCH_INDEX_NAME=pdf-documents-with-images
VECTOR_DIMENSIONS=1536
EOF
    
    echo "📝 Please edit the .env file with your Azure credentials and configuration."
    echo "   Required fields:"
    echo "   - AZURE_SEARCH_SERVICE_NAME"
    echo "   - AZURE_SEARCH_ADMIN_KEY"
    echo "   - AZURE_OPENAI_ENDPOINT"
    echo "   - AZURE_OPENAI_KEY"
    echo ""
    echo "   Make sure you have deployed both:"
    echo "   - An embedding model (text-embedding-ada-002)"
    echo "   - A vision model (gpt-4-vision-preview)"
    echo ""
    exit 1
fi

# Create directories if they don't exist
echo "📁 Creating directories..."
mkdir -p pdfs
mkdir -p extracted_images

# Check if PDFs directory has files
pdf_count=$(find pdfs -name "*.pdf" -type f | wc -l)
if [ $pdf_count -eq 0 ]; then
    echo "⚠️  No PDF files found in ./pdfs directory."
    echo "   Please add PDF files to the ./pdfs directory before running the application."
else
    echo "✅ Found $pdf_count PDF file(s) in ./pdfs directory"
fi

# Test configuration
echo "🧪 Testing configuration..."
python3 -c "
import sys
sys.path.append('.')
try:
    from config import settings
    print('✅ Configuration loaded successfully')
    print(f'   - Search Service: {settings.azure_search_service_name}')
    print(f'   - OpenAI Endpoint: {settings.azure_openai_endpoint}')
    print(f'   - PDF Directory: {settings.pdf_directory_path}')
    print(f'   - Images Directory: {settings.extracted_images_path}')
    print(f'   - Extract Images: {settings.extract_images}')
    print(f'   - Search Index: {settings.search_index_name}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Configuration test failed. Please check your .env file."
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Add PDF files to the ./pdfs directory"
echo "2. Run the application: python3 main.py"
echo "3. Or run examples: python3 example_usage.py"
echo ""
echo "📊 To monitor the application:"
echo "- Check logs for processing status"
echo "- Use Azure AI Search Studio to explore the index"
echo "- Use example_usage.py to test search functionality"
echo ""
echo "🔧 Configuration file: .env"
echo "📁 PDF files: ./pdfs/"
echo "🖼️  Extracted images: ./extracted_images/"
echo ""

# Deactivate virtual environment
deactivate
