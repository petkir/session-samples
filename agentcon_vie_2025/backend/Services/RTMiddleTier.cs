using System.Net.WebSockets;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Azure.Core;
using Azure.Identity;
using Backend.Models;

namespace Backend.Services;

public class RTMiddleTier
{
    private readonly string _endpoint;
    private readonly string _deployment;
    private readonly string? _apiKey;
    private readonly TokenCredential? _tokenCredential;
    private readonly string? _voiceChoice;
    private readonly ILogger<RTMiddleTier> _logger;
    private readonly string _apiVersion = "2024-10-01-preview";

    public Dictionary<string, Tool> Tools { get; } = new();
    public string? SystemMessage { get; set; }
    private readonly Dictionary<string, RTToolCall> _toolsPending = new();

    public RTMiddleTier(
        string endpoint,
        string deployment,
        object credentials,
        string? voiceChoice,
        ILogger<RTMiddleTier> logger)
    {
        _endpoint = endpoint.Replace("https://", "wss://").Replace("http://", "ws://");
        _deployment = deployment;
        _voiceChoice = voiceChoice;
        _logger = logger;

        if (credentials is string apiKey)
        {
            _apiKey = apiKey;
        }
        else if (credentials is TokenCredential tokenCredential)
        {
            _tokenCredential = tokenCredential;
        }
        else
        {
            throw new ArgumentException("Credentials must be either a string API key or a TokenCredential");
        }

        _logger.LogInformation("RTMiddleTier initialized with voice choice: {VoiceChoice}", _voiceChoice ?? "default");
    }

    public async Task HandleWebSocketAsync(WebSocket clientWebSocket)
    {
        _logger.LogInformation("Client WebSocket connected");

        ClientWebSocket? serverWebSocket = null;
        
        try
        {
            // Build the WebSocket URI
            var uriBuilder = new UriBuilder(_endpoint)
            {
                Path = $"/openai/realtime",
                Query = $"api-version={_apiVersion}&deployment={_deployment}"
            };

            // Retry logic for rate limiting (429 errors)
            int maxRetries = 3;
            int retryDelayMs = 1000;
            
            for (int attempt = 1; attempt <= maxRetries; attempt++)
            {
                serverWebSocket?.Dispose();
                serverWebSocket = new ClientWebSocket();
                
                // Set authorization header
                if (!string.IsNullOrEmpty(_apiKey))
                {
                    serverWebSocket.Options.SetRequestHeader("api-key", _apiKey);
                }
                else if (_tokenCredential != null)
                {
                    var token = await _tokenCredential.GetTokenAsync(
                        new TokenRequestContext(new[] { "https://cognitiveservices.azure.com/.default" }),
                        CancellationToken.None);
                    serverWebSocket.Options.SetRequestHeader("Authorization", $"Bearer {token.Token}");
                }
                
                try
                {
                    await serverWebSocket.ConnectAsync(uriBuilder.Uri, CancellationToken.None);
                    _logger.LogInformation("Connected to Azure OpenAI Realtime API");
                    break;
                }
                catch (WebSocketException ex) when (ex.Message.Contains("429") && attempt < maxRetries)
                {
                    _logger.LogWarning($"Rate limited (429). Retry {attempt}/{maxRetries} after {retryDelayMs}ms...");
                    await Task.Delay(retryDelayMs);
                    retryDelayMs *= 2; // Exponential backoff
                }
            }

            // Send initial session configuration
            try
            {
                _logger.LogInformation("Sending session update to Azure OpenAI...");
                await SendSessionUpdateAsync(serverWebSocket);
                _logger.LogInformation("Session update sent successfully");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to send session update");
                throw;
            }

            // Start bidirectional message forwarding
            _logger.LogInformation("Starting message forwarding...");
            var clientToServer = ForwardMessagesAsync(clientWebSocket, serverWebSocket, ProcessMessageToServer);
            var serverToClient = ForwardMessagesAsync(serverWebSocket, clientWebSocket, ProcessMessageToClient);

            try
            {
                // Wait for either task to complete
                await Task.WhenAny(clientToServer, serverToClient);
                _logger.LogInformation("One WebSocket direction completed. Waiting for cleanup...");
                
                // Give the other task a moment to complete gracefully
                var remainingTask = clientToServer.IsCompleted ? serverToClient : clientToServer;
                var timeout = Task.Delay(TimeSpan.FromSeconds(2));
                await Task.WhenAny(remainingTask, timeout);
                
                // Check for exceptions
                if (clientToServer.IsFaulted)
                {
                    _logger.LogError(clientToServer.Exception, "Client->Server forwarding faulted");
                }
                if (serverToClient.IsFaulted)
                {
                    _logger.LogError(serverToClient.Exception, "Server->Client forwarding faulted");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during WebSocket communication");
            }
        }
        finally
        {
            _logger.LogInformation($"Cleanup: Client state={clientWebSocket.State}, Server state={serverWebSocket?.State}");
            if (serverWebSocket?.State == WebSocketState.Open)
            {
                await serverWebSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", CancellationToken.None);
            }
            serverWebSocket?.Dispose();
            _logger.LogInformation("WebSocket connection closed");
        }
    }

    private async Task SendSessionUpdateAsync(ClientWebSocket serverWebSocket)
    {
        var sessionUpdate = new JsonObject
        {
            ["type"] = "session.update",
            ["session"] = new JsonObject()
        };

        var session = sessionUpdate["session"]!.AsObject();

        if (!string.IsNullOrEmpty(SystemMessage))
        {
            session["instructions"] = SystemMessage;
            _logger.LogInformation("Setting system instructions");
        }

        if (!string.IsNullOrEmpty(_voiceChoice))
        {
            session["voice"] = _voiceChoice;
            _logger.LogInformation("Setting voice to: {Voice}", _voiceChoice);
        }

        if (Tools.Count > 0)
        {
            var toolsArray = new JsonArray();
            foreach (var tool in Tools.Values)
            {
                toolsArray.Add(JsonSerializer.SerializeToNode(tool.Schema));
            }
            session["tools"] = toolsArray;
            _logger.LogInformation("Configured {ToolCount} tools", Tools.Count);
        }

        var json = JsonSerializer.Serialize(sessionUpdate);
        _logger.LogDebug("Session config: {Json}", json);
        var bytes = Encoding.UTF8.GetBytes(json);
        
        if (serverWebSocket.State != WebSocketState.Open)
        {
            throw new InvalidOperationException($"Cannot send session update - WebSocket state is {serverWebSocket.State}");
        }
        
        await serverWebSocket.SendAsync(new ArraySegment<byte>(bytes), WebSocketMessageType.Text, true, CancellationToken.None);
        _logger.LogInformation("Sent session configuration to server");
    }

    private async Task ForwardMessagesAsync(
        WebSocket sourceWebSocket,
        WebSocket targetWebSocket,
        Func<JsonObject, WebSocket, WebSocket, Task<string?>> messageProcessor)
    {
        var buffer = new byte[1024 * 64];
        var messageBuilder = new StringBuilder();

        try
        {
            while (sourceWebSocket.State == WebSocketState.Open)
            {
                var result = await sourceWebSocket.ReceiveAsync(new ArraySegment<byte>(buffer), CancellationToken.None);

                if (result.MessageType == WebSocketMessageType.Close)
                {
                    _logger.LogInformation("Received close message from source WebSocket");
                    if (targetWebSocket.State == WebSocketState.Open || targetWebSocket.State == WebSocketState.CloseReceived)
                    {
                        await targetWebSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Client closed", CancellationToken.None);
                    }
                    break;
                }

                messageBuilder.Append(Encoding.UTF8.GetString(buffer, 0, result.Count));

                if (result.EndOfMessage)
                {
                    var messageText = messageBuilder.ToString();
                    messageBuilder.Clear();

                    try
                    {
                        var message = JsonSerializer.Deserialize<JsonObject>(messageText);
                        if (message != null)
                        {
                            var processedMessage = await messageProcessor(message, sourceWebSocket, targetWebSocket);
                            if (!string.IsNullOrEmpty(processedMessage))
                            {
                                // Check target WebSocket state before sending
                                if (targetWebSocket.State == WebSocketState.Open)
                                {
                                    var bytes = Encoding.UTF8.GetBytes(processedMessage);
                                    await targetWebSocket.SendAsync(
                                        new ArraySegment<byte>(bytes),
                                        WebSocketMessageType.Text,
                                        true,
                                        CancellationToken.None);
                                }
                                else
                                {
                                    _logger.LogWarning("Target WebSocket is not open (State: {State}). Stopping forwarding.", targetWebSocket.State);
                                    break;
                                }
                            }
                        }
                    }
                    catch (JsonException ex)
                    {
                        _logger.LogError(ex, "Failed to parse message: {Message}", messageText);
                    }
                    catch (WebSocketException ex)
                    {
                        _logger.LogWarning(ex, "WebSocket error while processing message");
                        throw; // Re-throw to be caught by outer catch
                    }
                }
            }
            
            _logger.LogInformation("Message forwarding loop completed. Source state: {State}", sourceWebSocket.State);
        }
        catch (WebSocketException ex) when (ex.WebSocketErrorCode == WebSocketError.ConnectionClosedPrematurely || 
                                             ex.Message.Contains("close handshake"))
        {
            _logger.LogWarning("Remote party closed the WebSocket connection unexpectedly");
        }
        catch (WebSocketException ex)
        {
            _logger.LogWarning(ex, "WebSocket connection error");
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Unexpected error in message forwarding");
            throw;
        }
    }

    private async Task<string?> ProcessMessageToServer(JsonObject message, WebSocket clientWs, WebSocket serverWs)
    {
        // Messages from client to server can be passed through or modified
        return JsonSerializer.Serialize(message);
    }

    private async Task<string?> ProcessMessageToClient(JsonObject message, WebSocket serverWs, WebSocket clientWs)
    {
        var messageType = message["type"]?.ToString();

        switch (messageType)
        {
            case "session.created":
                // Hide server-side details from client
                if (message["session"] is JsonObject session)
                {
                    session["instructions"] = "";
                    session["tools"] = new JsonArray();
                    if (!string.IsNullOrEmpty(_voiceChoice))
                    {
                        session["voice"] = _voiceChoice;
                    }
                    session["tool_choice"] = "none";
                    session["max_response_output_tokens"] = null;
                }
                return JsonSerializer.Serialize(message);

            case "response.output_item.added":
                if (message["item"]?["type"]?.ToString() == "function_call")
                {
                    return null; // Hide function call items from client
                }
                return JsonSerializer.Serialize(message);

            case "conversation.item.created":
                if (message["item"]?["type"]?.ToString() == "function_call")
                {
                    var item = message["item"]!.AsObject();
                    var callId = item["call_id"]?.ToString();
                    var previousId = message["previous_item_id"]?.ToString();
                    
                    if (!string.IsNullOrEmpty(callId))
                    {
                        _toolsPending[callId] = new RTToolCall(callId, previousId ?? "");
                    }
                    return null; // Hide from client
                }
                return JsonSerializer.Serialize(message);

            case "response.function_call_arguments.done":
                var functionCallId = message["call_id"]?.ToString();
                var functionName = message["name"]?.ToString();
                var argumentsJson = message["arguments"]?.ToString();

                if (!string.IsNullOrEmpty(functionCallId) &&
                    !string.IsNullOrEmpty(functionName) &&
                    !string.IsNullOrEmpty(argumentsJson) &&
                    Tools.TryGetValue(functionName, out var tool))
                {
                    _logger.LogInformation("Executing tool: {FunctionName}", functionName);

                    try
                    {
                        var result = await tool.Target(argumentsJson);

                        if (result.Direction == ToolResultDirection.ToServer)
                        {
                            // Send result back to server
                            if (serverWs.State == WebSocketState.Open)
                            {
                                var toolResponse = new JsonObject
                                {
                                    ["type"] = "conversation.item.create",
                                    ["item"] = new JsonObject
                                    {
                                        ["type"] = "function_call_output",
                                        ["call_id"] = functionCallId,
                                        ["output"] = result.Result
                                    }
                                };

                                var responseBytes = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(toolResponse));
                                await serverWs.SendAsync(new ArraySegment<byte>(responseBytes), WebSocketMessageType.Text, true, CancellationToken.None);

                                // Trigger response generation
                                var createResponse = new JsonObject
                                {
                                    ["type"] = "response.create"
                                };
                                var createBytes = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(createResponse));
                                await serverWs.SendAsync(new ArraySegment<byte>(createBytes), WebSocketMessageType.Text, true, CancellationToken.None);
                            }
                            else
                            {
                                _logger.LogWarning("Server WebSocket is not open (State: {State}). Cannot send tool response.", serverWs.State);
                            }
                        }
                        else
                        {
                            // Send result to client as extension message
                            var clientMessage = new JsonObject
                            {
                                ["type"] = "extension.middle_tier_tool_response",
                                ["tool_name"] = functionName,
                                ["tool_result"] = result.Result
                            };
                            return JsonSerializer.Serialize(clientMessage);
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Error executing tool {FunctionName}", functionName);
                    }

                    _toolsPending.Remove(functionCallId);
                }
                return null;

            case "response.done":
            case "error":
                return JsonSerializer.Serialize(message);

            default:
                return JsonSerializer.Serialize(message);
        }
    }
}
