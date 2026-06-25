using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using elat.local.llm.Server.DTOs;
using elat.local.llm.Server.Services;

namespace elat.local.llm.Server.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class KnowledgeBaseController : ControllerBase
{
    private readonly IKnowledgeBaseService _knowledgeBaseService;
    private readonly ILogger<KnowledgeBaseController> _logger;

    public KnowledgeBaseController(
        IKnowledgeBaseService knowledgeBaseService,
        ILogger<KnowledgeBaseController> logger)
    {
        _knowledgeBaseService = knowledgeBaseService;
        _logger = logger;
    }

    /// <summary>
    /// Add a document to the knowledge base
    /// </summary>
    /// <param name="request">Document content and metadata</param>
    /// <returns>Document ID of the added document</returns>
    [HttpPost("documents")]
    public async Task<ActionResult<AddDocumentResponse>> AddDocument([FromBody] AddDocumentRequest request)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(request.Content))
            {
                return BadRequest("Document content cannot be empty");
            }

            var documentId = await _knowledgeBaseService.AddDocumentAsync(
                request.Content, 
                request.FileName, 
                request.Category);

            return Ok(new AddDocumentResponse
            {
                DocumentId = documentId,
                Message = "Document added successfully to knowledge base"
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error adding document to knowledge base");
            return StatusCode(500, "An error occurred while adding the document");
        }
    }

    /// <summary>
    /// Search the knowledge base for relevant documents
    /// </summary>
    /// <param name="request">Search query and parameters</param>
    /// <returns>List of relevant documents</returns>
    [HttpPost("search")]
    public async Task<ActionResult<SearchResponse>> Search([FromBody] SearchRequest request)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(request.Query))
            {
                return BadRequest("Search query cannot be empty");
            }

            var results = await _knowledgeBaseService.SearchAsync(request.Query, request.MaxResults);

            return Ok(new SearchResponse
            {
                Results = results,
                TotalResults = results.Count,
                Query = request.Query
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error searching knowledge base for query: {Query}", request.Query);
            return StatusCode(500, "An error occurred while searching the knowledge base");
        }
    }

    /// <summary>
    /// Get all documents from the knowledge base
    /// </summary>
    /// <param name="maxResults">Maximum number of documents to return</param>
    /// <returns>List of all documents</returns>
    [HttpGet("documents")]
    public async Task<ActionResult<SearchResponse>> GetAllDocuments([FromQuery] int maxResults = 100)
    {
        try
        {
            // Use search with wildcard to get all documents
            var results = await _knowledgeBaseService.SearchAsync("*", maxResults);

            return Ok(new SearchResponse
            {
                Results = results,
                TotalResults = results.Count,
                Query = "*"
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error retrieving all documents from knowledge base");
            return StatusCode(500, "An error occurred while retrieving documents");
        }
    }

    /// <summary>
    /// Delete a document from the knowledge base
    /// </summary>
    /// <param name="documentId">ID of the document to delete</param>
    /// <returns>Success status</returns>
    [HttpDelete("documents/{documentId}")]
    public async Task<ActionResult> DeleteDocument(string documentId)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(documentId))
            {
                return BadRequest("Document ID cannot be empty");
            }

            await _knowledgeBaseService.DeleteDocumentAsync(documentId);
            return Ok(new { Message = "Document deleted successfully" });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting document: {DocumentId}", documentId);
            return StatusCode(500, "An error occurred while deleting the document");
        }
    }

    /// <summary>
    /// Upload a file and add its content to the knowledge base
    /// </summary>
    /// <param name="file">File to upload</param>
    /// <param name="category">Optional category for the document</param>
    /// <returns>Document ID of the added document</returns>
    [HttpPost("upload")]
    public async Task<ActionResult<AddDocumentResponse>> UploadFile(
        IFormFile file, 
        [FromForm] string? category = null)
    {
        try
        {
            if (file == null || file.Length == 0)
            {
                return BadRequest("No file uploaded");
            }

            // Read file content as text
            string content;
            using (var reader = new StreamReader(file.OpenReadStream()))
            {
                content = await reader.ReadToEndAsync();
            }

            if (string.IsNullOrWhiteSpace(content))
            {
                return BadRequest("File content is empty or not readable as text");
            }

            var documentId = await _knowledgeBaseService.AddDocumentAsync(
                content, 
                file.FileName, 
                category);

            return Ok(new AddDocumentResponse
            {
                DocumentId = documentId,
                Message = $"File '{file.FileName}' added successfully to knowledge base"
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error uploading file to knowledge base: {FileName}", file?.FileName);
            return StatusCode(500, "An error occurred while uploading the file");
        }
    }
}
