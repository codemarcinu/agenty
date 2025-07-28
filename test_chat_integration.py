#!/usr/bin/env python3
"""
Test integracji agenta chatowego - uproszczony test bez pełnych zależności
"""

import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from console_app.chat_agent import ChatAgent, ConversationHistory
from rich.console import Console

class MockConfig:
    """Mockowa konfiguracja do testów"""
    def __init__(self):
        self.BACKEND_URL = "http://localhost:8000"
        self.PARAGONY_DIR = "PARAGONY"
        self.WIEDZA_RAG_DIR = "WIEDZA_RAG"

console = Console()

async def test_chat_agent_with_mock_backend():
    """Test agenta chatowego z mockowanym backendem"""
    console.print("[bold cyan]🧪 Test agenta chatowego z mock backendem...[/bold cyan]")
    
    config = MockConfig()
    chat_agent = ChatAgent(config)
    
    # Test inicjalnego stanu
    summary = chat_agent.get_conversation_summary()
    assert summary['total_messages'] == 0, "Początkowa historia powinna być pusta"
    
    # Test sugerowanych pytań
    suggestions = await chat_agent.get_suggested_questions()
    assert len(suggestions) > 0, "Powinny być dostępne sugerowane pytania"
    
    # Test dodawania wiadomości do historii
    chat_agent.history.add_message("user", "Test pytanie o paragony")
    chat_agent.history.add_message("assistant", "Pomogę Ci z paragonami")
    
    summary_after = chat_agent.get_conversation_summary()
    assert summary_after['total_messages'] == 2, "Historia powinna zawierać 2 wiadomości"
    assert summary_after['user_messages'] == 1, "Powinna być 1 wiadomość użytkownika"
    assert summary_after['assistant_messages'] == 1, "Powinna być 1 wiadomość asystenta"
    
    # Test wykrywania tematów
    topics = summary_after['topics']
    assert len(topics) > 0, "Powinny zostać wykryte tematy"
    assert any('paragon' in topic.lower() for topic in topics), "Powinien zostać wykryty temat paragonów"
    
    console.print("[green]✅ Test agenta chatowego z mock backendem zakończony pomyślnie[/green]")

async def test_conversation_persistence():
    """Test trwałości konwersacji"""
    console.print("[bold cyan]🧪 Test trwałości konwersacji...[/bold cyan]")
    
    config = MockConfig()
    
    # Pierwszy agent - dodaj wiadomości
    chat_agent1 = ChatAgent(config)
    chat_agent1.history.add_message("user", "Pytanie testowe")
    chat_agent1.history.add_message("assistant", "Odpowiedź testowa")
    
    # Symuluj zapis historii
    test_history_file = chat_agent1.history_file
    success = chat_agent1.history.export_to_file(test_history_file)
    assert success, "Eksport historii powinien zakończyć się sukcesem"
    
    # Drugi agent - załaduj historię
    chat_agent2 = ChatAgent(config)
    success = chat_agent2.history.import_from_file(test_history_file)
    assert success, "Import historii powinien zakończyć się sukcesem"
    
    # Sprawdź czy historia została załadowana
    summary = chat_agent2.get_conversation_summary()
    assert summary['total_messages'] == 2, "Historia powinna zawierać 2 wiadomości po załadowaniu"
    
    # Posprzątaj
    if test_history_file.exists():
        test_history_file.unlink()
    
    console.print("[green]✅ Test trwałości konwersacji zakończony pomyślnie[/green]")

async def test_chat_commands():
    """Test komend specjalnych czatu"""
    console.print("[bold cyan]🧪 Test komend specjalnych czatu...[/bold cyan]")
    
    config = MockConfig()
    chat_agent = ChatAgent(config)
    
    # Dodaj przykładową historię
    chat_agent.history.add_message("user", "Test 1")
    chat_agent.history.add_message("assistant", "Odpowiedź 1")
    chat_agent.history.add_message("user", "Test 2")
    chat_agent.history.add_message("assistant", "Odpowiedź 2")
    
    # Test przed wyczyszczeniem
    summary_before = chat_agent.get_conversation_summary()
    assert summary_before['total_messages'] == 4, "Historia powinna zawierać 4 wiadomości"
    
    # Test czyszczenia konwersacji
    chat_agent.clear_conversation()
    
    # Test po wyczyszczeniu
    summary_after = chat_agent.get_conversation_summary()
    assert summary_after['total_messages'] == 0, "Historia powinna być pusta po wyczyszczeniu"
    
    console.print("[green]✅ Test komend specjalnych czatu zakończony pomyślnie[/green]")

async def test_context_aware_suggestions():
    """Test kontekstowych sugestii"""
    console.print("[bold cyan]🧪 Test kontekstowych sugestii...[/bold cyan]")
    
    config = MockConfig()
    chat_agent = ChatAgent(config)
    
    # Test sugestii bez kontekstu
    suggestions_empty = await chat_agent.get_suggested_questions()
    assert len(suggestions_empty) > 0, "Powinny być dostępne podstawowe sugestie"
    
    # Dodaj kontekst o paragonach
    chat_agent.history.add_message("user", "Jak przetworzyć paragon OCR?")
    chat_agent.history.add_message("assistant", "Pomogę z OCR paragonów")
    
    suggestions_ocr = await chat_agent.get_suggested_questions()
    assert len(suggestions_ocr) > 0, "Powinny być dostępne sugestie kontekstowe"
    
    # Dodaj kontekst o RAG
    chat_agent.history.add_message("user", "Dodaj do bazy wiedzy RAG")
    chat_agent.history.add_message("assistant", "Dodam dokumenty do RAG")
    
    suggestions_rag = await chat_agent.get_suggested_questions()
    assert len(suggestions_rag) > 0, "Powinny być dostępne sugestie dla RAG"
    
    console.print("[green]✅ Test kontekstowych sugestii zakończony pomyślnie[/green]")

async def main():
    """Główna funkcja testowa"""
    from rich.panel import Panel
    
    console.print(Panel.fit(
        "[bold blue]🧪 Test Integracji Agenta Chatowego[/bold blue]\n"
        "[dim]Testowanie funkcjonalności bez pełnych zależności systemu[/dim]",
        border_style="blue"
    ))
    
    try:
        await test_chat_agent_with_mock_backend()
        await test_conversation_persistence()
        await test_chat_commands()
        await test_context_aware_suggestions()
        
        console.print("\n[bold green]🎉 Wszystkie testy integracji zakończone pomyślnie![/bold green]")
        console.print("[dim]Agent chatowy został pomyślnie zintegrowany z aplikacją konsolową.[/dim]")
        console.print("\n[bold cyan]📝 Funkcje agenta chatowego:[/bold cyan]")
        console.print("• 💬 Konwersacja w języku naturalnym")
        console.print("• 📚 Historia rozmów z trwałością")
        console.print("• 🤖 Kontekstowe sugestie pytań")
        console.print("• 🧹 Zarządzanie konwersacją (clear, history, itp.)")
        console.print("• 📊 Podsumowania i analiza tematów")
        console.print("• 🔄 Integracja z backendem AI")
        
        console.print("\n[bold yellow]📋 Aby uruchomić pełną aplikację:[/bold yellow]")
        console.print("1. Zainstaluj wszystkie zależności: pip install -r requirements-console.txt")
        console.print("2. Uruchom backend AI")
        console.print("3. Uruchom aplikację: python -m console_app.main")
        console.print("4. Wybierz opcję '3. 💬 Chat z agentem AI'")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Test zakończony błędem: {e}[/bold red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)