namespace MailAgentService.Services;

public sealed class GraphMailProcessorWorker : BackgroundService
{
    private readonly IServiceScopeFactory _scopeFactory;
    private readonly NotificationQueue _notificationQueue;
    private readonly GraphClientFactory _graphClientFactory;
    private readonly ProcessedMessageCache _processedMessageCache;
    private readonly ILogger<GraphMailProcessorWorker> _logger;

    public GraphMailProcessorWorker(
        IServiceScopeFactory scopeFactory,
        NotificationQueue notificationQueue,
        GraphClientFactory graphClientFactory,
        ProcessedMessageCache processedMessageCache,
        ILogger<GraphMailProcessorWorker> logger)
    {
        _scopeFactory = scopeFactory;
        _notificationQueue = notificationQueue;
        _graphClientFactory = graphClientFactory;
        _processedMessageCache = processedMessageCache;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await foreach (var notification in _notificationQueue.DequeueAllAsync(stoppingToken))
        {
            try
            {
                if (!_processedMessageCache.TryMarkAsNew(notification.MessageId))
                {
                    _logger.LogInformation("Message {MessageId} already processed recently. Skipping.", notification.MessageId);
                    continue;
                }

                await ProcessMessageAsync(notification.MessageId, stoppingToken);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to process message notification for {MessageId}.", notification.MessageId);
            }
        }
    }

    private async Task ProcessMessageAsync(string messageId, CancellationToken cancellationToken)
    {
        using var scope = _scopeFactory.CreateScope();
        var analyzer = scope.ServiceProvider.GetRequiredService<IMailAnalyzer>();
        var draftService = scope.ServiceProvider.GetRequiredService<MailDraftService>();
        var graphClient = _graphClientFactory.CreateAppClient();

        var mailboxUserId = scope.ServiceProvider
            .GetRequiredService<IConfiguration>()
            .GetValue<string>("Graph:MailboxUserId")
            ?? throw new InvalidOperationException("Graph:MailboxUserId missing.");

        var message = await graphClient.Users[mailboxUserId].Messages[messageId].GetAsync(cancellationToken: cancellationToken);
        if (message is null)
        {
            _logger.LogWarning("Graph message {MessageId} not found.", messageId);
            return;
        }

        var subject = message.Subject ?? "(ohne Betreff)";
        var bodyPreview = message.BodyPreview ?? string.Empty;
        var analysisResult = await analyzer.AnalyzeAsync(subject, bodyPreview, cancellationToken);
        await draftService.CreateDraftAsync(message, analysisResult, cancellationToken);
    }
}