# ImportDoc2AISearch

Kleine `net10.0` Console-App, die PDF-Dateien aus `docs` liest, Text-Chunks erzeugt, Embeddings ueber Azure OpenAI anfordert und die Chunks per `mergeOrUpload` in einen Azure AI Search Index schreibt.

## Konfiguration

Die Werte stehen in `appsettings.json`.

- `Search:Endpoint`: Endpoint des Azure AI Search Dienstes
- `Search:ApiKey`: Admin Key des Search Dienstes
- `Search:IndexName`: Zielindex
- `OpenAI:Endpoint`: Endpoint der Azure OpenAI Ressource
- `OpenAI:ApiKey`: API Key der Azure OpenAI Ressource
- `OpenAI:EmbeddingDeployment`: Name des Embedding Deployments
- `OpenAI:EmbeddingDimensions`: Vektordimension des verwendeten Modells
- `Import:DocsPath`: Quellordner der PDFs
- `Import:MaxChunkLength`: Zielgroesse eines Chunks in Zeichen
- `Import:ChunkOverlap`: Ueberlappung zwischen zwei Chunks in Zeichen
- `Import:BatchSize`: Anzahl Dokumente pro Search-Upsert

Alternativ koennen Werte per Umgebungsvariablen mit Prefix `IMPORTER_` gesetzt werden, zum Beispiel `IMPORTER_Search__ApiKey`.

## Ausfuehren

```bash
dotnet run
```

Beim Start erstellt oder aktualisiert die App den Search-Index automatisch mit folgenden Feldern:

- `id`
- `sourceFile`
- `sourcePath`
- `title`
- `chunkNumber`
- `content`
- `contentVector`