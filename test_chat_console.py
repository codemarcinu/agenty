#!/usr/bin/env python3
"""
Test funkcjonalności agenta chatowego w aplikacji konsolowej
"""

import asyncio
import sys
import os

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from console_app.config import Config
from console_app.chat_agent import ChatAgent, ConversationHistory
from rich.console import Console

console = Console()

async def test_conversation_history():
    """Test zarządzania historią konwersacji"""
    console.print("[bold cyan]🧪 Test historii konwersacji...[/bold cyan]")
    
    history = ConversationHistory(max_messages=5)
    
    # Dodaj testowe wiadomości
    history.add_message("user", "Jak przetworzyć paragon?")
    history.add_message("assistant", "Możesz wykorzystać funkcję przetwarzania paragonów.")
    history.add_message("user", "Jakie formaty są obsługiwane?")
    history.add_message("assistant", "Obsługujemy JPG, PNG, PDF i inne.")
    
    # Test pobrania wiadomości
    recent = history.get_recent_messages(3)
    assert len(recent) == 3, f"Spodziewano się 3 wiadomości, otrzymano {len(recent)}"
    
    # Test maksymalnej liczby wiadomości
    for i in range(10):
        history.add_message("user", f"Wiadomość {i}")
    
    assert len(history.messages) <= 5, f"Historia przekroczyła limit 5 wiadomości: {len(history.messages)}"
    
    console.print("[green]✅ Test historii konwersacji zakończony pomyślnie[/green]")

async def test_chat_agent_initialization():
    """Test inicjalizacji agenta chatowego"""
    console.print("[bold cyan]🧪 Test inicjalizacji agenta chatowego...[/bold cyan]")
    
    config = Config()
    chat_agent = ChatAgent(config)
    
    # Test podstawowych właściwości
    assert chat_agent.config is not None, "Konfiguracja nie została załadowana"
    assert chat_agent.history is not None, "Historia nie została zainicjalizowana"
    assert hasattr(chat_agent, 'history_file'), "Brak atrybutu history_file"
    
    # Test zarządzania historią
    summary = chat_agent.get_conversation_summary()
    assert isinstance(summary, dict), "Podsumowanie konwersacji nie jest słownikiem"
    assert 'total_messages' in summary, "Brak klucza total_messages w podsumowaniu"
    
    console.print("[green]✅ Test inicjalizacji agenta zakończony pomyślnie[/green]")

async def test_suggested_questions():
    """Test generowania sugerowanych pytań"""
    console.print("[bold cyan]🧪 Test sugerowanych pytań...[/bold cyan]")
    
    config = Config()
    chat_agent = ChatAgent(config)
    
    # Test bez historii
    suggestions = await chat_agent.get_suggested_questions()
    assert isinstance(suggestions, list), "Sugestie nie są listą"
    assert len(suggestions) > 0, "Brak sugerowanych pytań"
    
    # Test z historią zawierającą słowa kluczowe
    chat_agent.history.add_message("user", "Chcę przetworzyć paragon")
    chat_agent.history.add_message("assistant", "Pomogę Ci z OCR")
    
    suggestions_with_context = await chat_agent.get_suggested_questions()
    assert isinstance(suggestions_with_context, list), "Sugestie kontekstowe nie są listą"
    assert len(suggestions_with_context) > 0, "Brak sugerowanych pytań kontekstowych"
    
    console.print("[green]✅ Test sugerowanych pytań zakończony pomyślnie[/green]")

async def test_conversation_summary():
    """Test podsumowania konwersacji"""
    console.print("[bold cyan]🧪 Test podsumowania konwersacji...[/bold cyan]")
    
    config = Config()
    chat_agent = ChatAgent(config)
    
    # Test pustej historii
    summary = chat_agent.get_conversation_summary()
    assert summary['total_messages'] == 0, "Pusta historia powinna mieć 0 wiadomości"
    assert summary['user_messages'] == 0, "Pusta historia powinna mieć 0 wiadomości użytkownika"
    assert summary['assistant_messages'] == 0, "Pusta historia powinna mieć 0 wiadomości asystenta"
    
    # Test z wiadomościami
    chat_agent.history.add_message("user", "Test paragon OCR")
    chat_agent.history.add_message("assistant", "Rozumiem, pomogę z paragonami")
    chat_agent.history.add_message("user", "Dodaj do RAG wiedzy")
    chat_agent.history.add_message("assistant", "Dodam do bazy wiedzy")
    
    summary_with_messages = chat_agent.get_conversation_summary()
    assert summary_with_messages['total_messages'] == 4, f"Spodziewano się 4 wiadomości, otrzymano {summary_with_messages['total_messages']}"
    assert summary_with_messages['user_messages'] == 2, f"Spodziewano się 2 wiadomości użytkownika, otrzymano {summary_with_messages['user_messages']}"
    assert summary_with_messages['assistant_messages'] == 2, f"Spodziewano się 2 wiadomości asystenta, otrzymano {summary_with_messages['assistant_messages']}"
    
    # Test wykrywania tematów
    topics = summary_with_messages['topics']
    assert isinstance(topics, list), "Tematy nie są listą"
    # Powinny zostać wykryte tematy związane z paragonami i RAG
    topic_names = [topic.lower() for topic in topics]
    assert any('paragon' in topic for topic in topic_names), "Nie wykryto tematu paragonów"
    assert any('rag' in topic or 'wiedza' in topic for topic in topic_names), "Nie wykryto tematu RAG"
    
    console.print("[green]✅ Test podsumowania konwersacji zakończony pomyślnie[/green]")

async def test_clear_conversation():
    """Test czyszczenia konwersacji"""
    console.print("[bold cyan]🧪 Test czyszczenia konwersacji...[/bold cyan]")
    
    config = Config()
    chat_agent = ChatAgent(config)
    
    # Dodaj wiadomości
    chat_agent.history.add_message("user", "Test 1")
    chat_agent.history.add_message("assistant", "Odpowiedź 1")
    
    assert len(chat_agent.history.messages) == 2, "Historia powinna zawierać 2 wiadomości"
    
    # Wyczyść konwersację
    chat_agent.clear_conversation()
    
    assert len(chat_agent.history.messages) == 0, "Historia powinna być pusta po wyczyszczeniu"
    
    console.print("[green]✅ Test czyszczenia konwersacji zakończony pomyślnie[/green]")

async def main():
    """Główna funkcja testowa"""
    console.print(Panel.fit(
        "[bold blue]🧪 Testy Agenta Chatowego[/bold blue]\n"
        "[dim]Testowanie funkcjonalności chat agenta w aplikacji konsolowej[/dim]",
        border_style="blue"
    ))
    
    try:
        await test_conversation_history()
        await test_chat_agent_initialization()
        await test_suggested_questions()
        await test_conversation_summary()
        await test_clear_conversation()
        
        console.print("\n[bold green]🎉 Wszystkie testy zakończone pomyślnie![/bold green]")
        console.print("[dim]Agent chatowy jest gotowy do użycia w aplikacji konsolowej.[/dim]")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ Test zakończony błędem: {e}[/bold red]")
        import traceback
        console.print(f"[red]{traceback.format_exc()}[/red]")
        return 1
    
    return 0

if __name__ == "__main__":
    from rich.panel import Panel
    exit_code = asyncio.run(main())
    sys.exit(exit_code)