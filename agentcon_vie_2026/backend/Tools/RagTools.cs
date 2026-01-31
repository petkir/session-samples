using System.Text;
using System.Text.Json;
using Azure;
using Azure.Core;
using Azure.Identity;
using Azure.Search.Documents;
using Azure.Search.Documents.Models;
using Backend.Models;

namespace Backend.Tools;

public interface IRagTools
{
    void AttachToRTMiddleTier(Services.RTMiddleTier rtMiddleTier);
}

public class RagTools : IRagTools
{
    private readonly SearchClient _searchClient;
    private readonly string? _semanticConfiguration;
    private readonly string _identifierField;
    private readonly string _contentField;
    private readonly string _embeddingField;
    private readonly string _titleField;
    private readonly bool _useVectorQuery;
    private readonly ILogger<RagTools> _logger;

    public RagTools(
        object credentials,
        string searchEndpoint,
        string searchIndex,
        string? semanticConfiguration,
        string identifierField,
        string contentField,
        string embeddingField,
        string titleField,
        bool useVectorQuery,
        ILogger<RagTools> logger)
    {
        _semanticConfiguration = semanticConfiguration;
        _identifierField = identifierField;
        _contentField = contentField;
        _embeddingField = embeddingField;
        _titleField = titleField;
        _useVectorQuery = useVectorQuery;
        _logger = logger;

        if (credentials is string apiKey)
        {
            _searchClient = new SearchClient(new Uri(searchEndpoint), searchIndex, new AzureKeyCredential(apiKey));
        }
        else if (credentials is TokenCredential tokenCredential)
        {
            _searchClient = new SearchClient(new Uri(searchEndpoint), searchIndex, tokenCredential);
        }
        else
        {
            throw new ArgumentException("Credentials must be either a string API key or a TokenCredential");
        }

        _logger.LogInformation("RagTools initialized for index: {SearchIndex}", searchIndex);
    }

    public void AttachToRTMiddleTier(Services.RTMiddleTier rtMiddleTier)
    {
        rtMiddleTier.Tools["search"] = new Tool(
            Schema: GetSearchToolSchema(),
            Target: SearchToolAsync
        );

        rtMiddleTier.Tools["report_grounding"] = new Tool(
            Schema: GetGroundingToolSchema(),
            Target: ReportGroundingToolAsync
        );

        _logger.LogInformation("RAG tools attached to RTMiddleTier");
    }

    private object GetSearchToolSchema()
    {
        return new
        {
            type = "function",
            name = "search",
            description = "Search the knowledge base. The knowledge base is in English, translate to and from English if needed. " +
                         "Results are formatted as a source name first in square brackets, followed by the text content, " +
                         "and a line with '-----' at the end of each result.",
            parameters = new
            {
                type = "object",
                properties = new
                {
                    query = new
                    {
                        type = "string",
                        description = "Search query"
                    }
                },
                required = new[] { "query" },
                additionalProperties = false
            }
        };
    }

    private object GetGroundingToolSchema()
    {
        return new
        {
            type = "function",
            name = "report_grounding",
            description = "Report the source documents that were used to ground the response. This tool should be called after the search tool.",
            parameters = new
            {
                type = "object",
                properties = new
                {
                    sources = new
                    {
                        type = "array",
                        items = new
                        {
                            type = "object",
                            properties = new
                            {
                                chunk_id = new { type = "string" },
                                title = new { type = "string" },
                                chunk = new { type = "string" }
                            }
                        },
                        description = "List of source documents"
                    }
                },
                required = new[] { "sources" },
                additionalProperties = false
            }
        };
    }

    private async Task<ToolResult> SearchToolAsync(string argumentsJson)
    {
        var arguments = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(argumentsJson);
        if (arguments == null || !arguments.TryGetValue("query", out var queryElement))
        {
            return new ToolResult("Error: query parameter is required");
        }

        var query = queryElement.GetString();
        if (string.IsNullOrEmpty(query))
        {
            return new ToolResult("Error: query cannot be empty");
        }

        _logger.LogInformation("Searching for: {Query}", query);

        try
        {
            var searchOptions = new SearchOptions
            {
                Size = 5,
                Select = { _identifierField, _contentField }
            };

            if (!string.IsNullOrEmpty(_semanticConfiguration))
            {
                searchOptions.QueryType = SearchQueryType.Semantic;
                searchOptions.SemanticSearch = new SemanticSearchOptions
                {
                    SemanticConfigurationName = _semanticConfiguration
                };
            }

            if (_useVectorQuery)
            {
                // Note: For full vector search support, you'd need to generate embeddings
                // For now, we'll use hybrid search with text only
                _logger.LogInformation("Vector query requested but not yet implemented in this version");
            }

            var response = await _searchClient.SearchAsync<SearchDocument>(query, searchOptions);
            
            var resultBuilder = new StringBuilder();
            await foreach (var result in response.Value.GetResultsAsync())
            {
                var document = result.Document;
                var identifier = document.TryGetValue(_identifierField, out var id) ? id?.ToString() : "unknown";
                var content = document.TryGetValue(_contentField, out var cont) ? cont?.ToString() : "";
                
                resultBuilder.AppendLine($"[{identifier}]: {content}");
                resultBuilder.AppendLine("-----");
            }

            var searchResult = resultBuilder.ToString();
            if (string.IsNullOrEmpty(searchResult))
            {
                searchResult = "No results found.";
            }

            _logger.LogInformation("Search completed, found results");
            return new ToolResult(searchResult, ToolResultDirection.ToServer);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during search");
            return new ToolResult($"Error searching: {ex.Message}");
        }
    }

    private async Task<ToolResult> ReportGroundingToolAsync(string argumentsJson)
    {
        _logger.LogInformation("Reporting grounding sources");

        try
        {
            var arguments = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(argumentsJson);
            if (arguments == null || !arguments.TryGetValue("sources", out var sourcesElement))
            {
                return new ToolResult("[]", ToolResultDirection.ToClient);
            }

            var sources = JsonSerializer.Deserialize<List<Dictionary<string, string>>>(sourcesElement.GetRawText());
            if (sources == null || sources.Count == 0)
            {
                return new ToolResult("[]", ToolResultDirection.ToClient);
            }

            // Fetch full document details for grounding
            var groundingResults = new List<object>();
            foreach (var source in sources)
            {
                if (!source.TryGetValue("chunk_id", out var chunkId))
                    continue;

                try
                {
                    var getOptions = new GetDocumentOptions
                    {
                        SelectedFields = { _identifierField, _titleField, _contentField }
                    };

                    var document = await _searchClient.GetDocumentAsync<SearchDocument>(chunkId, getOptions);
                    
                    if (document?.Value != null)
                    {
                        var doc = document.Value;
                        groundingResults.Add(new
                        {
                            chunk_id = doc.TryGetValue(_identifierField, out var id) ? id?.ToString() : chunkId,
                            title = doc.TryGetValue(_titleField, out var title) ? title?.ToString() : "Untitled",
                            chunk = doc.TryGetValue(_contentField, out var content) ? content?.ToString() : ""
                        });
                    }
                }
                catch (RequestFailedException ex) when (ex.Status == 404)
                {
                    _logger.LogWarning("Document {ChunkId} not found", chunkId);
                }
            }

            var resultJson = JsonSerializer.Serialize(new { sources = groundingResults });
            return new ToolResult(resultJson, ToolResultDirection.ToClient);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error reporting grounding");
            return new ToolResult("[]", ToolResultDirection.ToClient);
        }
    }
}
