using Azure.AI.Projects;
using Azure.AI.Projects.Agents;
using Azure.Identity;
using Microsoft.Agents.AI;

if (args.Length > 0 && args[0].Equals("--help", StringComparison.OrdinalIgnoreCase))
{
	PrintHelp();
	return;
}

var mode = args.Length > 0 ? args[0].Trim().ToLowerInvariant() : "maf-chat";
var config = AppConfig.FromEnvironment();

switch (mode)
{
	case "maf-chat":
		await RunMafChatAsync(config);
		break;
	case "foundryiq":
		await RunFoundryIqAsync(config);
		break;
	default:
		Console.Error.WriteLine($"Unbekannter Modus: {mode}");
		PrintHelp();
		Environment.ExitCode = 1;
		break;
}

static async Task RunMafChatAsync(AppConfig config)
{
	Console.WriteLine("Starte Microsoft Agent Framework Chat (Foundry Responses API)...");

	var projectClient = new AIProjectClient(new Uri(config.ProjectEndpoint), new DefaultAzureCredential());
	AIAgent agent = projectClient.AsAIAgent(
		model: config.ModelDeploymentName,
		instructions: "You are a helpful assistant. Keep answers concise and actionable.",
		name: "FoundryIqMafConsoleAgent");

	Console.WriteLine("Tippe eine Nachricht und druecke Enter. Mit 'exit' beenden.");
	while (true)
	{
		Console.Write("Du: ");
		var prompt = Console.ReadLine();
		if (string.IsNullOrWhiteSpace(prompt))
		{
			continue;
		}

		if (prompt.Equals("exit", StringComparison.OrdinalIgnoreCase))
		{
			break;
		}

		Console.Write("Agent: ");
		await foreach (var update in agent.RunStreamingAsync(prompt))
		{
			Console.Write(update);
		}

		Console.WriteLine();
		Console.WriteLine();
	}
}

static Task RunFoundryIqAsync(AppConfig config)
{
	Console.WriteLine("Starte Foundry IQ Tool-Flow...");

	if (string.IsNullOrWhiteSpace(config.WorkIqConnectionName))
	{
		throw new InvalidOperationException("FOUNDRYIQ_CONNECTION_NAME oder WORKIQ_CONNECTION_NAME ist nicht gesetzt.");
	}

	var projectClient = new AIProjectClient(new Uri(config.ProjectEndpoint), new DefaultAzureCredential());

	AIProjectConnection workIqConnection = projectClient.Connections.GetConnection(config.WorkIqConnectionName);
	Console.WriteLine($"Foundry IQ Verbindung gefunden: {workIqConnection.Name} ({workIqConnection.Id})");

	var agentDefinition = new DeclarativeAgentDefinition(config.ModelDeploymentName)
	{
		Instructions = "You are a helpful assistant with access to Work IQ. "
					 + "Use FoundryIQ IQ to retrieve relevant Microsoft 365 information.",
	};

	// In der aktuellen SDK-Version wird Foundry IQ ueber WorkIQPreviewTool abgebildet.
	agentDefinition.Tools.Add(new WorkIQPreviewTool(workIqConnection.Id));

	ProjectsAgentVersion agentVersion = projectClient.AgentAdministrationClient.CreateAgentVersion(
		agentName: "foundryiq-console-agent",
		options: new ProjectsAgentVersionCreationOptions(agentDefinition));

	try
	{
		Console.WriteLine($"Foundry IQ Agent erstellt: {agentVersion.Name} v{agentVersion.Version}");
		Console.WriteLine("Verbindung zu Foundry IQ ist erfolgreich aufgebaut.");
	}
	finally
	{
		projectClient.AgentAdministrationClient.DeleteAgentVersion(
			agentName: agentVersion.Name,
			agentVersion: agentVersion.Version);
	}

	return Task.CompletedTask;
}

static void PrintHelp()
{
	Console.WriteLine("Verwendung:");
	Console.WriteLine("  dotnet run -- maf-chat");
	Console.WriteLine("  dotnet run -- foundryiq");
	Console.WriteLine();
	Console.WriteLine("Benoetigte Umgebungsvariablen:");
	Console.WriteLine("  FOUNDRY_PROJECT_ENDPOINT            z.B. https://<resource>.services.ai.azure.com/api/projects/<project>");
	Console.WriteLine("  FOUNDRY_MODEL_NAME                  z.B. gpt-4o-mini");
	Console.WriteLine("  FOUNDRYIQ_CONNECTION_NAME           nur fuer 'foundryiq' Modus");
	Console.WriteLine("  WORKIQ_CONNECTION_NAME              alternativ, falls bereits vorhanden");
}

internal sealed record AppConfig(string ProjectEndpoint, string ModelDeploymentName, string? WorkIqConnectionName)
{
	public static AppConfig FromEnvironment()
	{
		var endpoint = Environment.GetEnvironmentVariable("FOUNDRY_PROJECT_ENDPOINT")
					   ?? Environment.GetEnvironmentVariable("AZURE_AI_PROJECT_ENDPOINT")
					   ?? throw new InvalidOperationException("FOUNDRY_PROJECT_ENDPOINT oder AZURE_AI_PROJECT_ENDPOINT ist nicht gesetzt.");

		var model = Environment.GetEnvironmentVariable("FOUNDRY_MODEL_NAME")
					?? Environment.GetEnvironmentVariable("AZURE_AI_MODEL_DEPLOYMENT_NAME")
					?? throw new InvalidOperationException("FOUNDRY_MODEL_NAME oder AZURE_AI_MODEL_DEPLOYMENT_NAME ist nicht gesetzt.");

		var workIq = Environment.GetEnvironmentVariable("FOUNDRYIQ_CONNECTION_NAME")
					 ?? Environment.GetEnvironmentVariable("WORKIQ_CONNECTION_NAME");
		return new AppConfig(endpoint, model, workIq);
	}
}
