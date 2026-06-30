using MailAgentService.Options;
using Microsoft.Agents.AI;
using Microsoft.Extensions.Options;

namespace MailAgentService.Services;

public interface IMailAnalyzer
{
    Task<string> AnalyzeAsync(string subject, string bodyPreview, CancellationToken cancellationToken);
}

public sealed class MicrosoftAgentFrameworkMailAnalyzer : IMailAnalyzer
{
    private readonly AIAgent _agent;
    private readonly AgentOptions _agentOptions;
    private readonly ILogger<MicrosoftAgentFrameworkMailAnalyzer> _logger;

    public MicrosoftAgentFrameworkMailAnalyzer(
        IServiceProvider serviceProvider,
        IOptions<AgentOptions> agentOptions,
        ILogger<MicrosoftAgentFrameworkMailAnalyzer> logger)
    {
        _agent = serviceProvider.GetRequiredKeyedService<AIAgent>("mail-analyzer");
        _agentOptions = agentOptions.Value;
        _logger = logger;
    }

    public async Task<string> AnalyzeAsync(string subject, string bodyPreview, CancellationToken cancellationToken)
    {
        var safeBody = bodyPreview.Length > _agentOptions.MaxInputCharacters
            ? bodyPreview[.._agentOptions.MaxInputCharacters]
            : bodyPreview;

        var prompt = $"""
        {_agentOptions.SystemPrompt}

        INPUT MAIL
        Subject: {subject}
        Body:
        {safeBody}

        OUTPUT FORMAT
        1) Kurze Zusammenfassung (1-2 Sätze)
        2) Antwortvorschlag als E-Mail-Text
        3) Offene Rückfragen (falls nötig)
        """;

        _logger.LogInformation("Running MAF analyzer for incoming email subject '{Subject}'.", subject);
        var result = await _agent.RunAsync(prompt, cancellationToken: cancellationToken);
        return result?.ToString() ?? "Keine Analyseantwort vom Agent erhalten.";
    }
}