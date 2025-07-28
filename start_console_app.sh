#!/bin/bash

# Skrypt uruchamiania aplikacji konsolowej Agenty

set -e

echo "🚀 Uruchamianie aplikacji konsolowej Agenty..."

# Sprawdzenie czy Docker jest zainstalowany
if ! command -v docker &> /dev/null; then
    echo "❌ Docker nie jest zainstalowany!"
    exit 1
fi

# Sprawdzenie czy docker-compose jest dostępny
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose nie jest dostępny!"
    exit 1
fi

# Sprawdzenie czy katalogi istnieją
PARAGONY_DIR="/home/marcin/Dokumenty/PROJEKT/AGENTY/PARAGONY"
WIEDZA_RAG_DIR="/home/marcin/Dokumenty/PROJEKT/AGENTY/WIEDZA_RAG"

if [ ! -d "$PARAGONY_DIR" ]; then
    echo "📁 Tworzenie katalogu paragonów: $PARAGONY_DIR"
    mkdir -p "$PARAGONY_DIR"
fi

if [ ! -d "$WIEDZA_RAG_DIR" ]; then
    echo "📁 Tworzenie katalogu wiedzy RAG: $WIEDZA_RAG_DIR"
    mkdir -p "$WIEDZA_RAG_DIR"
fi

echo "📂 Katalogi gotowe:"
echo "   Paragony: $PARAGONY_DIR"
echo "   Wiedza RAG: $WIEDZA_RAG_DIR"

# Uruchomienie kontenerów
echo "🐳 Uruchamianie kontenerów Docker..."
docker-compose -f docker-compose.console.yaml up -d

# Czekanie na gotowość backendu
echo "⏳ Czekanie na gotowość backendu..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo "✅ Backend gotowy!"
        break
    fi
    echo "⏳ Czekanie... ($i/30)"
    sleep 2
done

# Czekanie na gotowość Ollama
echo "⏳ Czekanie na gotowość Ollama..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/version > /dev/null; then
        echo "✅ Ollama gotowa!"
        break
    fi
    echo "⏳ Czekanie... ($i/30)"
    sleep 2
done

# Uruchomienie aplikacji konsolowej
echo "🤖 Uruchamianie aplikacji konsolowej..."
docker-compose -f docker-compose.console.yaml run --rm console-app

echo "👋 Aplikacja zakończona." 