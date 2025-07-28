"""
Interfejs użytkownika konsolowego
"""

import structlog
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.columns import Columns
from rich.align import Align
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner

logger = structlog.get_logger()
console = Console()


class ConsoleUI:
    """Klasa interfejsu użytkownika konsolowego"""
    
    def __init__(self):
        self.console = console
    
    async def show_main_menu(self) -> str:
        """Wyświetlenie głównego menu"""
        self.console.print("\n" + "="*60)
        self.console.print(Panel.fit(
            "[bold blue]🤖 Agenty Console App - Menu Główne[/bold blue]",
            border_style="blue"
        ))
        
        menu_items = [
            "[1] 📄 Przetwarzanie paragonów",
            "[2] 📚 Zarządzanie bazą wiedzy RAG",
            "[3] 💬 Chat z agentem AI",
            "[4] 📊 Statystyki",
            "[5] 📤 Zarządzanie eksportami",  
            "[6] ❓ Pomoc",
            "[7] 🚪 Wyjście"
        ]
        
        for item in menu_items:
            self.console.print(item)
        
        self.console.print("="*60)
        
        return Prompt.ask(
            "[bold blue]Wybierz opcję",
            choices=["1", "2", "3", "4", "5", "6", "7"],
            default="1"
        )
    
    async def show_receipt_processing_menu(self, file_count: int) -> str:
        """Menu przetwarzania paragonów"""
        self.console.print("\n" + "-"*50)
        self.console.print(Panel.fit(
            f"[bold blue]📄 Przetwarzanie paragonów ({file_count} plików)[/bold blue]",
            border_style="blue"
        ))
        
        menu_items = [
            "[1] 🔄 Przetwarzaj wszystkie pliki",
            "[2] 📁 Wybierz konkretny plik",
            "[3] ↩️  Powrót"
        ]
        
        for item in menu_items:
            self.console.print(item)
        
        self.console.print("-"*50)
        
        return Prompt.ask(
            "[bold blue]Wybierz opcję",
            choices=["1", "2", "3"],
            default="1"
        )
    
    async def select_file(self, files: List[Path]) -> Optional[Path]:
        """Wybór konkretnego pliku"""
        if not files:
            return None
        
        self.console.print("\n[bold blue]📁 Dostępne pliki:[/bold blue]")
        
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Nr", style="cyan", width=5)
        table.add_column("Nazwa pliku", style="green")
        table.add_column("Rozmiar", style="yellow")
        table.add_column("Typ", style="magenta")
        
        for i, file_path in enumerate(files, 1):
            size = file_path.stat().st_size
            size_str = self._format_file_size(size)
            file_type = file_path.suffix.upper()
            
            table.add_row(str(i), file_path.name, size_str, file_type)
        
        self.console.print(table)
        
        try:
            choice = Prompt.ask(
                "[bold blue]Wybierz numer pliku",
                choices=[str(i) for i in range(1, len(files) + 1)]
            )
            return files[int(choice) - 1]
        except (ValueError, IndexError):
            self.console.print("[red]❌ Nieprawidłowy wybór![/red]")
            return None
    
    async def show_rag_menu(self) -> str:
        """Menu zarządzania RAG"""
        self.console.print("\n" + "-"*50)
        self.console.print(Panel.fit(
            "[bold blue]📚 Zarządzanie bazą wiedzy RAG[/bold blue]",
            border_style="blue"
        ))
        
        menu_items = [
            "[1] ➕ Dodaj dokumenty do bazy wiedzy",
            "[2] 🔍 Wyszukaj w bazie wiedzy",
            "[3] 📋 Lista dokumentów",
            "[4] ↩️  Powrót"
        ]
        
        for item in menu_items:
            self.console.print(item)
        
        self.console.print("-"*50)
        
        return Prompt.ask(
            "[bold blue]Wybierz opcję",
            choices=["1", "2", "3", "4"],
            default="1"
        )
    
    async def show_processing_results(self, results: List[Dict[str, Any]]):
        """Wyświetlenie wyników przetwarzania"""
        if not results:
            return
        
        self.console.print("\n[bold blue]📊 Wyniki przetwarzania:[/bold blue]")
        
        successful = sum(1 for r in results if r.get('success', False))
        failed = len(results) - successful
        
        # Podsumowanie
        summary_table = Table(title="Podsumowanie")
        summary_table.add_column("Status", style="bold")
        summary_table.add_column("Liczba", style="bold")
        summary_table.add_column("Procent", style="bold")
        
        summary_table.add_row("✅ Pomyślne", str(successful), f"{(successful/len(results)*100):.1f}%")
        summary_table.add_row("❌ Błędne", str(failed), f"{(failed/len(results)*100):.1f}%")
        summary_table.add_row("📄 Wszystkie", str(len(results)), "100%")
        
        self.console.print(summary_table)
        
        # Szczegóły błędów
        if failed > 0:
            self.console.print("\n[bold red]❌ Szczegóły błędów:[/bold red]")
            error_table = Table()
            error_table.add_column("Plik", style="red")
            error_table.add_column("Błąd", style="red")
            
            for result in results:
                if not result.get('success', False):
                    error_table.add_row(
                        result.get('file', 'Nieznany'),
                        result.get('error', 'Nieznany błąd')
                    )
            
            self.console.print(error_table)
    
    async def show_receipt_details(self, result: Dict[str, Any]):
        """Wyświetlenie szczegółów paragonu"""
        self.console.print("\n[bold blue]📄 Szczegóły paragonu:[/bold blue]")
        
        # Podstawowe informacje
        info_table = Table(title="Informacje o pliku")
        info_table.add_column("Pole", style="bold")
        info_table.add_column("Wartość")
        
        info_table.add_row("Plik", result.get('file', 'Nieznany'))
        info_table.add_row("Status", "✅ Pomyślnie przetworzony")
        
        processing_info = result.get('processing_info', {})
        if processing_info:
            info_table.add_row("Rozmiar", f"{processing_info.get('file_size', 0)} bajtów")
            info_table.add_row("Format", processing_info.get('format', 'Nieznany'))
            info_table.add_row("Auto-enhance", "✅ Tak" if processing_info.get('auto_enhanced') else "❌ Nie")
        
        self.console.print(info_table)
        
        # Tekst z OCR
        text = result.get('text', '')
        if text:
            self.console.print("\n[bold blue]📝 Wyekstrahowany tekst:[/bold blue]")
            self.console.print(Panel(text, title="OCR Text", border_style="green"))
    
    async def show_search_results(self, results: List[Dict[str, Any]]):
        """Wyświetlenie wyników wyszukiwania"""
        if not results:
            self.console.print("[yellow]📭 Nie znaleziono wyników[/yellow]")
            return
        
        self.console.print(f"\n[bold blue]🔍 Znaleziono {len(results)} wyników:[/bold blue]")
        
        for i, result in enumerate(results, 1):
            self.console.print(f"\n[bold cyan]Wynik {i}:[/bold cyan]")
            
            result_table = Table()
            result_table.add_column("Pole", style="bold")
            result_table.add_column("Wartość")
            
            result_table.add_row("Źródło", result.get('source', 'Nieznane'))
            result_table.add_row("Podobieństwo", f"{result.get('similarity', 0):.2f}")
            
            content = result.get('content', '')
            if content:
                # Skróć długi tekst
                if len(content) > 200:
                    content = content[:200] + "..."
                result_table.add_row("Treść", content)
            
            self.console.print(result_table)
    
    async def show_documents_list(self, documents: List[Dict[str, Any]]):
        """Wyświetlenie listy dokumentów"""
        if not documents:
            self.console.print("[yellow]📭 Baza wiedzy jest pusta[/yellow]")
            return
        
        self.console.print(f"\n[bold blue]📚 Lista dokumentów ({len(documents)}):[/bold blue]")
        
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Nazwa pliku", style="green")
        table.add_column("Typ", style="cyan")
        table.add_column("Rozmiar", style="yellow")
        table.add_column("Ścieżka", style="dim")
        
        for doc in documents:
            size = self._format_file_size(doc.get('file_size', 0))
            table.add_row(
                doc.get('filename', 'Nieznany'),
                doc.get('file_type', 'Nieznany'),
                size,
                doc.get('file_path', 'Nieznana')
            )
        
        self.console.print(table)
    
    async def show_statistics(self, stats: Dict[str, Any]):
        """Wyświetlenie statystyk"""
        if 'error' in stats:
            self.console.print(f"[red]❌ Błąd pobierania statystyk: {stats['error']}[/red]")
            return
        
        self.console.print("\n[bold blue]📊 Statystyki systemu:[/bold blue]")
        
        stats_table = Table(title="Statystyki")
        stats_table.add_column("Metryka", style="bold")
        stats_table.add_column("Wartość", style="bold")
        
        # Dodaj dostępne statystyki
        for key, value in stats.items():
            if key != 'error':
                stats_table.add_row(key.replace('_', ' ').title(), str(value))
        
        self.console.print(stats_table)
    
    async def show_help(self):
        """Wyświetlenie pomocy"""
        help_text = """
[bold blue]🤖 Agenty Console App - Pomoc[/bold blue]

[bright_blue]Funkcje aplikacji:[/bright_blue]

📄 [bold]Przetwarzanie paragonów:[/bold]
   • Automatyczne wykrywanie plików obrazów i PDF
   • OCR z obsługą języka polskiego
   • Auto-enhancement obrazów
   • Walidacja jakości przed przetwarzaniem

📚 [bold]Zarządzanie bazą wiedzy RAG:[/bold]
   • Dodawanie dokumentów tekstowych i PDF
   • Wyszukiwanie semantyczne
   • Indeksowanie i chunking dokumentów
   • Zarządzanie metadanymi

💬 [bold]Chat z Agentem AI:[/bold]
   • Konwersacja w języku naturalnym
   • Historia rozmów z agentem
   • Kontekstowe odpowiedzi
   • Komendy specjalne i sugestie

📊 [bold]Statystyki:[/bold]
   • Liczba przetworzonych paragonów
   • Statystyki błędów
   • Informacje o bazie wiedzy

[bright_blue]Obsługiwane formaty:[/bright_blue]
   • Obrazy: JPG, JPEG, PNG, BMP, TIFF
   • Dokumenty: PDF, TXT, MD, DOCX, HTML

[bright_blue]Katalogi:[/bright_blue]
   • Paragony: /home/marcin/Dokumenty/PROJEKT/AGENTY/PARAGONY
   • Wiedza RAG: /home/marcin/Dokumenty/PROJEKT/AGENTY/WIEDZA_RAG

[bright_blue]Skróty klawiszowe:[/bright_blue]
   • Ctrl+C - Wyjście z aplikacji
   • Enter - Potwierdzenie wyboru
"""
        
        self.console.print(Panel(help_text, title="Pomoc", border_style="blue"))
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Formatowanie rozmiaru pliku"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def show_error(self, message: str):
        """Wyświetlenie błędu"""
        self.console.print(f"[bold red]❌ Błąd: {message}[/bold red]")
    
    def show_success(self, message: str):
        """Wyświetlenie komunikatu o sukcesie"""
        self.console.print(f"[bold green]✅ {message}[/bold green]")
    
    def show_warning(self, message: str):
        """Wyświetlenie ostrzeżenia"""
        self.console.print(f"[bold yellow]⚠️  {message}[/bold yellow]")
    
    async def show_export_menu(self) -> str:
        """Menu zarządzania eksportami"""
        self.console.print("\n" + "-"*50)
        self.console.print(Panel.fit(
            "[bold blue]📤 Zarządzanie eksportami[/bold blue]",
            border_style="blue"
        ))
        
        menu_items = [
            "[1] 📋 Lista eksportów",
            "[2] 📄 Eksport wyników paragonów",
            "[3] 📚 Eksport wyników RAG",
            "[4] 🗑️  Usuń eksport",
            "[5] ↩️  Powrót"
        ]
        
        for item in menu_items:
            self.console.print(item)
        
        self.console.print("-"*50)
        
        return Prompt.ask(
            "[bold blue]Wybierz opcję",
            choices=["1", "2", "3", "4", "5"],
            default="1"
        )
    
    async def show_export_format_menu(self) -> str:
        """Menu wyboru formatu eksportu"""
        self.console.print("\n[bold blue]📤 Wybierz format eksportu:[/bold blue]")
        
        menu_items = [
            "[1] 📄 JSON",
            "[2] 📊 CSV",
            "[3] 📝 TXT",
            "[4] ❌ Anuluj"
        ]
        
        for item in menu_items:
            self.console.print(item)
        
        choice = Prompt.ask(
            "[bold blue]Wybierz format",
            choices=["1", "2", "3", "4"],
            default="1"
        )
        
        format_map = {
            "1": "json",
            "2": "csv",
            "3": "txt",
            "4": None
        }
        
        return format_map.get(choice)
    
    async def show_exports_list(self, exports: List[Dict[str, Any]]):
        """Wyświetlenie listy eksportów"""
        if not exports:
            self.console.print("[yellow]📭 Brak dostępnych eksportów[/yellow]")
            return
        
        self.console.print(f"\n[bold blue]📤 Lista eksportów ({len(exports)}):[/bold blue]")
        
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Nazwa pliku", style="green")
        table.add_column("Format", style="cyan")
        table.add_column("Rozmiar", style="yellow")
        table.add_column("Data modyfikacji", style="dim")
        
        for export in exports:
            size = self._format_file_size(export.get('size', 0))
            modified = datetime.fromtimestamp(export.get('modified', 0)).strftime('%Y-%m-%d %H:%M')
            
            table.add_row(
                export.get('filename', 'Nieznany'),
                export.get('format', 'Nieznany').upper(),
                size,
                modified
            )
        
        self.console.print(table)
    
    async def select_export(self, exports: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Wybór eksportu do usunięcia"""
        if not exports:
            return None
        
        self.console.print("\n[bold blue]🗑️  Wybierz eksport do usunięcia:[/bold blue]")
        
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Nr", style="cyan", width=5)
        table.add_column("Nazwa pliku", style="green")
        table.add_column("Format", style="cyan")
        table.add_column("Rozmiar", style="yellow")
        
        for i, export in enumerate(exports, 1):
            size = self._format_file_size(export.get('size', 0))
            table.add_row(
                str(i),
                export.get('filename', 'Nieznany'),
                export.get('format', 'Nieznany').upper(),
                size
            )
        
        self.console.print(table)
        
        try:
            choice = Prompt.ask(
                "[bold blue]Wybierz numer eksportu",
                choices=[str(i) for i in range(1, len(exports) + 1)]
            )
            return exports[int(choice) - 1]
        except (ValueError, IndexError):
            self.console.print("[red]❌ Nieprawidłowy wybór![/red]")
            return None
    
    def show_info(self, message: str):
        """Wyświetlenie informacji"""
        self.console.print(f"[bold blue]ℹ️  {message}[/bold blue]")
    
    async def show_chat_interface(self, chat_agent):
        """Interfejs czatu z agentem AI"""
        from .chat_agent import ChatAgent
        
        self.console.print("\n" + "="*60)
        self.console.print(Panel.fit(
            "[bold blue]💬 Chat z Agentem AI[/bold blue]\n"
            "[dim]Wpisz 'exit' lub 'quit' aby wyjść\n"
            "Wpisz 'clear' aby wyczyścić historię\n"
            "Wpisz 'history' aby zobaczyć historię konwersacji\n"
            "Wpisz 'help' aby zobaczyć dostępne komendy[/dim]",
            border_style="blue"
        ))
        
        # Sprawdź połączenie z backendem
        async with chat_agent as agent:
            if not await agent.check_backend_connection():
                self.console.print("[bold red]❌ Brak połączenia z backendem! Chat może nie działać poprawnie.[/bold red]")
            
            # Pokaż podsumowanie konwersacji
            summary = agent.get_conversation_summary()
            if summary["total_messages"] > 0:
                self.console.print(f"\n[dim]📊 Kontynuujesz konwersację: {summary['total_messages']} wiadomości, "
                                 f"ostatnia aktywność: {summary['last_activity'][:19] if summary['last_activity'] else 'brak'}[/dim]")
            
            # Pokaż sugerowane pytania
            suggestions = await agent.get_suggested_questions()
            if suggestions:
                self.console.print("\n[bold cyan]💡 Sugerowane pytania:[/bold cyan]")
                for i, suggestion in enumerate(suggestions[:3], 1):
                    self.console.print(f"  {i}. {suggestion}")
            
            self.console.print("\n" + "-"*60)
            
            while True:
                try:
                    # Pobierz input od użytkownika
                    user_input = Prompt.ask("\n[bold green]Ty", default="").strip()
                    
                    if not user_input:
                        continue
                    
                    # Obsługa komend specjalnych
                    if user_input.lower() in ['exit', 'quit', 'wyjście']:
                        self.console.print("[bold blue]👋 Kończę chat...[/bold blue]")
                        break
                    
                    elif user_input.lower() in ['clear', 'wyczyść']:
                        agent.clear_conversation()
                        self.console.print("[bold yellow]🧹 Historia konwersacji została wyczyszczona![/bold yellow]")
                        continue
                    
                    elif user_input.lower() in ['history', 'historia']:
                        await self._show_chat_history(agent)
                        continue
                    
                    elif user_input.lower() in ['help', 'pomoc']:
                        await self._show_chat_help()
                        continue
                    
                    elif user_input.lower() in ['summary', 'podsumowanie']:
                        await self._show_conversation_summary(agent)
                        continue
                    
                    elif user_input.lower() in ['suggestions', 'sugestie']:
                        suggestions = await agent.get_suggested_questions()
                        self.console.print("\n[bold cyan]💡 Sugerowane pytania:[/bold cyan]")
                        for i, suggestion in enumerate(suggestions, 1):
                            self.console.print(f"  {i}. {suggestion}")
                        continue
                    
                    # Wyślij wiadomość do agenta
                    with Live(Spinner("dots", text="[bold blue]🤖 Agent myśli...[/bold blue]"), 
                             refresh_per_second=10) as live:
                        response = await agent.send_message(user_input)
                        live.stop()
                    
                    if response.get("success", False):
                        assistant_response = response.get("response", "")
                        metadata = response.get("metadata", {})
                        
                        # Wyświetl odpowiedź agenta
                        self.console.print(f"\n[bold blue]🤖 Agent:[/bold blue]")
                        
                        # Renderuj markdown jeśli odpowiedź zawiera formatowanie
                        if any(marker in assistant_response for marker in ['**', '*', '`', '#', '-', '1.']):
                            self.console.print(Markdown(assistant_response))
                        else:
                            self.console.print(Panel(assistant_response, border_style="blue"))
                        
                        # Pokaż metadane jeśli dostępne
                        if metadata and any(metadata.values()):
                            self._show_response_metadata(metadata)
                        
                    else:
                        error_msg = response.get("error", "Nieznany błąd")
                        self.console.print(f"\n[bold red]❌ Błąd: {error_msg}[/bold red]")
                        
                        # Sugestie w przypadku błędu
                        self.console.print("\n[dim]💡 Spróbuj:[/dim]")
                        self.console.print("[dim]• Sprawdź czy backend jest uruchomiony[/dim]")
                        self.console.print("[dim]• Sprawdź połączenie internetowe[/dim]")  
                        self.console.print("[dim]• Wpisz 'help' aby zobaczyć dostępne komendy[/dim]")
                
                except KeyboardInterrupt:
                    self.console.print("\n[bold blue]👋 Kończę chat...[/bold blue]")
                    break
                except Exception as e:
                    logger.error(f"Błąd w interfejsie czatu: {e}")
                    self.console.print(f"\n[bold red]❌ Błąd interfejsu: {e}[/bold red]")
    
    async def _show_chat_history(self, agent):
        """Wyświetlenie historii czatu"""
        history = agent.history.get_recent_messages(20)
        
        if not history:
            self.console.print("[yellow]📭 Historia czatu jest pusta[/yellow]")
            return
        
        self.console.print(f"\n[bold blue]📜 Historia czatu (ostatnie {len(history)} wiadomości):[/bold blue]")
        
        for msg in history:
            timestamp = msg["timestamp"][:19].replace('T', ' ')
            role = "🤖 Agent" if msg["role"] == "assistant" else "👤 Ty"
            content = msg["content"]
            
            # Skróć długie wiadomości
            if len(content) > 100:
                content = content[:97] + "..."
            
            self.console.print(f"\n[dim]{timestamp}[/dim] [bold]{role}:[/bold]")
            self.console.print(content)
    
    async def _show_chat_help(self):
        """Pomoc dla czatu"""
        help_text = """
[bold blue]💬 Pomoc Chat - Dostępne komendy:[/bold blue]

[bold cyan]Komendy specjalne:[/bold cyan]
• [bold]exit, quit, wyjście[/bold] - Wyjście z czatu
• [bold]clear, wyczyść[/bold] - Wyczyszczenie historii konwersacji  
• [bold]history, historia[/bold] - Wyświetlenie historii czatu
• [bold]summary, podsumowanie[/bold] - Podsumowanie konwersacji
• [bold]suggestions, sugestie[/bold] - Sugerowane pytania
• [bold]help, pomoc[/bold] - Ta pomoc

[bold cyan]Przykłady pytań:[/bold cyan]
• "Jak przetworzyć paragony wsadowo?"
• "Jakie formaty plików obsługujesz?"
• "Pokaż mi statystyki systemu"
• "Jak dodać dokumenty do bazy wiedzy?"
• "Eksportuj wyniki do CSV"

[bold cyan]Funkcje agenta:[/bold cyan]
• Odpowiada na pytania o system
• Pomaga w przetwarzaniu paragonów
• Zarządza bazą wiedzy RAG
• Eksportuje dane w różnych formatach
• Zapewnia wsparcie techniczne
"""
        self.console.print(Panel(help_text, title="Pomoc Chat", border_style="cyan"))
    
    async def _show_conversation_summary(self, agent):
        """Podsumowanie konwersacji"""
        summary = agent.get_conversation_summary()
        
        self.console.print(f"\n[bold blue]📊 Podsumowanie konwersacji:[/bold blue]")
        
        summary_table = Table()
        summary_table.add_column("Metryka", style="bold")
        summary_table.add_column("Wartość", style="bold")
        
        summary_table.add_row("Wszystkie wiadomości", str(summary["total_messages"]))
        summary_table.add_row("Twoje wiadomości", str(summary["user_messages"]))  
        summary_table.add_row("Odpowiedzi agenta", str(summary["assistant_messages"]))
        summary_table.add_row("Ostatnia aktywność", 
                             summary["last_activity"][:19].replace('T', ' ') if summary["last_activity"] else "Brak")
        
        if summary["topics"]:
            summary_table.add_row("Omawiane tematy", ", ".join(summary["topics"]))
        
        self.console.print(summary_table)
    
    def _show_response_metadata(self, metadata: Dict[str, Any]):
        """Wyświetlenie metadanych odpowiedzi"""
        if not any(metadata.values()):
            return
        
        self.console.print("\n[dim]📋 Dodatkowe informacje:[/dim]")
        
        for key, value in metadata.items():
            if value:
                key_display = key.replace('_', ' ').title()
                self.console.print(f"[dim]• {key_display}: {value}[/dim]") 