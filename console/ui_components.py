"""
UI Components for AGENTY Console Application
Rich-based user interface components with enhanced UX
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich.columns import Columns
from rich.tree import Tree


class StatusIndicator:
    """Enhanced status indicators with icons and colors"""
    
    @staticmethod
    def online() -> str:
        return "[green]🟢 Online[/green]"
    
    @staticmethod  
    def offline() -> str:
        return "[red]🔴 Offline[/red]"
    
    @staticmethod
    def connecting() -> str:
        return "[yellow]🟡 Łączenie...[/yellow]"
    
    @staticmethod
    def error() -> str:
        return "[red]❌ Błąd[/red]"
    
    @staticmethod
    def success() -> str:
        return "[green]✅ Sukces[/green]"
    
    @staticmethod
    def processing() -> str:
        return "[blue]🔄 Przetwarzanie[/blue]"


class MenuRenderer:
    """Advanced menu rendering with consistent styling"""
    
    def __init__(self, console: Console):
        self.console = console
    
    def render_main_menu(self) -> Table:
        """Render main menu with enhanced styling"""
        table = Table(
            title="📋 Menu Główne - System AGENTY",
            show_header=True,
            header_style="bold magenta",
            border_style="blue",
            title_style="bold cyan"
        )
        
        table.add_column("Nr", style="cyan", width=6, justify="center")
        table.add_column("🎯 Funkcja", style="white", min_width=20)
        table.add_column("📝 Opis", style="dim", min_width=30)
        table.add_column("⌨️ Skrót", style="yellow", width=8)
        
        menu_items = [
            ("1", "🤖 Lista Agentów", "Wyświetl i zarządzaj dostępnymi agentami", "Ctrl+A"),
            ("2", "💬 Chat Interaktywny", "Rozpocznij rozmowę z wybranym agentem", "Ctrl+C"),
            ("3", "📊 Dashboard", "Monitor systemu w czasie rzeczywistym", "Ctrl+D"),
            ("4", "⚙️ Konfiguracja", "Ustawienia i preferencje aplikacji", "Ctrl+S"),
            ("5", "📈 Statystyki", "Analiza wydajności i statystyki użycia", "Ctrl+T"),
            ("6", "📚 Pomoc", "Dokumentacja i wskazówki użytkowania", "F1"),
            ("0", "🚪 Wyjście", "Zamknij aplikację bezpiecznie", "Ctrl+Q")
        ]
        
        for item in menu_items:
            table.add_row(*item)
        
        return table
    
    def render_agents_table(self, agents_data: List[Dict[str, Any]]) -> Table:
        """Render agents list with enhanced information"""
        table = Table(
            title="🤖 Dostępni Agenci AI",
            show_header=True,
            header_style="bold green",
            border_style="green"
        )
        
        table.add_column("#", style="cyan", width=4)
        table.add_column("Typ Agenta", style="bold white", min_width=15)
        table.add_column("Status", justify="center", width=12)
        table.add_column("Możliwości", style="dim", min_width=25)
        table.add_column("Ostatnia aktywność", style="blue", width=15)
        
        if not agents_data:
            table.add_row(
                "-",
                "Brak agentów",
                StatusIndicator.error(),
                "Sprawdź połączenie z serwerem",
                "Nigdy"
            )
        else:
            for i, agent in enumerate(agents_data, 1):
                capabilities = self._format_capabilities(agent)
                table.add_row(
                    str(i),
                    agent.get("name", "Unknown"),
                    StatusIndicator.online(),
                    capabilities,
                    "Aktywny"
                )
        
        return table
    
    def _format_capabilities(self, agent: Dict[str, Any]) -> str:
        """Format agent capabilities for display"""
        agent_type = agent.get("name", "").lower()
        
        capability_map = {
            "chef": "🍳 Przepisy, planowanie posiłków",
            "weather": "🌤️ Prognoza pogody, klimat",
            "rag": "🔍 Wyszukiwanie dokumentów, Q&A",
            "ocr": "📖 Rozpoznawanie tekstu z obrazów",
            "search": "🔍 Wyszukiwanie informacji online",
            "analytics": "📊 Analiza danych, statystyki"
        }
        
        for key, capabilities in capability_map.items():
            if key in agent_type:
                return capabilities
        
        return "🤖 Ogólne przetwarzanie AI"
    
    def render_status_bar(self, status_data: Dict[str, Any]) -> Panel:
        """Render enhanced status bar"""
        status_text = (
            f"Status: {status_data.get('server_status', StatusIndicator.offline())} | "
            f"Agenci: [yellow]{status_data.get('agents_count', 0)}[/yellow] | "
            f"Czas: [blue]{status_data.get('current_time', 'N/A')}[/blue] | "
            f"Sesja: [cyan]{status_data.get('session_id', 'N/A')[:8]}[/cyan] | "
            f"Ping: [green]{status_data.get('response_time', 'N/A')}ms[/green]"
        )
        
        return Panel(
            status_text,
            height=3,
            border_style="dim",
            title="System Status",
            title_align="left"
        )
    
    def render_welcome_panel(self, system_info: Dict[str, Any]) -> Panel:
        """Render enhanced welcome screen"""
        content = Text()
        content.append("🤖 SYSTEM AGENTY\n", style="bold cyan")
        content.append("Zaawansowany system zarządzania agentami AI\n\n", style="dim")
        
        # System info
        content.append(f"Status: {system_info.get('status', 'N/A')}\n")
        content.append(f"Wersja: ", style="bold")
        content.append(f"{system_info.get('version', '1.0.0')}\n", style="yellow")
        content.append(f"Backend: ", style="bold")
        content.append(f"{system_info.get('backend_url', 'localhost:8000')}\n", style="blue")
        content.append(f"Sesja: ", style="bold") 
        content.append(f"{system_info.get('session_id', 'N/A')[:8]}...\n", style="cyan")
        
        return Panel(
            content,
            title="[bold]Witaj w systemie AGENTY[/bold]",
            border_style="green",
            padding=(1, 2)
        )


class ProgressManager:
    """Enhanced progress indicators and loading animations"""
    
    def __init__(self, console: Console):
        self.console = console
    
    def startup_sequence(self, steps: List[str]) -> Progress:
        """Create startup sequence progress"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
            transient=True
        )
    
    def task_progress(self, description: str) -> Progress:
        """Create task progress indicator"""
        return Progress(
            SpinnerColumn(),
            TextColumn(f"[bold blue]{description}[/bold blue]"),
            console=self.console,
            transient=True
        )
    
    async def simulate_startup(self, steps: List[str], delay: float = 1.0) -> None:
        """Simulate startup sequence with progress"""
        with self.startup_sequence(steps) as progress:
            for step in steps:
                task = progress.add_task(step, total=100)
                
                # Simulate work with progress updates
                for i in range(100):
                    await asyncio.sleep(delay / 100)
                    progress.update(task, advance=1)
                
                progress.update(task, completed=100)


class DialogManager:
    """Enhanced dialog and input handling"""
    
    def __init__(self, console: Console):
        self.console = console
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Enhanced confirmation dialog with EOF handling"""
        import sys
        
        # Check if we're in an interactive terminal
        if not sys.stdin.isatty():
            # Non-interactive mode - return default
            return default
        
        try:
            return Confirm.ask(f"🤔 {message}", default=default)
        except EOFError:
            # Handle EOF gracefully
            return default
    
    def get_choice(
        self, 
        prompt: str, 
        choices: List[str], 
        default: Optional[str] = None
    ) -> str:
        """Enhanced choice selection with EOF handling"""
        import sys
        
        # Check if we're in an interactive terminal
        if not sys.stdin.isatty():
            # Non-interactive mode - return default or first choice
            if default is not None:
                return default
            elif choices:
                return choices[0]
            else:
                raise EOFError("Choice required but not available in non-interactive mode")
        
        try:
            return Prompt.ask(
                f"🎯 {prompt}",
                choices=choices,
                default=default
            )
        except EOFError:
            # Handle EOF gracefully
            if default is not None:
                return default
            elif choices:
                return choices[0]
            else:
                raise EOFError("EOF encountered during choice selection")
    
    def get_input(
        self,
        prompt: str,
        default: Optional[str] = None,
        password: bool = False
    ) -> str:
        """Enhanced text input with EOF handling"""
        import sys
        
        # Check if we're in an interactive terminal
        if not sys.stdin.isatty():
            # Non-interactive mode - return default or exit gracefully
            if default is not None:
                return default
            else:
                # No default provided in non-interactive mode
                raise EOFError("Input required but not available in non-interactive mode")
        
        try:
            return Prompt.ask(
                f"✏️ {prompt}",
                default=default,
                password=password
            )
        except EOFError:
            # Handle EOF gracefully
            if default is not None:
                return default
            else:
                raise EOFError("EOF encountered during input")
    
    def show_error(self, message: str, title: str = "Błąd") -> None:
        """Show error dialog"""
        error_panel = Panel(
            f"❌ [red]{message}[/red]",
            title=f"[red]{title}[/red]",
            border_style="red"
        )
        self.console.print(error_panel)
    
    def show_success(self, message: str, title: str = "Sukces") -> None:
        """Show success dialog"""
        success_panel = Panel(
            f"✅ [green]{message}[/green]",
            title=f"[green]{title}[/green]",
            border_style="green"
        )
        self.console.print(success_panel)
    
    def show_info(self, message: str, title: str = "Informacja") -> None:
        """Show info dialog"""
        info_panel = Panel(
            f"ℹ️ [blue]{message}[/blue]",
            title=f"[blue]{title}[/blue]",
            border_style="blue"
        )
        self.console.print(info_panel)


class DashboardRenderer:
    """Enhanced dashboard with real-time updates"""
    
    def __init__(self, console: Console):
        self.console = console
    
    def create_dashboard_layout(self) -> Layout:
        """Create dashboard layout structure"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="agents", ratio=2),
            Layout(name="stats", ratio=1)
        )
        
        return layout
    
    def render_system_metrics(self, metrics: Dict[str, Any]) -> Table:
        """Render system metrics table"""
        table = Table(title="📊 Metryki Systemu", border_style="blue")
        table.add_column("Metryka", style="cyan")
        table.add_column("Wartość", style="green")
        table.add_column("Status", justify="center")
        table.add_column("Trend", style="yellow")
        
        metrics_data = [
            ("Czas odpowiedzi", f"{metrics.get('response_time', 0)}ms", "🟢", "📈"),
            ("Agenci aktywni", str(metrics.get('active_agents', 0)), "🟢", "➡️"),
            ("Zapytania/min", str(metrics.get('queries_per_min', 0)), "🟢", "📈"),
            ("Użycie pamięci", f"{metrics.get('memory_usage', 0)}%", "🟡", "📈"),
            ("Połączenia", str(metrics.get('connections', 0)), "🟢", "➡️")
        ]
        
        for metric in metrics_data:
            table.add_row(*metric)
        
        return table
    
    def render_agent_status_tree(self, agents: List[Dict[str, Any]]) -> Tree:
        """Render agent status as tree"""
        tree = Tree("🤖 Status Agentów")
        
        if not agents:
            tree.add("❌ Brak dostępnych agentów")
            return tree
        
        for agent in agents:
            name = agent.get("name", "Unknown")
            status_node = tree.add(f"🟢 {name}")
            status_node.add(f"Typ: {agent.get('type', 'generic')}")
            status_node.add(f"Status: Aktywny")
            status_node.add(f"Ostatnia aktywność: Teraz")
        
        return tree


class HelpSystem:
    """Comprehensive help and documentation system"""
    
    def __init__(self, console: Console):
        self.console = console
    
    def show_main_help(self) -> None:
        """Show main help screen"""
        help_content = """
[bold cyan]🤖 SYSTEM AGENTY - Pomoc[/bold cyan]

[bold]Podstawowe funkcje:[/bold]
• Lista Agentów (1) - Zarządzanie dostępnymi agentami AI
• Chat Interaktywny (2) - Rozmowa z agentami w czasie rzeczywistym  
• Dashboard (3) - Monitoring systemu i statystyki
• Konfiguracja (4) - Ustawienia aplikacji
• Statystyki (5) - Analiza wydajności

[bold]Skróty klawiszowe:[/bold]
• Ctrl+C - Przerwanie bieżącej operacji
• Ctrl+Q - Szybkie wyjście z aplikacji
• F1 - Wyświetlenie pomocy kontekstowej
• Tab - Autouzupełnianie (gdzie dostępne)

[bold]Tryb Chat:[/bold]
• /help - Pomoc dla trybu chat
• /clear - Czyszczenie ekranu
• /status - Status systemu
• /exit - Wyjście z chatu

[bold]Wskazówki:[/bold]
• Używaj numerów do nawigacji w menu
• Agenci rozumieją naturalne zapytania w języku polskim
• System zachowuje kontekst rozmowy w ramach sesji
• W przypadku problemów sprawdź status połączenia
        """
        
        help_panel = Panel(
            help_content.strip(),
            title="📚 Centrum Pomocy",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(help_panel)
    
    def show_chat_help(self) -> None:
        """Show chat-specific help"""
        chat_help = """
[bold]Dostępne komendy:[/bold]
/help - Wyświetl tę pomoc
/clear - Wyczyść ekran czatu
/status - Pokaż aktualny status systemu
/session - Informacje o bieżącej sesji
/agents - Lista dostępnych agentów
/exit - Zakończ tryb chat

[bold]Przykłady zapytań:[/bold]
• "Jaka będzie pogoda jutro w Warszawie?"
• "Zaproponuj przepis na obiad dla 4 osób"
• "Wyszukaj informacje o sztucznej inteligencji"
• "Przeanalizuj ten dokument" (z załącznikiem)

[bold]Wskazówki:[/bold]
• Pisz naturalnie - agenci zrozumieją kontekst
• Możesz zadawać pytania następcze
• System pamięta poprzednie części rozmowy
• Używaj polskich znaków - są w pełni obsługiwane
        """
        
        help_panel = Panel(
            chat_help.strip(),
            title="💬 Pomoc - Tryb Interaktywny",
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(help_panel)
    
    def show_troubleshooting(self) -> None:
        """Show troubleshooting guide"""
        troubleshooting = """
[bold red]🔧 Rozwiązywanie problemów[/bold red]

[bold]Problem: Brak połączenia z serwerem[/bold]
• Sprawdź czy backend działa na porcie 8000
• Uruchom: cd agenty/backend && python main.py
• Sprawdź logi serwera w poszukiwaniu błędów

[bold]Problem: Agenci nie odpowiadają[/bold]  
• Sprawdź status agentów w Dashboard (opcja 3)
• Zrestartuj backend
• Sprawdź dostępność modeli AI (Ollama/Bielik)

[bold]Problem: Błędy podczas czatu[/bold]
• Spróbuj krótszych zapytań
• Sprawdź połączenie internetowe
• Zrestartuj sesję (/exit i ponowne wejście)

[bold]Problem: Aplikacja działa wolno[/bold]
• Sprawdź obciążenie procesora/pamięci
• Zamknij inne aplikacje
• Sprawdź status modelu AI

[bold]Dodatkowa pomoc:[/bold]
• Logi aplikacji: ~/.agenty/logs/
• Konfiguracja: ~/.agenty/config/
• GitHub: https://github.com/codemarcinu/agenty
        """
        
        troubleshooting_panel = Panel(
            troubleshooting.strip(),
            title="🛠️ Rozwiązywanie problemów",
            border_style="red",
            padding=(1, 2)
        )
        
        self.console.print(troubleshooting_panel)