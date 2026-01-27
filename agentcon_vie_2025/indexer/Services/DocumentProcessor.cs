using System.Text;

namespace Indexer.Services;

public class DocumentProcessor
{
    private readonly EmbeddingService _embeddingService;
    private const int MaxChunkSize = 1000; // characters per chunk
    private const int ChunkOverlap = 100; // overlap between chunks

    public DocumentProcessor(EmbeddingService embeddingService)
    {
        _embeddingService = embeddingService;
    }

    public List<string> ChunkDocument(string text, string documentTitle)
    {
        var chunks = new List<string>();
        
        // Clean the text
        text = CleanText(text);
        
        if (string.IsNullOrWhiteSpace(text))
        {
            return chunks;
        }

        // Split by paragraphs first
        var paragraphs = text.Split(new[] { "\n\n", "\r\n\r\n" }, StringSplitOptions.RemoveEmptyEntries)
                            .Select(p => p.Trim())
                            .Where(p => !string.IsNullOrWhiteSpace(p))
                            .ToList();

        var currentChunk = new StringBuilder();
        
        foreach (var paragraph in paragraphs)
        {
            // If adding this paragraph would exceed max size, save current chunk
            if (currentChunk.Length + paragraph.Length > MaxChunkSize && currentChunk.Length > 0)
            {
                chunks.Add(currentChunk.ToString().Trim());
                
                // Start new chunk with overlap from previous chunk
                var overlapText = GetOverlapText(currentChunk.ToString(), ChunkOverlap);
                currentChunk.Clear();
                currentChunk.Append(overlapText);
                currentChunk.Append(" ");
            }
            
            currentChunk.Append(paragraph);
            currentChunk.Append("\n\n");
            
            // If current chunk is at or near max size, save it
            if (currentChunk.Length >= MaxChunkSize)
            {
                chunks.Add(currentChunk.ToString().Trim());
                
                var overlapText = GetOverlapText(currentChunk.ToString(), ChunkOverlap);
                currentChunk.Clear();
                currentChunk.Append(overlapText);
                currentChunk.Append(" ");
            }
        }
        
        // Add final chunk if there's remaining text
        if (currentChunk.Length > 0)
        {
            chunks.Add(currentChunk.ToString().Trim());
        }

        return chunks;
    }

    private string CleanText(string text)
    {
        if (string.IsNullOrWhiteSpace(text))
            return string.Empty;

        // Remove excessive whitespace
        text = System.Text.RegularExpressions.Regex.Replace(text, @"\s+", " ");
        
        // Normalize line breaks
        text = text.Replace("\r\n", "\n").Replace("\r", "\n");
        
        // Remove multiple consecutive newlines (keep max 2)
        text = System.Text.RegularExpressions.Regex.Replace(text, @"\n{3,}", "\n\n");
        
        return text.Trim();
    }

    private string GetOverlapText(string text, int overlapLength)
    {
        if (text.Length <= overlapLength)
            return text;

        // Get last N characters, trying to break at word boundary
        var lastChars = text.Substring(text.Length - overlapLength);
        var lastSpaceIndex = lastChars.LastIndexOf(' ');
        
        if (lastSpaceIndex > 0)
        {
            return lastChars.Substring(lastSpaceIndex + 1);
        }
        
        return lastChars;
    }
}
