#!/usr/bin/env python3
"""
Główny moduł aplikacji konsolowej do przetwarzania paragonów
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import click
import structlog
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from .config import Config
from .receipt_processor import ReceiptProcessor
from .rag_manager import RAGManager
from .export_manager import ExportManager
from .console_ui import ConsoleUI
from .chat_agent import ChatAgent

# Konfiguracja logowania
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
console = Console()


class AgentyConsoleApp:
    """Główna klasa aplikacji konsolowej"""
    
    def __init__(self):
        self.config = Config()
        self.ui = ConsoleUI()
        self.receipt_processor = ReceiptProcessor(self.config)
        self.rag_manager = RAGManager(self.config)
        self.export_manager = ExportManager()
        self.chat_agent = None
        
    async def initialize(self):
        """Inicjalizacja aplikacji"""
        try:
            console.print("[bold green]🚀 Inicjalizacja aplikacji Agenty...[/bold green]")
            
            # Sprawdzenie połączenia z backendem
            if not await self.receipt_processor.check_backend_connection():
                console.print("[bold red]❌ Nie można połączyć się z backendem![/bold red]")
                return False
                
            # Sprawdzenie katalogów
            if not self._check_directories():
                return False
            
            # Inicjalizacja chat agenta
            self.chat_agent = ChatAgent(self.config)
                
            console.print("[bold green]✅ Aplikacja gotowa![/bold green]")
            return True
            
        except Exception as e:
            logger.error(f"Błąd inicjalizacji: {e}")
            console.print(f"[bold red]❌ Błąd inicjalizacji: {e}[/bold red]")
            return False
    
    def _check_directories(self) -> bool:
        """Sprawdzenie katalogów z danymi"""
        paragony_dir = Path(self.config.PARAGONY_DIR)
        wiedza_dir = Path(self.config.WIEDZA_RAG_DIR)
        
        if not paragony_dir.exists():
            console.print(f"[yellow]⚠️  Katalog paragonów nie istnieje: {paragony_dir}[/yellow]")
            paragony_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✅ Utworzono katalog: {paragony_dir}[/green]")
            
        if not wiedza_dir.exists():
            console.print(f"[yellow]⚠️  Katalog wiedzy RAG nie istnieje: {wiedza_dir}[/yellow]")
            wiedza_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[green]✅ Utworzono katalog: {wiedza_dir}[/green]")
            
        return True
    
    async def run(self):
        """Główna pętla aplikacji"""
        if not await self.initialize():
            return
            
        while True:
            try:
                choice = await self.ui.show_main_menu()
                
                if choice == "1":
                    await self.process_receipts()
                elif choice == "2":
                    await self.manage_rag_knowledge()
                elif choice == "3":
                    await self.chat_conversation()
                elif choice == "4":
                    await self.show_statistics()
                elif choice == "5":
                    await self.manage_exports()
                elif choice == "6":
                    await self.show_help()
                elif choice == "7":
                    console.print("[bold blue]👋 Do widzenia![/bold blue]")
                    break
                else:
                    console.print("[red]❌ Nieprawidłowy wybór![/red]")
                    
            except KeyboardInterrupt:
                console.print("\n[bold blue]👋 Do widzenia![/bold blue]")
                break
            except Exception as e:
                logger.error(f"Błąd w głównej pętli: {e}")
                console.print(f"[bold red]❌ Błąd: {e}[/bold red]")
    
    async def process_receipts(self):
        """Przetwarzanie paragonów"""
        try:
            paragony_dir = Path(self.config.PARAGONY_DIR)
            files = list(paragony_dir.glob("*"))
            
            if not files:
                console.print("[yellow]📁 Katalog paragonów jest pusty![/yellow]")
                return
                
            console.print(f"[bold blue]📄 Znaleziono {len(files)} plików do przetworzenia[/bold blue]")
            
            # Filtruj tylko pliki obrazów i PDF
            image_files = [f for f in files if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.pdf']]
            
            if not image_files:
                console.print("[yellow]📁 Brak plików obrazów lub PDF do przetworzenia[/yellow]")
                return
                
            console.print(f"[bold blue]🖼️  Znaleziono {len(image_files)} plików obrazów/PDF[/bold blue]")
            
            # Menu wyboru
            choice = await self.ui.show_receipt_processing_menu(len(image_files))
            
            if choice == "1":
                # Przetwarzaj wszystkie
                await self._process_all_receipts(image_files)
            elif choice == "2":
                # Wybierz konkretny plik
                selected_file = await self.ui.select_file(image_files)
                if selected_file:
                    await self._process_single_receipt(selected_file)
            elif choice == "3":
                # Powrót
                return
                
        except Exception as e:
            logger.error(f"Błąd przetwarzania paragonów: {e}")
            console.print(f"[bold red]❌ Błąd: {e}[/bold red]")
    
    async def _process_all_receipts(self, files: list[Path]):
        """Przetwarzanie wszystkich paragonów"""
        console.print("[bold blue]🔄 Przetwarzanie wszystkich paragonów...[/bold blue]")
        
        results = []
        for i, file in enumerate(files, 1):
            console.print(f"[blue]📄 Przetwarzanie {i}/{len(files)}: {file.name}[/blue]")
            result = await self.receipt_processor.process_file(file)
            results.append(result)
            
        # Podsumowanie
        successful = sum(1 for r in results if r.get('success', False))
        console.print(f"[bold green]✅ Przetworzono {successful}/{len(files)} paragonów[/bold green]")
        
        # Pokaż szczegóły
        await self.ui.show_processing_results(results)
    
    async def _process_single_receipt(self, file: Path):
        """Przetwarzanie pojedynczego paragonu"""
        console.print(f"[bold blue]📄 Przetwarzanie: {file.name}[/bold blue]")
        
        result = await self.receipt_processor.process_file(file)
        
        if result.get('success', False):
            console.print("[bold green]✅ Paragon przetworzony pomyślnie![/bold green]")
            await self.ui.show_receipt_details(result)
        else:
            console.print(f"[bold red]❌ Błąd przetwarzania: {result.get('error', 'Nieznany błąd')}[/bold red]")
    
    async def manage_rag_knowledge(self):
        """Zarządzanie wiedzą RAG"""
        try:
            choice = await self.ui.show_rag_menu()
            
            if choice == "1":
                await self._add_rag_documents()
            elif choice == "2":
                await self._search_rag_knowledge()
            elif choice == "3":
                await self._list_rag_documents()
            elif choice == "4":
                return
                
        except Exception as e:
            logger.error(f"Błąd zarządzania RAG: {e}")
            console.print(f"[bold red]❌ Błąd: {e}[/bold red]")
    
    async def _add_rag_documents(self):
        """Dodawanie dokumentów do RAG"""
        console.print("[bold blue]📚 Dodawanie dokumentów do bazy wiedzy...[/bold blue]")
        
        wiedza_dir = Path(self.config.WIEDZA_RAG_DIR)
        files = list(wiedza_dir.glob("*"))
        
        if not files:
            console.print("[yellow]📁 Katalog wiedzy RAG jest pusty![/yellow]")
            return
            
        # Filtruj pliki tekstowe
        text_files = [f for f in files if f.suffix.lower() in ['.txt', '.md', '.pdf', '.docx']]
        
        if not text_files:
            console.print("[yellow]📁 Brak plików tekstowych do dodania[/yellow]")
            return
            
        console.print(f"[bold blue]📄 Znaleziono {len(text_files)} plików do dodania[/bold blue]")
        
        # Dodaj wszystkie pliki
        for file in text_files:
            console.print(f"[blue]📄 Dodawanie: {file.name}[/blue]")
            result = await self.rag_manager.add_document(file)
            if result.get('success', False):
                console.print(f"[green]✅ Dodano: {file.name}[/green]")
            else:
                console.print(f"[red]❌ Błąd dodawania: {file.name}[/red]")
    
    async def _search_rag_knowledge(self):
        """Wyszukiwanie w bazie wiedzy"""
        query = Prompt.ask("[bold blue]🔍 Wprowadź zapytanie do wyszukania")
        
        if not query.strip():
            return
            
        console.print("[blue]🔍 Wyszukiwanie...[/blue]")
        results = await self.rag_manager.search(query)
        
        if results:
            await self.ui.show_search_results(results)
        else:
            console.print("[yellow]📭 Nie znaleziono wyników[/yellow]")
    
    async def _list_rag_documents(self):
        """Lista dokumentów w bazie wiedzy"""
        documents = await self.rag_manager.list_documents()
        
        if documents:
            await self.ui.show_documents_list(documents)
        else:
            console.print("[yellow]📭 Baza wiedzy jest pusta[/yellow]")
    
    async def show_statistics(self):
        """Wyświetlanie statystyk"""
        try:
            stats = await self.receipt_processor.get_statistics()
            await self.ui.show_statistics(stats)
        except Exception as e:
            logger.error(f"Błąd pobierania statystyk: {e}")
            console.print(f"[bold red]❌ Błąd: {e}[/bold red]")
    
    async def manage_exports(self):
        """Zarządzanie eksportami"""
        try:
            choice = await self.ui.show_export_menu()
            
            if choice == "1":
                await self._list_exports()
            elif choice == "2":
                await self._export_receipt_results()
            elif choice == "3":
                await self._export_rag_results()
            elif choice == "4":
                await self._delete_export()
            elif choice == "5":
                return
                
        except Exception as e:
            logger.error(f"Błąd zarządzania eksportami: {e}")
            console.print(f"[bold red]❌ Błąd: {e}[/bold red]")
    
    async def _list_exports(self):
        """Lista dostępnych eksportów"""
        exports = await self.export_manager.list_exports()
        
        if exports:
            await self.ui.show_exports_list(exports)
        else:
            console.print("[yellow]📭 Brak dostępnych eksportów[/yellow]")
    
    async def _export_receipt_results(self):
        """Eksport wyników przetwarzania paragonów"""
        # Tutaj można dodać logikę do pobrania ostatnich wyników
        # Na razie używamy pustej listy jako przykład
        results = []
        
        if not results:
            console.print("[yellow]📭 Brak wyników do eksportu[/yellow]")
            return
        
        format_choice = await self.ui.show_export_format_menu()
        if format_choice:
            result = await self.export_manager.export_receipt_results(results, format_choice)
            
            if result.get('success', False):
                console.print(f"[green]✅ Wyeksportowano: {result['filename']}[/green]")
            else:
                console.print(f"[red]❌ Błąd eksportu: {result.get('error', 'Nieznany błąd')}[/red]")
    
    async def _export_rag_results(self):
        """Eksport wyników wyszukiwania RAG"""
        # Tutaj można dodać logikę do pobrania ostatnich wyników
        # Na razie używamy pustej listy jako przykład
        results = []
        
        if not results:
            console.print("[yellow]📭 Brak wyników do eksportu[/yellow]")
            return
        
        format_choice = await self.ui.show_export_format_menu()
        if format_choice:
            result = await self.export_manager.export_rag_results(results, format_choice)
            
            if result.get('success', False):
                console.print(f"[green]✅ Wyeksportowano: {result['filename']}[/green]")
            else:
                console.print(f"[red]❌ Błąd eksportu: {result.get('error', 'Nieznany błąd')}[/red]")
    
    async def _delete_export(self):
        """Usunięcie eksportu"""
        exports = await self.export_manager.list_exports()
        
        if not exports:
            console.print("[yellow]📭 Brak eksportów do usunięcia[/yellow]")
            return
        
        selected_export = await self.ui.select_export(exports)
        if selected_export:
            result = await self.export_manager.delete_export(selected_export['filename'])
            
            if result.get('success', False):
                console.print(f"[green]✅ {result['message']}[/green]")
            else:
                console.print(f"[red]❌ Błąd usuwania: {result.get('error', 'Nieznany błąd')}[/red]")
    
    async def chat_conversation(self):
        """Chat z agentem AI"""
        if not self.chat_agent:
            console.print("[bold red]❌ Agent chatowy nie został zainicjalizowany![/bold red]")
            return
        
        try:
            await self.ui.show_chat_interface(self.chat_agent)
        except Exception as e:
            logger.error(f"Błąd czatu: {e}")
            console.print(f"[bold red]❌ Błąd czatu: {e}[/bold red]")

    async def show_help(self):
        """Wyświetlanie pomocy"""
        await self.ui.show_help()


@click.command()
@click.option('--config', '-c', help='Ścieżka do pliku konfiguracyjnego')
@click.option('--debug', '-d', is_flag=True, help='Tryb debug')
def main(config: Optional[str], debug: bool):
    """Aplikacja konsolowa do przetwarzania paragonów z AI"""
    
    if debug:
        structlog.configure(processors=[structlog.dev.ConsoleRenderer()])
    
    console.print(Panel.fit(
        "[bold blue]🤖 Agenty Console App[/bold blue]\n"
        "[dim]Aplikacja do przetwarzania paragonów z wykorzystaniem AI[/dim]",
        border_style="blue"
    ))
    
    app = AgentyConsoleApp()
    
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        console.print("\n[bold blue]👋 Do widzenia![/bold blue]")
    except Exception as e:
        logger.error(f"Błąd aplikacji: {e}")
        console.print(f"[bold red]❌ Błąd aplikacji: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main() 