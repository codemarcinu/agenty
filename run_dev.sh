#!/bin/bash

# Skrypt uruchamiania aplikacji w trybie deweloperskim

set -e

echo "🚀 Uruchamianie aplikacji w trybie deweloperskim..."

# Sprawdzenie czy środowisko wirtualne istnieje
if [ ! -d "venv" ]; then
    echo "📦 Tworzenie środowiska wirtualnego..."
    python -m venv venv
fi

# Aktywacja środowiska wirtualnego
echo "🔧 Aktywacja środowiska wirtualnego..."
source venv/bin/activate

# Instalacja zależności
echo "📦 Instalacja zależności..."
pip install -r requirements-console.txt

# Sprawdzenie katalogów
echo "📁 Sprawdzenie katalogów..."
mkdir -p PARAGONY WIEDZA_RAG exports

# Uruchomienie testów
echo "🧪 Uruchamianie testów..."
python test_app.py

# Uruchomienie aplikacji
echo "🤖 Uruchamianie aplikacji..."
python -m console_app.main --debug 