# AgentWithFoundryIQ (.NET 10 Console Sample)

Dieses Sample zeigt zwei Modi in einer .NET 10 Konsolenanwendung:

- `maf-chat`: Microsoft Agent Framework Agent mit Azure AI Foundry Responses API
- `foundryiq`: Verbindungs- und Tool-Check fuer Foundry IQ

## Voraussetzungen

- .NET SDK 10
- Azure Login: `az login`
- Berechtigungen auf dem Foundry Projekt
- In Foundry konfigurierte Foundry IQ Connection (fuer `foundryiq` Modus)

## Umgebungsvariablen

- `FOUNDRY_PROJECT_ENDPOINT` oder `AZURE_AI_PROJECT_ENDPOINT`
- `FOUNDRY_MODEL_NAME` oder `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `FOUNDRYIQ_CONNECTION_NAME` (bevorzugt, nur fuer `foundryiq`)
- `WORKIQ_CONNECTION_NAME` (alternativ, gleiche Verbindung)

Beispiel endpoint:

`https://<resource>.services.ai.azure.com/api/projects/<project>`

## Start

1. Variablen setzen (siehe `.env.example`)
2. Starten:

```bash
dotnet run -- maf-chat
```

oder

```bash
dotnet run -- foundryiq
```

## Was der `foundryiq` Modus macht

- Laedt die konfigurierte Foundry IQ Connection aus dem Foundry Projekt
- Erstellt einen Agent mit `WorkIQPreviewTool` (aktueller SDK-Typname)
- Meldet erfolgreiche Verbindung
- Raeumt den temporaeren Agenten wieder auf
