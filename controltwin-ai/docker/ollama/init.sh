#!/bin/sh
set -e

echo "Waiting for Ollama..."
sleep 10

export OLLAMA_HOST=${OLLAMA_HOST:-http://ollama:11434}

echo "Pulling models..."
ollama pull mistral:7b
ollama pull nomic-embed-text
ollama pull llama3.2:3b

echo "Models ready"
