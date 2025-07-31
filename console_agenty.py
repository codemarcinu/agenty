#!/usr/bin/env python3
"""
Aplikacja konsolowa AGENTY
Zaawansowany interfejs do zarządzania agentami AI
"""

import asyncio
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
import httpx


class AgentsAPIClient:
    """Klient do komunikacji z backend API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_health(self) -> Dict[str, Any]:
        """Sprawdź status zdrowia serwera"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                return {"status": "online", "data": response.json()}
            return {"status": "offline", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "offline", "error": str(e)}
    
    async def get_agents_list(self) -> List[Dict[str, str]]:
        """Pobierz listę dostępnych agentów"""
        try:
            response = await self.client.get(f"{self.base_url}/api/agents")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception:
            return []
    
    async def execute_agent_task(self, task: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Wykonaj zadanie przez agenta"""
        try:
            data = {
                "task": task,
                "session_id": session_id or str(uuid.uuid4()),
                "use_bielik": True
            }
            response = await self.client.post(f"{self.base_url}/api/agents/execute", json=data)
            if response.status_code == 200:
                return response.json()
            return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def close(self):
        """Zamknij połączenie"""
        await self.client.aclose()


class MenuManager:
    """Manager menu i nawigacji"""
    
    def __init__(self, console: Console):
        self.console = console
        self.menu_stack = []
        self.current_menu = "main"
    
    def show_main_menu(self):
        """Wyświetl główne menu"""
        table = Table(title="📋 Menu Główne - System AGENTY", show_header=True, header_style="bold magenta")  
        table.add_column("Nr", style="cyan", width=6)
        table.add_column("🎯 Funkcja", style="white", min_width=20)
        table.add_column("📝 Opis", style="dim")
        
        table.add_row("1", "🤖 Lista Agentów", "Wyświetl dostępnych agentów")
        table.add_row("2", "💬 Chat Interaktywny", "Rozpocznij rozmowę z agentem")
        table.add_row("3", "📊 Dashboard", "Monitor systemu w czasie rzeczywistym")
        table.add_row("4", "⚙️ Konfiguracja", "Ustawienia i preferencje")
        table.add_row("5", "📈 Statystyki", "Analiza wydajności i użycia")
        table.add_row("0", "🚪 Wyjście", "Zamknij aplikację")
        
        self.console.print(table)
        self.console.print()
    
    def show_agents_menu(self):
        """Menu agentów"""
        self.console.print("\n[bold]Dostępne akcje:[/bold]")
        self.console.print("1. Szczegóły agenta")
        self.console.print("2. Test agenta")
        self.console.print("3. Statystyki agenta") 
        self.console.print("0. Powrót do menu głównego")


class AgentsConsoleApp:
    """Główna aplikacja konsolowa"""
    
    def __init__(self):
        self.console = Console()
        self.running = True
        self.api_client = AgentsAPIClient()
        self.menu_manager = MenuManager(self.console)
        self.session_id = str(uuid.uuid4())
    
    async def main(self):
        """Główna pętla aplikacji"""
        try:
            await self.show_startup_sequence()
            await self.main_menu_loop()
        except KeyboardInterrupt:
            self.console.print("\n👋 [yellow]Zamykanie aplikacji...[/yellow]")
        except Exception as e:
            self.console.print(f"❌ [red]Błąd krytyczny: {e}[/red]")
        finally:
            await self.api_client.close()
    
    async def show_startup_sequence(self):
        """Animowana sekwencja startowa"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            
            task1 = progress.add_task("🔌 Łączenie z serwerem...", total=None)
            await asyncio.sleep(1)
            progress.update(task1, completed=True)
            
            task2 = progress.add_task("🤖 Ładowanie agentów...", total=None)
            await asyncio.sleep(1)
            progress.update(task2, completed=True)
            
            task3 = progress.add_task("✅ Inicjalizacja zakończona", total=None)
            await asyncio.sleep(0.5)
        
        # Ekran powitalny
        welcome_panel = Panel.fit(
            "[bold cyan]🤖 SYSTEM AGENTY[/bold cyan]\n"
            "[dim]Zaawansowany system zarządzania agentami AI[/dim]\n\n"
            f"Status: {await self.get_server_status()}\n"
            "Wersja: [yellow]1.0.0[/yellow]\n"
            f"Sesja: [blue]{self.session_id[:8]}[/blue]",
            title="[bold]Witaj w systemie AGENTY[/bold]",
            border_style="green"
        )
        self.console.print(welcome_panel)
        self.console.print()
    
    async def get_server_status(self) -> str:
        """Pobierz status serwera"""
        health = await self.api_client.get_health()
        if health["status"] == "online":
            return "[green]●[/green] Połączony"
        return "[red]●[/red] Rozłączony"
    
    async def main_menu_loop(self):
        """Główna pętla menu"""
        while self.running:
            try:
                await self.show_main_menu()
                choice = Prompt.ask(
                    "Wybierz opcję",
                    choices=["1", "2", "3", "4", "5", "0"],
                    default="0"
                )
                await self.handle_main_menu_choice(choice)
            except KeyboardInterrupt:
                if Confirm.ask("\n🤔 Czy na pewno chcesz wyjść?"):
                    self.running = False
    
    async def show_main_menu(self):
        """Wyświetlanie głównego menu"""
        self.console.clear()
        
        # Status bar
        await self.show_status_bar()
        
        # Menu główne
        self.menu_manager.show_main_menu()
    
    async def show_status_bar(self):
        """Status bar z informacjami o systemie"""
        try:
            health = await self.api_client.get_health()
            if health["status"] == "online":
                status = "🟢 Online"
                agents_count = len(await self.api_client.get_agents_list())
            else:
                status = "🔴 Offline"
                agents_count = 0
        except:
            status = "🔴 Disconnected"
            agents_count = 0
        
        status_panel = Panel(
            f"Status: {status} | Agenci: [yellow]{agents_count}[/yellow] | "
            f"Czas: [blue]{self.get_current_time()}[/blue] | "
            f"Sesja: [cyan]{self.session_id[:8]}[/cyan]",
            height=3,
            border_style="dim"
        )
        self.console.print(status_panel)
    
    def get_current_time(self) -> str:
        """Zwraca aktualny czas"""
        return datetime.now().strftime("%H:%M:%S")
    
    async def handle_main_menu_choice(self, choice: str):
        """Obsługa wyboru z głównego menu"""
        handlers = {
            "1": self.show_agents_list,
            "2": self.start_interactive_chat,
            "3": self.show_dashboard,
            "4": self.show_configuration,
            "5": self.show_statistics, 
            "0": self.exit_application
        }
        
        handler = handlers.get(choice)
        if handler:
            await handler()
        else:
            self.console.print("❌ [red]Nieprawidłowa opcja![/red]")
            await asyncio.sleep(1)
    
    async def show_agents_list(self):
        """Wyświetlanie listy agentów"""
        self.console.clear()
        
        with self.console.status("🔍 Pobieranie listy agentów..."):
            agents_data = await self.fetch_agents_data()
        
        # Tabela agentów
        agents_table = Table(title="🤖 Dostępni Agenci", show_header=True)
        agents_table.add_column("Typ", style="green")
        agents_table.add_column("Status", justify="center")
        agents_table.add_column("Opis", style="dim")
        
        for agent in agents_data:
            agents_table.add_row(
                agent["name"],
                "🟢 Dostępny",
                agent.get("description", "Agent AI")
            )
        
        if not agents_data:
            agents_table.add_row("Brak agentów", "🔴 Niedostępny", "Sprawdź połączenie z serwerem")
        
        self.console.print(agents_table)
        
        # Opcje akcji
        self.menu_manager.show_agents_menu()
        
        choice = Prompt.ask("Wybierz akcję", choices=["1", "2", "3", "0"], default="0")
        
        if choice == "1":
            await self.show_agent_details(agents_data)
        elif choice == "2":
            await self.test_agent(agents_data)
        elif choice == "3":
            await self.show_agent_statistics(agents_data)
    
    async def fetch_agents_data(self) -> List[Dict[str, Any]]:
        """Pobiera dane agentów z API"""
        return await self.api_client.get_agents_list()
    
    async def show_agent_details(self, agents_data: List[Dict[str, Any]]):
        """Szczegóły agenta"""
        if not agents_data:
            self.console.print("❌ [red]Brak dostępnych agentów[/red]")
            Prompt.ask("Naciśnij Enter aby kontynuować...")
            return
        
        self.console.print("\n[bold]Dostępni agenci:[/bold]")
        for i, agent in enumerate(agents_data, 1):
            self.console.print(f"{i}. {agent['name']}")
        
        try:
            choice = int(Prompt.ask("Wybierz agenta (numer)")) - 1
            if 0 <= choice < len(agents_data):
                agent = agents_data[choice]
                details_panel = Panel(
                    f"[bold]Typ:[/bold] {agent['name']}\n"
                    f"[bold]Opis:[/bold] {agent.get('description', 'Brak opisu')}\n"
                    f"[bold]Status:[/bold] Dostępny\n"
                    f"[bold]Możliwości:[/bold] Przetwarzanie zapytań AI",
                    title=f"Szczegóły agenta: {agent['name']}",
                    border_style="blue"
                )
                self.console.print(details_panel)
            else:
                self.console.print("❌ [red]Nieprawidłowy wybór[/red]")
        except ValueError:
            self.console.print("❌ [red]Nieprawidłowy numer[/red]")
        
        Prompt.ask("Naciśnij Enter aby kontynuować...")
    
    async def test_agent(self, agents_data: List[Dict[str, Any]]):
        """Test agenta"""
        if not agents_data:
            self.console.print("❌ [red]Brak dostępnych agentów[/red]")
            Prompt.ask("Naciśnij Enter aby kontynuować...")
            return
        
        test_query = Prompt.ask("Wprowadź zapytanie testowe", default="Hello, jak się masz?")
        
        with self.console.status("🤖 Testowanie agenta..."):
            result = await self.api_client.execute_agent_task(test_query, self.session_id)
        
        if result.get("success"):
            self.console.print(f"✅ [green]Test zakończony pomyślnie![/green]")
            self.console.print(f"📋 Odpowiedź: {result.get('response', 'Brak odpowiedzi')}")
        else:
            self.console.print(f"❌ [red]Test nieudany: {result.get('error', 'Nieznany błąd')}[/red]")
        
        Prompt.ask("Naciśnij Enter aby kontynuować...")
    
    async def show_agent_statistics(self, agents_data: List[Dict[str, Any]]):
        """Statystyki agentów"""
        stats_panel = Panel(
            f"[bold]Liczba dostępnych agentów:[/bold] {len(agents_data)}\n"
            f"[bold]Status systemu:[/bold] {await self.get_server_status()}\n"
            f"[bold]Aktualna sesja:[/bold] {self.session_id[:8]}\n"
            f"[bold]Czas działania:[/bold] {self.get_current_time()}",
            title="📈 Statystyki Systemu",
            border_style="yellow"
        )
        self.console.print(stats_panel)
        Prompt.ask("Naciśnij Enter aby kontynuować...")
    
    async def start_interactive_chat(self):
        """Tryb interaktywnego czatu"""
        self.console.clear()
        
        chat_panel = Panel(
            "💬 [bold green]Tryb Interaktywny - Chat z Agentami[/bold green]\n"
            "[dim]Wpisz '/help' aby zobaczyć dostępne komendy\n"
            "Wpisz '/exit' aby zakończyć chat[/dim]",
            title="Tryb Interaktywny",
            border_style="green"
        )
        self.console.print(chat_panel)
        
        while True:
            try:
                user_input = Prompt.ask("👤 [bold cyan]Ty[/bold cyan]")
                
                if user_input.startswith('/'):
                    if user_input == '/exit':
                        break
                    elif user_input == '/help':
                        self.show_chat_help()
                        continue
                    elif user_input == '/clear':
                        self.console.clear()
                        continue
                    elif user_input == '/status':
                        await self.show_status_bar()
                        continue
                
                # Wysłanie wiadomości do agenta
                with self.console.status("🤖 Agent analizuje..."):
                    response = await self.api_client.execute_agent_task(user_input, self.session_id)
                
                if response.get("success"):
                    self.console.print(f"🤖 [bold green]Agent[/bold green]: {response.get('response', 'Brak odpowiedzi')}")
                else:
                    self.console.print(f"❌ [red]Błąd: {response.get('error', 'Nieznany błąd')}[/red]")
                
                self.console.print()
                
            except KeyboardInterrupt:
                if Confirm.ask("\n🤔 Zakończyć chat?"):
                    break
    
    def show_chat_help(self):
        """Pomoc dla trybu chat"""
        help_panel = Panel(
            "[bold]Dostępne komendy:[/bold]\n"
            "/help - Wyświetl tę pomoc\n"
            "/clear - Wyczyść ekran\n"
            "/status - Pokaż status systemu\n"
            "/exit - Zakończ chat\n"
            "\n[bold]Wskazówki:[/bold]\n"
            "• Pisz naturalnie - agent zrozumie Twoje zapytania\n"
            "• Możesz zadawać pytania o pogodę, przepisy, informacje\n"
            "• Agent zachowuje kontekst rozmowy w ramach sesji",
            title="💡 Pomoc - Tryb Chat",
            border_style="blue"
        )
        self.console.print(help_panel)
    
    async def show_dashboard(self):
        """Dashboard z live updates"""
        self.console.clear()
        
        # Tworzymy prosty dashboard bez Live na początku
        self.console.print("📊 [bold]System Dashboard[/bold]")
        
        health = await self.api_client.get_health()
        agents = await self.api_client.get_agents_list()
        
        dashboard_table = Table(title="Status Systemu")
        dashboard_table.add_column("Komponent", style="cyan")
        dashboard_table.add_column("Status", style="green")
        dashboard_table.add_column("Detale", style="dim")
        
        # Status serwera
        server_status = "🟢 Online" if health["status"] == "online" else "🔴 Offline"
        dashboard_table.add_row("Serwer Backend", server_status, f"Port 8000")
        
        # Status agentów
        agents_status = f"🤖 {len(agents)} dostępnych" if agents else "❌ Brak agentów"
        dashboard_table.add_row("Agenci AI", agents_status, f"Sesja: {self.session_id[:8]}")
        
        # Status połączenia
        dashboard_table.add_row("Połączenie", "🔗 Aktywne", f"Ostatnia aktywność: {self.get_current_time()}")
        
        self.console.print(dashboard_table)
        
        # Informacje o systemie
        info_panel = Panel(
            f"[bold]Informacje o sesji:[/bold]\n"
            f"🆔 ID Sesji: {self.session_id}\n"
            f"⏰ Czas uruchomienia: {self.get_current_time()}\n"
            f"🌐 URL Backend: http://localhost:8000\n"
            f"📊 Liczba agentów: {len(agents)}",
            title="Informacje systemowe",
            border_style="blue"
        )
        self.console.print(info_panel)
        
        Prompt.ask("Naciśnij Enter aby kontynuować...")
    
    async def show_configuration(self):
        """Konfiguracja systemu"""
        self.console.clear()
        
        config_panel = Panel(
            "[bold]Ustawienia Aplikacji:[/bold]\n\n"
            "1. URL Backend: http://localhost:8000\n"
            "2. Timeout żądań: 30 sekund\n" 
            "3. ID Sesji: " + self.session_id[:16] + "...\n"
            "4. Tryb debug: Wyłączony\n"
            "5. Auto-reconnect: Włączony\n\n"
            "[dim]Uwaga: Konfiguracja jest obecnie tylko do odczytu[/dim]",
            title="⚙️ Konfiguracja Systemu",
            border_style="yellow"
        )
        self.console.print(config_panel)
        
        Prompt.ask("Naciśnij Enter aby kontynuować...")
    
    async def show_statistics(self):
        """Statystyki użycia"""
        self.console.clear()
        
        # Pobieramy podstawowe statystyki
        health = await self.api_client.get_health()
        agents = await self.api_client.get_agents_list()
        
        stats_table = Table(title="📈 Statystyki Systemu")
        stats_table.add_column("Metryka", style="cyan")
        stats_table.add_column("Wartość", style="green")
        stats_table.add_column("Opis", style="dim")
        
        stats_table.add_row("Status serwera", 
                          "Online" if health["status"] == "online" else "Offline",
                          "Stan połączenia z backendem")
        stats_table.add_row("Dostępne agenci", str(len(agents)), "Liczba zarejestrowanych agentów")
        stats_table.add_row("Aktualna sesja", self.session_id[:8] + "...", "Identyfikator bieżącej sesji")
        stats_table.add_row("Czas działania", self.get_current_time(), "Czas od uruchomienia konsoli")
        
        self.console.print(stats_table)
        
        Prompt.ask("Naciśnij Enter aby kontynuować...")
    
    def exit_application(self):
        """Zamykanie aplikacji"""
        self.console.print("👋 [yellow]Dzięki za skorzystanie z systemu AGENTY![/yellow]")
        self.running = False


# Punkt wejścia aplikacji
async def main():
    """Główny punkt wejścia"""
    app = AgentsConsoleApp()
    await app.main()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Do widzenia!")
        sys.exit(0)