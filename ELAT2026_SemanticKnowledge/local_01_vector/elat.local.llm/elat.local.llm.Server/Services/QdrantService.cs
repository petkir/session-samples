#pragma warning disable SKEXP0001
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Memory;
using Qdrant.Client;
using Qdrant.Client.Grpc;
using elat.local.llm.Server.Models;
using Microsoft.Extensions.Options;

namespace elat.local.llm.Server.Services;

public interface IQdrantService
{
    Task InitializeAsync();
    Task<string> StoreDocumentAsync(string documentId, string text, Dictionary<string, object>? metadata = null);
    Task<IList<MemoryQueryResult>> SearchAsync(string query, int limit = 5, double minRelevanceScore = 0.7);
    Task DeleteDocumentAsync(string documentId);
    Task<bool> CollectionExistsAsync();
}

public class QdrantService : IQdrantService
{
    private readonly QdrantClient _qdrantClient;
    private readonly ISemanticTextMemory _memory;
    private readonly QdrantOptions _options;
    private readonly ILogger<QdrantService> _logger;

    public QdrantService(
        QdrantClient qdrantClient,
        ISemanticTextMemory memory,
        IOptions<QdrantOptions> options,
        ILogger<QdrantService> logger)
    {
        _qdrantClient = qdrantClient;
        _memory = memory;
        _options = options.Value;
        _logger = logger;
    }

    public async Task InitializeAsync()
    {
        try
        {
            var collectionExists = await CollectionExistsAsync();
            if (!collectionExists)
            {
                _logger.LogInformation("Creating Qdrant collection: {CollectionName}", _options.CollectionName);
                
                await _qdrantClient.CreateCollectionAsync(_options.CollectionName, new VectorParams
                {
                    Size = (ulong)_options.VectorSize,
                    Distance = Distance.Cosine
                });
                
                _logger.LogInformation("Successfully created Qdrant collection: {CollectionName}", _options.CollectionName);
            }
            else
            {
                _logger.LogInformation("Qdrant collection already exists: {CollectionName}", _options.CollectionName);
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to initialize Qdrant collection: {CollectionName}", _options.CollectionName);
            throw;
        }
    }

    public async Task<string> StoreDocumentAsync(string documentId, string text, Dictionary<string, object>? metadata = null)
    {
        try
        {
            // Combine metadata for better searchability
            var additionalMetadata = metadata ?? new Dictionary<string, object>();
            additionalMetadata["document_id"] = documentId;
            additionalMetadata["stored_at"] = DateTimeOffset.UtcNow.ToString("O");

            var result = await _memory.SaveInformationAsync(
                collection: _options.CollectionName,
                text: text,
                id: documentId,
                description: $"Document: {documentId}");

            _logger.LogInformation("Successfully stored document in Qdrant: {DocumentId}", documentId);
            return result;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to store document in Qdrant: {DocumentId}", documentId);
            throw;
        }
    }

    public async Task<IList<MemoryQueryResult>> SearchAsync(string query, int limit = 5, double minRelevanceScore = 0.7)
    {
        try
        {
            _logger.LogInformation("Performing semantic search in Qdrant for query: {Query}", query);
            
            var results = _memory.SearchAsync(
                collection: _options.CollectionName,
                query: query,
                limit: limit,
                minRelevanceScore: minRelevanceScore);

            var resultList = new List<MemoryQueryResult>();
            await foreach (var result in results)
            {
                resultList.Add(result);
            }

            _logger.LogInformation("Found {Count} results for query: {Query}", resultList.Count, query);
            return resultList;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to search in Qdrant for query: {Query}", query);
            throw;
        }
    }

    public async Task DeleteDocumentAsync(string documentId)
    {
        try
        {
            await _memory.RemoveAsync(_options.CollectionName, documentId);
            _logger.LogInformation("Successfully deleted document from Qdrant: {DocumentId}", documentId);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to delete document from Qdrant: {DocumentId}", documentId);
            throw;
        }
    }

    public async Task<bool> CollectionExistsAsync()
    {
        try
        {
            var collections = await _qdrantClient.ListCollectionsAsync();
            return collections.Any(c => c == _options.CollectionName);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to check if collection exists: {CollectionName}", _options.CollectionName);
            return false;
        }
    }
}
#pragma warning restore SKEXP0001
