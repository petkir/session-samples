using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Authorization;
using Microsoft.Identity.Web;
using elat.local.llm.Server.Services;
using elat.local.llm.Server.DTOs;
using elat.local.llm.Server.Models;
using System.Security.Claims;
using System.Text;
using System.Text.Json;

namespace elat.local.llm.Server.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class ChatController : ControllerBase
{
    private readonly IChatService _chatService;
    private readonly ILogger<ChatController> _logger;
    private readonly IWebHostEnvironment _environment;

    public ChatController(IChatService chatService, ILogger<ChatController> logger, IWebHostEnvironment environment)
    {
        _chatService = chatService;
        _logger = logger;
        _environment = environment;
    }

    private string GetUserId()
    {
        return User.GetObjectId() ?? User.FindFirst(ClaimTypes.NameIdentifier)?.Value ?? "anonymous";
    }

    /// <summary>
    /// Get all chat sessions for the authenticated user
    /// </summary>
    /// <returns>List of chat sessions</returns>
    /// <response code="200">Returns the list of chat sessions</response>
    /// <response code="401">If the user is not authenticated</response>
    /// <response code="500">If there was an internal server error</response>
    [HttpGet("sessions")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status500InternalServerError)]
    public async Task<ActionResult<IEnumerable<ChatSessionDto>>> GetChatSessions()
    {
        try
        {
            var userId = GetUserId();
            var sessions = await _chatService.GetChatSessionsAsync(userId);
            
            var sessionDtos = sessions.Select(s => new ChatSessionDto
            {
                Id = s.Id,
                Title = s.Title,
                CreatedAt = s.CreatedAt,
                UpdatedAt = s.UpdatedAt,
                Messages = s.Messages.Select(m => new ChatMessageDto
                {
                    Id = m.Id,
                    Role = m.Role,
                    Content = m.Content,
                    CreatedAt = m.CreatedAt,
                    Attachments = m.Attachments.Select(a => new ChatAttachmentDto
                    {
                        Id = a.Id,
                        FileName = a.FileName,
                        ContentType = a.ContentType,
                        FileSize = a.FileSize,
                        CreatedAt = a.CreatedAt
                    }).ToList()
                }).ToList()
            }).ToList();

            return Ok(sessionDtos);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting chat sessions");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Create a new chat session
    /// </summary>
    /// <param name="request">The request containing the session title</param>
    /// <returns>The created chat session</returns>
    /// <response code="200">Returns the created chat session</response>
    /// <response code="400">If the request is invalid</response>
    /// <response code="401">If the user is not authenticated</response>
    /// <response code="500">If there was an internal server error</response>
    [HttpPost("sessions")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status500InternalServerError)]
    public async Task<ActionResult<ChatSessionDto>> CreateChatSession([FromBody] CreateChatSessionRequest request)
    {
        try
        {
            var userId = GetUserId();
            var session = await _chatService.CreateChatSessionAsync(userId, request.Title);
            
            var sessionDto = new ChatSessionDto
            {
                Id = session.Id,
                Title = session.Title,
                CreatedAt = session.CreatedAt,
                UpdatedAt = session.UpdatedAt,
                Messages = new List<ChatMessageDto>()
            };

            return Ok(sessionDto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error creating chat session");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("sessions/{sessionId}")]
    public async Task<ActionResult<ChatSessionDto>> GetChatSession(Guid sessionId)
    {
        try
        {
            var userId = GetUserId();
            var session = await _chatService.GetChatSessionAsync(sessionId, userId);
            
            if (session == null)
            {
                return NotFound();
            }

            var sessionDto = new ChatSessionDto
            {
                Id = session.Id,
                Title = session.Title,
                CreatedAt = session.CreatedAt,
                UpdatedAt = session.UpdatedAt,
                Messages = session.Messages.Select(m => new ChatMessageDto
                {
                    Id = m.Id,
                    Role = m.Role,
                    Content = m.Content,
                    CreatedAt = m.CreatedAt,
                    Attachments = m.Attachments.Select(a => new ChatAttachmentDto
                    {
                        Id = a.Id,
                        FileName = a.FileName,
                        ContentType = a.ContentType,
                        FileSize = a.FileSize,
                        CreatedAt = a.CreatedAt
                    }).ToList()
                }).ToList()
            };

            return Ok(sessionDto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting chat session");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Update a chat session
    /// </summary>
    /// <param name="sessionId">The ID of the chat session to update</param>
    /// <param name="request">The request containing the updated session data</param>
    /// <returns>The updated chat session</returns>
    /// <response code="200">Returns the updated chat session</response>
    /// <response code="400">If the request is invalid</response>
    /// <response code="401">If the user is not authenticated</response>
    /// <response code="404">If the chat session is not found</response>
    /// <response code="500">If there was an internal server error</response>
    [HttpPut("sessions/{sessionId}")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status500InternalServerError)]
    public async Task<ActionResult<ChatSessionDto>> UpdateChatSession(Guid sessionId, [FromBody] UpdateChatSessionRequest request)
    {
        try
        {
            var userId = GetUserId();
            var session = await _chatService.UpdateChatSessionAsync(sessionId, userId, request.Title);
            
            if (session == null)
            {
                return NotFound();
            }

            var sessionDto = new ChatSessionDto
            {
                Id = session.Id,
                Title = session.Title,
                CreatedAt = session.CreatedAt,
                UpdatedAt = session.UpdatedAt,
                Messages = new List<ChatMessageDto>()
            };

            return Ok(sessionDto);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error updating chat session");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Delete a chat session
    /// </summary>
    /// <param name="sessionId">The ID of the chat session to delete</param>
    /// <returns>Success status</returns>
    /// <response code="204">If the session was successfully deleted</response>
    /// <response code="401">If the user is not authenticated</response>
    /// <response code="404">If the chat session is not found</response>
    /// <response code="500">If there was an internal server error</response>
    [HttpDelete("sessions/{sessionId}")]
    [ProducesResponseType(StatusCodes.Status204NoContent)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status500InternalServerError)]
    public async Task<ActionResult> DeleteChatSession(Guid sessionId)
    {
        try
        {
            var userId = GetUserId();
            var deleted = await _chatService.DeleteChatSessionAsync(sessionId, userId);
            
            if (!deleted)
            {
                return NotFound();
            }

            return NoContent();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error deleting chat session {SessionId}", sessionId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Send a message to a chat session and receive AI response via Server-Sent Events
    /// </summary>
    /// <param name="sessionId">The ID of the chat session</param>
    /// <param name="request">The message content and optional file attachments</param>
    /// <returns>Server-Sent Events stream with AI response</returns>
    /// <response code="200">Returns SSE stream with AI response</response>
    /// <response code="400">If the request is invalid</response>
    /// <response code="401">If the user is not authenticated</response>
    /// <response code="404">If the chat session is not found</response>
    /// <response code="500">If there was an internal server error</response>
    [HttpPost("sessions/{sessionId}/messages")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    [ProducesResponseType(StatusCodes.Status500InternalServerError)]
    public async Task<IActionResult> SendMessage(Guid sessionId, [FromForm] SendMessageRequest request)
    {
        try
        {
            var userId = GetUserId();
            var session = await _chatService.GetChatSessionAsync(sessionId, userId);
            
            if (session == null)
            {
                return NotFound();
            }

            // Process file uploads
            var attachments = new List<ChatAttachment>();
            if (request.Files?.Any() == true)
            {
                var uploadsPath = Path.Combine(_environment.ContentRootPath, "uploads");
                
                foreach (var file in request.Files)
                {
                    var filePath = await _chatService.ProcessFileAsync(file, uploadsPath);
                    attachments.Add(new ChatAttachment
                    {
                        FileName = file.FileName,
                        ContentType = file.ContentType,
                        FilePath = filePath,
                        FileSize = file.Length
                    });
                }
            }

            // Save user message
            await _chatService.SaveUserMessageAsync(sessionId, request.Content, attachments);

            // Set up SSE response
            Response.Headers["Content-Type"] = "text/event-stream";
            Response.Headers["Cache-Control"] = "no-cache";
            Response.Headers["Connection"] = "keep-alive";
            Response.Headers["Access-Control-Allow-Origin"] = "*";

            // Stream the AI response
            await foreach (var chunk in _chatService.StreamChatResponseAsync(sessionId, request.Content, HttpContext.RequestAborted))
            {
                var sseData = new ChatStreamResponse
                {
                    Type = "chunk",
                    Content = chunk
                };

                var json = JsonSerializer.Serialize(sseData);
                var sseMessage = $"data: {json}\n\n";
                var bytes = Encoding.UTF8.GetBytes(sseMessage);
                
                await Response.Body.WriteAsync(bytes, HttpContext.RequestAborted);
                await Response.Body.FlushAsync(HttpContext.RequestAborted);
            }

            // Send completion event
            var completeData = new ChatStreamResponse
            {
                Type = "complete",
                Content = ""
            };
            var completeJson = JsonSerializer.Serialize(completeData);
            var completeMessage = $"data: {completeJson}\n\n";
            var completeBytes = Encoding.UTF8.GetBytes(completeMessage);
            
            await Response.Body.WriteAsync(completeBytes, HttpContext.RequestAborted);
            await Response.Body.FlushAsync(HttpContext.RequestAborted);

            return new EmptyResult();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error sending message");
            
            // Send error event
            var errorData = new ChatStreamResponse
            {
                Type = "error",
                Error = ex.Message
            };
            var errorJson = JsonSerializer.Serialize(errorData);
            var errorMessage = $"data: {errorJson}\n\n";
            var errorBytes = Encoding.UTF8.GetBytes(errorMessage);
            
            await Response.Body.WriteAsync(errorBytes, HttpContext.RequestAborted);
            await Response.Body.FlushAsync(HttpContext.RequestAborted);

            return new EmptyResult();
        }
    }

    [HttpGet("attachments/{attachmentId}")]
    public IActionResult GetAttachment(Guid attachmentId)
    {
        try
        {
            // This would need to be implemented to serve files
            // For now, return NotFound
            return NotFound();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting attachment");
            return StatusCode(500, "Internal server error");
        }
    }
}
