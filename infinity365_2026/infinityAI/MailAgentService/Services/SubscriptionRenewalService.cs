using MailAgentService.Options;
using Microsoft.Extensions.Options;
using Microsoft.Graph.Models;

namespace MailAgentService.Services;

public sealed class SubscriptionRenewalService : BackgroundService
{
    private readonly GraphClientFactory _graphClientFactory;
    private readonly SubscriptionStateStore _subscriptionStateStore;
    private readonly IOptions<GraphOptions> _graphOptions;
    private readonly ILogger<SubscriptionRenewalService> _logger;

    public SubscriptionRenewalService(
        GraphClientFactory graphClientFactory,
        SubscriptionStateStore subscriptionStateStore,
        IOptions<GraphOptions> graphOptions,
        ILogger<SubscriptionRenewalService> logger)
    {
        _graphClientFactory = graphClientFactory;
        _subscriptionStateStore = subscriptionStateStore;
        _graphOptions = graphOptions;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            var state = _subscriptionStateStore.Get();
            if (!string.IsNullOrWhiteSpace(state.SubscriptionId))
            {
                var renewBefore = TimeSpan.FromMinutes(_graphOptions.Value.SubscriptionRenewBeforeMinutes);
                if (DateTimeOffset.UtcNow >= state.Expiration - renewBefore)
                {
                    await RenewSubscriptionAsync(state.SubscriptionId!, stoppingToken);
                }
            }

            await Task.Delay(TimeSpan.FromMinutes(1), stoppingToken);
        }
    }

    private async Task RenewSubscriptionAsync(string subscriptionId, CancellationToken cancellationToken)
    {
        var graphClient = _graphClientFactory.CreateAppClient();
        var newExpiration = DateTimeOffset.UtcNow.AddMinutes(_graphOptions.Value.SubscriptionDurationMinutes);

        var updated = await graphClient.Subscriptions[subscriptionId]
            .PatchAsync(new Subscription { ExpirationDateTime = newExpiration }, cancellationToken: cancellationToken);

        var expiration = updated?.ExpirationDateTime ?? newExpiration;
        _subscriptionStateStore.Set(subscriptionId, expiration);
        _logger.LogInformation("Renewed Graph subscription {SubscriptionId} until {Expiration}.", subscriptionId, expiration);
    }
}