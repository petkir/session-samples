using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;

namespace Indexer.Services;

public class SearchIndexManager
{
    private readonly SearchIndexClient _indexClient;
    private readonly string _indexName;
    private readonly int _embeddingDimensions;

    public SearchIndexManager(SearchIndexClient indexClient, string indexName, int embeddingDimensions)
    {
        _indexClient = indexClient;
        _indexName = indexName;
        _embeddingDimensions = embeddingDimensions;
    }

    public async Task CreateOrUpdateIndexAsync()
    {
        var fields = new List<SearchField>
        {
            new SimpleField("chunk_id", SearchFieldDataType.String) { IsKey = true, IsFilterable = true },
            new SimpleField("parent_id", SearchFieldDataType.String) { IsFilterable = true, IsSortable = true },
            new SearchableField("title") { IsFilterable = true, IsSortable = true },
            new SearchableField("chunk") { AnalyzerName = LexicalAnalyzerName.EnMicrosoft },
            new SimpleField("chunk_index", SearchFieldDataType.Int32) { IsFilterable = true, IsSortable = true },
            new SimpleField("source_file", SearchFieldDataType.String) { IsFilterable = true },
            new VectorSearchField("text_vector", _embeddingDimensions, "vector-config")
        };

        var vectorSearch = new VectorSearch();
        vectorSearch.Algorithms.Add(new HnswAlgorithmConfiguration("hnsw-algorithm")
        {
            Parameters = new HnswParameters
            {
                Metric = VectorSearchAlgorithmMetric.Cosine,
                M = 4,
                EfConstruction = 400,
                EfSearch = 500
            }
        });

        vectorSearch.Profiles.Add(new VectorSearchProfile("vector-config", "hnsw-algorithm"));

        var semanticSearch = new SemanticSearch
        {
            Configurations =
            {
                new SemanticConfiguration("default", new SemanticPrioritizedFields
                {
                    TitleField = new SemanticField("title"),
                    ContentFields = { new SemanticField("chunk") }
                })
            }
        };

        var index = new SearchIndex(_indexName)
        {
            Fields = fields,
            VectorSearch = vectorSearch,
            SemanticSearch = semanticSearch
        };

        try
        {
            var existingIndex = await _indexClient.GetIndexAsync(_indexName);
            Console.WriteLine($"  Index '{_indexName}' already exists, updating if needed...");
            await _indexClient.CreateOrUpdateIndexAsync(index);
            Console.WriteLine($"  ✓ Index updated");
        }
        catch (Azure.RequestFailedException ex) when (ex.Status == 404)
        {
            Console.WriteLine($"  Creating new index '{_indexName}'...");
            await _indexClient.CreateIndexAsync(index);
            Console.WriteLine($"  ✓ Index created");
        }
    }
}
