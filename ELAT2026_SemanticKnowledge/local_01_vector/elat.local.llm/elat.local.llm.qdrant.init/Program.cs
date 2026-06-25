using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Qdrant.Client;
using elat.local.llm.qdrant.init.Services;
using elat.local.llm.qdrant.init.Models;

#pragma warning disable SKEXP0001

namespace elat.local.llm.qdrant.init;

class Program
{
    static async Task Main(string[] args)
    {
        // Build configuration
        var configuration = new ConfigurationBuilder()
            .SetBasePath(Directory.GetCurrentDirectory())
            .AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
            .Build();

        // Setup dependency injection
        var serviceCollection = new ServiceCollection();
        ConfigureServices(serviceCollection, configuration);
        var serviceProvider = serviceCollection.BuildServiceProvider();

        // Get logger
        var logger = serviceProvider.GetRequiredService<ILogger<Program>>();

        try
        {
            logger.LogInformation("🚀 Starting Qdrant Document Initialization");
            logger.LogInformation("=========================================");

            // Get services
            var qdrantService = serviceProvider.GetRequiredService<IQdrantInitService>();
            var documentService = serviceProvider.GetRequiredService<IDocumentProcessingService>();

            // Check if user wants to upload documents
            Console.WriteLine();
            Console.Write("Do you want to upload sample documents to Qdrant? (y/N): ");
            var response = Console.ReadLine();
            
            if (response?.ToLowerInvariant() != "y" && response?.ToLowerInvariant() != "yes")
            {
                logger.LogInformation("Skipping document upload as requested by user");
                return;
            }

            // Initialize Qdrant collection
            logger.LogInformation("Initializing Qdrant collection...");
            await qdrantService.InitializeAsync();

            // Process sample documents from JSON
            logger.LogInformation("Loading sample documents from JSON...");
            var sampleDocuments = await documentService.LoadSampleDocumentsAsync("sample-documents.json");
            
            foreach (var doc in sampleDocuments)
            {
                await qdrantService.AddDocumentAsync(doc.Content, doc.FileName, doc.Category);
            }

            // Process PDF files from sample_files folder
            var sampleFilesPath = configuration["SampleFilesPath"] ?? Path.Combine("..", "elat.local.llm", "sample_files");
            if (Directory.Exists(sampleFilesPath))
            {
                logger.LogInformation("Processing PDF files from sample_files folder...");
                var pdfFiles = Directory.GetFiles(sampleFilesPath, "*.pdf");
                
                foreach (var pdfFile in pdfFiles)
                {
                    try
                    {
                        var content = await documentService.ExtractTextFromPdfAsync(pdfFile);
                        if (!string.IsNullOrWhiteSpace(content))
                        {
                            var fileName = Path.GetFileName(pdfFile);
                            await qdrantService.AddDocumentAsync(content, fileName, "PDF Document");
                        }
                        else
                        {
                            logger.LogWarning("PDF file appears to be empty or unreadable: {FileName}", Path.GetFileName(pdfFile));
                        }
                    }
                    catch (Exception ex)
                    {
                        logger.LogError(ex, "Failed to process PDF file: {FileName}", Path.GetFileName(pdfFile));
                    }
                }
            }
            else
            {
                logger.LogWarning("Sample files directory not found: {Path}", sampleFilesPath);
            }

            logger.LogInformation("✅ Document initialization completed successfully!");
            Console.WriteLine();
            Console.WriteLine("🎉 All documents have been uploaded to Qdrant!");
            Console.WriteLine("You can now start the main application to use the knowledge base.");
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "❌ Failed to initialize documents");
            Console.WriteLine($"Error: {ex.Message}");
            Environment.Exit(1);
        }
    }

    private static void ConfigureServices(IServiceCollection services, IConfiguration configuration)
    {
        // Add logging
        services.AddLogging(builder =>
        {
            builder.AddConfiguration(configuration.GetSection("Logging"));
            builder.AddConsole();
        });

        // Shared settings and single Ollama client + vector size probe
        var ollamaEndpointGlobal = configuration["Ollama:Endpoint"] ?? "http://localhost:11434";
        var embeddingModelGlobal = configuration["Ollama:EmbeddingModel"] ?? "nomic-embed-text:latest";
        var recreateOnInitGlobal = bool.TryParse(configuration["Qdrant:RecreateCollectionOnInit"], out var tmp) && tmp;
        var ollamaClientGlobal = new elat.local.llm.qdrant.init.Services.OllamaEmbeddingClient(new Uri(ollamaEndpointGlobal));
        var vectorSizeGlobal = ollamaClientGlobal.GenerateAsync("dimension probe", embeddingModelGlobal).GetAwaiter().GetResult().Length;
        if (vectorSizeGlobal <= 0)
        {
            // Fallback heuristics based on common embedding models
            if (embeddingModelGlobal.Contains("nomic-embed-text", StringComparison.OrdinalIgnoreCase))
            {
                vectorSizeGlobal = 768;
            }
            else if (embeddingModelGlobal.Contains("minilm", StringComparison.OrdinalIgnoreCase))
            {
                vectorSizeGlobal = 384;
            }
            else if (embeddingModelGlobal.Contains("mxbai", StringComparison.OrdinalIgnoreCase) || embeddingModelGlobal.Contains("e5", StringComparison.OrdinalIgnoreCase))
            {
                vectorSizeGlobal = 1024;
            }
            else
            {
                vectorSizeGlobal = 768; // reasonable default
            }
        }

        services.AddSingleton<elat.local.llm.qdrant.init.Services.IOllamaEmbeddingClient>(sp => ollamaClientGlobal);

        // Configure Qdrant client
        services.AddSingleton<QdrantClient>(serviceProvider =>
        {
            var endpoint = configuration["Qdrant:Endpoint"] ?? "http://localhost:6333";
            // Parse endpoint (usually REST on 6333) but select gRPC port 6334
            Uri uri;
            try { uri = new Uri(endpoint); }
            catch { uri = new Uri("http://" + endpoint.Trim()); }
            var host = uri.Host;
            var configuredGrpc = configuration["Qdrant:GrpcPort"];
            int port;
            if (!string.IsNullOrWhiteSpace(configuredGrpc) && int.TryParse(configuredGrpc, out var grpcPort))
            {
                port = grpcPort;
            }
            else if (uri.IsDefaultPort)
            {
                port = 6334; // default gRPC port
            }
            else
            {
                port = uri.Port == 6333 ? 6334 : uri.Port; // map REST 6333 -> gRPC 6334
            }
            var useHttps = false; // most local Qdrant gRPC setups are plaintext
            return new QdrantClient(host: host, port: port, https: useHttps, apiKey: configuration["Qdrant:ApiKey"]);
        });
        
        // Configure Semantic Memory with Ollama embeddings and Qdrant
        #pragma warning disable SKEXP0001, SKEXP0020, SKEXP0070 // Type is for evaluation purposes only
        services.AddSingleton<ISemanticTextMemory>(serviceProvider =>
        {
            var qdrantEndpoint = configuration["Qdrant:Endpoint"] ?? "http://localhost:6333";

            // Normalize Qdrant endpoint for MemoryStore base URL without path
            Uri qUri;
            try { qUri = new Uri(qdrantEndpoint); } catch { qUri = new Uri("http://" + qdrantEndpoint.Trim()); }
            var baseQdrant = $"{qUri.Scheme}://{qUri.Host}:{(qUri.IsDefaultPort ? (qUri.Scheme == "https" ? 6334 : 6333) : qUri.Port)}";

            var ollamaClient = serviceProvider.GetRequiredService<elat.local.llm.qdrant.init.Services.IOllamaEmbeddingClient>();
            var textEmbeddingService = new elat.local.llm.qdrant.init.Services.SkOllamaEmbeddingService(
                ollamaClient, embeddingModelGlobal);

            return new MemoryBuilder()
                .WithQdrantMemoryStore(baseQdrant, vectorSizeGlobal)
                .WithTextEmbeddingGeneration(textEmbeddingService)
                .Build();
        });
        #pragma warning restore SKEXP0001, SKEXP0020, SKEXP0070

        // Add services
        services.AddScoped<IQdrantInitService>(sp =>
        {
            var client = sp.GetRequiredService<QdrantClient>();
            var logger = sp.GetRequiredService<ILogger<QdrantInitService>>();
            var memory = sp.GetRequiredService<ISemanticTextMemory>();
            var embedClient = sp.GetRequiredService<elat.local.llm.qdrant.init.Services.IOllamaEmbeddingClient>();
            return new QdrantInitService(client, logger, memory, embedClient, embeddingModelGlobal, vectorSizeGlobal, recreateOnInitGlobal);
        });
        services.AddScoped<IDocumentProcessingService, DocumentProcessingService>();
    }
}
