#!/usr/bin/env python3
"""
Skrypt testowy dla aplikacji konsolowej Agenty
"""

import asyncio
import sys
from pathlib import Path

# Dodaj ścieżkę do modułów
sys.path.insert(0, str(Path(__file__).parent))

from console_app.config import Config
from console_app.receipt_processor import ReceiptProcessor
from console_app.rag_manager import RAGManager
from console_app.export_manager import ExportManager
from console_app.console_ui import ConsoleUI


async def test_config():
    """Test konfiguracji"""
    print("🔧 Test konfiguracji...")
    
    config = Config()
    print(f"✅ Backend URL: {config.BACKEND_URL}")
    print(f"✅ Paragony dir: {config.PARAGONY_DIR}")
    print(f"✅ Wiedza RAG dir: {config.WIEDZA_RAG_DIR}")
    
    return True


async def test_ui():
    """Test interfejsu użytkownika"""
    print("🎨 Test interfejsu użytkownika...")
    
    ui = ConsoleUI()
    print("✅ UI zainicjalizowany")
    
    return True


async def test_export_manager():
    """Test menedżera eksportów"""
    print("📤 Test menedżera eksportów...")
    
    export_manager = ExportManager()
    
    # Test listy eksportów
    exports = await export_manager.list_exports()
    print(f"✅ Lista eksportów: {len(exports)} plików")
    
    return True


async def test_directories():
    """Test katalogów"""
    print("📁 Test katalogów...")
    
    config = Config()
    
    paragony_dir = Path(config.PARAGONY_DIR)
    wiedza_dir = Path(config.WIEDZA_RAG_DIR)
    
    print(f"✅ Katalog paragonów: {paragony_dir} ({'istnieje' if paragony_dir.exists() else 'nie istnieje'})")
    print(f"✅ Katalog wiedzy RAG: {wiedza_dir} ({'istnieje' if wiedza_dir.exists() else 'nie istnieje'})")
    
    return True


async def test_docker_compose():
    """Test konfiguracji Docker Compose"""
    print("🐳 Test konfiguracji Docker Compose...")
    
    compose_file = Path("docker-compose.console.yaml")
    if compose_file.exists():
        print("✅ Plik docker-compose.console.yaml istnieje")
        
        # Sprawdź zawartość
        with open(compose_file, 'r') as f:
            content = f.read()
            
        if 'agenty-backend' in content:
            print("✅ Konfiguracja backendu OK")
        if 'ollama' in content:
            print("✅ Konfiguracja Ollama OK")
        if 'redis' in content:
            print("✅ Konfiguracja Redis OK")
        if 'console-app' in content:
            print("✅ Konfiguracja aplikacji konsolowej OK")
    else:
        print("❌ Plik docker-compose.console.yaml nie istnieje")
        return False
    
    return True


async def test_dockerfile():
    """Test Dockerfile"""
    print("🐳 Test Dockerfile...")
    
    dockerfile = Path("Dockerfile.console")
    if dockerfile.exists():
        print("✅ Dockerfile.console istnieje")
        
        with open(dockerfile, 'r') as f:
            content = f.read()
            
        if 'python:3.11-slim' in content:
            print("✅ Obraz bazowy OK")
        if 'console_app' in content:
            print("✅ Kopiowanie aplikacji OK")
        if 'requirements-console.txt' in content:
            print("✅ Zależności OK")
    else:
        print("❌ Dockerfile.console nie istnieje")
        return False
    
    return True


async def test_requirements():
    """Test pliku requirements"""
    print("📦 Test pliku requirements...")
    
    requirements_file = Path("requirements-console.txt")
    if requirements_file.exists():
        print("✅ requirements-console.txt istnieje")
        
        with open(requirements_file, 'r') as f:
            content = f.read()
            
        required_packages = [
            'requests', 'aiohttp', 'click', 'rich', 'Pillow',
            'structlog', 'pydantic'
        ]
        
        for package in required_packages:
            if package in content:
                print(f"✅ {package} OK")
            else:
                print(f"❌ {package} brakuje")
                return False
    else:
        print("❌ requirements-console.txt nie istnieje")
        return False
    
    return True


async def main():
    """Główna funkcja testowa"""
    print("🧪 Test aplikacji konsolowej Agenty")
    print("="*50)
    
    tests = [
        test_config,
        test_ui,
        test_export_manager,
        test_directories,
        test_docker_compose,
        test_dockerfile,
        test_requirements
    ]
    
    results = []
    
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Błąd w teście: {e}")
            results.append(False)
    
    print("\n" + "="*50)
    print("📊 Podsumowanie testów:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Przeszło: {passed}/{total}")
    print(f"❌ Nie przeszło: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 Wszystkie testy przeszły! Aplikacja jest gotowa.")
        return True
    else:
        print("⚠️  Niektóre testy nie przeszły. Sprawdź konfigurację.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 