using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.Identity.Web;
using Microsoft.EntityFrameworkCore;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Memory;
using Qdrant.Client;
using elat.local.llm.Server.Data;
using elat.local.llm.Server.Services;
using elat.local.llm.Server.Plugins;
using elat.local.llm.Server.Models;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllers();

// Configure Entity Framework
builder.Services.AddDbContext<ChatDbContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("DefaultConnection") ?? "Data Source=chat.db"));

// Configure Authentication with Entra ID
builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddMicrosoftIdentityWebApi(builder.Configuration.GetSection("AzureAd"));

// Add authorization
builder.Services.AddAuthorization();

// Configure Semantic Kernel with Ollama
#pragma warning disable SKEXP0070 // Type is for evaluation purposes only
var kernelBuilder = builder.Services.AddKernel();

kernelBuilder.Plugins.AddFromType<DateTimePlugin>();

kernelBuilder.AddOllamaChatCompletion(
    modelId: builder.Configuration["Ollama:ModelId"] ?? "llama3.2",
    endpoint: new Uri(builder.Configuration["Ollama:Endpoint"] ?? "http://localhost:11434"));

kernelBuilder.AddOllamaTextEmbeddingGeneration(
    modelId: builder.Configuration["Ollama:EmbeddingModel"] ?? "all-minilm",
    endpoint: new Uri(builder.Configuration["Ollama:Endpoint"] ?? "http://localhost:11434"));
#pragma warning restore SKEXP0070

// Configure Qdrant options
builder.Services.Configure<QdrantOptions>(builder.Configuration.GetSection(QdrantOptions.SectionName));

// Configure Qdrant client - use grpcPort explicitly to avoid connection issues
builder.Services.AddSingleton<QdrantClient>(serviceProvider =>
{
    var configuration = serviceProvider.GetRequiredService<IConfiguration>();
    var endpoint = configuration["Qdrant:Endpoint"] ?? "http://localhost:6333";
    // Defensive: allow full URLs, strip path/query/fragment, and pass discrete values
    Uri uri;
    try
    {
        uri = new Uri(endpoint);
    }
    catch
    {
        // If a bare host was provided (e.g., "localhost"), default port and scheme
        uri = new Uri("http://" + endpoint.Trim());
    }

    var https = string.Equals(uri.Scheme, "https", StringComparison.OrdinalIgnoreCase);
    var host = uri.Host;
    
    // Qdrant runs gRPC on port 6334 by default
    // The QdrantClient constructor uses 'port' for gRPC port
    return new QdrantClient(
        host: host, 
        port: 6334,
        https: https, 
        apiKey: configuration["Qdrant:ApiKey"]);
});

// Configure Semantic Memory with Qdrant

#pragma warning disable SKEXP0001, SKEXP0010, SKEXP0020, SKEXP0070 // Type is for evaluation purposes only
builder.Services.AddSingleton<ISemanticTextMemory>(serviceProvider =>
{
    var configuration = serviceProvider.GetRequiredService<IConfiguration>();
    var qdrantEndpoint = configuration["Qdrant:Endpoint"] ?? "http://localhost:6333";
    var ollamaEndpoint = configuration["Ollama:Endpoint"] ?? "http://localhost:11434";
    var embeddingModel = configuration["Ollama:EmbeddingModel"] ?? "all-minilm";
    
    // Normalize Qdrant endpoint for Semantic Kernel store as base URL without path
    Uri qdrantUri;
    try
    {
        qdrantUri = new Uri(qdrantEndpoint);
    }
    catch
    {
        qdrantUri = new Uri("http://" + qdrantEndpoint.Trim());
    }

    var normalizedQdrantBase = $"{qdrantUri.Scheme}://{qdrantUri.Host}:{(qdrantUri.IsDefaultPort ? (qdrantUri.Scheme == "https" ? 6334 : 6333) : qdrantUri.Port)}";

    // Determine embedding vector size based on model
    var vectorSize = embeddingModel.Contains("minilm", StringComparison.OrdinalIgnoreCase) ? 384 : 768;

    // Build memory with Qdrant store and Ollama embeddings using Kernel's embedding service
    var memoryStore = new QdrantMemoryStore(normalizedQdrantBase, vectorSize);
    var kernel = serviceProvider.GetRequiredService<Kernel>();
    
    // Get the embedding generation service from the kernel which was configured earlier
    var embeddingGenerator = kernel.GetRequiredService<Microsoft.SemanticKernel.Embeddings.ITextEmbeddingGenerationService>();
    
    return new MemoryBuilder()
        .WithMemoryStore(memoryStore)
        .WithTextEmbeddingGeneration(embeddingGenerator)
        .Build();
});
#pragma warning restore SKEXP0001, SKEXP0010, SKEXP0020, SKEXP0070

// Register services
builder.Services.AddScoped<IChatService, ChatService>();
builder.Services.AddScoped<IQdrantService, QdrantService>();
builder.Services.AddScoped<IKnowledgeBaseService, KnowledgeBaseService>();

// Configure CORS
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins("https://localhost:54375", "http://localhost:5173")
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});

// Learn more about configuring OpenAPI at https://aka.ms/aspnet/openapi
builder.Services.AddOpenApi();

// Add Swagger services
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo
    {
        Title = "elat Local LLM Chat API",
        Version = "v1",
        Description = "A modern chat application API built with .NET 9 that provides chat functionality with AI streaming using Ollama LLM via Semantic Kernel.",
        Contact = new Microsoft.OpenApi.Models.OpenApiContact
        {
            Name = "API Support",
            Email = "support@example.com"
        },
        License = new Microsoft.OpenApi.Models.OpenApiLicense
        {
            Name = "MIT",
            Url = new Uri("https://opensource.org/licenses/MIT")
        }
    });

    // Include XML documentation
    var xmlFile = $"{System.Reflection.Assembly.GetExecutingAssembly().GetName().Name}.xml";
    var xmlPath = Path.Combine(AppContext.BaseDirectory, xmlFile);
    if (File.Exists(xmlPath))
    {
        options.IncludeXmlComments(xmlPath);
    }

    // Configure JWT authentication for Swagger
    options.AddSecurityDefinition("Bearer", new Microsoft.OpenApi.Models.OpenApiSecurityScheme
    {
        Description = "JWT Authorization header using the Bearer scheme. Enter 'Bearer' [space] and then your token in the text input below.",
        Name = "Authorization",
        In = Microsoft.OpenApi.Models.ParameterLocation.Header,
        Type = Microsoft.OpenApi.Models.SecuritySchemeType.ApiKey,
        Scheme = "Bearer"
    });

    options.AddSecurityRequirement(new Microsoft.OpenApi.Models.OpenApiSecurityRequirement
    {
        {
            new Microsoft.OpenApi.Models.OpenApiSecurityScheme
            {
                Reference = new Microsoft.OpenApi.Models.OpenApiReference
                {
                    Type = Microsoft.OpenApi.Models.ReferenceType.SecurityScheme,
                    Id = "Bearer"
                }
            },
            new string[] {}
        }
    });
});

var app = builder.Build();

// Ensure database is created
using (var scope = app.Services.CreateScope())
{
    var context = scope.ServiceProvider.GetRequiredService<ChatDbContext>();
    context.Database.EnsureCreated();
    
    // Initialize Qdrant knowledge base
    try
    {
        var knowledgeBaseService = scope.ServiceProvider.GetRequiredService<IKnowledgeBaseService>();
        await knowledgeBaseService.InitializeAsync();
    }
    catch (Exception ex)
    {
        var logger = scope.ServiceProvider.GetRequiredService<ILogger<Program>>();
        logger.LogWarning(ex, "Failed to initialize Qdrant knowledge base. Make sure Qdrant is running.");
    }
}

app.UseDefaultFiles();
app.MapStaticAssets();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.UseSwagger();
    app.UseSwaggerUI(options =>
    {
        options.SwaggerEndpoint("/swagger/v1/swagger.json", "elat Local LLM Chat API v1");
        options.RoutePrefix = "swagger";
        options.DocumentTitle = "elat Local LLM Chat API";
        options.DocExpansion(Swashbuckle.AspNetCore.SwaggerUI.DocExpansion.List);
        options.DisplayRequestDuration();
    });
}

app.UseHttpsRedirection();

app.UseCors();

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.MapFallbackToFile("/index.html");

app.Run();

// Make the implicit Program class public for testing
public partial class Program { }
