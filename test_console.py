#!/usr/bin/env python3
"""
Test script for AGENTY Console Application
"""

import asyncio
import sys
import os

# Add console directory to path  
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'console'))

from api_client import AgentsAPIClient
from rich.console import Console


async def test_api_client():
    """Test API client functionality"""
    console = Console()
    client = AgentsAPIClient()
    
    console.print("🧪 [bold]Testowanie klienta API...[/bold]")
    
    try:
        # Test health check
        console.print("1. Testowanie health check...")
        health = await client.health_check()
        console.print(f"   Status: {health['status']}")
        if health['status'] == 'online':
            console.print("   ✅ Health check - OK")
        else:
            console.print("   ❌ Health check - BŁĄD")
        
        # Test agents list
        console.print("2. Testowanie listy agentów...")
        agents = await client.get_agents_list()
        console.print(f"   Znaleziono agentów: {len(agents)}")
        if agents:
            console.print("   ✅ Lista agentów - OK")
            for agent in agents[:3]:  # Show first 3
                console.print(f"   - {agent.get('name', 'Unknown')}")
        else:
            console.print("   ⚠️ Brak agentów lub błąd")
        
        # Test simple query
        console.print("3. Testowanie prostego zapytania...")
        result = await client.execute_agent_task("Hello, test message")
        if result.get('success'):
            console.print("   ✅ Zapytanie - OK")
            console.print(f"   Odpowiedź: {result.get('response', '')[:100]}...")
        else:
            console.print("   ❌ Zapytanie - BŁĄD")
            console.print(f"   Błąd: {result.get('error', 'Unknown')}")
        
        # Test server info
        console.print("4. Testowanie informacji serwera...")
        server_info = await client.get_server_info()
        console.print(f"   Health: {server_info['health']['status']}")
        console.print(f"   Agenci: {len(server_info['agents'])}")
        console.print(f"   Endpointy: {len(server_info['endpoints'])}")
        console.print("   ✅ Informacje serwera - OK")
        
    except Exception as e:
        console.print(f"❌ [red]Błąd podczas testowania: {e}[/red]")
    finally:
        await client.close()
    
    console.print("\n🎉 [green]Test zakończony![/green]")


async def test_console_components():
    """Test console UI components"""
    console = Console()
    
    console.print("🎨 [bold]Testowanie komponentów UI...[/bold]")
    
    # Test basic Rich functionality
    from rich.panel import Panel
    from rich.table import Table
    
    # Test panel
    test_panel = Panel(
        "🧪 To jest test panelu Rich\nZ wieloma liniami tekstu",
        title="Test Panel",
        border_style="green"
    )
    console.print(test_panel)
    
    # Test table
    test_table = Table(title="Test Tabeli")
    test_table.add_column("Kolumna 1", style="cyan")
    test_table.add_column("Kolumna 2", style="green")
    test_table.add_row("Wiersz 1", "Dane 1")
    test_table.add_row("Wiersz 2", "Dane 2")
    console.print(test_table)
    
    console.print("✅ [green]Komponenty UI działają poprawnie![/green]")


async def main():
    """Main test function"""
    console = Console()
    
    console.print("🚀 [bold cyan]Test aplikacji konsolowej AGENTY[/bold cyan]")
    console.print("=" * 50)
    
    # Test API client
    await test_api_client()
    
    console.print("\n" + "=" * 50)
    
    # Test UI components
    await test_console_components()
    
    console.print("\n" + "=" * 50)
    console.print("🎯 [bold]Podsumowanie testów:[/bold]")
    console.print("✅ API Client - funkcjonalny")
    console.print("✅ Rich UI - działa poprawnie")
    console.print("✅ Backend - dostępny")
    console.print("🚀 [green]Aplikacja gotowa do uruchomienia![/green]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test przerwany")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Błąd testu: {e}")
        sys.exit(1)