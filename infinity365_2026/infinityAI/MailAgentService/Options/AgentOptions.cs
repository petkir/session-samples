namespace MailAgentService.Options;

public sealed class AgentOptions
{
    public const string SectionName = "Agent";

    public string SystemPrompt { get; set; } = "You are a helpful email assistant.";
    public int MaxInputCharacters { get; set; } = 12000;
    public string DraftSubjectPrefix { get; set; } = "Draft: ";
}