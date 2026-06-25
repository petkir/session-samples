using Microsoft.Extensions.Logging;
using iText.Kernel.Pdf;
using iText.Kernel.Pdf.Canvas.Parser;
using System.Text.Json;

namespace elat.local.llm.qdrant.init.Services;

public interface IDocumentProcessingService
{
    Task<string> ExtractTextFromPdfAsync(string filePath);
    Task<string> ReadTextFileAsync(string filePath);
    string DetermineFileType(string filePath);
    Task<List<Models.DocumentData>> LoadSampleDocumentsAsync(string jsonFilePath);
}

public class DocumentProcessingService : IDocumentProcessingService
{
    private readonly ILogger<DocumentProcessingService> _logger;

    public DocumentProcessingService(ILogger<DocumentProcessingService> logger)
    {
        _logger = logger;
    }

    public Task<string> ExtractTextFromPdfAsync(string filePath)
    {
        try
        {
            _logger.LogInformation("Extracting text from PDF: {FilePath}", filePath);
            
            using var reader = new PdfReader(filePath);
            using var pdfDoc = new PdfDocument(reader);
            
            var text = string.Empty;
            for (int i = 1; i <= pdfDoc.GetNumberOfPages(); i++)
            {
                var page = pdfDoc.GetPage(i);
                var pageText = PdfTextExtractor.GetTextFromPage(page);
                text += pageText + "\n";
            }

            _logger.LogInformation("Successfully extracted {Length} characters from PDF: {FilePath}", 
                text.Length, Path.GetFileName(filePath));
            
            return Task.FromResult(text.Trim());
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to extract text from PDF: {FilePath}", filePath);
            throw;
        }
    }

    public async Task<string> ReadTextFileAsync(string filePath)
    {
        try
        {
            _logger.LogInformation("Reading text file: {FilePath}", filePath);
            var content = await File.ReadAllTextAsync(filePath);
            _logger.LogInformation("Successfully read {Length} characters from: {FilePath}", 
                content.Length, Path.GetFileName(filePath));
            return content;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to read text file: {FilePath}", filePath);
            throw;
        }
    }

    public string DetermineFileType(string filePath)
    {
        var extension = Path.GetExtension(filePath).ToLowerInvariant();
        return extension switch
        {
            ".pdf" => "pdf",
            ".txt" => "text",
            ".md" => "text",
            ".json" => "text",
            ".xml" => "text",
            ".csv" => "text",
            _ => "unknown"
        };
    }

    public async Task<List<Models.DocumentData>> LoadSampleDocumentsAsync(string jsonFilePath)
    {
        try
        {
            _logger.LogInformation("Loading sample documents from: {FilePath}", jsonFilePath);
            
            var jsonContent = await File.ReadAllTextAsync(jsonFilePath);
            var documents = JsonSerializer.Deserialize<List<Models.DocumentData>>(jsonContent, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });

            if (documents == null)
            {
                _logger.LogWarning("No documents found in JSON file: {FilePath}", jsonFilePath);
                return new List<Models.DocumentData>();
            }

            _logger.LogInformation("Successfully loaded {Count} sample documents", documents.Count);
            return documents;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to load sample documents from: {FilePath}", jsonFilePath);
            throw;
        }
    }
}
