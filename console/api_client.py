import httpx
from rich.console import Console
import uuid
import os

class APIClient:
    """Klient do komunikacji z API Agenty."""

    def __init__(self):
        backend_url = os.environ.get("BACKEND_URL", "http://agenty-backend:8000")
        ollama_url = os.environ.get("OLLAMA_URL", "http://ollama:11434")
        self.backend_url = backend_url.rstrip('/')
        self.ollama_url = ollama_url.rstrip('/')
        self.console = Console()
        self.session_id = str(uuid.uuid4())

    def check_backend_status(self):
        """Sprawdza status backendu API."""
        url = f"{self.backend_url}/api/health"
        try:
            response = httpx.get(url, timeout=5)
            if response.status_code == 200:
                return "[bold green]Online[/bold green]", url
            else:
                return f"[bold red]Offline ({response.status_code})[/bold red]", url
        except httpx.RequestError as e:
            return f"[bold red]Offline (Błąd połączenia)[/bold red]", url

    def check_ollama_status(self):
        """Sprawdza status usługi Ollama."""
        url = f"{self.ollama_url}/api/version"
        try:
            response = httpx.get(url, timeout=5)
            if response.status_code == 200:
                return "[bold green]Online[/bold green]", url
            else:
                return f"[bold red]Offline ({response.status_code})[/bold red]", url
        except httpx.RequestError as e:
            return f"[bold red]Offline (Błąd połączenia)[/bold red]", url

    async def send_chat_message(self, message: str) -> str:
        """Wysyła wiadomość do agenta czatowego i zwraca odpowiedź."""
        url = f"{self.backend_url}/api/v2/chat/process"
        payload = {
            "message": message,
            "session_id": self.session_id
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=120)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("output", {}).get("response", "Brak odpowiedzi w formacie JSON.")
                else:
                    return f"Błąd API: {response.status_code} - {response.text}"
            except httpx.RequestError as e:
                return f"Błąd połączenia: {e}"