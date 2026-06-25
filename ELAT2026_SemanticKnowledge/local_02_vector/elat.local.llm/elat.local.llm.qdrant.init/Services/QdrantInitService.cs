using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Memory;
using Qdrant.Client;
using Qdrant.Client.Grpc;


#pragma warning disable SKEXP0001

namespace elat.local.llm.qdrant.init.Services;

public interface IQdrantInitService
{
    Task InitializeAsync();
    Task<string> AddDocumentAsync(string content, string? fileName = null, string? category = null);
    Task<bool> IsQdrantHealthyAsync();
    Task<bool> CollectionExistsAsync(string collectionName);
}

public class QdrantInitService : IQdrantInitService
{
    private readonly QdrantClient _qdrantClient;
    private readonly ILogger<QdrantInitService> _logger;
    private readonly ISemanticTextMemory _memory;
    private readonly IOllamaEmbeddingClient _embedClient;
    private readonly string _embedModel;
    private readonly int _vectorSize;
    private readonly bool _recreateOnInit;
    private readonly string _collectionName = "knowledge_base";

    public QdrantInitService(
        QdrantClient qdrantClient,
        ILogger<QdrantInitService> logger,
        ISemanticTextMemory memory,
        IOllamaEmbeddingClient embedClient,
        string embedModel,
        int vectorSize,
        bool recreateOnInit)
    {
        _qdrantClient = qdrantClient;
        _logger = logger;
        _memory = memory;
        _embedClient = embedClient;
        _embedModel = embedModel;
        _vectorSize = vectorSize;
        _recreateOnInit = recreateOnInit;
    }

    public async Task<bool> IsQdrantHealthyAsync()
    {
        try
        {
            var health = await _qdrantClient.HealthAsync();
            _logger.LogInformation("Qdrant health check: {Status}", health);
            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Qdrant health check failed");
            return false;
        }
    }

    public async Task<bool> CollectionExistsAsync(string collectionName)
    {
        try
        {
            var collections = await _qdrantClient.ListCollectionsAsync();
            return collections.Any(c => c == collectionName);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error checking if collection exists: {CollectionName}", collectionName);
            return false;
        }
    }

    public async Task InitializeAsync()
    {
        try
        {
            _logger.LogInformation("Checking Qdrant health...");
            if (!await IsQdrantHealthyAsync())
            {
                throw new InvalidOperationException("Qdrant is not healthy. Please ensure Qdrant server is running.");
            }

            _logger.LogInformation("Initializing Qdrant collection: {CollectionName}", _collectionName);

            // Check if collection exists
            if (await CollectionExistsAsync(_collectionName))
            {
                if (_recreateOnInit)
                {
                    _logger.LogInformation("Recreating collection {CollectionName} as requested", _collectionName);
                    await _qdrantClient.DeleteCollectionAsync(_collectionName);
                }
                else
                {
                    _logger.LogInformation("Collection {CollectionName} already exists", _collectionName);
                    return;
                }
            }

            // Create collection with configured vector size
            await _qdrantClient.CreateCollectionAsync(_collectionName, new VectorParams
            {
                Size = (ulong)_vectorSize,
                Distance = Distance.Cosine
            });

            _logger.LogInformation("Successfully created collection: {CollectionName}", _collectionName);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to initialize Qdrant collection");
            throw;
        }
    }

    public async Task<string> AddDocumentAsync(string content, string? fileName = null, string? category = null)
    {
        try
        {
            var documentId = Guid.NewGuid().ToString();
            var vector = await _embedClient.GenerateAsync(content, _embedModel);

            if (vector == null || vector.Length == 0)
            {
                throw new InvalidOperationException($"Embedding returned empty vector for model '{_embedModel}'. Ensure Ollama is serving and the model is pulled.");
            }
            if (_vectorSize > 0 && vector.Length != _vectorSize)
            {
                throw new InvalidOperationException($"Embedding dimension mismatch. Expected: {_vectorSize}, got: {vector.Length}. Check your embedding model and collection size.");
            }

            _logger.LogInformation("Embedding length: {Length}", vector.Length);

            // Build vectors
            var v = new Vector { Data = { vector } };
            var vectors = new Vectors { Vector = v };

            var point = new PointStruct
            {
                Id = new PointId { Uuid = documentId },
                Vectors = vectors
            };
            point.Payload.Add("fileName", new Qdrant.Client.Grpc.Value { StringValue = fileName ?? string.Empty });
            point.Payload.Add("category", new Qdrant.Client.Grpc.Value { StringValue = category ?? string.Empty });
            point.Payload.Add("text", new Qdrant.Client.Grpc.Value { StringValue = content });

            await _qdrantClient.UpsertAsync(_collectionName, new[] { point }, wait: true);

            _logger.LogInformation(
                "Added document to Qdrant: {DocumentId} (File: {FileName}, Category: {Category})",
                documentId, fileName ?? "Unknown", category ?? "General");
            return documentId;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to add document: {FileName}", fileName);
            throw;
        }
    }
}
