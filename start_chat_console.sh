#!/bin/bash

# Skrypt startowy dla aplikacji konsolowej z agentem chatowym
# Uruchomienie: ./start_chat_console.sh

echo "🤖 Agenty Console App - Uruchomienie z Chat Agentem"
echo "=============================================="

# Sprawdź czy istnieją wymagane katalogi
if [ ! -d "console_app" ]; then
    echo "❌ Błąd: Katalog console_app nie został znaleziony!"
    echo "Upewnij się, że znajdujesz się w głównym katalogu projektu."
    exit 1
fi

# Sprawdź czy Python jest zainstalowany
if ! command -v python &> /dev/null; then
    echo "❌ Błąd: Python nie jest zainstalowany!"
    exit 1
fi

# Informacje o wymaganiach
echo "📋 Wymagania:"
echo "1. Backend AI musi być uruchomiony (http://localhost:8000)"
echo "2. Katalogi PARAGONY/ i WIEDZA_RAG/ będą utworzone automatycznie"
echo ""

# Sprawdź podstawowe zależności
echo "🔍 Sprawdzanie zależności..."
python -c "import aiohttp, rich, structlog" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Podstawowe zależności są dostępne"
else
    echo "⚠️  Niektóre zależności mogą być niedostępne"
    echo "Aby zainstalować wszystkie zależności uruchom:"
    echo "pip install aiohttp rich structlog"
    echo ""
    read -p "Kontynuować mimo to? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Uruchom aplikację
echo ""
echo "🚀 Uruchamiam aplikację konsolową..."
echo "Wybierz opcję '3. 💬 Chat z agentem AI' z menu głównego"
echo ""
echo "💡 Komendy w chacie:"
echo "• 'help' - pomoc"
echo "• 'history' - historia rozmów"
echo "• 'clear' - wyczyść historię"
echo "• 'exit' - wyjście z chatu"
echo ""

# Uruchom aplikację
python -m console_app.main

echo ""
echo "👋 Aplikacja zakończona. Do widzenia!"