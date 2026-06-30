using Azure.Identity;
using MailAgentService.Options;
using Microsoft.Extensions.Options;
using Microsoft.Graph;

namespace MailAgentService.Services;

public sealed class GraphClientFactory
{
    private readonly GraphOptions _graphOptions;

    public GraphClientFactory(IOptions<GraphOptions> graphOptions)
    {
        _graphOptions = graphOptions.Value;
    }

    public GraphServiceClient CreateAppClient()
    {
        var credential = new ClientSecretCredential(_graphOptions.TenantId, _graphOptions.ClientId, _graphOptions.ClientSecret);
        return new GraphServiceClient(credential);
    }
}

public sealed class SubscriptionStateStore
{
    private readonly Lock _lock = new();
    private string? _subscriptionId;
    private DateTimeOffset _expiration;

    public void Set(string subscriptionId, DateTimeOffset expiration)
    {
        lock (_lock)
        {
            _subscriptionId = subscriptionId;
            _expiration = expiration;
        }
    }

    public (string? SubscriptionId, DateTimeOffset Expiration) Get()
    {
        lock (_lock)
        {
            return (_subscriptionId, _expiration);
        }
    }
}