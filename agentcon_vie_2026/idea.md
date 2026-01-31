VoiceRAG+Tools: RAG + Voice with Azure AI Search and GPT-4o Realtime

## Overview

Build a full-stack sample that combines:

- Voice-first interaction using the browser microphone and the Azure OpenAI GPT-4o Realtime API
- Retrieval Augmented Generation (RAG) over Azure AI Search
- Tool / function calling for simple personal-data operations ("My Fields", "My Todos", current data)
- Audio responses plus visual citations and debug views

The goal is to have a minimal but complete blueprint for a Voice + RAG + Tools app on Azure.

## Core Features

- **Voice interface**  
	- Capture audio via the browser microphone.  
	- Stream audio to the backend, which connects to the Azure OpenAI GPT-4o Realtime API.

- **RAG (Retrieval Augmented Generation)**  
	- Use Azure AI Search to query a knowledge base in Azure AI Search.  
	- Pass retrieved documents (snippets + metadata) as context into GPT-4o Realtime to ground the answer.

- **Tool / function calling**  
	- Implement function-calling tools for:  
		- `MyFields` – simple key/value or profile-style fields.  
		- `MyTodos` – todo management (add, list, mark complete).  
		- `CurrentData` – expose current app/session state.  
	- Expose tool calls in a debug view in the frontend (see below).

- **Audio output**  
	- Stream the model's response back as audio.  
	- Play audio in the browser using the standard audio APIs.

- **Citations / sources**  
	- Show which Azure AI Search documents and passages were used to answer the query.  
	- Link back to the underlying document where possible.

## Frontend

- Location: `/frontend`
- Stack: React + Vite
- Reference implementations:  
	- Azure sample app (frontend patterns): https://github.com/Azure-Samples/aisearch-openai-rag-audio/tree/main/app/frontend  
	- Azure OpenAI GPT-4o Realtime audio how-to (protocol & API details): https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio?view=foundry-classic#get-started

### Frontend requirements

- Voice capture and control UI (start/stop listening, status indicator).
- Display of:
	- User transcript
	- Model transcript
	- Citations (documents from RAG step)
- **Debug panel**: 
	- List RAG search requests/responses (queries, top documents).  
	- List function calls and results (`MyFields`, `MyTodos`, `CurrentData`).

## Backend

- Location: `/backend`
- Language: C# 10
- Responsibilities:
	- WebSocket or HTTP endpoint that the frontend connects to for realtime audio.  
	- Connect to Azure OpenAI GPT-4o Realtime API.  
	- Perform RAG queries against Azure AI Search.  
	- Implement tool / function endpoints used by the model (MyFields, MyTodos, CurrentData).  
	- Return both audio and structured metadata (transcripts, citations, tool calls) to the frontend.

### Backend environment configuration

Required configuration (e.g., environment variables or app settings):

- `AZURE_OPENAI_ENDPOINT` = `wss://<your-instance-name>.openai.azure.com`
- `AZURE_OPENAI_REALTIME_DEPLOYMENT` = `gpt-4o-realtime-preview`
- `AZURE_OPENAI_REALTIME_VOICE_CHOICE` = `<echo | alloy | shimmer>`
- `AZURE_OPENAI_API_KEY` = `<your-api-key>`
- `AZURE_SEARCH_ENDPOINT` = `https://<your-service-name>.search.windows.net`
- `AZURE_SEARCH_INDEX` = `<your-index-name>`
- `AZURE_SEARCH_API_KEY` = `<your-api-key>`

## Data & Documents

- Location: `/data`
- Purpose: raw/source documents that will be pushed into Azure AI Search.  
- Format: flexible (e.g., markdown, PDF, text); the indexer program (below) will handle parsing and embedding.

## Indexer

- Location: `/indexer`
- Language: C# (console app)
- Purpose: upload / sync documents from `/data` into Azure AI Search, including embeddings.

### Indexer behavior

- Walk the `/data` folder and read documents.  
- Chunk content and generate embeddings using Azure OpenAI.  
- Push content and embeddings into the configured Azure AI Search index.

### Indexer environment configuration

- `AZURE_OPENAI_API_KEY` = `<your-api-key>`
- `AZURE_SEARCH_ENDPOINT` = `https://<your-service-name>.search.windows.net`
- `AZURE_SEARCH_INDEX` = `<your-index-name>`
- `AZURE_SEARCH_API_KEY` = `<your-api-key>`

Optionally: add additional settings for model/embedding deployment names and chunking strategy as the design evolves.