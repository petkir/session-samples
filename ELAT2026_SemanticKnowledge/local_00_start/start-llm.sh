#!/bin/bash

# Installation instructions:
#
# macOS:
#   brew install ollama
#   OR download from: https://ollama.com/download/mac
#
# Linux:
#   curl -fsSL https://ollama.com/install.sh | sh
#
# Windows:
#   Download installer from: https://ollama.com/download/windows
#

echo "🚀 Starting Ollama..."

# Check if Ollama is installed
if ! command -v ollama >/dev/null 2>&1; then
    echo "❌ Ollama is not installed"
    echo ""
    echo "Install Ollama:"
    echo "  macOS:   brew install ollama"
    echo "  Linux:   curl -fsSL https://ollama.com/install.sh | sh"
    echo "  Windows: https://ollama.com/download/windows"
    exit 1
fi

# Start Ollama if not running
if ! curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    echo "📡 Starting Ollama server..."
    ollama serve &
    sleep 3
else
    echo "✅ Ollama is already running"
fi

# Show available models
echo ""
echo "📦 Available models:"
ollama list

# Pull llama3.2 if not present
if ! ollama list | grep -q "llama3.2"; then
    echo ""
    echo "⬇️  Downloading llama3.2 model..."
    ollama pull llama3.2
fi

echo ""
echo "✅ Ollama is ready at http://localhost:11434"
echo "💡 Test it with: llm-test.http"
echo "🛑 Stop with: pkill ollama"
