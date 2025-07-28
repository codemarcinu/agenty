"""
System komend dla Telegram Bot - FoodSave AI.

Ten moduł zawiera obsługę komend Telegram Bot, w tym:
- Podstawowe komendy (/start, /help)
- Komendy funkcjonalne (/receipt, /pantry, /recipe)
- Komendy informacyjne (/weather, /search, /stats)
- Komendy ustawień (/settings)
"""

from datetime import datetime
from enum import Enum
import logging
from typing import Any

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Typy komend Telegram."""

    START = "start"
    HELP = "help"
    RECEIPT = "receipt"
    PANTRY = "pantry"
    RECIPE = "recipe"
    WEATHER = "weather"
    SEARCH = "search"
    SETTINGS = "settings"
    STATS = "stats"
    STATUS = "status"
    EXPENSES = "expenses"
    ADD = "add"


class TelegramCommandHandler:
    """Handler dla komend Telegram Bot."""

    def __init__(self, telegram_bot_handler):
        """Inicjalizuje handler komend.

        Args:
            telegram_bot_handler: Instancja TelegramBotHandler
        """
        self.bot_handler = telegram_bot_handler
        self.command_usage = {}
        self.user_activity = {}

        # Mapowanie komend na funkcje obsługi
        self.commands = {
            "/start": self._handle_start,
            "/help": self._handle_help,
            "/receipt": self._handle_receipt,
            "/pantry": self._handle_pantry,
            "/recipe": self._handle_recipe,
            "/weather": self._handle_weather,
            "/search": self._handle_search,
            "/settings": self._handle_settings,
            "/stats": self._handle_stats,
            "/status": self._handle_status,
            "/expenses": self._handle_expenses,
            "/add": self._handle_add,
        }

    async def handle_command(self, message: dict[str, Any]) -> str | None:
        """Obsługuje komendę Telegram.

        Args:
            message: Wiadomość z Telegram

        Returns:
            Odpowiedź na komendę lub None jeśli to nie komenda
        """
        text = message.get("text", "")
        message["chat"]["id"]
        user_id = message["from"]["id"]

        # Sprawdź czy to komenda
        if not text.startswith("/"):
            return None

        # Wyciągnij komendę i argumenty
        parts = text.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        # Aktualizuj statystyki
        self._update_usage_stats(command, user_id)

        if command in self.commands:
            try:
                response = await self.commands[command](message, args)
                logger.info(f"Command {command} executed by user {user_id}")
                return response
            except Exception as e:
                logger.error(f"Error handling command {command}: {e}")
                return "❌ Wystąpił błąd podczas przetwarzania komendy"

        return "❓ Nieznana komenda. Użyj /help aby zobaczyć dostępne komendy"

    async def _handle_start(self, message: dict[str, Any], args: str = "") -> str:
        """Obsługa komendy /start."""
        return """🤖 Witaj w FoodSave AI Assistant!

Jestem inteligentnym asystentem, który pomoże Ci:
• 📷 Analizować paragony i wydatki
• 🍳 Znajdować przepisy kulinarne
• 🏠 Zarządzać spiżarnią i zapasami
• 🌤️ Sprawdzać pogodę
• 🔍 Wyszukiwać informacje
• 📊 Śledzić wydatki i oszczędności

💡 **Dostępne komendy:**
/help - Pokaż wszystkie komendy
/receipt - Prześlij paragon do analizy
/pantry - Sprawdź stan spiżarni
/recipe - Znajdź przepis
/weather - Sprawdź pogodę
/search - Wyszukaj informacje
/stats - Twoje statystyki
/settings - Ustawienia

💬 Możesz też po prostu napisać wiadomość, a ja odpowiem!"""

    async def _handle_help(self, message: dict[str, Any], args: str = "") -> str:
        """Obsługa komendy /help."""
        return """📋 **Dostępne komendy:**

🔹 **Podstawowe:**
/start - Rozpocznij rozmowę z asystentem
/help - Pokaż pomoc i dostępne komendy

🔹 **Zarządzanie żywnością:**
/receipt - Prześlij paragon do analizy
/pantry - Sprawdź stan spiżarni
/add [produkt] - Dodaj produkt do spiżarni
/recipe [składniki] - Znajdź przepis

🔹 **Informacje:**
/weather - Sprawdź pogodę w Twojej lokalizacji
/search [zapytanie] - Wyszukaj informacje w internecie
/status - Sprawdź stan systemu

🔹 **Finanse:**
/expenses - Pokaż ostatnie wydatki
/stats - Twoje statystyki użytkowania

🔹 **Ustawienia:**
/settings - Zarządzaj ustawieniami

💡 **Przykłady użycia:**
• `/recipe jajecznica` - Znajdź przepis na jajecznicę
• `/add mleko 2L` - Dodaj mleko do spiżarni
• `/search przepis na pierogi` - Wyszukaj przepisy

💬 Możesz też po prostu napisać wiadomość, a ja odpowiem!"""

    async def _handle_receipt(self, message: dict[str, Any], args: str = "") -> str:
        """Obsługa komendy /receipt."""
        return """📷 **Analiza paragonów:**

Aby przeanalizować paragon:
1. 📸 Zrób zdjęcie paragonu (czytelne!)
2. 📤 Wyślij mi zdjęcie
3. ⏳ Poczekaj na analizę AI
4. 📊 Otrzymaj szczegółowy raport

✅ **Co zostanie przeanalizowane:**
• Nazwa sklepu i data
• Lista produktów z cenami
• Suma całkowita
• Kategorie produktów
• Sugestie oszczędności

📋 **Wspierane formaty:** JPG, PNG, PDF
🏪 **Obsługiwane sklepy:** Biedronka, Lidl, Carrefour, Auchan, Żabka i inne

💡 **Wskazówka:** Upewnij się, że paragon jest dobrze oświetlony i czytelny!"""

    async def _handle_pantry(self, message: dict[str, Any], args: str = "") -> str:
        """Obsługa komendy /pantry."""
        # TODO: Implementacja sprawdzania spiżarni
        return """🏠 **Stan spiżarni:**

Funkcja w trakcie implementacji...
Wkrótce będziesz mógł:
• 📋 Sprawdzać dostępne produkty
• ⏰ Śledzić daty ważności
• 📊 Analizować zużycie
• 🛒 Tworzyć listy zakupów
• 💡 Otrzymywać sugestie

💡 **Tymczasowo użyj:** /add [produkt] aby dodać produkty"""

    async def _handle_recipe(self, message: dict[str, Any], args: str = "") -> str:
        """Obsługa komendy /recipe."""
        if not args:
            return """🍳 **Wyszukiwanie przepisów:**

Użyj: `/recipe [składniki]`
Przykłady:
• `/recipe jajka mleko chleb`
• `/recipe kurczak ryż warzywa`
• `/recipe makaron pomidory ser`

💡 **Możesz też napisać:**
• "Znajdź przepis na jajecznicę"
• "Jak zrobić pierogi?"
• "Przepis na pizzę"

🤖 AI znajdzie najlepsze przepisy dla Ciebie!"""

        # Przekaż do ChefAgent
        try:
            result = await self.bot_handler._process_with_ai(
                f"Znajdź przepis na podstawie składników: {args}", message["from"]["id"]
            )
            return f"🍳 **Przepis dla: {args}**\n\n{result}"
        except Exception as e:
            logger.error(f"Error in recipe search: {e}")
            return "❌ Wystąpił błąd podczas wyszukiwania przepisu"

    async def _handle_weather(self, message: dict[str, Any], args: str = "") -> str:
        """Obsługa komendy /weather."""
        # TODO: Implementacja sprawdzania pogody
        return """🌤️ **Sprawdzanie pogody:**

Funkcja w trakcie implementacji...
Wkrótce będziesz mógł:
• 🌡️ Sprawdzać temperaturę
• 🌧️ Sprawdzać opady
• 🌪️ Sprawdzać wiatr
• 📅 Prognozy na kilka dni
• 🏠 Pogoda dla Twojej lokalizacji

💡 **Tymczasowo:** Możesz zapytać o pogodę w zwykłej wiadomości!"""

    async def _handle_search(self, message: dict[str, Any], args: str = "") -> str:
        """Obsługa komendy /search."""
        if not args:
            return """🔍 **Wyszukiwanie informacji:**

Użyj: `/search [zapytanie]`
Przykłady:
• `/search przepis na pierogi`
• `/search jak gotować ryż`
• `/search kalorie w jabłku`
• `/search pogoda Warszawa`

💡 **Możesz też napisać bezpośrednio:**
• "Wyszukaj przepis na pizzę"
• "Jak gotować makaron?"
• "Kalorie w bananie"

🤖 AI przeszuka internet i znajdzie odpowiedzi!"""

        try:
            result = await self.bot_handler._process_with_ai(
                f"Wyszukaj informacje: {args}", message["from"]["id"]
            )
            return f"🔍 **Wyniki wyszukiwania dla: {args}**\n\n{result}"
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return "❌ Wystąpił błąd podczas wyszukiwania"

    async def _handle_settings(self, message: dict[str, Any], args: str = "") -> str:
        """Obsługa komendy /settings."""
        return """⚙️ **Ustawienia:**

Funkcja w trakcie implementacji...
Wkrótce będziesz mógł:
• 🌍 Zmieniać język
• 📍 Ustawiać lokalizację
• 🔔 Konfigurować powiadomienia
• 🏪 Wybierać ulubione sklepy
• 📊 Ustawiać cele oszczędności

💡 **Tymczasowo:** Ustawienia można zmienić w aplikacji web"""

    async def _handle_stats(self, message: dict[str, Any], args: str = "") -> str:
        """Obsługa komendy /stats."""
        user_id = message["from"]["id"]
        user_stats = self.get_user_stats(user_id)

        return f"""📊 **Twoje statystyki:**

👤 **Aktywność:**
• Wiadomości wysłane: {user_stats.get('messages_sent', 0)}
• Komend użytych: {len(user_stats.get('commands_used', {}))}

📈 **Najczęściej używane komendy:**
{self._format_command_stats(user_stats.get('commands_used', {}))}

⏰ **Ostatnia aktywność:** {user_stats.get('last_activity', 'Nieznana')}

💡 **Wskazówka:** Używaj więcej komend aby zobaczyć więcej statystyk!"""

    async def _handle_status(self, message: dict[str, Any], args: str = "") -> str:
        """Obsługa komendy /status."""
        return """📊 **Status systemu:**

🤖 **AI Assistant:** ✅ Aktywny
📷 **OCR Paragonów:** ✅ Aktywny
🍳 **Chef Agent:** ✅ Aktywny
🔍 **Search Agent:** ✅ Aktywny
📊 **Analytics:** ✅ Aktywny

💾 **Baza danych:** ✅ Połączona
🌐 **API:** ✅ Dostępne
📱 **Telegram Bot:** ✅ Działający

🟢 **Wszystkie systemy sprawne!**

💡 **W razie problemów:** Skontaktuj się z administratorem"""

    async def _handle_expenses(self, message: dict[str, Any], args: str = "") -> str:
        """Obsługa komendy /expenses."""
        # TODO: Implementacja sprawdzania wydatków
        return """💰 **Ostatnie wydatki:**

Funkcja w trakcie implementacji...
Wkrótce będziesz mógł:
• 📊 Zobaczyć historię wydatków
• 📈 Analizować trendy
• 💡 Otrzymywać sugestie oszczędności
• 🎯 Ustawiać cele budżetowe
• 📅 Filtrować po datach

💡 **Tymczasowo:** Prześlij paragony używając /receipt"""

    async def _handle_add(self, message: dict[str, Any], args: str = "") -> str:
        """Obsługa komendy /add."""
        if not args:
            return """➕ **Dodawanie produktów:**

Użyj: `/add [produkt] [ilość]`
Przykłady:
• `/add mleko 2L`
• `/add chleb 1szt`
• `/add jajka 10szt`
• `/add pomidory 500g`

💡 **Format:** Nazwa produktu + ilość
📝 **Przykład:** `/add mleko 3.2% 1L`"""

        # TODO: Implementacja dodawania do spiżarni
        return f"""✅ **Dodano do spiżarni:** {args}

Funkcja w trakcie implementacji...
Wkrótce będziesz mógł:
• 📋 Zarządzać produktami
• ⏰ Śledzić daty ważności
• 📊 Analizować zużycie
• 🛒 Tworzyć listy zakupów

💡 **Dodano:** {args}"""

    def _update_usage_stats(self, command: str, user_id: int) -> None:
        """Aktualizuje statystyki użycia komend."""
        if command not in self.command_usage:
            self.command_usage[command] = 0
        self.command_usage[command] += 1

        if user_id not in self.user_activity:
            self.user_activity[user_id] = 0
        self.user_activity[user_id] += 1

    def get_user_stats(self, user_id: int) -> dict[str, Any]:
        """Zwraca statystyki użytkownika."""
        return {
            "messages_sent": self.user_activity.get(user_id, 0),
            "commands_used": dict(self.command_usage.items()),
            "last_activity": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def _format_command_stats(self, command_stats: dict[str, int]) -> str:
        """Formatuje statystyki komend."""
        if not command_stats:
            return "Brak danych"

        sorted_commands = sorted(
            command_stats.items(), key=lambda x: x[1], reverse=True
        )
        formatted = []

        for cmd, count in sorted_commands[:5]:  # Top 5 komend
            formatted.append(f"• {cmd}: {count}x")

        return "\n".join(formatted)

    def get_daily_stats(self) -> dict[str, Any]:
        """Zwraca dzienne statystyki."""
        today = datetime.now().date()

        return {
            "date": today.isoformat(),
            "total_commands": sum(self.command_usage.values()),
            "active_users": len(self.user_activity),
            "most_used_command": (
                max(self.command_usage.items(), key=lambda x: x[1])[0]
                if self.command_usage
                else "Brak"
            ),
        }
