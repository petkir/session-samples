# PDF Upload with Image Extraction to Azure AI Search Sample

This sample demonstrates how to read PDF files from a directory, extract text content AND images, use Azure OpenAI GPT-4 Vision to describe images, and upload the processed data to Microsoft Azure AI Search with proper chunking and headlines.

## Overview

This Python application processes PDF documents by:

1. Reading PDF files from a specified directory
2. Extracting text content from each PDF
3. **Extracting images from PDFs and saving them locally**
4. **Using Azure OpenAI GPT-4 Vision to describe images and extract text from images**
5. Creating intelligent chunks with headlines (including image descriptions as "chunks")
6. Generating embeddings for the text content and image descriptions
7. Uploading the processed data to Azure AI Search for indexing

## Prerequisites

- Python 3.8 or higher
- Azure subscription with Azure AI Search service
- Azure OpenAI or Azure AI Services for embeddings
- **Azure OpenAI GPT-4 Vision model deployment for image analysis**
- Required Python packages (see requirements.txt)

## Required Azure Services

1. **Azure AI Search**: For storing and indexing the processed documents
2. **Azure OpenAI Service**: For generating embeddings (text-embedding-ada-002 or similar)
3. **Azure OpenAI GPT-4 Vision**: For analyzing and describing images extracted from PDFs
4. **Azure Storage Account** (optional): For storing original PDF files and extracted images

## Installation

1. Clone this repository
2. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# Azure AI Search Configuration
AZURE_SEARCH_SERVICE_NAME=your-search-service-name
AZURE_SEARCH_ADMIN_KEY=your-search-admin-key
AZURE_SEARCH_API_VERSION=2023-11-01

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_VISION_MODEL=gpt-4-vision-preview

# PDF Processing Configuration
PDF_DIRECTORY_PATH=./pdfs
EXTRACTED_IMAGES_PATH=./extracted_images
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## Project Structure

```text
02_Upload_PDF_Images/
├── main.py                 # Main application entry point
├── pdf_processor.py        # PDF text extraction and chunking
├── image_extractor.py      # NEW: Image extraction from PDFs
├── image_analyzer.py       # NEW: Image analysis using GPT-4 Vision
├── embedding_generator.py  # Text embedding generation
├── search_uploader.py      # Azure AI Search upload functionality
├── requirements.txt        # Python dependencies
├── .env                   # Environment configuration
├── pdfs/                  # Directory containing PDF files
├── extracted_images/      # Directory for extracted images
└── ReadMe.md             # This file
```

## Key Features

### 1. PDF Text Extraction

- Reads PDF files from a specified directory
- Extracts text content while preserving structure
- Handles various PDF formats and encodings

### 2. **Image Extraction (NEW)**

- Extracts images from PDF files
- Saves images in various formats (JPEG, PNG, etc.)
- Maintains image metadata and page references

### 3. **Image Analysis with GPT-4 Vision (NEW)**

- Uses Azure OpenAI GPT-4 Vision to analyze extracted images
- Generates detailed descriptions of image content
- Extracts text from images (OCR capabilities)
- Creates searchable "chunks" from image descriptions

### 4. Intelligent Chunking

- Creates meaningful text chunks with appropriate size limits
- Generates descriptive headlines for each chunk
- **Includes image descriptions as special chunks**
- Maintains context across chunk boundaries

### 5. Embedding Generation

- Uses Azure OpenAI to generate high-quality embeddings
- Optimizes for semantic search capabilities
- **Generates embeddings for both text and image descriptions**
- Handles batch processing for efficiency

### 6. Azure AI Search Integration

- Creates or updates search index with proper schema
- Uploads documents with metadata and embeddings
- **Includes image metadata and descriptions in search index**
- Enables hybrid search (keyword + semantic)

## Usage

1. **Prepare PDF Files**: Place your PDF files in the `pdfs/` directory
2. **Configure Environment**: Set up your `.env` file with Azure credentials
3. **Run the Application**:

   ```bash
   python main.py
   ```

## Image Processing Features

The enhanced version includes:

- **Automatic image extraction** from PDF files
- **GPT-4 Vision analysis** for comprehensive image understanding
- **Text extraction from images** using OCR capabilities
- **Searchable image descriptions** integrated into the search index
- **Image metadata preservation** for reference tracking

## Search Capabilities

Users can now search for:

- Traditional text content from PDFs
- Image descriptions and content
- Text extracted from images
- Combined text and visual content

This makes the search experience much richer and more comprehensive for documents containing both text and visual elements.


```
source venv/bin/activate && python test_azure_openai.py
```

```
source venv/bin/activate && python main.py 
```