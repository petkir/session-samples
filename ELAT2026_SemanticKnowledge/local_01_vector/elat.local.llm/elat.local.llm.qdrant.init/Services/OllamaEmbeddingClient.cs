using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;

namespace elat.local.llm.qdrant.init.Services;

public interface IOllamaEmbeddingClient
{
    Task<float[]> GenerateAsync(string input, string model);
}

public class OllamaEmbeddingClient : IOllamaEmbeddingClient
{
    private readonly HttpClient _http;
    private readonly Uri _endpoint;

    public OllamaEmbeddingClient(Uri endpoint)
    {
        _http = new HttpClient();
        _endpoint = endpoint;
    }

    private record EmbeddingRequest(string model, string input);

    public async Task<float[]> GenerateAsync(string input, string model)
    {
        var url = new Uri(_endpoint, "/api/embed");
        using var resp = await _http.PostAsJsonAsync(url, new EmbeddingRequest(model, input));
        resp.EnsureSuccessStatusCode();
        var vec = await ParseEmbeddingAsync(resp);
        if (vec == null || vec.Length == 0)
        {
            throw new InvalidOperationException("No embeddings returned from Ollama");
        }
        return vec;
    }

    private static async Task<float[]> ParseEmbeddingAsync(HttpResponseMessage resp)
    {
        using var stream = await resp.Content.ReadAsStreamAsync();
        using var doc = await JsonDocument.ParseAsync(stream);
        var root = doc.RootElement;

        // Prefer single vector format: { "embedding": [ ... ] }
        if (root.TryGetProperty("embedding", out var single))
        {
            return ToFloatArray(single);
        }

        // Fallback: { "embeddings": [[...], ...] } or { "embeddings": [{ "embedding": [...] }, ...] }
        if (root.TryGetProperty("embeddings", out var multiple) && multiple.ValueKind == JsonValueKind.Array && multiple.GetArrayLength() > 0)
        {
            var first = multiple[0];
            if (first.ValueKind == JsonValueKind.Array)
            {
                return ToFloatArray(first);
            }
            if (first.ValueKind == JsonValueKind.Object && first.TryGetProperty("embedding", out var nested))
            {
                return ToFloatArray(nested);
            }
        }

        // OpenAI-style: { "data": [ { "embedding": [...] } ] }
        if (root.TryGetProperty("data", out var data) && data.ValueKind == JsonValueKind.Array && data.GetArrayLength() > 0)
        {
            var first = data[0];
            if (first.ValueKind == JsonValueKind.Object && first.TryGetProperty("embedding", out var nested))
            {
                return ToFloatArray(nested);
            }
        }

        throw new InvalidOperationException("No embeddings returned from Ollama");
    }

    private static float[] ToFloatArray(JsonElement arr)
    {
        if (arr.ValueKind != JsonValueKind.Array)
        {
            throw new InvalidOperationException("Invalid embedding format from Ollama");
        }
        var len = arr.GetArrayLength();
        var result = new float[len];
        int i = 0;
        foreach (var el in arr.EnumerateArray())
        {
            // accommodate double or single
            result[i++] = el.ValueKind switch
            {
                JsonValueKind.Number when el.TryGetDouble(out var d) => (float)d,
                _ => throw new InvalidOperationException("Embedding contains non-numeric value")
            };
        }
        return result;
    }
}
