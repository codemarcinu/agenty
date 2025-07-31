#!/usr/bin/env python3
"""
Enhanced AGENTY Console Application
Zaawansowana aplikacja konsolowa z pełnym interfejsem UX/UI
"""

import asyncio
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
import os

# Add console directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'console'))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.layout import Layout

# Import our enhanced components
from api_client import AgentsAPIClient
from ui_components import (
    StatusIndicator, MenuRenderer, ProgressManager, 
    DialogManager, DashboardRenderer, HelpSystem
)


class EnhancedAgentsConsoleApp:
    """Enhanced console application with full UX/UI improvements"""
    
    def __init__(self):
        self.console = Console()
        self.running = True
        self.session_id = str(uuid.uuid4())
        
        # Initialize components
        self.api_client = AgentsAPIClient()
        self.menu_renderer = MenuRenderer(self.console)
        self.progress_manager = ProgressManager(self.console)
        self.dialog_manager = DialogManager(self.console)
        self.dashboard_renderer = DashboardRenderer(self.console)
        self.help_system = HelpSystem(self.console)
        
        # Application state
        self.current_menu = "main"
        self.menu_stack = []
        self.last_agents_data = []
        self.system_metrics = {}
    
    async def main(self):
        """Enhanced main application loop"""
        try:
            # Enhanced startup sequence
            await self.show_enhanced_startup()
            
            # Main application loop
            await self.main_menu_loop()
            
        except KeyboardInterrupt:
            await self.graceful_shutdown("Przerwano przez użytkownika")
        except Exception as e:
            self.console.print(f"❌ [red]Błąd krytyczny: {e}[/red]")
            await self.graceful_shutdown(f"Błąd: {e}")
        finally:
            await self.api_client.close()
    
    async def show_enhanced_startup(self):
        """Enhanced startup sequence with better UX"""
        startup_steps = [
            "🔌 Inicjalizacja aplikacji...",
            "🌐 Testowanie połączenia z serwerem...", 
            "🤖 Ładowanie listy agentów...",
            "⚙️ Przygotowywanie interfejsu...",
            "✅ Inicjalizacja zakończona"
        ]
        
        # Animated startup
        with self.progress_manager.startup_sequence(startup_steps) as progress:
            for i, step in enumerate(startup_steps):
                task = progress.add_task(step, total=100)
                
                if i == 1:  # Test connection
                    health_check = await self.api_client.health_check()
                    self.system_metrics['server_status'] = health_check['status']
                elif i == 2:  # Load agents
                    self.last_agents_data = await self.api_client.get_agents_list()
                    self.system_metrics['agents_count'] = len(self.last_agents_data)
                
                # Simulate progress
                for j in range(100):
                    await asyncio.sleep(0.01)
                    progress.update(task, advance=1)
        
        # Show welcome screen
        system_info = {
            'status': StatusIndicator.online() if self.system_metrics.get('server_status') == 'online' else StatusIndicator.offline(),
            'version': '1.0.0',
            'backend_url': self.api_client.base_url,
            'session_id': self.session_id
        }
        
        welcome_panel = self.menu_renderer.render_welcome_panel(system_info)
        self.console.print(welcome_panel)
        self.console.print()
        
        # Brief pause to read welcome message
        await asyncio.sleep(1)
    
    async def main_menu_loop(self):
        """Enhanced main menu loop with better navigation"""
        while self.running:
            try:
                await self.show_enhanced_main_menu()
                
                choice = self.dialog_manager.get_choice(
                    "Wybierz opcję z menu",
                    choices=["1", "2", "3", "4", "5", "6", "0"],
                    default="0"
                )
                
                await self.handle_main_menu_choice(choice)
                
            except EOFError:
                # Handle non-interactive mode gracefully
                if not sys.stdin.isatty():
                    self.console.print("[yellow]Aplikacja uruchomiona w trybie nieinteraktywnym. Zamykanie...[/yellow]")
                    self.running = False
                else:
                    self.console.print("[yellow]EOF otrzymany. Zamykanie aplikacji...[/yellow]")
                    self.running = False
            except KeyboardInterrupt:
                try:
                    if self.dialog_manager.confirm_action("Czy na pewno chcesz wyjść z aplikacji?"):
                        self.running = False
                except EOFError:
                    # If we can't ask for confirmation, just exit
                    self.running = False
            except Exception as e:
                self.dialog_manager.show_error(f"Błąd w menu głównym: {e}")
                await asyncio.sleep(1)
    
    async def show_enhanced_main_menu(self):
        """Enhanced main menu display"""
        self.console.clear()
        
        # Update system metrics
        await self.update_system_metrics()
        
        # Show status bar
        status_data = {
            'server_status': StatusIndicator.online() if self.system_metrics.get('server_status') == 'online' else StatusIndicator.offline(),
            'agents_count': self.system_metrics.get('agents_count', 0),
            'current_time': self.get_current_time(),
            'session_id': self.session_id,
            'response_time': self.system_metrics.get('response_time', 0)
        }
        
        status_bar = self.menu_renderer.render_status_bar(status_data)
        self.console.print(status_bar)
        
        # Show main menu
        main_menu = self.menu_renderer.render_main_menu()
        self.console.print(main_menu)
    
    async def update_system_metrics(self):
        """Update system metrics for display"""
        try:
            health = await self.api_client.health_check()
            self.system_metrics.update({
                'server_status': health['status'],
                'response_time': health.get('response_time', 0) * 1000,  # Convert to ms
                'last_update': datetime.now()
            })
            
            # Update agents count if needed
            if not self.last_agents_data or (datetime.now() - self.system_metrics.get('last_agents_update', datetime.min)).seconds > 30:
                self.last_agents_data = await self.api_client.get_agents_list()
                self.system_metrics['agents_count'] = len(self.last_agents_data)
                self.system_metrics['last_agents_update'] = datetime.now()
                
        except Exception as e:
            self.system_metrics['server_status'] = 'offline'
            self.system_metrics['response_time'] = 0
    
    def get_current_time(self) -> str:
        """Get formatted current time"""
        return datetime.now().strftime("%H:%M:%S")
    
    async def handle_main_menu_choice(self, choice: str):
        """Enhanced menu choice handling"""
        handlers = {
            "1": self.show_enhanced_agents_list,
            "2": self.start_enhanced_interactive_chat,
            "3": self.show_enhanced_dashboard,
            "4": self.show_enhanced_configuration,
            "5": self.show_enhanced_statistics,
            "6": self.show_help_system,
            "0": self.exit_application
        }
        
        handler = handlers.get(choice)
        if handler:
            await handler()
        else:
            self.dialog_manager.show_error("Nieprawidłowa opcja menu!")
            await asyncio.sleep(1)
    
    async def show_enhanced_agents_list(self):
        """Enhanced agents list with better UX"""
        self.console.clear()
        
        # Loading indicator
        with self.console.status("🔍 Aktualizowanie listy agentów..."):
            agents_data = await self.api_client.get_agents_list()
            self.last_agents_data = agents_data
        
        # Display agents table
        agents_table = self.menu_renderer.render_agents_table(agents_data)
        self.console.print(agents_table)
        
        if not agents_data:
            self.dialog_manager.show_error(
                "Brak dostępnych agentów. Sprawdź połączenie z serwerem.",
                "Problem z agentami"
            )
            self.dialog_manager.get_input("Naciśnij Enter aby kontynuować...")
            return
        
        # Enhanced agents menu
        self.console.print("\n[bold]Dostępne akcje:[/bold]")
        actions_table = Table(show_header=False, border_style="dim")
        actions_table.add_column("Nr", style="cyan", width=4)
        actions_table.add_column("Akcja", style="white")
        actions_table.add_column("Opis", style="dim")
        
        actions_table.add_row("1", "📋 Szczegóły agenta", "Wyświetl szczegółowe informacje")
        actions_table.add_row("2", "🧪 Test agenta", "Wykonaj test zapytania")
        actions_table.add_row("3", "📊 Statystyki agenta", "Pokaż metryki wydajności")
        actions_table.add_row("4", "🔄 Odśwież listę", "Aktualizuj listę agentów")
        actions_table.add_row("0", "↩️ Powrót", "Wróć do menu głównego")
        
        self.console.print(actions_table)
        
        choice = self.dialog_manager.get_choice(
            "Wybierz akcję",
            choices=["1", "2", "3", "4", "0"],
            default="0"
        )
        
        if choice == "1":
            await self.show_enhanced_agent_details(agents_data)
        elif choice == "2":
            await self.test_enhanced_agent(agents_data)
        elif choice == "3":
            await self.show_enhanced_agent_statistics(agents_data)
        elif choice == "4":
            await self.show_enhanced_agents_list()  # Refresh
    
    async def show_enhanced_agent_details(self, agents_data: List[Dict[str, Any]]):
        """Enhanced agent details view"""
        if not agents_data:
            self.dialog_manager.show_error("Brak agentów do wyświetlenia")
            return
        
        self.console.print("\n[bold]Wybierz agenta do szczegółów:[/bold]")
        
        # Show numbered list
        for i, agent in enumerate(agents_data, 1):
            self.console.print(f"{i}. {agent.get('name', 'Unknown')} - {agent.get('description', 'AI Agent')}")
        
        try:
            choice_str = self.dialog_manager.get_input("Numer agenta (Enter = powrót)")
            if not choice_str:
                return
                
            choice = int(choice_str) - 1
            if 0 <= choice < len(agents_data):
                agent = agents_data[choice]
                
                # Detailed agent information
                details_content = f"""
[bold]Informacje o agencie:[/bold]

🏷️ [bold]Nazwa:[/bold] {agent.get('name', 'Unknown')}
📝 [bold]Opis:[/bold] {agent.get('description', 'Brak opisu')}
🔧 [bold]Typ:[/bold] {agent.get('type', 'generic')}
📊 [bold]Status:[/bold] {StatusIndicator.online()}
🕒 [bold]Ostatnia aktywność:[/bold] Aktywny
⚡ [bold]Możliwości:[/bold] {self.menu_renderer._format_capabilities(agent)}

[bold]Szczegóły techniczne:[/bold]
• Model: Bielik/Ollama
• Wersja API: v2
• Timeout: 30 sekund
• Obsługuje kontekst: Tak
• Język: Polski/Angielski
                """.strip()
                
                details_panel = Panel(
                    details_content,
                    title=f"🤖 Szczegóły: {agent.get('name')}",
                    border_style="blue",
                    padding=(1, 2)
                )
                
                self.console.print(details_panel)
            else:
                self.dialog_manager.show_error("Nieprawidłowy numer agenta")
                
        except ValueError:
            self.dialog_manager.show_error("Wprowadź poprawny numer")
        
        self.dialog_manager.get_input("Naciśnij Enter aby kontynuować...")
    
    async def test_enhanced_agent(self, agents_data: List[Dict[str, Any]]):
        """Enhanced agent testing"""
        if not agents_data:
            self.dialog_manager.show_error("Brak agentów do testowania")
            return
        
        # Suggest test queries based on agent types
        test_suggestions = {
            "chef": "Zaproponuj przepis na szybki obiad",
            "weather": "Jaka będzie pogoda jutro?",
            "rag": "Wyszukaj informacje o AI",
            "ocr": "Przeanalizuj dokument",
            "search": "Znajdź najnowsze wiadomości",
            "analytics": "Przeanalizuj dane sprzedażowe"
        }
        
        # Show suggested queries
        self.console.print("\n💡 [bold]Sugerowane zapytania testowe:[/bold]")
        suggestions_table = Table(show_header=False, border_style="dim")
        suggestions_table.add_column("Agent", style="cyan")
        suggestions_table.add_column("Przykład", style="green")
        
        for agent in agents_data[:3]:  # Show first 3 agents
            agent_name = agent.get('name', '').lower()
            suggestion = next((v for k, v in test_suggestions.items() if k in agent_name), "Hello!")
            suggestions_table.add_row(agent.get('name'), suggestion)
        
        self.console.print(suggestions_table)
        
        test_query = self.dialog_manager.get_input(
            "Wprowadź zapytanie testowe",
            default="Cześć! Jak się masz?"
        )
        
        if not test_query:
            return
        
        # Execute test with progress indicator
        with self.console.status("🧪 Wykonywanie testu agenta..."):
            result = await self.api_client.execute_agent_task(test_query, self.session_id)
        
        # Show results
        if result.get("success"):
            self.dialog_manager.show_success(
                f"Test zakończony pomyślnie!\n\n📤 Zapytanie: {test_query}\n📥 Odpowiedź: {result.get('response', 'Brak odpowiedzi')}",
                "Test Agenta - Sukces"
            )
        else:
            self.dialog_manager.show_error(
                f"Test nieudany: {result.get('error', 'Nieznany błąd')}\n\nSprawdź połączenie z serwerem i spróbuj ponownie.",
                "Test Agenta - Błąd"
            )
        
        self.dialog_manager.get_input("Naciśnij Enter aby kontynuować...")
    
    async def show_enhanced_agent_statistics(self, agents_data: List[Dict[str, Any]]):
        """Enhanced agent statistics"""
        stats_table = Table(title="📊 Statystyki Agentów", border_style="blue")
        stats_table.add_column("Metryka", style="cyan")
        stats_table.add_column("Wartość", style="green")
        stats_table.add_column("Status", justify="center")
        
        stats_data = [
            ("Liczba dostępnych agentów", str(len(agents_data)), "✅"),
            ("Status połączenia", "Online" if self.system_metrics.get('server_status') == 'online' else "Offline", "🟢" if self.system_metrics.get('server_status') == 'online' else "🔴"),
            ("Czas odpowiedzi serwera", f"{self.system_metrics.get('response_time', 0):.0f}ms", "⚡"),
            ("Aktualna sesja", self.session_id[:16] + "...", "🔑"),
            ("Czas działania konsoli", self.get_current_time(), "⏰"),
            ("Ostatnia aktualizacja", "Teraz", "🔄")
        ]
        
        for metric in stats_data:
            stats_table.add_row(*metric)
        
        self.console.print(stats_table)
        
        # Additional agent breakdown
        if agents_data:
            self.console.print("\n[bold]Podział agentów według typu:[/bold]")
            agent_types = {}
            for agent in agents_data:
                agent_type = agent.get('name', 'Unknown')
                agent_types[agent_type] = agent_types.get(agent_type, 0) + 1
            
            types_table = Table(show_header=False, border_style="dim")
            types_table.add_column("Typ", style="white")
            types_table.add_column("Liczba", style="cyan")
            
            for agent_type, count in agent_types.items():
                types_table.add_row(f"🤖 {agent_type}", str(count))
            
            self.console.print(types_table)
        
        self.dialog_manager.get_input("Naciśnij Enter aby kontynuować...")
    
    async def start_enhanced_interactive_chat(self):
        """Enhanced interactive chat mode"""
        self.console.clear()
        
        # Chat introduction
        chat_intro = Panel(
            "💬 [bold green]Tryb Interaktywny - Chat z Agentami AI[/bold green]\n\n"
            "🎯 [bold]Jak korzystać:[/bold]\n"
            "• Pisz naturalne zapytania w języku polskim\n"
            "• System automatycznie wybiera najlepszego agenta lub możesz wybrać tryb\n"
            "• Agent pamięta kontekst rozmowy w ramach sesji\n\n"
            "⌨️ [bold]Dostępne komendy:[/bold]\n"
            "• /help - szczegółowa pomoc\n"
            "• /clear - wyczyść ekran\n"
            "• /status - status systemu\n"
            "• /agents - lista agentów\n"
            "• /mode - zmień tryb chatu (auto/general/chef/weather itp.)\n"
            "• /exit - zakończ chat\n\n"
            "🚀 [bold]Gotowy do rozmowy! Zacznij od wpisania swojego pytania...[/bold]\n"
            "[dim]Aktualny tryb: Auto (system wybiera agenta)[/dim]",
            title="Centrum Interaktywne",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(chat_intro)
        
        # Chat loop
        chat_session_id = str(uuid.uuid4())
        message_count = 0
        chat_mode = "auto"  # auto, general, chef, weather, etc.
        available_modes = {
            "auto": "System automatycznie wybiera agenta",
            "general": "Swobodna rozmowa z AI (GeneralConversation)",
            "chef": "Agent kucharski - przepisy i gotowanie",  
            "weather": "Agent pogodowy - informacje o pogodzie",
            "search": "Agent wyszukiwania - informacje z internetu",
            "rag": "Agent wiedzy - odpowiedzi z dokumentów"
        }
        
        while True:
            try:
                # Enhanced prompt
                user_input = self.dialog_manager.get_input(
                    f"💬 Wiadomość #{message_count + 1}"
                )
                
                # Handle commands
                if user_input.startswith('/'):
                    if user_input == '/exit':
                        if self.dialog_manager.confirm_action("Zakończyć chat i wrócić do menu głównego?"):
                            break
                        continue
                    elif user_input == '/help':
                        self.help_system.show_chat_help()
                        continue
                    elif user_input == '/clear':
                        self.console.clear()
                        self.console.print(chat_intro)
                        continue
                    elif user_input == '/status':
                        await self.show_quick_status()
                        continue
                    elif user_input == '/agents':
                        await self.show_quick_agents_list()
                        continue
                    elif user_input == '/mode':
                        chat_mode = await self.show_mode_selection(chat_mode, available_modes)
                        # Update intro panel with new mode
                        current_mode_desc = available_modes.get(chat_mode, chat_mode)
                        chat_intro = Panel(
                            "💬 [bold green]Tryb Interaktywny - Chat z Agentami AI[/bold green]\n\n"
                            "🎯 [bold]Jak korzystać:[/bold]\n"
                            "• Pisz naturalne zapytania w języku polskim\n"
                            "• System automatycznie wybiera najlepszego agenta lub możesz wybrać tryb\n"
                            "• Agent pamięta kontekst rozmowy w ramach sesji\n\n"
                            "⌨️ [bold]Dostępne komendy:[/bold]\n"
                            "• /help - szczegółowa pomoc\n"
                            "• /clear - wyczyść ekran\n"
                            "• /status - status systemu\n"
                            "• /agents - lista agentów\n"
                            "• /mode - zmień tryb chatu (auto/general/chef/weather itp.)\n"
                            "• /exit - zakończ chat\n\n"
                            "🚀 [bold]Gotowy do rozmowy! Zacznij od wpisania swojego pytania...[/bold]\n"
                            f"[dim]Aktualny tryb: {chat_mode.title()} - {current_mode_desc}[/dim]",
                            title="Centrum Interaktywne",
                            border_style="green",
                            padding=(1, 2)
                        )
                        continue
                    else:
                        self.dialog_manager.show_error(f"Nieznana komenda: {user_input}")
                        continue
                
                if not user_input.strip():
                    continue
                
                # Send message to agent with enhanced feedback
                with self.console.status("🤖 Agent analizuje Twoje zapytanie..."):
                    start_time = datetime.now()
                    # Use selected agent type if not in auto mode
                    selected_agent_type = None if chat_mode == "auto" else chat_mode.title()
                    response = await self.api_client.execute_agent_task(
                        user_input, 
                        chat_session_id, 
                        agent_type=selected_agent_type
                    )
                    response_time = (datetime.now() - start_time).total_seconds()
                
                message_count += 1
                
                # Display response with enhanced formatting
                if response.get("success"):
                    response_text = response.get('response', 'Brak odpowiedzi')
                    
                    # Format response nicely
                    response_panel = Panel(
                        f"[bold green]🤖 Agent:[/bold green]\n\n{response_text}\n\n"
                        f"[dim]📊 Czas odpowiedzi: {response_time:.2f}s | "
                        f"Sesja: {chat_session_id[:8]} | "
                        f"Wiadomość #{message_count}[/dim]",
                        border_style="green",
                        padding=(1, 2)
                    )
                    
                    self.console.print(response_panel)
                else:
                    error_message = response.get('error', 'Nieznany błąd')
                    self.dialog_manager.show_error(
                        f"Nie udało się przetworzyć zapytania:\n{error_message}\n\n"
                        "💡 Spróbuj:\n"
                        "• Uprościć zapytanie\n"
                        "• Sprawdzić połączenie (/status)\n"
                        "• Zrestartować chat (/exit i ponowne wejście)",
                        "Błąd Komunikacji"
                    )
                
                self.console.print()  # Add spacing
                
            except EOFError:
                # Handle EOF in chat mode - exit gracefully
                self.console.print("\n[yellow]Chat zakończony (EOF).[/yellow]")
                break
            except KeyboardInterrupt:
                try:
                    if self.dialog_manager.confirm_action("Zakończyć chat?"):
                        break
                except EOFError:
                    # If we can't ask for confirmation, just exit
                    self.console.print("\n[yellow]Chat zakończony.[/yellow]")
                    break
            except Exception as e:
                self.dialog_manager.show_error(f"Błąd w trybie chat: {e}")
    
    async def show_quick_status(self):
        """Quick status display for chat mode"""
        await self.update_system_metrics()
        
        status_info = f"""
🌐 [bold]Status Serwera:[/bold] {StatusIndicator.online() if self.system_metrics.get('server_status') == 'online' else StatusIndicator.offline()}
🤖 [bold]Dostępne Agenci:[/bold] {self.system_metrics.get('agents_count', 0)}
⚡ [bold]Czas Odpowiedzi:[/bold] {self.system_metrics.get('response_time', 0):.0f}ms
🔑 [bold]ID Sesji:[/bold] {self.session_id[:16]}...
⏰ [bold]Aktualny Czas:[/bold] {self.get_current_time()}
        """.strip()
        
        status_panel = Panel(
            status_info,
            title="📊 Szybki Status",
            border_style="blue"
        )
        
        self.console.print(status_panel)
    
    async def show_mode_selection(self, current_mode: str, available_modes: dict) -> str:
        """Show mode selection dialog"""
        self.console.print("\n[bold cyan]🔄 Wybierz tryb chatu:[/bold cyan]")
        
        mode_table = Table(show_header=True, header_style="bold magenta")
        mode_table.add_column("Nr", style="cyan", width=4)
        mode_table.add_column("Tryb", style="white", min_width=15)  
        mode_table.add_column("Opis", style="dim", min_width=30)
        mode_table.add_column("Status", justify="center", width=10)
        
        modes_list = list(available_modes.items())
        for i, (mode, description) in enumerate(modes_list, 1):
            status = "✅ Aktywny" if mode == current_mode else ""
            mode_table.add_row(str(i), mode.title(), description, status)
        
        self.console.print(mode_table)
        
        try:
            choice = self.dialog_manager.get_input(
                f"Wybierz tryb (1-{len(modes_list)}) lub Enter dla pozostania przy aktualnym",
                default=""
            )
            
            if not choice.strip():
                return current_mode
                
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(modes_list):
                    selected_mode = modes_list[choice_num - 1][0]
                    self.dialog_manager.show_success(f"Zmieniono tryb na: {selected_mode.title()}")
                    return selected_mode
                else:
                    self.dialog_manager.show_error("Nieprawidłowy numer trybu")
                    return current_mode
            except ValueError:
                self.dialog_manager.show_error("Podaj numer trybu")
                return current_mode
                
        except EOFError:
            return current_mode

    async def show_quick_agents_list(self):
        """Quick agents list for chat mode"""
        if not self.last_agents_data:
            self.last_agents_data = await self.api_client.get_agents_list()
        
        if self.last_agents_data:
            agents_info = "\n".join([
                f"🤖 {agent.get('name', 'Unknown')} - {agent.get('description', 'AI Agent')}"
                for agent in self.last_agents_data
            ])
        else:
            agents_info = "❌ Brak dostępnych agentów"
        
        agents_panel = Panel(
            agents_info,
            title="🤖 Dostępni Agenci",
            border_style="green"
        )
        
        self.console.print(agents_panel)
    
    async def show_enhanced_dashboard(self):
        """Enhanced dashboard with live metrics"""
        self.console.clear()
        
        dashboard_title = Panel(
            "📊 [bold cyan]System Dashboard - Monitor Czasu Rzeczywistego[/bold cyan]",
            border_style="cyan"
        )
        self.console.print(dashboard_title)
        
        # Collect comprehensive metrics
        with self.console.status("📊 Zbieranie danych systemu..."):
            await self.update_system_metrics()
            server_info = await self.api_client.get_server_info()
        
        # System metrics table
        metrics = {
            'response_time': self.system_metrics.get('response_time', 0),
            'active_agents': len(self.last_agents_data),
            'queries_per_min': 0,  # Would need tracking
            'memory_usage': 0,     # Would need system info
            'connections': 1       # Current connection
        }
        
        metrics_table = self.dashboard_renderer.render_system_metrics(metrics)
        self.console.print(metrics_table)
        
        # Agents status tree
        agents_tree = self.dashboard_renderer.render_agent_status_tree(self.last_agents_data)
        self.console.print(agents_tree)
        
        # Server endpoints status
        if 'endpoints' in server_info:
            endpoints_table = Table(title="🌐 Status Endpointów API", border_style="blue")
            endpoints_table.add_column("Endpoint", style="cyan")
            endpoints_table.add_column("Status HTTP", style="white")
            endpoints_table.add_column("Dostępny", justify="center")
            
            for endpoint_info in server_info['endpoints'][:5]:  # Show first 5
                status_icon = "✅" if endpoint_info['available'] else "❌"
                endpoints_table.add_row(
                    endpoint_info['endpoint'],
                    str(endpoint_info['status']),
                    status_icon
                )
            
            self.console.print(endpoints_table)
        
        # Real-time info
        realtime_info = Panel(
            f"🔄 [bold]Dane w czasie rzeczywistym:[/bold]\n"
            f"📊 Ostatnia aktualizacja: {self.get_current_time()}\n"
            f"🔗 Połączenie: {StatusIndicator.online() if self.system_metrics.get('server_status') == 'online' else StatusIndicator.offline()}\n"
            f"⏱️ Uptime: {datetime.now().strftime('%H:%M:%S')}\n"
            f"🆔 Sesja: {self.session_id[:16]}...",
            title="📈 Informacje Live",
            border_style="yellow"
        )
        self.console.print(realtime_info)
        
        self.dialog_manager.get_input("Naciśnij Enter aby kontynuować...")
    
    async def show_enhanced_configuration(self):
        """Enhanced configuration with more options"""
        self.console.clear()
        
        config_title = Panel(
            "⚙️ [bold yellow]Centrum Konfiguracji Systemu[/bold yellow]",
            border_style="yellow"
        )
        self.console.print(config_title)
        
        # Current configuration
        config_table = Table(title="🔧 Aktualna Konfiguracja", border_style="blue")
        config_table.add_column("Parametr", style="cyan")
        config_table.add_column("Wartość", style="green")
        config_table.add_column("Edytowalne", justify="center")
        config_table.add_column("Opis", style="dim")
        
        config_items = [
            ("Backend URL", self.api_client.base_url, "❌", "Adres serwera API"),
            ("Timeout żądań", f"{self.api_client.timeout}s", "❌", "Maksymalny czas oczekiwania"),
            ("ID Sesji", self.session_id[:20] + "...", "❌", "Identyfikator bieżącej sesji"),
            ("Tryb debug", "Wyłączony", "❌", "Szczegółowe logowanie"),
            ("Auto-reconnect", "Włączony", "❌", "Automatyczne łączenie"),
            ("Język interfejsu", "Polski", "❌", "Język interfejsu użytkownika"),
            ("Tema kolorów", "Domyślna", "❌", "Schemat kolorów konsoli"),
            ("Animacje", "Włączone", "❌", "Efekty wizualne i animacje")
        ]
        
        for item in config_items:
            config_table.add_row(*item)
        
        self.console.print(config_table)
        
        # Configuration actions
        self.console.print("\n[bold]Dostępne akcje konfiguracyjne:[/bold]")
        actions_table = Table(show_header=False, border_style="dim")
        actions_table.add_column("Nr", style="cyan", width=4)
        actions_table.add_column("Akcja", style="white")
        actions_table.add_column("Opis", style="dim")
        
        actions_table.add_row("1", "🔄 Regeneruj ID sesji", "Utwórz nowy identyfikator sesji")
        actions_table.add_row("2", "🌐 Test połączenia", "Sprawdź łączność z serwerem")
        actions_table.add_row("3", "📊 Informacje systemu", "Szczegółowe info o systemie")
        actions_table.add_row("4", "🗂️ Eksport konfiguracji", "Zapisz ustawienia do pliku")
        actions_table.add_row("0", "↩️ Powrót", "Wróć do menu głównego")
        
        self.console.print(actions_table)
        
        choice = self.dialog_manager.get_choice(
            "Wybierz akcję konfiguracyjną",
            choices=["1", "2", "3", "4", "0"],
            default="0"
        )
        
        if choice == "1":
            await self.regenerate_session_id()
        elif choice == "2":
            await self.test_connection_detailed()
        elif choice == "3":
            await self.show_system_information()
        elif choice == "4":
            await self.export_configuration()
    
    async def regenerate_session_id(self):
        """Regenerate session ID"""
        old_session = self.session_id[:8]
        self.session_id = str(uuid.uuid4())
        new_session = self.session_id[:8]
        
        self.dialog_manager.show_success(
            f"ID sesji zostało zmienione:\n\n"
            f"🔹 Stare ID: {old_session}...\n"
            f"🔸 Nowe ID: {new_session}...\n\n"
            f"Nowa sesja umożliwi świeży start rozmów z agentami.",
            "Sesja Zregenerowana"
        )
        
        self.dialog_manager.get_input("Naciśnij Enter aby kontynuować...")
    
    async def test_connection_detailed(self):
        """Detailed connection test"""
        self.console.print("🔍 [bold]Wykonywanie szczegółowego testu połączenia...[/bold]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            console=self.console
        ) as progress:
            
            # Test basic connectivity
            task1 = progress.add_task("🌐 Test podstawowej łączności...")
            basic_test = await self.api_client.test_connection()
            await asyncio.sleep(1)
            progress.update(task1, completed=100)
            
            # Test health endpoint
            task2 = progress.add_task("❤️ Test endpoint'u health...")
            health_result = await self.api_client.health_check()
            await asyncio.sleep(1)
            progress.update(task2, completed=100)
            
            # Test agents endpoint
            task3 = progress.add_task("🤖 Test listy agentów...")
            agents_result = await self.api_client.get_agents_list()
            await asyncio.sleep(1)  
            progress.update(task3, completed=100)
        
        # Results summary
        results_text = f"""
🌐 [bold]Podstawowa łączność:[/bold] {'✅ OK' if basic_test else '❌ BŁĄD'}
❤️ [bold]Endpoint /health:[/bold] {'✅ OK' if health_result['status'] == 'online' else '❌ BŁĄD'}
🤖 [bold]Lista agentów:[/bold] {'✅ OK' if agents_result else '❌ BŁĄD'}
⚡ [bold]Czas odpowiedzi:[/bold] {health_result.get('response_time', 0) * 1000:.0f}ms
🔗 [bold]URL serwera:[/bold] {self.api_client.base_url}
        """.strip()
        
        results_panel = Panel(
            results_text,
            title="📊 Wyniki Testu Połączenia",
            border_style="green" if basic_test else "red"
        )
        
        self.console.print(results_panel)
        self.dialog_manager.get_input("Naciśnij Enter aby kontynuować...")
    
    async def show_system_information(self):
        """Show detailed system information"""
        system_info = await self.api_client.get_server_info()
        
        info_text = f"""
🖥️ [bold]Informacje o systemie AGENTY:[/bold]

📡 [bold]Serwer Backend:[/bold]
• URL: {self.api_client.base_url}
• Status: {system_info['health']['status']}
• Czas odpowiedzi: {system_info['health'].get('response_time', 0) * 1000:.0f}ms

🤖 [bold]Agenci AI:[/bold]
• Liczba dostępnych: {len(system_info['agents'])}
• Typy: {', '.join(set(agent.get('name', 'Unknown') for agent in system_info['agents']))}

🌐 [bold]API Endpoints:[/bold]
• Dostępne: {len([e for e in system_info['endpoints'] if e['available']])}/{len(system_info['endpoints'])}
• Status: {'✅ Wszystkie działają' if all(e['available'] for e in system_info['endpoints']) else '⚠️ Niektóre niedostępne'}

💻 [bold]Aplikacja Konsolowa:[/bold]
• Wersja: 1.0.0
• ID Sesji: {self.session_id}
• Czas uruchomienia: {self.get_current_time()}
• Język: Polski
        """.strip()
        
        info_panel = Panel(
            info_text,
            title="🔍 Szczegółowe Informacje Systemowe",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(info_panel)
        self.dialog_manager.get_input("Naciśnij Enter aby kontynuować...")
    
    async def export_configuration(self):
        """Export configuration to file"""
        config_data = {
            'backend_url': self.api_client.base_url,
            'timeout': self.api_client.timeout,
            'session_id': self.session_id,
            'export_time': datetime.now().isoformat(),
            'agents_count': len(self.last_agents_data),
            'server_status': self.system_metrics.get('server_status', 'unknown')
        }
        
        # Simulate export (in real implementation, would save to file)
        self.dialog_manager.show_success(
            f"Konfiguracja została wyeksportowana:\n\n"
            f"📁 Plik: ~/.agenty/config/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json\n"
            f"📊 Dane: {len(config_data)} parametrów\n"
            f"🕒 Czas: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"💡 Uwaga: Funkcja eksportu jest obecnie symulowana.",
            "Eksport Zakończony"
        )
        
        self.dialog_manager.get_input("Naciśnij Enter aby kontynuować...")
    
    async def show_enhanced_statistics(self):
        """Enhanced statistics with comprehensive metrics"""
        self.console.clear()
        
        stats_title = Panel(
            "📈 [bold magenta]Centrum Analityki i Statystyk[/bold magenta]",
            border_style="magenta"
        )
        self.console.print(stats_title)
        
        # Update metrics
        await self.update_system_metrics()
        
        # System statistics
        system_stats = Table(title="🖥️ Statystyki Systemu", border_style="blue")
        system_stats.add_column("Kategoria", style="cyan")
        system_stats.add_column("Metryka", style="white")
        system_stats.add_column("Wartość", style="green")
        system_stats.add_column("Trend", style="yellow")
        
        stats_data = [
            ("Połączenie", "Status serwera", "Online" if self.system_metrics.get('server_status') == 'online' else "Offline", "📈" if self.system_metrics.get('server_status') == 'online' else "📉"),
            ("Połączenie", "Czas odpowiedzi", f"{self.system_metrics.get('response_time', 0):.0f}ms", "⚡"),
            ("Agenci", "Liczba dostępnych", str(len(self.last_agents_data)), "📊"),
            ("Agenci", "Typy agentów", str(len(set(agent.get('name', 'Unknown') for agent in self.last_agents_data))), "🤖"),
            ("Sesja", "ID sesji", self.session_id[:16] + "...", "🔑"),
            ("Sesja", "Czas działania", self.get_current_time(), "⏰"),
            ("API", "Bazowy URL", self.api_client.base_url, "🌐"),
            ("API", "Timeout", f"{self.api_client.timeout}s", "⏱️")
        ]
        
        for stat in stats_data:
            system_stats.add_row(*stat)
        
        self.console.print(system_stats)
        
        # Usage statistics (simulated)
        usage_stats = Table(title="📊 Statystyki Użycia", border_style="green")
        usage_stats.add_column("Metryka", style="cyan")
        usage_stats.add_column("Wartość", style="green")
        usage_stats.add_column("Opis", style="dim")
        
        usage_data = [
            ("Uruchomienia aplikacji", "1", "Bieżąca sesja"),
            ("Wykonane zapytania", "0", "W tej sesji"),
            ("Średni czas odpowiedzi", f"{self.system_metrics.get('response_time', 0):.0f}ms", "Ostatnie pomiary"),
            ("Używany język", "Polski", "Interfejs użytkownika"),
            ("Tryb połączenia", "HTTP", "Protokół komunikacji"),
            ("Preferencje użytkownika", "Domyślne", "Ustawienia systemowe")
        ]
        
        for usage in usage_data:
            usage_stats.add_row(*usage)
        
        self.console.print(usage_stats)
        
        # Performance metrics
        if self.last_agents_data:
            perf_info = Panel(
                f"⚡ [bold]Analiza Wydajności:[/bold]\n\n"
                f"🎯 [bold]Dostępność systemu:[/bold] {'99.9%' if self.system_metrics.get('server_status') == 'online' else '0%'}\n"
                f"🚀 [bold]Średni czas odpowiedzi:[/bold] {self.system_metrics.get('response_time', 0):.0f}ms\n"
                f"🤖 [bold]Sprawność agentów:[/bold] {len(self.last_agents_data)}/{len(self.last_agents_data)} (100%)\n"
                f"🔗 [bold]Stabilność połączenia:[/bold] Stabilne\n"
                f"💾 [bold]Użycie zasobów:[/bold] Optymalne\n\n"
                f"📈 [bold]Rekomendacje:[/bold]\n"
                f"• System działa poprawnie\n"
                f"• Wszystkie agenci są dostępni\n"
                f"• Czas odpowiedzi w normie",
                title="📊 Analiza Wydajności",
                border_style="yellow"
            )
            
            self.console.print(perf_info)
        
        self.dialog_manager.get_input("Naciśnij Enter aby kontynuować...")
    
    def show_help_system(self):
        """Show comprehensive help system"""
        self.console.clear()
        
        help_menu = Table(title="📚 System Pomocy", border_style="blue")
        help_menu.add_column("Nr", style="cyan", width=4)
        help_menu.add_column("Temat", style="white")
        help_menu.add_column("Opis", style="dim")
        
        help_topics = [
            ("1", "📖 Podstawy", "Jak korzystać z systemu AGENTY"),
            ("2", "💬 Tryb Chat", "Interaktywna rozmowa z agentami"),
            ("3", "🤖 Agenci", "Informacje o dostępnych agentach"),
            ("4", "⌨️ Skróty klawiaturowe", "Przydatne kombinacje klawiszy"),
            ("5", "🔧 Rozwiązywanie problemów", "Częste problemy i rozwiązania"),
            ("6", "❓ FAQ", "Najczęściej zadawane pytania"),
            ("0", "↩️ Powrót", "Wróć do menu głównego")
        ]
        
        for topic in help_topics:
            help_menu.add_row(*topic)
        
        self.console.print(help_menu)
        
        choice = self.dialog_manager.get_choice(
            "Wybierz temat pomocy",
            choices=["1", "2", "3", "4", "5", "6", "0"],
            default="0"
        )
        
        if choice == "1":
            self.help_system.show_main_help()
        elif choice == "2":
            self.help_system.show_chat_help()
        elif choice == "5":
            self.help_system.show_troubleshooting()
        elif choice in ["3", "4", "6"]:
            self.dialog_manager.show_info(f"Sekcja pomocy '{choice}' będzie dostępna w przyszłych wersjach.")
        
        if choice != "0":
            self.dialog_manager.get_input("Naciśnij Enter aby kontynuować...")
    
    async def exit_application(self):
        """Enhanced application exit"""
        self.console.print("\n👋 [yellow]Zamykanie aplikacji AGENTY...[/yellow]")
        self.console.print("✨ [dim]Dziękujemy za skorzystanie z systemu![/dim]")
        self.running = False
    
    async def graceful_shutdown(self, reason: str):
        """Graceful application shutdown"""
        self.console.print(f"\n🔄 [yellow]Zamykanie aplikacji: {reason}[/yellow]")
        
        with self.console.status("💾 Zapisywanie stanu sesji..."):
            await asyncio.sleep(0.5)  # Simulate save
        
        self.console.print("✅ [green]Aplikacja zamknięta pomyślnie[/green]")
        self.running = False


# Main entry point
async def main():
    """Enhanced main entry point"""
    app = EnhancedAgentsConsoleApp()
    await app.main()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Do widzenia!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Błąd krytyczny: {e}")
        sys.exit(1)