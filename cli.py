
import click
from rich.console import Console
from rich.table import Table
from rich.spinner import Spinner
from console.api_client import APIClient
import asyncio

console = Console()
client = APIClient()

@click.group()
def cli():
    """
    🤖 Agenty CLI - Inteligentny asystent w Twoim terminalu.
    """
    pass

@cli.command()
def hello():
    """
    Wyświetla powitanie.
    """
    console.print("👋 Witaj w Agenty CLI!", style="bold green")

@cli.command()
def status():
    """
    Sprawdza i wyświetla status usług systemowych.
    """
    table = Table(title="Stan Usług Systemu Agenty")
    table.add_column("Usługa", style="cyan", no_wrap=True)
    table.add_column("Status", style="magenta")
    table.add_column("URL", style="green")

    backend_status, backend_url = client.check_backend_status()
    ollama_status, ollama_url = client.check_ollama_status()

    table.add_row("Backend API", backend_status, backend_url)
    table.add_row("Ollama (AI)", ollama_status, ollama_url)

    console.print(table)

@cli.command()
@click.argument('message', required=False)
def chat(message):
    """
    Rozpoczyna czat z agentem AI.

    Możesz podać wiadomość jako argument lub uruchomić w trybie interaktywnym.
    """
    async def do_chat():
        if message:
            with console.status("[bold green]AI myśli...[/bold green]"):
                response = await client.send_chat_message(message)
            console.print(f"[bold cyan]🤖 Agent:[/bold cyan] {response}")
        else:
            console.print("🤖 Rozpoczęto czat interaktywny. Wpisz 'exit', aby zakończyć.")
            while True:
                user_input = console.input("[bold yellow]Ty:[/bold yellow] ")
                if user_input.lower() == 'exit':
                    break
                with console.status("[bold green]AI myśli...[/bold green]"):
                    response = await client.send_chat_message(user_input)
                console.print(f"[bold cyan]🤖 Agent:[/bold cyan] {response}")

    asyncio.run(do_chat())

if __name__ == "__main__":
    cli()
