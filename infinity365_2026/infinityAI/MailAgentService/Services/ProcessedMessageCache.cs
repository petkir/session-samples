namespace MailAgentService.Services;

public sealed class ProcessedMessageCache
{
    private readonly Lock _lock = new();
    private readonly Dictionary<string, DateTimeOffset> _processed = new(StringComparer.OrdinalIgnoreCase);
    private readonly TimeSpan _ttl = TimeSpan.FromHours(12);

    public bool TryMarkAsNew(string messageId)
    {
        var now = DateTimeOffset.UtcNow;

        lock (_lock)
        {
            CleanupExpired(now);

            if (_processed.TryGetValue(messageId, out var seenAt) && now - seenAt < _ttl)
            {
                return false;
            }

            _processed[messageId] = now;
            return true;
        }
    }

    private void CleanupExpired(DateTimeOffset now)
    {
        var expired = _processed.Where(x => now - x.Value >= _ttl).Select(x => x.Key).ToArray();
        foreach (var key in expired)
        {
            _processed.Remove(key);
        }
    }
}