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
- **Entra ID Application Registration** for group-based access control
- **Entra ID Groups** for document permissions
- Required Python packages (see requirements.txt)

## Required Azure Services

1. **Azure AI Search**: For storing and indexing the processed documents
2. **Azure OpenAI Service**: For generating embeddings (text-embedding-ada-002 or similar)
3. **Azure Storage Account** (optional): For storing original PDF files
4. **Entra ID Application Registration**: For authenticating and authorizing users
5. **Entra ID Groups**: For managing document access permissions

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

# Entra ID Configuration for Group-Based Permissions
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-app-registration-client-id
AZURE_CLIENT_SECRET=your-app-registration-client-secret
AZURE_AUTHORITY=https://login.microsoftonline.com/your-tenant-id

# Document Permission Configuration
DOCUMENT_ACCESS_GROUPS=group-id-1,group-id-2,group-id-3
DEFAULT_DOCUMENT_GROUP=default-group-id

# PDF Processing Configuration
PDF_DIRECTORY_PATH=./pdfs
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

# PDF Processing Configuration
PDF_DIRECTORY_PATH=./pdfs
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

## Project Structure

```text
03_Upload_PDF_Permissions/
├── main.py                          # Main application entry point
├── pdf_processor.py                 # PDF text extraction and chunking
├── embedding_generator.py           # Text embedding generation
├── search_uploader.py               # Azure AI Search upload functionality
├── secure_search.py                 # Secure search with group permissions
├── entraid_auth.py                  # Entra ID authentication and authorization
├── example_usage_permissions.py     # Example with permission system
├── config.py                        # Application configuration
├── requirements.txt                 # Python dependencies
├── .env                            # Environment configuration
├── pdfs/                           # Directory containing PDF files
└── ReadMe.md                       # This file
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

### 5. Entra ID Group-Based Permissions

- **Document Access Control**: Restricts document access to specific Entra ID groups
- **User Authentication**: Validates user identity using Entra ID
- **Group Membership Validation**: Checks if users belong to authorized groups
- **Permission Filtering**: Filters search results based on user's group membership
- **Secure Document Upload**: Associates documents with specific groups during upload

#### Permission System Architecture

The permission system works by:

1. **Group Association**: Each document is associated with one or more Entra ID groups during upload
2. **User Authentication**: Users authenticate using Entra ID credentials
3. **Group Validation**: The system validates the user's group membership
4. **Search Filtering**: Search results are filtered to only show documents the user has access to
5. **Security Headers**: Search queries include security filters based on user's groups

#### Setting Up Permissions

1. **Create Entra ID Groups**: Create groups in Entra ID for different document categories
2. **Configure Application**: Register an application in Entra ID with appropriate permissions
3. **Set Environment Variables**: Configure group IDs and authentication details
4. **Upload Documents**: Associate documents with groups during the upload process
5. **Implement Search Filtering**: Filter search results based on user's group membership

## Usage

### Basic Usage (without permissions)

1. **Prepare PDF Files**: Place your PDF files in the `pdfs/` directory

2. **Run the Application**:

   ```bash
   python main.py
   ```

3. **Monitor Progress**: The application will display processing status for each PDF

4. **Verify Upload**: Check your Azure AI Search service for the uploaded documents

### Using Group-Based Permissions

1. **Configure Entra ID**:
   - Set up your Entra ID application registration
   - Create groups for document access
   - Update your `.env` file with the configuration

2. **Run with Permissions**:

   ```bash
   python example_usage_permissions.py
   ```

3. **Test Secure Search**:
   - Use the `SecureSearchClient` class to perform searches
   - Search results will be automatically filtered based on user's group membership

### Example Permission Configuration

```python
# Define specific groups for different documents
document_groups = {
    "financial-report.pdf": ["finance-team", "executives"],
    "hr-policies.pdf": ["hr-team", "executives"],
    "marketing-strategy.pdf": ["marketing-team"]
}

# Process and upload with permissions
result = await processor.process_and_upload_with_permissions(
    pdf_directory="./pdfs",
    document_groups=document_groups
)
```

### Secure Search Example

```python
from secure_search import SecureSearchClient

client = SecureSearchClient()

# Search with automatic permission filtering
results = await client.search_with_permissions(
    query="financial report",
    user_id="user@example.com",
    search_type="hybrid",
    top=10
)

# Results will only include documents the user has access to
for result in results['results']:
    print(f"Title: {result['title']}")
    print(f"File: {result['file_name']}")
```

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
- `token_count`: Number of tokens in the chunk
- **Permission fields for group-based access control:**
  - `document_groups`: Collection of Entra ID group IDs that can access the document
  - `default_group`: Default group ID for the document
  - `permission_level`: Permission level (e.g., "read", "write")

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



## How the Permission System Works
Document Upload: Documents are associated with specific Entra ID groups during upload
User Authentication: Users authenticate using their Entra ID credentials
Group Validation: System validates user's group membership via Microsoft Graph API
Search Filtering: Search queries are automatically filtered using OData filters
Access Control: Only documents from groups the user belongs to are returned


```
source venv/bin/activate && python test_azure_openai.py
```

```
source venv/bin/activate && python main.py 
```


https://learn.microsoft.com/en-us/azure/search/search-document-level-access-overview

https://learn.microsoft.com/en-us/azure/search/search-security-trimming-for-azure-search


https://learn.microsoft.com/en-us/azure/search/search-index-access-control-lists-and-rbac-push-api