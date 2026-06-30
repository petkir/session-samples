using System.Text.Json;
using MailAgentService.Options;
using MailAgentService.Services;
using Microsoft.Agents.AI.Hosting;

var builder = WebApplication.CreateBuilder(args);

builder.Services.Configure<GraphOptions>(builder.Configuration.GetSection(GraphOptions.SectionName));
builder.Services.Configure<AgentOptions>(builder.Configuration.GetSection(AgentOptions.SectionName));

builder.Services.AddSingleton<GraphClientFactory>();
builder.Services.AddSingleton<NotificationQueue>();
builder.Services.AddSingleton<SubscriptionStateStore>();
builder.Services.AddSingleton<ProcessedMessageCache>();
builder.Services.AddScoped<MailDraftService>();
builder.Services.AddScoped<IMailAnalyzer, MicrosoftAgentFrameworkMailAnalyzer>();

builder.Services.AddHostedService<SubscriptionBootstrapService>();
builder.Services.AddHostedService<SubscriptionRenewalService>();
builder.Services.AddHostedService<GraphMailProcessorWorker>();

// MAF sample registration: keyed AI agent that will be resolved by the analyzer.
builder.AddAIAgent("mail-analyzer", instructions: builder.Configuration["Agent:SystemPrompt"] ?? "Analyze incoming mail and produce a clear reply draft.");

var app = builder.Build();

app.MapGet("/health", () => Results.Ok(new { status = "ok", service = "MailAgentService" }));

app.MapMethods("/api/graph/notifications", new[] { "GET", "POST" }, async (
    HttpContext httpContext,
    NotificationQueue queue,
    ILoggerFactory loggerFactory,
    CancellationToken cancellationToken) =>
{
    var logger = loggerFactory.CreateLogger("GraphWebhook");

    var validationToken = httpContext.Request.Query["validationToken"].ToString();
    if (!string.IsNullOrWhiteSpace(validationToken))
    {
        logger.LogInformation("Received Graph validation token handshake.");
        return Results.Text(validationToken, "text/plain");
    }

    using var document = await JsonDocument.ParseAsync(httpContext.Request.Body, cancellationToken: cancellationToken);
    var root = document.RootElement;

    if (!root.TryGetProperty("value", out var notifications) || notifications.ValueKind != JsonValueKind.Array)
    {
        logger.LogWarning("Graph notification payload did not contain a value array.");
        return Results.Accepted();
    }

    foreach (var item in notifications.EnumerateArray())
    {
        var subscriptionId = item.TryGetProperty("subscriptionId", out var sid) ? sid.GetString() : null;
        var resource = item.TryGetProperty("resource", out var res) ? res.GetString() : null;

        string? messageId = null;
        if (item.TryGetProperty("resourceData", out var resourceData)
            && resourceData.ValueKind == JsonValueKind.Object
            && resourceData.TryGetProperty("id", out var resourceDataId))
        {
            messageId = resourceDataId.GetString();
        }

        if (string.IsNullOrWhiteSpace(messageId) && !string.IsNullOrWhiteSpace(resource))
        {
            var parts = resource.Split('/', StringSplitOptions.RemoveEmptyEntries);
            messageId = parts.LastOrDefault();
        }

        if (!string.IsNullOrWhiteSpace(subscriptionId) && !string.IsNullOrWhiteSpace(messageId))
        {
            await queue.EnqueueAsync(new IncomingMailNotification(subscriptionId, messageId), cancellationToken);
        }
    }

    return Results.Accepted();
});

app.Run();
