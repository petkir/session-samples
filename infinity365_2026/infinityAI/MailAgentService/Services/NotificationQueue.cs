using System.Threading.Channels;

namespace MailAgentService.Services;

public readonly record struct IncomingMailNotification(string SubscriptionId, string MessageId);

public sealed class NotificationQueue
{
    private readonly Channel<IncomingMailNotification> _channel = Channel.CreateUnbounded<IncomingMailNotification>();

    public ValueTask EnqueueAsync(IncomingMailNotification notification, CancellationToken cancellationToken)
        => _channel.Writer.WriteAsync(notification, cancellationToken);

    public IAsyncEnumerable<IncomingMailNotification> DequeueAllAsync(CancellationToken cancellationToken)
        => _channel.Reader.ReadAllAsync(cancellationToken);
}