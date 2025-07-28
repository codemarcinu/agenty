"""
Agent chatowy dla aplikacji konsolowej
"""

import asyncio
import structlog
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import aiohttp
from rich.console import Console
from rich.markdown import Markdown

from .config import Config

logger = structlog.get_logger()
console = Console()


class ConversationHistory:
    """Zarządzanie historią konwersacji"""
    
    def __init__(self, max_messages: int = 50):
        self.messages: List[Dict[str, Any]] = []
        self.max_messages = max_messages
        
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Dodanie wiadomości do historii"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
        
        # Ograniczenie liczby wiadomości
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Pobranie ostatnich wiadomości"""
        return self.messages[-count:] if self.messages else []
    
    def clear(self):
        """Wyczyszczenie historii"""
        self.messages.clear()
    
    def export_to_file(self, filepath: Path):
        """Eksport historii do pliku"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.messages, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Błąd eksportu historii: {e}")
            return False
    
    def import_from_file(self, filepath: Path):
        """Import historii z pliku"""
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.messages = json.load(f)
            return True
        except Exception as e:
            logger.error(f"Błąd importu historii: {e}")
            return False


class ChatAgent:
    """Agent chatowy do konwersacji z użytkownikiem"""
    
    def __init__(self, config: Config):
        self.config = config
        self.history = ConversationHistory()
        self.session: Optional[aiohttp.ClientSession] = None
        self.history_file = Path("chat_history.json")
        
        # Załaduj historię przy starcie
        self.history.import_from_file(self.history_file)
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        # Zapisz historię przy wyjściu
        self.history.export_to_file(self.history_file)
    
    async def send_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Wysłanie wiadomości do agenta i otrzymanie odpowiedzi"""
        try:
            # Dodaj wiadomość użytkownika do historii
            self.history.add_message("user", message, {"context": context})
            
            # Przygotuj dane do wysłania
            payload = {
                "message": message,
                "conversation_history": self.history.get_recent_messages(10),
                "context": context or {}
            }
            
            # Wysłanie do backendu
            response = await self._send_to_backend(payload)
            
            if response.get("success", False):
                assistant_message = response.get("response", "")
                metadata = response.get("metadata", {})
                
                # Dodaj odpowiedź asystenta do historii
                self.history.add_message("assistant", assistant_message, metadata)
                
                return {
                    "success": True,
                    "response": assistant_message,
                    "metadata": metadata
                }
            else:
                error_msg = response.get("error", "Nieznany błąd")
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except Exception as e:
            logger.error(f"Błąd wysyłania wiadomości: {e}")
            return {
                "success": False,
                "error": f"Błąd połączenia: {str(e)}"
            }
    
    async def _send_to_backend(self, payload: Dict) -> Dict[str, Any]:
        """Wysłanie zapytania do backendu"""
        if not self.session:
            raise Exception("Sesja HTTP nie została zainicjalizowana")
        
        url = f"{self.config.BACKEND_URL}/api/v2/chat/conversation"
        
        try:
            async with self.session.post(
                url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}"
                    }
                    
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Timeout - backend nie odpowiada"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Błąd połączenia: {str(e)}"
            }
    
    async def get_suggested_questions(self) -> List[str]:
        """Pobranie sugerowanych pytań na podstawie kontekstu"""
        try:
            recent_messages = self.history.get_recent_messages(5)
            if not recent_messages:
                return [
                    "Jak mogę przetworzyć paragony?",
                    "Jakie formaty plików są obsługiwane?",
                    "Jak dodać dokumenty do bazy wiedzy?",
                    "Pokaż mi statystyki systemu",
                    "Jak eksportować wyniki?"
                ]
            
            # Tutaj można dodać logikę generowania pytań na podstawie kontekstu
            context_keywords = []
            for msg in recent_messages[-3:]:
                if msg["role"] == "user":
                    context_keywords.extend(msg["content"].lower().split())
            
            suggestions = []
            if "paragon" in context_keywords or "ocr" in context_keywords:
                suggestions.extend([
                    "Jakiej jakości obrazy dają najlepsze wyniki OCR?",
                    "Czy mogę przetworzyć paragony wsadowo?",
                    "Jak poprawić dokładność rozpoznawania tekstu?"
                ])
            
            if "rag" in context_keywords or "wiedza" in context_keywords:
                suggestions.extend([
                    "Jakie typy dokumentów mogę dodać do bazy wiedzy?",
                    "Jak optymalizować wyszukiwanie w RAG?",
                    "Czy mogę usunąć dokumenty z bazy wiedzy?"
                ])
            
            if "eksport" in context_keywords:
                suggestions.extend([
                    "W jakich formatach mogę eksportować dane?",
                    "Gdzie są zapisywane pliki eksportu?",
                    "Jak automatyzować eksporty?"
                ])
            
            return suggestions[:5] if suggestions else [
                "Opowiedz mi więcej o możliwościach systemu",
                "Jakie są najlepsze praktyki użytkowania?",
                "Jak rozwiązać typowe problemy?",
                "Pokaż mi zaawansowane funkcje",
                "Jak optymalizować wydajność?"
            ]
            
        except Exception as e:
            logger.error(f"Błąd generowania sugestii: {e}")
            return ["Jak mogę Ci pomóc?"]
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Podsumowanie obecnej konwersacji"""
        if not self.history.messages:
            return {
                "total_messages": 0,
                "user_messages": 0,
                "assistant_messages": 0,
                "last_activity": None,
                "topics": []
            }
        
        user_messages = [msg for msg in self.history.messages if msg["role"] == "user"]
        assistant_messages = [msg for msg in self.history.messages if msg["role"] == "assistant"]
        
        # Analiza tematów (prosta implementacja)
        topics = set()
        for msg in user_messages[-10:]:  # Ostatnie 10 wiadomości użytkownika
            content_lower = msg["content"].lower()
            if "paragon" in content_lower or "receipt" in content_lower:
                topics.add("Przetwarzanie paragonów")
            if "rag" in content_lower or "wiedza" in content_lower:
                topics.add("Baza wiedzy RAG")
            if "eksport" in content_lower:
                topics.add("Eksport danych")
            if "statystyki" in content_lower:
                topics.add("Statystyki")
            if "pomoc" in content_lower or "help" in content_lower:
                topics.add("Pomoc")
        
        return {
            "total_messages": len(self.history.messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "last_activity": self.history.messages[-1]["timestamp"] if self.history.messages else None,
            "topics": list(topics)
        }
    
    def clear_conversation(self):
        """Wyczyszczenie konwersacji"""
        self.history.clear()
        # Usuń plik historii
        if self.history_file.exists():
            self.history_file.unlink()
    
    async def check_backend_connection(self) -> bool:
        """Sprawdzenie połączenia z backendem"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = f"{self.config.BACKEND_URL}/health"
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Błąd sprawdzania połączenia: {e}")
            return False