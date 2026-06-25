namespace elat.local.llm.Server.DTOs;

public class ChatSessionDto
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public List<ChatMessageDto> Messages { get; set; } = new();
}

public class ChatMessageDto
{
    public Guid Id { get; set; }
    public string Role { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public DateTime CreatedAt { get; set; }
    public List<ChatAttachmentDto> Attachments { get; set; } = new();
}

public class ChatAttachmentDto
{
    public Guid Id { get; set; }
    public string FileName { get; set; } = string.Empty;
    public string ContentType { get; set; } = string.Empty;
    public long FileSize { get; set; }
    public DateTime CreatedAt { get; set; }
}

public class CreateChatSessionRequest
{
    public string Title { get; set; } = string.Empty;
}

public class UpdateChatSessionRequest
{
    public string Title { get; set; } = string.Empty;
}

public class SendMessageRequest
{
    public string Content { get; set; } = string.Empty;
    public List<IFormFile> Files { get; set; } = new();
}

public class ChatStreamResponse
{
    public string Type { get; set; } = string.Empty; // "message", "chunk", "complete", "error"
    public string Content { get; set; } = string.Empty;
    public Guid? MessageId { get; set; }
    public string? Error { get; set; }
}
