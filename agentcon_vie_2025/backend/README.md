# VoiceRAG Backend (C#)

This is the C# ASP.NET Core backend for the VoiceRAG application, implementing real-time voice interaction with RAG (Retrieval Augmented Generation) using Azure AI Search and Azure OpenAI GPT-4o Realtime API.

## Features

- **Real-time WebSocket communication** between client and Azure OpenAI Realtime API
- **RAG integration** with Azure AI Search for knowledge base queries
- **Custom function tools**:
  - `MyFields`: Get/set user profile fields
  - `MyTodos`: Manage todo items (add, list, complete)
  - `CurrentData`: Get current session and application state
- **Audio streaming** with GPT-4o Realtime API
- **Flexible authentication** supporting both API keys and Azure Managed Identity

## Prerequisites

- .NET 9.0 SDK or later
- Azure OpenAI resource with GPT-4o Realtime deployment
- Azure AI Search resource with an indexed knowledge base
- Visual Studio Code or Visual Studio 2022 (optional)

## Setup

### 1. Install Dependencies

```bash
cd backend
dotnet restore
```

### 2. Configure Environment

Copy `.env.template` to `.env` and fill in your Azure credentials:

```bash
cp .env.template .env
```

Edit `.env` with your actual Azure service endpoints and keys:

```env
AZURE_OPENAI_ENDPOINT=wss://<your-instance-name>.openai.azure.com
AZURE_OPENAI_REALTIME_DEPLOYMENT=gpt-4o-realtime-preview
AZURE_OPENAI_REALTIME_VOICE_CHOICE=alloy
AZURE_OPENAI_API_KEY=<your-api-key>

AZURE_SEARCH_ENDPOINT=https://<your-service-name>.search.windows.net
AZURE_SEARCH_INDEX=<your-index-name>
AZURE_SEARCH_API_KEY=<your-api-key>
```

**Using Managed Identity (Recommended for Production):**

Omit the `AZURE_OPENAI_API_KEY` and `AZURE_SEARCH_API_KEY` settings. The backend will automatically use:
- `AzureDeveloperCliCredential` when `AZURE_TENANT_ID` is set
- `DefaultAzureCredential` otherwise

### 3. Run the Backend

```bash
dotnet run
```

The backend will start on `http://localhost:8765`.

## API Endpoints

### WebSocket Endpoint

- **`/realtime`** - WebSocket endpoint for real-time audio communication with the Azure OpenAI GPT-4o Realtime API

### HTTP Endpoints

- **`GET /`** - Simple info page showing the backend is running

## Architecture

### Key Components

1. **`Program.cs`** - Application entry point, dependency injection, and middleware configuration
2. **`RTMiddleTier.cs`** - Core service managing WebSocket connections and message routing between client and Azure OpenAI
3. **`RagTools.cs`** - RAG implementation with Azure AI Search integration
4. **`CustomTools.cs`** - Custom function tools (MyFields, MyTodos, CurrentData)

### Message Flow

```
Client (Browser)
    ↓ WebSocket (/realtime)
RTMiddleTier
    ↓ WebSocket (Azure OpenAI API)
Azure OpenAI GPT-4o Realtime API
    ↓ Function calls
Tools (RAG, MyFields, MyTodos, CurrentData)
```

### Tool Implementations

#### RAG Tools

- **`search`** - Searches the Azure AI Search knowledge base and returns relevant passages
- **`report_grounding`** - Reports citation sources used for response grounding

#### Custom Tools

- **`get_my_fields`** - Get all user profile fields
- **`set_my_field`** - Set or update a user profile field
- **`get_todos`** - List all todo items
- **`add_todo`** - Add a new todo item
- **`complete_todo`** - Mark a todo as complete
- **`get_current_data`** - Get current application state

## Development

### Project Structure

```
backend/
├── Backend.csproj          # Project file with NuGet dependencies
├── Program.cs              # Application startup and configuration
├── .env                    # Environment configuration (not committed)
├── .env.template           # Template for environment configuration
├── Models/
│   └── ToolModels.cs       # Tool and result models
├── Services/
│   └── RTMiddleTier.cs     # WebSocket handler and message router
└── Tools/
    ├── RagTools.cs         # RAG integration with Azure AI Search
    └── CustomTools.cs      # Custom function tools
```

### Adding New Tools

To add a new tool:

1. Create a schema object defining the function signature
2. Implement the tool logic as a `Task<ToolResult>` method
3. Register the tool in the appropriate service (or create a new one)
4. Attach it to `RTMiddleTier` in `Program.cs`

Example:

```csharp
public void AttachToRTMiddleTier(RTMiddleTier rtMiddleTier)
{
    rtMiddleTier.Tools["my_tool"] = new Tool(
        Schema: GetMyToolSchema(),
        Target: ExecuteMyToolAsync
    );
}

private object GetMyToolSchema()
{
    return new
    {
        type = "function",
        name = "my_tool",
        description = "Description of what my tool does",
        parameters = new
        {
            type = "object",
            properties = new
            {
                param = new { type = "string", description = "Parameter description" }
            },
            required = new[] { "param" }
        }
    };
}

private async Task<ToolResult> ExecuteMyToolAsync(string argumentsJson)
{
    // Implementation
    return new ToolResult("result", ToolResultDirection.ToClient);
}
```

## Troubleshooting

### WebSocket Connection Issues

- Ensure the Azure OpenAI endpoint uses `wss://` (not `https://`)
- Check that the realtime deployment exists and is accessible
- Verify API keys or managed identity permissions

### Search Not Working

- Verify Azure AI Search endpoint and index name
- Ensure the index has the expected fields (`chunk_id`, `chunk`, `text_vector`, `title`)
- Check search API key or managed identity has read permissions

### Audio Not Playing

- Check browser console for WebSocket errors
- Verify the voice choice is valid (`alloy`, `echo`, `shimmer`)
- Ensure audio codec is supported by the browser

## References

- [Azure OpenAI GPT-4o Realtime API Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio)
- [Azure AI Search .NET SDK](https://learn.microsoft.com/en-us/dotnet/api/overview/azure/search.documents-readme)
- [Python VoiceRAG Sample](https://github.com/Azure-Samples/aisearch-openai-rag-audio)

## License

MIT
