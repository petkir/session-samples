using Azure;
using Azure.AI.OpenAI;
using Azure.Core;
using Azure.Identity;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using Indexer.Services;

// Load environment variables from .env file
var envPath = Path.Combine(Directory.GetCurrentDirectory(), ".env");
if (File.Exists(envPath))
{
    foreach (var line in File.ReadAllLines(envPath))
    {
        if (string.IsNullOrWhiteSpace(line) || line.StartsWith('#'))
            continue;

        var parts = line.Split('=', 2, StringSplitOptions.TrimEntries);
        if (parts.Length == 2)
        {
            Environment.SetEnvironmentVariable(parts[0], parts[1]);
        }
    }
}

Console.WriteLine("=== Azure AI Search Indexer ===\n");

// Get configuration
var openAiEndpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT")?.Replace("wss://", "https://").Replace("ws://", "http://")
    ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT not set");
var openAiKey = Environment.GetEnvironmentVariable("AZURE_OPENAI_API_KEY");
var embeddingDeployment = Environment.GetEnvironmentVariable("AZURE_OPENAI_EMBEDDING_DEPLOYMENT") ?? "text-embedding-3-large";
var embeddingModel = Environment.GetEnvironmentVariable("AZURE_OPENAI_EMBEDDING_MODEL") ?? "text-embedding-3-large";
var embeddingDimensions = int.Parse(Environment.GetEnvironmentVariable("AZURE_OPENAI_EMBEDDING_DIMENSIONS") ?? "3072");

var searchEndpoint = Environment.GetEnvironmentVariable("AZURE_SEARCH_ENDPOINT")
    ?? throw new InvalidOperationException("AZURE_SEARCH_ENDPOINT not set");
var searchKey = Environment.GetEnvironmentVariable("AZURE_SEARCH_API_KEY");
var searchIndex = Environment.GetEnvironmentVariable("AZURE_SEARCH_INDEX")
    ?? throw new InvalidOperationException("AZURE_SEARCH_INDEX not set");

var dataFolder = Path.Combine(Directory.GetCurrentDirectory(), "..", "data");
if (!Directory.Exists(dataFolder))
{
    throw new DirectoryNotFoundException($"Data folder not found: {dataFolder}");
}

// Setup credentials
TokenCredential? credential = null;
if (string.IsNullOrEmpty(openAiKey) || string.IsNullOrEmpty(searchKey))
{
    var tenantId = Environment.GetEnvironmentVariable("AZURE_TENANT_ID");
    if (!string.IsNullOrEmpty(tenantId))
    {
        Console.WriteLine($"Using AzureDeveloperCliCredential with tenant_id {tenantId}");
        credential = new AzureDeveloperCliCredential(new AzureDeveloperCliCredentialOptions
        {
            TenantId = tenantId
        });
    }
    else
    {
        Console.WriteLine("Using DefaultAzureCredential");
        credential = new DefaultAzureCredential();
    }
}

// Initialize services
var azureOpenAiClient = !string.IsNullOrEmpty(openAiKey)
    ? new AzureOpenAIClient(new Uri(openAiEndpoint), new AzureKeyCredential(openAiKey))
    : new AzureOpenAIClient(new Uri(openAiEndpoint), credential!);

var embeddingClient = azureOpenAiClient.GetEmbeddingClient(embeddingDeployment);

var searchIndexClient = !string.IsNullOrEmpty(searchKey)
    ? new SearchIndexClient(new Uri(searchEndpoint), new AzureKeyCredential(searchKey))
    : new SearchIndexClient(new Uri(searchEndpoint), credential!);

var searchClient = searchIndexClient.GetSearchClient(searchIndex);

// Create or update the search index
Console.WriteLine($"Setting up Azure AI Search index: {searchIndex}");
var indexManager = new SearchIndexManager(searchIndexClient, searchIndex, embeddingDimensions);
await indexManager.CreateOrUpdateIndexAsync();

// Initialize document processor
var embeddingService = new EmbeddingService(embeddingClient);
var documentProcessor = new DocumentProcessor(embeddingService);

// Process all PDFs in the data folder
Console.WriteLine($"\nProcessing PDFs from: {dataFolder}");
var pdfFiles = Directory.GetFiles(dataFolder, "*.pdf", SearchOption.AllDirectories);
Console.WriteLine($"Found {pdfFiles.Length} PDF file(s)\n");

var allChunks = new List<Dictionary<string, object>>();
int documentId = 1;

foreach (var pdfFile in pdfFiles)
{
    try
    {
        Console.WriteLine($"Processing: {Path.GetFileName(pdfFile)}");
        var fileName = Path.GetFileNameWithoutExtension(pdfFile);
        
        // Extract text from PDF
        var text = PdfReader.ExtractText(pdfFile);
        if (string.IsNullOrWhiteSpace(text))
        {
            Console.WriteLine($"  ⚠️  No text extracted from {fileName}");
            continue;
        }

        // Chunk the document
        var chunks = documentProcessor.ChunkDocument(text, fileName);
        Console.WriteLine($"  Created {chunks.Count} chunk(s)");

        // Generate embeddings for each chunk
        int chunkIndex = 1;
        foreach (var chunk in chunks)
        {
            var chunkId = $"{fileName}_chunk_{chunkIndex}";
            var embedding = await embeddingService.GenerateEmbeddingAsync(chunk);
            
            var searchDoc = new Dictionary<string, object>
            {
                { "chunk_id", chunkId },
                { "parent_id", fileName },
                { "title", fileName },
                { "chunk", chunk },
                { "text_vector", embedding.ToList() },
                { "chunk_index", chunkIndex },
                { "source_file", Path.GetFileName(pdfFile) }
            };

            allChunks.Add(searchDoc);
            chunkIndex++;
        }

        Console.WriteLine($"  ✓ Generated embeddings for {chunks.Count} chunk(s)");
        documentId++;
    }
    catch (Exception ex)
    {
        Console.WriteLine($"  ✗ Error processing {Path.GetFileName(pdfFile)}: {ex.Message}");
    }
}

// Upload all chunks to Azure AI Search
if (allChunks.Count > 0)
{
    Console.WriteLine($"\nUploading {allChunks.Count} chunk(s) to Azure AI Search...");
    
    try
    {
        // Upload in batches of 100
        const int batchSize = 100;
        for (int i = 0; i < allChunks.Count; i += batchSize)
        {
            var batch = allChunks.Skip(i).Take(batchSize).ToList();
            var response = await searchClient.MergeOrUploadDocumentsAsync(batch);
            
            var succeeded = response.Value.Results.Count(r => r.Succeeded);
            var failed = response.Value.Results.Count(r => !r.Succeeded);
            
            Console.WriteLine($"  Batch {(i / batchSize) + 1}: {succeeded} succeeded, {failed} failed");
            
            if (failed > 0)
            {
                foreach (var result in response.Value.Results.Where(r => !r.Succeeded))
                {
                    Console.WriteLine($"    ✗ {result.Key}: {result.ErrorMessage}");
                }
            }
        }
        
        Console.WriteLine("\n✓ Indexing complete!");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"\n✗ Error uploading documents: {ex.Message}");
        if (ex.InnerException != null)
        {
            Console.WriteLine($"  Inner exception: {ex.InnerException.Message}");
        }
        Environment.Exit(1);
    }
}
else
{
    Console.WriteLine("\nNo chunks to upload.");
}

Console.WriteLine($"\nTotal documents indexed: {allChunks.Count}");
Console.WriteLine("Index name: " + searchIndex);
Console.WriteLine("Search endpoint: " + searchEndpoint);
