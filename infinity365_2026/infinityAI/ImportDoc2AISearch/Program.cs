using System.Net.Http.Headers;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Azure;
using Azure.Search.Documents;
using Azure.Search.Documents.Indexes;
using Azure.Search.Documents.Indexes.Models;
using Azure.Search.Documents.Models;
using Microsoft.Extensions.Configuration;
using UglyToad.PdfPig;

var configuration = new ConfigurationBuilder()
	.SetBasePath(Directory.GetCurrentDirectory())
	.AddJsonFile("appsettings.json", optional: true)
	.AddEnvironmentVariables(prefix: "IMPORTER_")
	.Build();

var settings = configuration.Get<AppSettings>() ?? new AppSettings();
settings.Validate();

var docsPath = ResolveDocsPath(settings.Import.DocsPath);
if (!Directory.Exists(docsPath))
{
	throw new DirectoryNotFoundException($"Das Dokumentverzeichnis wurde nicht gefunden: {docsPath}");
}

var pdfFiles = Directory
	.EnumerateFiles(
		docsPath,
		settings.Import.FilePattern,
		settings.Import.RecurseSubdirectories ? SearchOption.AllDirectories : SearchOption.TopDirectoryOnly)
	.OrderBy(path => path, StringComparer.OrdinalIgnoreCase)
	.ToArray();

if (pdfFiles.Length == 0)
{
	Console.WriteLine($"Keine Dateien gefunden unter {docsPath} mit Pattern {settings.Import.FilePattern}.");
	return;
}

Console.WriteLine($"Starte Import von {pdfFiles.Length} PDF-Datei(en) aus {docsPath} in Index '{settings.Search.IndexName}'.");

var searchCredential = new AzureKeyCredential(settings.Search.ApiKey);
var indexClient = new SearchIndexClient(new Uri(settings.Search.Endpoint), searchCredential);
var searchClient = indexClient.GetSearchClient(settings.Search.IndexName);

await EnsureIndexExistsAsync(indexClient, settings, CancellationToken.None);

using var httpClient = CreateEmbeddingHttpClient(settings.OpenAI.ApiKey);

var pendingDocuments = new List<SearchDocument>(settings.Import.BatchSize);
var indexedChunkCount = 0;

foreach (var pdfFile in pdfFiles)
{
	Console.WriteLine($"Lese {Path.GetFileName(pdfFile)} ...");

	var extractedText = ExtractTextFromPdf(pdfFile);
	var chunks = BuildChunks(extractedText, settings.Import.MaxChunkLength, settings.Import.ChunkOverlap);

	if (chunks.Count == 0)
	{
		Console.WriteLine($"  Uebersprungen: kein extrahierbarer Text in {Path.GetFileName(pdfFile)}.");
		continue;
	}

	Console.WriteLine($"  {chunks.Count} Chunk(s) erzeugt.");

	for (var chunkIndex = 0; chunkIndex < chunks.Count; chunkIndex++)
	{
		var chunkText = chunks[chunkIndex];
		var embedding = await GenerateEmbeddingAsync(httpClient, settings.OpenAI, chunkText, CancellationToken.None);

		pendingDocuments.Add(new SearchDocument
		{
			["id"] = CreateChunkId(pdfFile, chunkIndex),
			["sourceFile"] = Path.GetFileName(pdfFile),
			["sourcePath"] = Path.GetRelativePath(docsPath, pdfFile),
			["title"] = Path.GetFileNameWithoutExtension(pdfFile),
			["chunkNumber"] = chunkIndex,
			["content"] = chunkText,
			["contentVector"] = embedding
		});

		if (pendingDocuments.Count >= settings.Import.BatchSize)
		{
			indexedChunkCount += await UploadBatchAsync(searchClient, pendingDocuments, CancellationToken.None);
			pendingDocuments.Clear();
		}
	}
}

if (pendingDocuments.Count > 0)
{
	indexedChunkCount += await UploadBatchAsync(searchClient, pendingDocuments, CancellationToken.None);
}

Console.WriteLine($"Import abgeschlossen. {indexedChunkCount} Chunk(s) wurden in '{settings.Search.IndexName}' upserted.");

static HttpClient CreateEmbeddingHttpClient(string apiKey)
{
	var client = new HttpClient();
	client.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
	client.DefaultRequestHeaders.Add("api-key", apiKey);
	return client;
}

static string ResolveDocsPath(string docsPath)
{
	return Path.IsPathRooted(docsPath)
		? docsPath
		: Path.GetFullPath(Path.Combine(Directory.GetCurrentDirectory(), docsPath));
}

static string ExtractTextFromPdf(string pdfPath)
{
	using var document = PdfDocument.Open(pdfPath);

	var builder = new StringBuilder();
	foreach (var page in document.GetPages())
	{
		builder.AppendLine(page.Text);
		builder.AppendLine();
	}

	return NormalizeWhitespace(builder.ToString());
}

static string NormalizeWhitespace(string text)
{
	var normalizedNewLines = text.Replace("\r\n", "\n").Replace('\r', '\n');
	var paragraphs = normalizedNewLines
		.Split('\n')
		.Select(line => Regex.Replace(line.Trim(), @"\s+", " "))
		.Where(line => !string.IsNullOrWhiteSpace(line));

	return string.Join(Environment.NewLine + Environment.NewLine, paragraphs).Trim();
}

static List<string> BuildChunks(string text, int maxChunkLength, int overlapLength)
{
	if (string.IsNullOrWhiteSpace(text))
	{
		return new List<string>();
	}

	if (maxChunkLength <= 0)
	{
		throw new InvalidOperationException("Import:MaxChunkLength muss groesser als 0 sein.");
	}

	if (overlapLength >= maxChunkLength)
	{
		throw new InvalidOperationException("Import:ChunkOverlap muss kleiner als Import:MaxChunkLength sein.");
	}

	var words = Regex.Split(text, @"\s+")
		.Where(word => !string.IsNullOrWhiteSpace(word))
		.ToArray();

	var chunks = new List<string>();
	var currentWords = new List<string>();
	var currentLength = 0;

	foreach (var word in words)
	{
		var additionalLength = currentWords.Count == 0 ? word.Length : word.Length + 1;
		if (currentWords.Count > 0 && currentLength + additionalLength > maxChunkLength)
		{
			var chunk = string.Join(' ', currentWords).Trim();
			if (!string.IsNullOrWhiteSpace(chunk))
			{
				chunks.Add(chunk);
			}

			currentWords = BuildOverlapSeed(currentWords, overlapLength);
			currentLength = currentWords.Sum(existingWord => existingWord.Length) + Math.Max(0, currentWords.Count - 1);
		}

		currentWords.Add(word);
		currentLength += currentWords.Count == 1 ? word.Length : word.Length + 1;
	}

	if (currentWords.Count > 0)
	{
		var finalChunk = string.Join(' ', currentWords).Trim();
		if (!string.IsNullOrWhiteSpace(finalChunk))
		{
			chunks.Add(finalChunk);
		}
	}

	return chunks;
}

static List<string> BuildOverlapSeed(List<string> words, int overlapLength)
{
	if (overlapLength <= 0 || words.Count == 0)
	{
		return new List<string>();
	}

	var overlapWords = new List<string>();
	var length = 0;

	for (var index = words.Count - 1; index >= 0; index--)
	{
		var word = words[index];
		var additionalLength = overlapWords.Count == 0 ? word.Length : word.Length + 1;
		if (length + additionalLength > overlapLength)
		{
			break;
		}

		overlapWords.Insert(0, word);
		length += additionalLength;
	}

	return overlapWords;
}

static async Task<float[]> GenerateEmbeddingAsync(HttpClient httpClient, OpenAISettings settings, string text, CancellationToken cancellationToken)
{
	var requestUri = BuildEmbeddingsRequestUri(settings);
	using var request = new HttpRequestMessage(HttpMethod.Post, requestUri)
	{
		Content = new StringContent(
			JsonSerializer.Serialize(new { input = text }),
			Encoding.UTF8,
			"application/json")
	};

	using var response = await httpClient.SendAsync(request, cancellationToken);
	var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);

	if (!response.IsSuccessStatusCode)
	{
		throw new InvalidOperationException($"Embedding-Request fehlgeschlagen ({(int)response.StatusCode}): {responseContent}");
	}

	using var jsonDocument = JsonDocument.Parse(responseContent);
	var embeddingValues = jsonDocument.RootElement
		.GetProperty("data")[0]
		.GetProperty("embedding")
		.EnumerateArray()
		.Select(value => value.GetSingle())
		.ToArray();

	if (embeddingValues.Length != settings.EmbeddingDimensions)
	{
		throw new InvalidOperationException(
			$"Embedding-Dimension stimmt nicht: erwartet {settings.EmbeddingDimensions}, erhalten {embeddingValues.Length}. " +
			"Bitte Import:EmbeddingDimensions bzw. das eingesetzte Modell anpassen.");
	}

	return embeddingValues;
}

static string BuildEmbeddingsRequestUri(OpenAISettings settings)
{
	var endpoint = settings.Endpoint.TrimEnd('/');

	if (endpoint.EndsWith("/openai/v1", StringComparison.OrdinalIgnoreCase))
	{
		endpoint = endpoint[..^10];
	}
	else if (endpoint.EndsWith("/openai", StringComparison.OrdinalIgnoreCase))
	{
		endpoint = endpoint[..^7];
	}

	return $"{endpoint}/openai/deployments/{settings.EmbeddingDeployment}/embeddings?api-version={settings.ApiVersion}";
}

static async Task EnsureIndexExistsAsync(SearchIndexClient indexClient, AppSettings settings, CancellationToken cancellationToken)
{
	const string vectorProfileName = "default-vector-profile";
	const string hnswConfigName = "default-hnsw";

	var fields = new List<SearchField>
	{
		new SimpleField("id", SearchFieldDataType.String)
		{
			IsKey = true,
			IsFilterable = true,
			IsSortable = true
		},
		new SearchableField("sourceFile")
		{
			IsFilterable = true,
			IsSortable = true,
			IsFacetable = true
		},
		new SearchableField("sourcePath")
		{
			IsFilterable = true,
			IsSortable = true
		},
		new SearchableField("title")
		{
			IsFilterable = true,
			IsSortable = true
		},
		new SimpleField("chunkNumber", SearchFieldDataType.Int32)
		{
			IsFilterable = true,
			IsSortable = true
		},
		new SearchableField("content"),
		new SearchField("contentVector", SearchFieldDataType.Collection(SearchFieldDataType.Single))
		{
			IsSearchable = true,
			VectorSearchDimensions = settings.OpenAI.EmbeddingDimensions,
			VectorSearchProfileName = vectorProfileName
		}
	};

	var index = new SearchIndex(settings.Search.IndexName, fields)
	{
		VectorSearch = new VectorSearch
		{
			Algorithms =
			{
				new HnswAlgorithmConfiguration(hnswConfigName)
			},
			Profiles =
			{
				new VectorSearchProfile(vectorProfileName, hnswConfigName)
			}
		}
	};

	await indexClient.CreateOrUpdateIndexAsync(index, cancellationToken: cancellationToken);
	Console.WriteLine($"Index '{settings.Search.IndexName}' ist bereit.");
}

static async Task<int> UploadBatchAsync(SearchClient searchClient, IReadOnlyCollection<SearchDocument> documents, CancellationToken cancellationToken)
{
	if (documents.Count == 0)
	{
		return 0;
	}

	var batch = IndexDocumentsBatch.MergeOrUpload(documents);
	var options = new IndexDocumentsOptions { ThrowOnAnyError = true };

	var response = await searchClient.IndexDocumentsAsync(batch, options, cancellationToken);
	Console.WriteLine($"  {response.Value.Results.Count} Chunk(s) upserted.");
	return response.Value.Results.Count;
}

static string CreateChunkId(string pdfPath, int chunkNumber)
{
	var value = $"{Path.GetFileName(pdfPath)}::{chunkNumber}";
	var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(value));
	return Convert.ToHexString(bytes).ToLowerInvariant();
}

internal sealed class AppSettings
{
	public SearchSettings Search { get; init; } = new();

	public OpenAISettings OpenAI { get; init; } = new();

	public ImportSettings Import { get; init; } = new();

	public void Validate()
	{
		Search.Validate();
		OpenAI.Validate();
		Import.Validate();
	}
}

internal sealed class SearchSettings
{
	public string Endpoint { get; init; } = string.Empty;

	public string ApiKey { get; init; } = string.Empty;

	public string IndexName { get; init; } = "pdf-chunks";

	public void Validate()
	{
		if (string.IsNullOrWhiteSpace(Endpoint))
		{
			throw new InvalidOperationException("Search:Endpoint fehlt.");
		}

		if (string.IsNullOrWhiteSpace(ApiKey))
		{
			throw new InvalidOperationException("Search:ApiKey fehlt.");
		}

		if (string.IsNullOrWhiteSpace(IndexName))
		{
			throw new InvalidOperationException("Search:IndexName fehlt.");
		}
	}
}

internal sealed class OpenAISettings
{
	public string Endpoint { get; init; } = string.Empty;

	public string ApiKey { get; init; } = string.Empty;

	public string EmbeddingDeployment { get; init; } = string.Empty;

	public string ApiVersion { get; init; } = "2024-02-01";

	public int EmbeddingDimensions { get; init; } = 1536;

	public void Validate()
	{
		if (string.IsNullOrWhiteSpace(Endpoint))
		{
			throw new InvalidOperationException("OpenAI:Endpoint fehlt.");
		}

		if (string.IsNullOrWhiteSpace(ApiKey))
		{
			throw new InvalidOperationException("OpenAI:ApiKey fehlt.");
		}

		if (string.IsNullOrWhiteSpace(EmbeddingDeployment))
		{
			throw new InvalidOperationException("OpenAI:EmbeddingDeployment fehlt.");
		}

		if (EmbeddingDimensions <= 0)
		{
			throw new InvalidOperationException("OpenAI:EmbeddingDimensions muss groesser als 0 sein.");
		}
	}
}

internal sealed class ImportSettings
{
	public string DocsPath { get; init; } = "docs";

	public string FilePattern { get; init; } = "*.pdf";

	public bool RecurseSubdirectories { get; init; }

	public int MaxChunkLength { get; init; } = 2000;

	public int ChunkOverlap { get; init; } = 250;

	public int BatchSize { get; init; } = 25;

	public void Validate()
	{
		if (string.IsNullOrWhiteSpace(DocsPath))
		{
			throw new InvalidOperationException("Import:DocsPath fehlt.");
		}

		if (string.IsNullOrWhiteSpace(FilePattern))
		{
			throw new InvalidOperationException("Import:FilePattern fehlt.");
		}

		if (MaxChunkLength <= 0)
		{
			throw new InvalidOperationException("Import:MaxChunkLength muss groesser als 0 sein.");
		}

		if (ChunkOverlap < 0)
		{
			throw new InvalidOperationException("Import:ChunkOverlap darf nicht negativ sein.");
		}

		if (ChunkOverlap >= MaxChunkLength)
		{
			throw new InvalidOperationException("Import:ChunkOverlap muss kleiner als Import:MaxChunkLength sein.");
		}

		if (BatchSize <= 0)
		{
			throw new InvalidOperationException("Import:BatchSize muss groesser als 0 sein.");
		}
	}
}
