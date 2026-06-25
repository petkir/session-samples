using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Embeddings;
using System.Collections.Generic;

namespace elat.local.llm.qdrant.init.Services;

public class SkOllamaEmbeddingService : ITextEmbeddingGenerationService
{
    private readonly IOllamaEmbeddingClient _client;
    private readonly string _model;

    public SkOllamaEmbeddingService(IOllamaEmbeddingClient client, string model)
    {
        _client = client;
        _model = model;
    }

    public IReadOnlyDictionary<string, object?> Attributes { get; } = new Dictionary<string, object?>();

    public async Task<ReadOnlyMemory<float>> GenerateEmbeddingAsync(string text, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        var vec = await GenerateOneAsync(text, cancellationToken);
        return new ReadOnlyMemory<float>(vec);
    }

    public async Task<IList<ReadOnlyMemory<float>>> GenerateEmbeddingsAsync(IList<string> data, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        var list = new List<ReadOnlyMemory<float>>(data.Count);
        foreach (var text in data)
        {
            var vec = await GenerateOneAsync(text, cancellationToken);
            list.Add(new ReadOnlyMemory<float>(vec));
        }
        return list;
    }

    private async Task<float[]> GenerateOneAsync(string input, CancellationToken ct)
    {
        return await _client.GenerateAsync(input, _model);
    }
}
