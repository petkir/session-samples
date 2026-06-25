# Qdrant Vector Database Initialization

This folder contains a C# console application and utilities for initializing and managing the Qdrant vector database for the elat Local LLM project.

## What is Qdrant?

Qdrant is a vector database designed for high-performance similarity search and retrieval. In this project, it's used to:

- Store document embeddings for semantic search
- Enable RAG (Retrieval-Augmented Generation) capabilities
- Provide context-aware responses based on your knowledge base

## Console Application

The `elat.local.llm.qdrant.init` console application automatically:

1. **Initializes Qdrant Collection**: Creates the knowledge base collection with proper vector configuration
2. **Processes Sample Documents**: Loads and embeds sample documents from `sample-documents.json`
3. **Processes PDF Files**: Extracts text from PDF files in the `sample_files` folder and creates embeddings
4. **Uploads to Vector Database**: Stores all documents with their embeddings in Qdrant

### Features

- **Interactive Setup**: Prompts user before uploading documents
- **Health Checks**: Verifies Qdrant server connectivity
- **PDF Processing**: Automatically extracts text from PDF files using iText7
- **Bulk Upload**: Handles both JSON sample documents and file-based documents
- **Error Handling**: Comprehensive logging and error recovery
- **Docker Integration**: Can automatically start Qdrant container if needed

## Quick Start

### 1. Automatic Setup (Recommended)

The setup scripts (`setup.sh`, `setup-macos.sh`, `setup-linux.sh`, `setup-windows.bat`) will automatically:
- Check if you want to upload sample documents
- Start Qdrant container if needed
- Run the initialization application
- Upload all sample documents and PDFs

### 2. Manual Setup

#### Start Qdrant Server

```bash
# Using Docker (recommended)
docker run -d --name qdrant-elat -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

#### Run the Initialization Application

```bash
# Navigate to the init project
cd elat.local.llm.qdrant.init

# Restore dependencies
dotnet restore

# Run the application
dotnet run
```

### 3. Initialize with Sample Data

The application will automatically:
- Create the knowledge base collection
- Set up the vector dimensions (384 for all-MiniLM-L6-v2)
- Configure distance metrics (Cosine similarity)
- Upload sample documents from `sample-documents.json`
- Process and upload PDF files from `../elat.local.llm/sample_files/`

## Sample Documents

### JSON Sample Documents (`sample-documents.json`)
Contains pre-defined Microsoft 365 related content including:
- Microsoft 365 overview
- SharePoint basics
- Microsoft Teams overview
- Power Platform introduction
- Azure AD basics
- OneDrive overview
- Microsoft Viva platform
- Microsoft Graph API

### PDF Documents (`sample_files/`)
The application automatically processes PDF files from the `sample_files` folder:
- Extracts text content using iText7 library
- Creates embeddings for semantic search
- Stores with appropriate metadata

## Configuration

### `appsettings.json`
```json
{
  "Ollama": {
    "Endpoint": "http://localhost:11434"
  },
  "Qdrant": {
    "Endpoint": "http://localhost:6333"
  }
}
```

### Environment Variables
- `OLLAMA_ENDPOINT`: Override Ollama server URL
- `QDRANT_ENDPOINT`: Override Qdrant server URL

## API Endpoints

Once the server is running, you can interact with the knowledge base via these endpoints:

### Add Document
```http
POST /api/knowledgebase/documents
Content-Type: application/json
Authorization: Bearer <your-token>

{
    "content": "Your document content here",
    "fileName": "optional-filename.txt",
    "category": "optional-category"
}
```

### Search Documents
```http
POST /api/knowledgebase/search
Content-Type: application/json
Authorization: Bearer <your-token>

{
    "query": "search query",
    "maxResults": 5
}
```

### Upload File
```http
POST /api/knowledgebase/upload
Content-Type: multipart/form-data
Authorization: Bearer <your-token>

file: <your-file>
category: optional-category
```

### Delete Document
```http
DELETE /api/knowledgebase/documents/{documentId}
Authorization: Bearer <your-token>
```

## Configuration

The Qdrant configuration is stored in `appsettings.json`:

```json
{
  "Qdrant": {
    "Endpoint": "http://localhost:6333",
    "CollectionName": "knowledge_base"
  }
}
```

## Sample Data Scripts

You can use the sample scripts in this folder to populate your knowledge base with test data:

1. `sample-documents.json` - Sample documents for testing
2. `init-script.ps1` - PowerShell script for Windows initialization
3. `init-script.sh` - Bash script for Mac/Linux initialization

## Embedding Model

The project uses Ollama with the `all-minilm:latest` model for generating embeddings. Make sure you have this model pulled:

```bash
ollama pull all-minilm:latest
```

If you don't have this model, the system will fall back to a default embedding model or you can change the configuration in `Program.cs`.

## Troubleshooting

### Qdrant Connection Issues

1. **Check if Qdrant is running:**
   ```bash
   curl http://localhost:6333/collections
   ```

2. **Check Docker container:**
   ```bash
   docker ps | grep qdrant
   ```

3. **View Qdrant logs:**
   ```bash
   docker logs <qdrant-container-id>
   ```

### Embedding Issues

1. **Check if Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Pull the embedding model:**
   ```bash
   ollama pull all-minilm:latest
   ```

### Application Logs

Check the application logs for detailed error messages about Qdrant initialization and operations.

## Performance Tips

1. **Vector Dimensions**: The default 384 dimensions work well for most use cases. Larger dimensions provide better accuracy but require more memory and computation.

2. **Collection Size**: Qdrant can handle millions of vectors efficiently. Consider partitioning very large datasets.

3. **Search Parameters**: Adjust the `minRelevanceScore` in search operations to balance precision and recall.

4. **Batch Operations**: For large data imports, consider implementing batch upload functionality.

## Advanced Usage

### Custom Embedding Models

You can configure different embedding models by modifying the memory builder in `Program.cs`:

```csharp
.WithOllamaTextEmbeddingGeneration("your-model:latest", new Uri(ollamaEndpoint))
```

### Custom Vector Dimensions

If using a different embedding model, update the vector dimensions in:
1. `QdrantOptions.cs` - Default vector size
2. `Program.cs` - Memory store configuration

### Production Deployment

For production deployments:
1. Use persistent storage for Qdrant data
2. Configure proper authentication and authorization
3. Set up monitoring and logging
4. Consider clustering for high availability

## Links

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Semantic Kernel Documentation](https://learn.microsoft.com/semantic-kernel/)
- [Ollama Models](https://ollama.ai/library)
