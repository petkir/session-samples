# PDF Upload to Azure AI Search Sample

This sample demonstrates how to read PDF files from a directory, extract text content, create embeddings, and upload the processed data to Microsoft Azure AI Search with proper chunking and headlines.

## Overview

This Python application processes PDF documents by:

1. Reading PDF files from a specified directory
2. Extracting text content from each PDF
3. Creating intelligent chunks with headlines
4. Generating embeddings for the text content
5. Uploading the processed data to Azure AI Search for indexing

## Prerequisites

- Python 3.8 or higher
- Azure subscription with Azure AI Search service
- Azure OpenAI or Azure AI Services for embeddings
- Required Python packages (see requirements.txt)

## Required Azure Services

1. **Azure AI Search**: For storing and indexing the processed documents
2. **Azure OpenAI Service**: For generating embeddings (text-embedding-ada-002 or similar)
3. **Azure Storage Account** (optional): For storing original PDF files

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

# PDF Processing Configuration
PDF_DIRECTORY_PATH=./pdfs
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## Project Structure

```text
01_Upload_PDF/
├── main.py                 # Main application entry point
├── pdf_processor.py        # PDF text extraction and chunking
├── embedding_generator.py  # Text embedding generation
├── search_uploader.py      # Azure AI Search upload functionality
├── requirements.txt        # Python dependencies
├── .env                   # Environment configuration
├── pdfs/                  # Directory containing PDF files
└── ReadMe.md             # This file
```

## Key Features

### 1. PDF Text Extraction

- Reads PDF files from a specified directory
- Extracts text content while preserving structure
- Handles various PDF formats and encodings

### 2. Intelligent Chunking

- Creates meaningful text chunks with appropriate size limits
- Generates descriptive headlines for each chunk
- Maintains context across chunk boundaries

### 3. Embedding Generation

- Uses Azure OpenAI to generate high-quality embeddings
- Optimizes for semantic search capabilities
- Handles batch processing for efficiency

### 4. Azure AI Search Integration

- Creates or updates search index with proper schema
- Uploads documents with metadata and embeddings
- Enables hybrid search (keyword + semantic)

## Usage

1. **Prepare PDF Files**: Place your PDF files in the `pdfs/` directory

2. **Run the Application**:

   ```bash
   python main.py
   ```

3. **Monitor Progress**: The application will display processing status for each PDF

4. **Verify Upload**: Check your Azure AI Search service for the uploaded documents

## Search Index Schema

The application creates an index with the following fields:

- `id`: Unique identifier for each chunk
- `title`: Document title (extracted from PDF)
- `content`: Text content of the chunk
- `headline`: Generated headline for the chunk
- `embedding`: Vector embedding for semantic search
- `file_name`: Original PDF filename
- `page_number`: Source page number
- `chunk_index`: Position of chunk within document
- `created_at`: Timestamp of processing

## Error Handling

The application includes comprehensive error handling for:

- Invalid PDF files or corrupted documents
- Azure service connection issues
- Embedding generation failures
- Search index creation/update errors

## Performance Considerations

- **Batch Processing**: Processes multiple PDFs in parallel
- **Chunking Strategy**: Optimizes chunk size for embedding model limits
- **Rate Limiting**: Respects Azure service rate limits
- **Memory Management**: Handles large PDF files efficiently

## Troubleshooting

### Common Issues

1. **PDF Reading Errors**:
   - Ensure PDFs are not password-protected
   - Check file permissions and encoding

2. **Azure Connection Issues**:
   - Verify service endpoints and credentials
   - Check network connectivity and firewall settings

3. **Embedding Generation Failures**:
   - Monitor Azure OpenAI quota and rate limits
   - Validate text content length and format

### Debugging Tips

- Enable verbose logging by setting `LOG_LEVEL=DEBUG`
- Check Azure portal for service health and usage
- Validate environment variables and configuration

## Security Best Practices

- Store sensitive credentials in Azure Key Vault
- Use managed identities for Azure service authentication
- Implement proper access controls for PDF files
- Monitor and audit search operations

## Next Steps

After running this sample, you can:

1. Test search functionality using Azure AI Search REST API
2. Build a web interface for document search
3. Implement advanced features like faceted search
4. Add support for additional document formats

## Contributing

Please follow the repository's contributing guidelines when submitting improvements or bug fixes.

## License

This sample is provided under the MIT License. See LICENSE file for details.

## Support

For issues related to this sample, please create an issue in the repository. For Azure service support, contact Azure Support.

```
source venv/bin/activate && python test_azure_openai.py
```

```
source venv/bin/activate && python main.py 
```