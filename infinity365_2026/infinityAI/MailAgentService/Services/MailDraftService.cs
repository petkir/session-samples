using MailAgentService.Options;
using Microsoft.Extensions.Options;
using Microsoft.Graph.Models;

namespace MailAgentService.Services;

public sealed class MailDraftService
{
    private readonly GraphClientFactory _graphClientFactory;
    private readonly IOptions<GraphOptions> _graphOptions;
    private readonly IOptions<AgentOptions> _agentOptions;
    private readonly ILogger<MailDraftService> _logger;

    public MailDraftService(
        GraphClientFactory graphClientFactory,
        IOptions<GraphOptions> graphOptions,
        IOptions<AgentOptions> agentOptions,
        ILogger<MailDraftService> logger)
    {
        _graphClientFactory = graphClientFactory;
        _graphOptions = graphOptions;
        _agentOptions = agentOptions;
        _logger = logger;
    }

    public async Task CreateDraftAsync(Message sourceMessage, string analysisResult, CancellationToken cancellationToken)
    {
        var mailboxUserId = _graphOptions.Value.MailboxUserId;
        var graphClient = _graphClientFactory.CreateAppClient();

        var subject = sourceMessage.Subject ?? "(ohne Betreff)";
        var senderAddress = sourceMessage.From?.EmailAddress?.Address;
        if (string.IsNullOrWhiteSpace(senderAddress))
        {
            _logger.LogWarning("Skipping draft creation because source message has no sender address.");
            return;
        }

        var draft = new Message
        {
            Subject = _agentOptions.Value.DraftSubjectPrefix + subject,
            Body = new ItemBody
            {
                ContentType = BodyType.Text,
                Content = analysisResult
            },
            ToRecipients =
            [
                new Recipient
                {
                    EmailAddress = new EmailAddress
                    {
                        Address = senderAddress
                    }
                }
            ]
        };

        await graphClient.Users[mailboxUserId].Messages.PostAsync(draft, cancellationToken: cancellationToken);
        _logger.LogInformation("Created draft for source message '{MessageId}'.", sourceMessage.Id);
    }
}