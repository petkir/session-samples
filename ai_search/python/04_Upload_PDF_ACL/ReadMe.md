# PDF Upload to Azure AI Search Sample with ACL Support

This sample demonstrates how to read PDF files from a directory, extract text content, create embeddings, and upload the processed data to Microsoft Azure AI Search with proper chunking, headlines, and **Access Control Lists (ACL)** for document-level permissions.

## Overview

This Python application processes PDF documents by:

1. Reading PDF files from a specified directory
2. Extracting text content from each PDF
3. Creating intelligent chunks with headlines
4. Generating embeddings for the text content
5. Uploading the processed data to Azure AI Search for indexing
6. **NEW: Applying Access Control Lists (ACL) to restrict document access to specific Entra groups**

## Prerequisites

- Python 3.8 or higher
- Azure subscription with Azure AI Search service
- Azure OpenAI or Azure AI Services for embeddings
- **Microsoft Entra ID group with appropriate permissions for document access**
- Required Python packages (see requirements.txt)

## Required Azure Services

1. **Azure AI Search**: For storing and indexing the processed documents
2. **Azure OpenAI Service**: For generating embeddings (text-embedding-ada-002 or similar)
3. **Microsoft Entra ID**: For managing group-based access control
4. **Azure Storage Account** (optional): For storing original PDF files

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
AZURE_SEARCH_API_VERSION=2025-05-01-preview

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002

# PDF Processing Configuration
PDF_DIRECTORY_PATH=./pdfs
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Access Control Configuration (NEW)
# Set this to the Object ID of your Entra Group
ENTRA_GROUP_ID=12345678-1234-1234-1234-123456789012
# Set to true to enable permission-based filtering
ENABLE_PERMISSION_FILTER=true
```

## NEW: Access Control Lists (ACL) Feature

This implementation now supports document-level access control using Microsoft Entra ID groups. This feature allows you to:

- **Restrict document access** to specific Entra groups
- **Secure sensitive documents** at the document level
- **Integrate with existing organizational security** structures
- **Enforce permissions** at query time

### How ACL Works

1. **Index Creation**: The search index is created with `permission_filter` enabled
2. **Document Upload**: Each document is tagged with the specified Entra Group ID
3. **Query Security**: Only users in the specified group can access documents during search
4. **Automatic Filtering**: The search engine automatically filters results based on user permissions

### ACL Configuration

1. **Get your Entra Group ID**:
   - Go to Azure Portal → Microsoft Entra ID → Groups
   - Find your group and copy the Object ID
   - Set `ENTRA_GROUP_ID` in your `.env` file

2. **Enable Permission Filtering**:
   - Set `ENABLE_PERMISSION_FILTER=true` in your `.env` file
   - Ensure you're using API version `2025-05-01-preview`

3. **Security Best Practices**:
   - Use the principle of least privilege
   - Regularly review group memberships
   - Monitor access patterns
   - Consider using multiple groups for different document types

### ACL Example Usage

```python
# Run the ACL example
python acl_example.py
```

This will demonstrate:

- How to configure ACL settings
- Upload documents with group restrictions
- Understand security implications

## PDF Processing Configuration

```env

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
- **`groupIds`: NEW - Entra Group IDs that have access to this document (ACL field)**

## ACL Security Features

### Document-Level Security

- **Group-based access**: Documents are tagged with specific Entra Group IDs
- **Automatic filtering**: Search results are filtered based on user's group membership
- **Permission enforcement**: Only authorized users can access documents
- **Preview API**: Uses Azure AI Search 2025-05-01-preview API for ACL support

### Query-Time Security

When querying with ACL enabled, users must:

1. **Authenticate with Entra ID**: Provide valid authentication token
2. **Group membership validation**: System validates user's group membership
3. **Automatic filtering**: Search engine filters results based on permissions
4. **Secure responses**: Only authorized documents are returned

Example query with ACL (for application integration):

```http
POST https://your-search-service.search.windows.net/indexes/pdf-documents-acl/docs/search?api-version=2025-05-01-preview
Content-Type: application/json
x-ms-query-source-authorization: Bearer <user-token>

{
  "search": "your query here",
  "top": 10
}
```

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

### General Security

- Store sensitive credentials in Azure Key Vault
- Use managed identities for Azure service authentication
- Implement proper access controls for PDF files
- Monitor and audit search operations

### ACL Security (NEW)

- **Group Management**: Regularly review and update Entra group memberships
- **Principle of Least Privilege**: Only grant access to users who need it
- **Audit Trail**: Monitor document access patterns and group changes
- **Token Security**: Ensure proper handling of authentication tokens
- **API Version**: Use the preview API version `2025-05-01-preview` for ACL features
- **Test Permissions**: Verify that ACL restrictions work as expected before production

### ACL Limitations

- Maximum 32 group IDs per document
- Maximum 5 unique `rbacScope` values across all documents
- Preview feature - not recommended for production workloads
- Existing fields cannot be converted to permission filter fields

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