using Azure.AI.OpenAI;
using OpenAI.Embeddings;

namespace Indexer.Services;

public class EmbeddingService
{
    private readonly EmbeddingClient _client;

    public EmbeddingService(EmbeddingClient client)
    {
        _client = client;
    }

    public async Task<float[]> GenerateEmbeddingAsync(string text)
    {
        var response = await _client.GenerateEmbeddingAsync(text);
        return response.Value.ToFloats().ToArray();
    }

    public async Task<List<float[]>> GenerateEmbeddingsAsync(List<string> texts)
    {
        var embeddings = new List<float[]>();
        
        // Process in batches to avoid rate limits
        const int batchSize = 16;
        for (int i = 0; i < texts.Count; i += batchSize)
        {
            var batch = texts.Skip(i).Take(batchSize).ToList();
            var response = await _client.GenerateEmbeddingsAsync(batch);
            
            embeddings.AddRange(response.Value.Select(e => e.ToFloats().ToArray()));
        }
        
        return embeddings;
    }
}
