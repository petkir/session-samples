using Microsoft.SemanticKernel.Memory;
using elat.local.llm.Server.DTOs;

namespace elat.local.llm.Server.Services;

public interface IKnowledgeBaseService
{
    Task<string> AddDocumentAsync(string content, string? fileName = null, string? category = null);
    Task<List<KnowledgeSearchResult>> SearchAsync(string query, int maxResults = 5);
    Task DeleteDocumentAsync(string documentId);
    Task<List<string>> GetAllDocumentIdsAsync();
    Task InitializeAsync();
}

public class KnowledgeBaseService : IKnowledgeBaseService
{
    private readonly IQdrantService _qdrantService;
    private readonly ILogger<KnowledgeBaseService> _logger;

    public KnowledgeBaseService(
        IQdrantService qdrantService,
        ILogger<KnowledgeBaseService> logger)
    {
        _qdrantService = qdrantService;
        _logger = logger;
    }

    public async Task InitializeAsync()
    {
        await _qdrantService.InitializeAsync();
    }

    public async Task<string> AddDocumentAsync(string content, string? fileName = null, string? category = null)
    {
        var documentId = Guid.NewGuid().ToString();
        
        var metadata = new Dictionary<string, object>
        {
            ["content_length"] = content.Length,
            ["added_at"] = DateTimeOffset.UtcNow.ToString("O")
        };

        if (!string.IsNullOrEmpty(fileName))
        {
            metadata["file_name"] = fileName;
        }

        if (!string.IsNullOrEmpty(category))
        {
            metadata["category"] = category;
        }

        await _qdrantService.StoreDocumentAsync(documentId, content, metadata);
        
        _logger.LogInformation("Added document to knowledge base: {DocumentId}, FileName: {FileName}", 
            documentId, fileName ?? "N/A");
        
        return documentId;
    }

    public async Task<List<KnowledgeSearchResult>> SearchAsync(string query, int maxResults = 5)
    {
        var threshold =0.6;
        if(query == "*")
        {
            threshold=0.0; // lower threshold for short queries
        }
        var results = await _qdrantService.SearchAsync(query, maxResults, threshold); // Lower threshold for more results
        
        return results.Select(r => new KnowledgeSearchResult
        {
            DocumentId = r.Metadata.Id,
            Content = r.Metadata.Text,
            RelevanceScore = r.Relevance,
            FileName = r.Metadata.Description ?? "Unknown",
            Category = "Document",
            AddedAt = DateTime.UtcNow.ToString("O")
        }).ToList();
    }

    public async Task DeleteDocumentAsync(string documentId)
    {
        await _qdrantService.DeleteDocumentAsync(documentId);
        _logger.LogInformation("Deleted document from knowledge base: {DocumentId}", documentId);
    }

    public Task<List<string>> GetAllDocumentIdsAsync()
    {
        // This would require additional implementation in QdrantService to list all documents
        // For now, we'll return an empty list as this is not commonly needed
        return Task.FromResult(new List<string>());
    }
}
