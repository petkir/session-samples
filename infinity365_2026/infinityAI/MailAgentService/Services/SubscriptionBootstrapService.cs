using MailAgentService.Options;
using Microsoft.Extensions.Options;
using Microsoft.Graph.Models;

namespace MailAgentService.Services;

public sealed class SubscriptionBootstrapService : IHostedService
{
    private readonly GraphClientFactory _graphClientFactory;
    private readonly SubscriptionStateStore _subscriptionStateStore;
    private readonly IOptions<GraphOptions> _graphOptions;
    private readonly ILogger<SubscriptionBootstrapService> _logger;

    public SubscriptionBootstrapService(
        GraphClientFactory graphClientFactory,
        SubscriptionStateStore subscriptionStateStore,
        IOptions<GraphOptions> graphOptions,
        ILogger<SubscriptionBootstrapService> logger)
    {
        _graphClientFactory = graphClientFactory;
        _subscriptionStateStore = subscriptionStateStore;
        _graphOptions = graphOptions;
        _logger = logger;
    }

    public async Task StartAsync(CancellationToken cancellationToken)
    {
        var options = _graphOptions.Value;
        var graphClient = _graphClientFactory.CreateAppClient();

        var expiration = DateTimeOffset.UtcNow.AddMinutes(options.SubscriptionDurationMinutes);

        var subscription = new Subscription
        {
            ChangeType = "created",
            NotificationUrl = options.NotificationUrl,
            LifecycleNotificationUrl = options.LifecycleNotificationUrl,
            Resource = $"/users/{options.MailboxUserId}/mailFolders('Inbox')/messages",
            ExpirationDateTime = expiration,
            ClientState = options.ClientState,
            LatestSupportedTlsVersion = "v1_2"
        };

        var created = await graphClient.Subscriptions.PostAsync(subscription, cancellationToken: cancellationToken);
        if (created?.Id is null || created.ExpirationDateTime is null)
        {
            throw new InvalidOperationException("Graph subscription creation failed. No subscription id or expiration returned.");
        }

        _subscriptionStateStore.Set(created.Id, created.ExpirationDateTime.Value);
        _logger.LogInformation("Created Graph subscription {SubscriptionId} expiring at {Expiration}.", created.Id, created.ExpirationDateTime.Value);
    }

    public Task StopAsync(CancellationToken cancellationToken)
        => Task.CompletedTask;
}