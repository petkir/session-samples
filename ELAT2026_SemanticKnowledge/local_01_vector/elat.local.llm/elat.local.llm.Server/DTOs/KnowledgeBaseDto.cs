namespace elat.local.llm.Server.DTOs;

public class KnowledgeSearchResult
{
    public string DocumentId { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public double RelevanceScore { get; set; }
    public string? FileName { get; set; }
    public string? Category { get; set; }
    public string? AddedAt { get; set; }
}

public class AddDocumentRequest
{
    public string Content { get; set; } = string.Empty;
    public string? FileName { get; set; }
    public string? Category { get; set; }
}

public class AddDocumentResponse
{
    public string DocumentId { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
}

public class SearchRequest
{
    public string Query { get; set; } = string.Empty;
    public int MaxResults { get; set; } = 5;
}

public class SearchResponse
{
    public List<KnowledgeSearchResult> Results { get; set; } = new();
    public int TotalResults { get; set; }
    public string Query { get; set; } = string.Empty;
}
