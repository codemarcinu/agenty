#!/bin/bash
# Skrypt startowy dla aplikacji konsolowej AGENTY
# Enhanced UX/UI Console Application

set -e

echo "🚀 Uruchamianie aplikacji konsolowej AGENTY..."

# Sprawdź czy python jest dostępny
if ! command -v python &> /dev/null; then
    echo "❌ Python nie jest zainstalowany"
    exit 1
fi

# Sprawdź czy backend jest uruchomiony
echo "🔍 Sprawdzanie połączenia z backend..."
if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "⚠️  Backend nie jest dostępny na porcie 8000"
    echo "💡 Uruchom backend poleceniem:"
    echo "   cd agenty/backend && python main.py"
    echo ""
    echo "📝 Aplikacja konsolowa może działać w trybie offline z ograniczoną funkcjonalnością"
    read -p "Czy chcesz kontynuować? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Backend dostępny"
fi

# Sprawdź zależności
echo "📦 Sprawdzanie zależności..."
python -c "import rich, httpx" 2>/dev/null || {
    echo "❌ Brakuje wymaganych bibliotek"
    echo "💡 Zainstaluj je poleceniem:"
    echo "   pip install -r requirements-console.txt"
    exit 1
}

echo "✅ Wszystkie zależności dostępne"
echo ""

# Uruchom aplikację
echo "🎯 Uruchamianie aplikacji konsolowej AGENTY..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Sprawdź która wersja uruchomić
if [ -f "console_agenty_enhanced.py" ]; then
    python console_agenty_enhanced.py
elif [ -f "console_agenty.py" ]; then
    python console_agenty.py
else
    echo "❌ Nie znaleziono pliku aplikacji konsolowej"
    exit 1
fi