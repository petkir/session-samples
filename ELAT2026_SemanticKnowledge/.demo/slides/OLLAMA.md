---
theme: default
layout: section
---

# Ollama? 

Ollama is a lightweight local runtime and model manager for large language models.

- Runs models locally (CPU or GPU) with simple install
- Provides curated model library (e.g. llama3, mistral, phi, codellama, deepseek-coder)
- Single command pull and serve: ollama pull llama3 && ollama run llama3
- Supports chat, embeddings, model composition (modelfile)
- Streams tokens for low-latency interactive use
- Works offline after initial model download
- Simple HTTP API (POST /api/chat, /api/generate, /api/embeddings)
- Modelfile lets you create custom variants (system prompts, templates, parameters)

