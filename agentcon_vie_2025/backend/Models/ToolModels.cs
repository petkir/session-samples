namespace Backend.Models;

public enum ToolResultDirection
{
    ToServer,
    ToClient
}

public record ToolResult(
    string Result,
    ToolResultDirection Direction = ToolResultDirection.ToServer
);

public record Tool(
    object Schema,
    Func<string, Task<ToolResult>> Target
);

public record RTToolCall(
    string CallId,
    string PreviousId
);
