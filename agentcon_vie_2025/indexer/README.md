# VoiceRAG Indexer (.NET 10)

Console application to process PDF documents from the `/data` folder, chunk them, generate embeddings using Azure OpenAI, and upload to Azure AI Search.

## Features

- **PDF Processing**: Extracts text from all PDF files in the data folder using iText7
- **Smart Chunking**: Splits documents into chunks with configurable size and overlap
- **Vector Embeddings**: Generates embeddings using Azure OpenAI (text-embedding-3-large)
- **Azure AI Search Integration**: Creates/updates the search index with vector search support
- **Batch Upload**: Efficiently uploads documents in batches

## Prerequisites

- .NET 10.0 SDK or later
- Azure OpenAI resource with text-embedding deployment
- Azure AI Search resource
- PDF files in the `../data` folder

## Setup

### 1. Install Dependencies

```bash
cd indexer
dotnet restore
```

### 2. Configure Environment

Copy `.env.template` to `.env` and fill in your Azure credentials:

```bash
cp .env.template .env
```

Edit `.env`:

```env
AZURE_OPENAI_ENDPOINT=https://<your-instance-name>.openai.azure.com
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-large
AZURE_OPENAI_EMBEDDING_DIMENSIONS=3072

AZURE_SEARCH_ENDPOINT=https://<your-service-name>.search.windows.net
AZURE_SEARCH_INDEX=<your-index-name>
AZURE_SEARCH_API_KEY=<your-api-key>
```

### 3. Add PDF Files

Place your PDF documents in the `../data` folder:

```
agentcon_vie_2025/
├── data/
│   ├── document1.pdf
│   ├── document2.pdf
│   └── ...
└── indexer/
```

### 4. Run the Indexer

```bash
dotnet run
```

## Index Schema

The indexer creates an Azure AI Search index with the following fields:

- **chunk_id** (key): Unique identifier for each chunk (e.g., "document1_chunk_1")
- **parent_id**: Original document identifier
- **title**: Document title (filename without extension)
- **chunk**: The text content of the chunk
- **text_vector**: Vector embedding (3072 dimensions for text-embedding-3-large)
- **chunk_index**: Sequential number of the chunk within the document
- **source_file**: Original PDF filename

### Vector Search Configuration

- **Algorithm**: HNSW (Hierarchical Navigable Small World)
- **Metric**: Cosine similarity
- **HNSW Parameters**:
  - M = 4
  - efConstruction = 400
  - efSearch = 500

### Semantic Search

Configured with:
- Title field: `title`
- Content field: `chunk`
- Configuration name: `default`

## Chunking Strategy

- **Chunk Size**: 1000 characters (configurable in DocumentProcessor.cs)
- **Overlap**: 100 characters between chunks (configurable)
- **Method**: Splits by paragraphs, maintains context with overlap

## Output

The indexer will:

1. Create or update the Azure AI Search index
2. Process each PDF in the data folder
3. Extract text and create chunks
4. Generate embeddings for each chunk
5. Upload all chunks to Azure AI Search
6. Display progress and statistics

Example output:

```
=== Azure AI Search Indexer ===

Setting up Azure AI Search index: voicerag-index
  Index 'voicerag-index' already exists, updating if needed...
  ✓ Index updated

Processing PDFs from: /path/to/data
Found 3 PDF file(s)

Processing: document1.pdf
  Created 15 chunk(s)
  ✓ Generated embeddings for 15 chunk(s)

Processing: document2.pdf
  Created 8 chunk(s)
  ✓ Generated embeddings for 8 chunk(s)

Uploading 23 chunk(s) to Azure AI Search...
  Batch 1: 23 succeeded, 0 failed

✓ Indexing complete!

Total documents indexed: 23
Index name: voicerag-index
Search endpoint: https://your-service.search.windows.net
```

## Troubleshooting

### No text extracted from PDF

- Ensure the PDF contains actual text (not scanned images)
- For scanned PDFs, use OCR preprocessing first

### Rate limit errors

- The indexer processes embeddings in batches of 16
- Adjust batch size in `EmbeddingService.cs` if needed

### Index creation fails

- Verify Azure AI Search service tier supports vector search
- Check that the embedding dimensions match your deployment
- Ensure proper permissions (Contributor role) on the search service

## Customization

### Change chunk size

Edit `DocumentProcessor.cs`:

```csharp
private const int MaxChunkSize = 1000; // Adjust as needed
private const int ChunkOverlap = 100;  // Adjust overlap
```

### Use different embedding model

Update `.env`:

```env
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-ada-002
AZURE_OPENAI_EMBEDDING_DIMENSIONS=1536
```

### Add more document types

Extend `PdfReader.cs` or create new readers for other formats (DOCX, TXT, etc.)

## References

- [Azure AI Search .NET SDK](https://learn.microsoft.com/en-us/dotnet/api/overview/azure/search.documents-readme)
- [Azure OpenAI Embeddings](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/embeddings)
- [iText7 Documentation](https://itextpdf.com/products/itext-7/itext-7-core)
