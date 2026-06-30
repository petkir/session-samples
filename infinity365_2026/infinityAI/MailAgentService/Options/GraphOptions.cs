namespace MailAgentService.Options;

public sealed class GraphOptions
{
    public const string SectionName = "Graph";

    public string TenantId { get; set; } = string.Empty;
    public string ClientId { get; set; } = string.Empty;
    public string ClientSecret { get; set; } = string.Empty;
    public string MailboxUserId { get; set; } = string.Empty;
    public string NotificationUrl { get; set; } = string.Empty;
    public string LifecycleNotificationUrl { get; set; } = string.Empty;
    public string ClientState { get; set; } = string.Empty;
    public int SubscriptionRenewBeforeMinutes { get; set; } = 10;
    public int SubscriptionDurationMinutes { get; set; } = 30;
}