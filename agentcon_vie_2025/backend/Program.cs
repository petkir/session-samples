using Azure.Core;
using Azure.Identity;
using System.Net.WebSockets;
using Backend.Services;
using Backend.Tools;

var builder = WebApplication.CreateBuilder(args);

// Load environment variables from .env file in development
if (!builder.Environment.IsProduction())
{
    var root = Directory.GetCurrentDirectory();
    var envPath = Path.Combine(root, ".env");
    if (File.Exists(envPath))
    {
        foreach (var line in File.ReadAllLines(envPath))
        {
            if (string.IsNullOrWhiteSpace(line) || line.StartsWith('#'))
                continue;

            var parts = line.Split('=', 2, StringSplitOptions.TrimEntries);
            if (parts.Length == 2)
            {
                Environment.SetEnvironmentVariable(parts[0], parts[1]);
            }
        }
    }
}

// Configure services
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

// Setup authentication credentials
var llmKey = Environment.GetEnvironmentVariable("AZURE_OPENAI_API_KEY");
var searchKey = Environment.GetEnvironmentVariable("AZURE_SEARCH_API_KEY");

TokenCredential? credential = null;
if (string.IsNullOrEmpty(llmKey) || string.IsNullOrEmpty(searchKey))
{
    var tenantId = Environment.GetEnvironmentVariable("AZURE_TENANT_ID");
    if (!string.IsNullOrEmpty(tenantId))
    {
        Console.WriteLine($"Using AzureDeveloperCliCredential with tenant_id {tenantId}");
        credential = new AzureDeveloperCliCredential(new AzureDeveloperCliCredentialOptions
        {
            TenantId = tenantId
        });
    }
    else
    {
        Console.WriteLine("Using DefaultAzureCredential");
        credential = new DefaultAzureCredential();
    }
}

// Register RTMiddleTier
builder.Services.AddSingleton(sp =>
{
    var logger = sp.GetRequiredService<ILogger<RTMiddleTier>>();
    var endpoint = Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT")
        ?? throw new InvalidOperationException("AZURE_OPENAI_ENDPOINT not set");
    var deployment = Environment.GetEnvironmentVariable("AZURE_OPENAI_REALTIME_DEPLOYMENT")
        ?? throw new InvalidOperationException("AZURE_OPENAI_REALTIME_DEPLOYMENT not set");
    var voiceChoice = Environment.GetEnvironmentVariable("AZURE_OPENAI_REALTIME_VOICE_CHOICE") ?? "alloy";

    var rtMiddleTier = new RTMiddleTier(
        endpoint: endpoint,
        deployment: deployment,
        credentials: llmKey != null ? llmKey : credential!,
        voiceChoice: voiceChoice,
        logger: logger
    );

    // Set system message
    rtMiddleTier.SystemMessage = @"
        You are a helpful assistant. Only answer questions based on information you searched in the knowledge base, accessible with the 'search' tool. 
        The user is listening to answers with audio, so it's *super* important that answers are as short as possible, a single sentence if at all possible. 
        Never read file names or source names or keys out loud. 
        Always use the following step-by-step instructions to respond: 
        1. Always use the 'search' tool to check the knowledge base before answering a question. 
        2. Always use the 'report_grounding' tool to report the source of information from the knowledge base. 
        3. Produce an answer that's as short as possible. If the answer isn't in the knowledge base, say you don't know.
    ".Trim();

    return rtMiddleTier;
});

// Register RAG tools
builder.Services.AddSingleton<IRagTools>(sp =>
{
    var logger = sp.GetRequiredService<ILogger<RagTools>>();
    var searchEndpoint = Environment.GetEnvironmentVariable("AZURE_SEARCH_ENDPOINT")
        ?? throw new InvalidOperationException("AZURE_SEARCH_ENDPOINT not set");
    var searchIndex = Environment.GetEnvironmentVariable("AZURE_SEARCH_INDEX")
        ?? throw new InvalidOperationException("AZURE_SEARCH_INDEX not set");
    var semanticConfiguration = Environment.GetEnvironmentVariable("AZURE_SEARCH_SEMANTIC_CONFIGURATION");
    var identifierField = Environment.GetEnvironmentVariable("AZURE_SEARCH_IDENTIFIER_FIELD") ?? "chunk_id";
    var contentField = Environment.GetEnvironmentVariable("AZURE_SEARCH_CONTENT_FIELD") ?? "chunk";
    var embeddingField = Environment.GetEnvironmentVariable("AZURE_SEARCH_EMBEDDING_FIELD") ?? "text_vector";
    var titleField = Environment.GetEnvironmentVariable("AZURE_SEARCH_TITLE_FIELD") ?? "title";
    var useVectorQuery = Environment.GetEnvironmentVariable("AZURE_SEARCH_USE_VECTOR_QUERY")?.ToLower() != "false";

    return new RagTools(
        credentials: searchKey != null ? searchKey : credential!,
        searchEndpoint: searchEndpoint,
        searchIndex: searchIndex,
        semanticConfiguration: semanticConfiguration,
        identifierField: identifierField,
        contentField: contentField,
        embeddingField: embeddingField,
        titleField: titleField,
        useVectorQuery: useVectorQuery,
        logger: logger
    );
});

// Register custom tools
builder.Services.AddSingleton<ICustomTools, CustomTools>();

var app = builder.Build();

app.UseCors();

// Configure WebSocket options
var webSocketOptions = new WebSocketOptions
{
    KeepAliveInterval = TimeSpan.FromMinutes(2)
};
app.UseWebSockets(webSocketOptions);

// Attach RTMiddleTier to handle /realtime endpoint
var rtMiddleTier = app.Services.GetRequiredService<RTMiddleTier>();
var ragTools = app.Services.GetRequiredService<IRagTools>();
var customTools = app.Services.GetRequiredService<ICustomTools>();

// Attach RAG tools
ragTools.AttachToRTMiddleTier(rtMiddleTier);

// Attach custom tools
customTools.AttachToRTMiddleTier(rtMiddleTier);

app.Map("/realtime", async context =>
{
    if (context.WebSockets.IsWebSocketRequest)
    {
        using var websocket = await context.WebSockets.AcceptWebSocketAsync();
        await rtMiddleTier.HandleWebSocketAsync(websocket);
    }
    else
    {
        context.Response.StatusCode = StatusCodes.Status400BadRequest;
    }
});

// Serve static files for the frontend
var staticPath = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot");
if (Directory.Exists(staticPath))
{
    app.UseDefaultFiles();
    app.UseStaticFiles();
}

app.MapGet("/", () => Results.Content(@"
<!DOCTYPE html>
<html>
<head><title>VoiceRAG Backend</title></head>
<body>
    <h1>VoiceRAG Backend</h1>
    <p>WebSocket endpoint: /realtime</p>
</body>
</html>
", "text/html"));

app.Run("http://localhost:8765");
