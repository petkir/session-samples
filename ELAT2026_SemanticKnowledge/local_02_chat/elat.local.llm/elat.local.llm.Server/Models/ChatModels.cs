using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace elat.local.llm.Server.Models;

public class ChatSession
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();
    
    [Required]
    public string UserId { get; set; } = string.Empty;
    
    [Required]
    public string Title { get; set; } = string.Empty;
    
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
    
    public List<ChatMessage> Messages { get; set; } = new();
}

public class ChatMessage
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();
    
    [Required]
    public Guid ChatSessionId { get; set; }
    
    [ForeignKey(nameof(ChatSessionId))]
    public ChatSession ChatSession { get; set; } = null!;
    
    [Required]
    public string Role { get; set; } = string.Empty; // "user" or "assistant"
    
    [Required]
    public string Content { get; set; } = string.Empty;
    
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    
    public List<ChatAttachment> Attachments { get; set; } = new();
}

public class ChatAttachment
{
    [Key]
    public Guid Id { get; set; } = Guid.NewGuid();
    
    [Required]
    public Guid ChatMessageId { get; set; }
    
    [ForeignKey(nameof(ChatMessageId))]
    public ChatMessage ChatMessage { get; set; } = null!;
    
    [Required]
    public string FileName { get; set; } = string.Empty;
    
    [Required]
    public string ContentType { get; set; } = string.Empty;
    
    [Required]
    public string FilePath { get; set; } = string.Empty;
    
    public long FileSize { get; set; }
    
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
