using System.Text.Json;
using Backend.Models;

namespace Backend.Tools;

public interface ICustomTools
{
    void AttachToRTMiddleTier(Services.RTMiddleTier rtMiddleTier);
}

public class CustomTools : ICustomTools
{
    private readonly Dictionary<string, string> _myFields = new();
    private readonly List<TodoItem> _todos = new();
    private readonly ILogger<CustomTools> _logger;

    public CustomTools(ILogger<CustomTools> logger)
    {
        _logger = logger;
        
        // Initialize with some sample data
        _myFields["name"] = "User";
        _myFields["location"] = "Vienna";
        _myFields["role"] = "Developer";
    }

    public void AttachToRTMiddleTier(Services.RTMiddleTier rtMiddleTier)
    {
        rtMiddleTier.Tools["get_my_fields"] = new Tool(
            Schema: GetMyFieldsSchema(),
            Target: GetMyFieldsAsync
        );

        rtMiddleTier.Tools["set_my_field"] = new Tool(
            Schema: SetMyFieldSchema(),
            Target: SetMyFieldAsync
        );

        rtMiddleTier.Tools["get_todos"] = new Tool(
            Schema: GetTodosSchema(),
            Target: GetTodosAsync
        );

        rtMiddleTier.Tools["add_todo"] = new Tool(
            Schema: AddTodoSchema(),
            Target: AddTodoAsync
        );

        rtMiddleTier.Tools["complete_todo"] = new Tool(
            Schema: CompleteTodoSchema(),
            Target: CompleteTodoAsync
        );

        rtMiddleTier.Tools["get_current_data"] = new Tool(
            Schema: GetCurrentDataSchema(),
            Target: GetCurrentDataAsync
        );

        _logger.LogInformation("Custom tools attached to RTMiddleTier");
    }

    #region MyFields Tools

    private object GetMyFieldsSchema()
    {
        return new
        {
            type = "function",
            name = "get_my_fields",
            description = "Retrieve all user profile fields and their values",
            parameters = new
            {
                type = "object",
                properties = new { },
                additionalProperties = false
            }
        };
    }

    private object SetMyFieldSchema()
    {
        return new
        {
            type = "function",
            name = "set_my_field",
            description = "Set or update a user profile field",
            parameters = new
            {
                type = "object",
                properties = new
                {
                    field_name = new
                    {
                        type = "string",
                        description = "Name of the field to set"
                    },
                    value = new
                    {
                        type = "string",
                        description = "Value to set for the field"
                    }
                },
                required = new[] { "field_name", "value" },
                additionalProperties = false
            }
        };
    }

    private Task<ToolResult> GetMyFieldsAsync(string argumentsJson)
    {
        _logger.LogInformation("Getting all user fields");
        var result = JsonSerializer.Serialize(new { fields = _myFields });
        return Task.FromResult(new ToolResult(result, ToolResultDirection.ToServer));
    }

    private Task<ToolResult> SetMyFieldAsync(string argumentsJson)
    {
        var arguments = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(argumentsJson);
        if (arguments == null ||
            !arguments.TryGetValue("field_name", out var fieldName) ||
            !arguments.TryGetValue("value", out var value))
        {
            return Task.FromResult(new ToolResult("Error: field_name and value are required"));
        }

        var field = fieldName.GetString();
        var val = value.GetString();

        if (string.IsNullOrEmpty(field) || string.IsNullOrEmpty(val))
        {
            return Task.FromResult(new ToolResult("Error: field_name and value cannot be empty"));
        }

        _myFields[field] = val;
        _logger.LogInformation("Set field {Field} to {Value}", field, val);

        var result = JsonSerializer.Serialize(new { success = true, field = field, value = val });
        return Task.FromResult(new ToolResult(result, ToolResultDirection.ToServer));
    }

    #endregion

    #region Todos Tools

    private object GetTodosSchema()
    {
        return new
        {
            type = "function",
            name = "get_todos",
            description = "Retrieve all todo items",
            parameters = new
            {
                type = "object",
                properties = new { },
                additionalProperties = false
            }
        };
    }

    private object AddTodoSchema()
    {
        return new
        {
            type = "function",
            name = "add_todo",
            description = "Add a new todo item",
            parameters = new
            {
                type = "object",
                properties = new
                {
                    title = new
                    {
                        type = "string",
                        description = "Title of the todo item"
                    },
                    description = new
                    {
                        type = "string",
                        description = "Optional description of the todo"
                    }
                },
                required = new[] { "title" },
                additionalProperties = false
            }
        };
    }

    private object CompleteTodoSchema()
    {
        return new
        {
            type = "function",
            name = "complete_todo",
            description = "Mark a todo item as complete",
            parameters = new
            {
                type = "object",
                properties = new
                {
                    id = new
                    {
                        type = "integer",
                        description = "ID of the todo item to complete"
                    }
                },
                required = new[] { "id" },
                additionalProperties = false
            }
        };
    }

    private Task<ToolResult> GetTodosAsync(string argumentsJson)
    {
        _logger.LogInformation("Getting all todos");
        var result = JsonSerializer.Serialize(new { todos = _todos });
        return Task.FromResult(new ToolResult(result, ToolResultDirection.ToServer));
    }

    private Task<ToolResult> AddTodoAsync(string argumentsJson)
    {
        var arguments = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(argumentsJson);
        if (arguments == null || !arguments.TryGetValue("title", out var titleElement))
        {
            return Task.FromResult(new ToolResult("Error: title is required"));
        }

        var title = titleElement.GetString();
        if (string.IsNullOrEmpty(title))
        {
            return Task.FromResult(new ToolResult("Error: title cannot be empty"));
        }

        var description = arguments.TryGetValue("description", out var descElement)
            ? descElement.GetString()
            : null;

        var todo = new TodoItem
        {
            Id = _todos.Count > 0 ? _todos.Max(t => t.Id) + 1 : 1,
            Title = title,
            Description = description,
            IsComplete = false,
            CreatedAt = DateTime.UtcNow
        };

        _todos.Add(todo);
        _logger.LogInformation("Added todo: {Title}", title);

        var result = JsonSerializer.Serialize(new { success = true, todo });
        return Task.FromResult(new ToolResult(result, ToolResultDirection.ToServer));
    }

    private Task<ToolResult> CompleteTodoAsync(string argumentsJson)
    {
        var arguments = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(argumentsJson);
        if (arguments == null || !arguments.TryGetValue("id", out var idElement))
        {
            return Task.FromResult(new ToolResult("Error: id is required"));
        }

        var id = idElement.GetInt32();
        var todo = _todos.FirstOrDefault(t => t.Id == id);

        if (todo == null)
        {
            return Task.FromResult(new ToolResult($"Error: Todo with id {id} not found"));
        }

        todo.IsComplete = true;
        _logger.LogInformation("Completed todo: {Title}", todo.Title);

        var result = JsonSerializer.Serialize(new { success = true, todo });
        return Task.FromResult(new ToolResult(result, ToolResultDirection.ToServer));
    }

    #endregion

    #region CurrentData Tool

    private object GetCurrentDataSchema()
    {
        return new
        {
            type = "function",
            name = "get_current_data",
            description = "Get current application state and session information",
            parameters = new
            {
                type = "object",
                properties = new { },
                additionalProperties = false
            }
        };
    }

    private Task<ToolResult> GetCurrentDataAsync(string argumentsJson)
    {
        _logger.LogInformation("Getting current data");

        var currentData = new
        {
            timestamp = DateTime.UtcNow,
            user_fields_count = _myFields.Count,
            todos_count = _todos.Count,
            todos_completed = _todos.Count(t => t.IsComplete),
            todos_pending = _todos.Count(t => !t.IsComplete),
            session_info = new
            {
                backend = "C# ASP.NET Core",
                version = "1.0.0"
            }
        };

        var result = JsonSerializer.Serialize(currentData);
        return Task.FromResult(new ToolResult(result, ToolResultDirection.ToServer));
    }

    #endregion
}

public class TodoItem
{
    public int Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public bool IsComplete { get; set; }
    public DateTime CreatedAt { get; set; }
}
