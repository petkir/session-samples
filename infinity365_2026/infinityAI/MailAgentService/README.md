# MailAgentService (.NET 10)

## 1. Architektur (ausfuehrlich)

Der Service besteht aus 4 Laufzeitbausteinen:

1. `SubscriptionBootstrapService`
- Startet beim App-Start.
- Erstellt sofort eine Microsoft Graph Subscription auf `Inbox/messages` des Ziel-Postfachs.
- Speichert Subscription-ID + Expiration in einem In-Memory-State.

2. Graph Webhook Endpoint `POST/GET /api/graph/notifications`
- Nimmt den Graph Validation-Handshake entgegen (`validationToken`) und antwortet `text/plain`.
- Nimmt Change Notifications entgegen.
- Extrahiert Message-ID aus `resourceData.id` (oder `resource`) und schiebt sie in eine interne Queue.

3. `SubscriptionRenewalService`
- Prueft zyklisch die Ablaufzeit.
- Erneuert Subscription rechtzeitig vor Ablauf.

4. `GraphMailProcessorWorker`
- Liest Queue-Eintraege.
- Holt Original-Mail per Graph.
- Laesst den Inhalt ueber Microsoft Agent Framework analysieren.
- Legt auf Basis der Analyse einen neuen Draft im Zielpostfach an.

```mermaid
flowchart LR
    A[Service Start] --> B[Create Graph Subscription]
    B --> C[Graph sends notifications]
    C --> D[/api/graph/notifications]
    D --> E[NotificationQueue]
    E --> F[GraphMailProcessorWorker]
    F --> G[Read message from Graph]
    G --> H[Microsoft Agent Framework Analyze]
    H --> I[Create Draft via Graph]
    B --> J[SubscriptionRenewalService]
    J --> B
```

## 2. App Registration Checkliste (kurz)

1. Entra App Registration erstellen (Single Tenant empfohlen).
2. Application Permissions vergeben:
- `Mail.Read`
- `Mail.ReadWrite`
3. `Grant admin consent` ausfuehren.
4. Client Secret oder Zertifikat erzeugen.
5. Werte in `appsettings.json` eintragen:
- `Graph:TenantId`
- `Graph:ClientId`
- `Graph:ClientSecret`
- `Graph:MailboxUserId`
- `Graph:NotificationUrl`
- `Graph:ClientState`

## 3. Umsetzung im Sample (mit Fokus)

### Enthaltene Features

1. .NET 10 Web Service Hosting.
2. Graph Subscription wird beim Start automatisch angelegt.
3. Graph Handshake + Notification-Verarbeitung.
4. Queue-basierte Entkopplung (Webhook bleibt schnell).
5. Dedupe-Schutz fuer Message-Events (In-Memory TTL Cache).
6. Analyse mit Microsoft Agent Framework (`AIAgent`).
7. Draft-Erstellung in das konfigurierte Postfach.
8. Subscription Renewal als Background Service.

### Wichtige Dateien

- `Program.cs` - DI, Endpoints, Agent Registrierung.
- `Services/SubscriptionBootstrapService.cs` - Subscription beim Start.
- `Services/SubscriptionRenewalService.cs` - Renewal-Loop.
- `Services/NotificationQueue.cs` - interne Queue.
- `Services/GraphMailProcessorWorker.cs` - End-to-End Verarbeitung.
- `Services/MicrosoftAgentFrameworkMailAnalyzer.cs` - MAF Analyse.
- `Services/MailDraftService.cs` - Draft Erstellung per Graph.

### Konfiguration

`appsettings.json` Beispiel:

```json
{
  "Graph": {
    "TenantId": "...",
    "ClientId": "...",
    "ClientSecret": "...",
    "MailboxUserId": "mailbox@contoso.com",
    "NotificationUrl": "https://<public-host>/api/graph/notifications",
    "LifecycleNotificationUrl": "https://<public-host>/api/graph/notifications",
    "ClientState": "<random-long-value>",
    "SubscriptionRenewBeforeMinutes": 10,
    "SubscriptionDurationMinutes": 30
  },
  "Agent": {
    "SystemPrompt": "Du bist ein professioneller E-Mail-Assistent...",
    "MaxInputCharacters": 12000,
    "DraftSubjectPrefix": "Entwurf: "
  }
}
```

### Lokaler Start

```bash
dotnet restore
dotnet run
```

### Produktionshinweise

1. `NotificationUrl` muss oeffentlich via HTTPS erreichbar sein.
2. Secret nicht in Klartext speichern, sondern Key Vault/Secret Store nutzen.
3. Fuer mehrere Instanzen Subscription-Zustand in persistente Storage auslagern.
4. Optional `includeResourceData` + Zertifikat aktivieren, wenn Payload-Volltext noetig ist.
