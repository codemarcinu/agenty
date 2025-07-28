"""
System powiadomień dla Telegram Bot - FoodSave AI.

Ten moduł zawiera system powiadomień dla Telegram Bot:
- Broadcast do wszystkich użytkowników
- Alerty systemowe
- Powiadomienia o wydarzeniach
- Dzienne podsumowania
"""

import asyncio
from datetime import datetime
import logging
from typing import Any

from settings import settings

logger = logging.getLogger(__name__)


class TelegramNotificationSystem:
    """System powiadomień dla Telegram Bot."""

    def __init__(self, telegram_bot_handler):
        """Inicjalizuje system powiadomień.

        Args:
            telegram_bot_handler: Instancja TelegramBotHandler
        """
        self.bot_handler = telegram_bot_handler
        self.api_base_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

        # Lista użytkowników do powiadomień
        self.subscribed_users: set[int] = set()

        # Historia powiadomień
        self.notification_history: list[dict[str, Any]] = []

        # Ustawienia powiadomień
        self.notification_settings = {
            "daily_summary": True,
            "system_alerts": True,
            "receipt_analysis": True,
            "expense_alerts": True,
            "weather_alerts": True,
        }

    async def broadcast_message(
        self, message: str, user_ids: list[int] | None = None
    ) -> dict[str, Any]:
        """Wysyła wiadomość do wszystkich użytkowników lub określonej listy.

        Args:
            message: Wiadomość do wysłania
            user_ids: Lista ID użytkowników (None = wszyscy)

        Returns:
            Dict z wynikiem broadcast
        """
        try:
            if user_ids is None:
                user_ids = list(self.subscribed_users)

            if not user_ids:
                return {"success": False, "error": "Brak użytkowników do powiadomienia"}

            success_count = 0
            error_count = 0
            errors = []

            # Wysyłaj wiadomości równolegle
            tasks = []
            for user_id in user_ids:
                task = self._send_notification(user_id, message)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_count += 1
                    errors.append(f"User {user_ids[i]}: {result!s}")
                elif result:
                    success_count += 1

            # Zapisz do historii
            self._log_notification("broadcast", message, success_count, error_count)

            return {
                "success": True,
                "sent": success_count,
                "errors": error_count,
                "error_details": errors,
            }

        except Exception as e:
            logger.error(f"Error in broadcast: {e}")
            return {"success": False, "error": str(e)}

    async def send_system_alert(
        self, alert_type: str, message: str, priority: str = "normal"
    ) -> dict[str, Any]:
        """Wysyła alert systemowy.

        Args:
            alert_type: Typ alertu (system, security, maintenance, etc.)
            message: Wiadomość alertu
            priority: Priorytet (low, normal, high, critical)

        Returns:
            Dict z wynikiem wysłania
        """
        try:
            # Formatuj wiadomość alertu
            formatted_message = self._format_alert_message(
                alert_type, message, priority
            )

            # Wybierz użytkowników na podstawie priorytetu
            target_users = self._get_users_for_alert(priority)

            result = await self.broadcast_message(formatted_message, target_users)

            # Zapisz alert
            self._log_alert(alert_type, message, priority, result)

            return result

        except Exception as e:
            logger.error(f"Error sending system alert: {e}")
            return {"success": False, "error": str(e)}

    async def send_daily_summary(self) -> dict[str, Any]:
        """Wysyła dzienne podsumowanie aktywności."""
        try:
            # Pobierz statystyki z ostatniego dnia
            stats = await self._get_daily_stats()

            # Formatuj podsumowanie
            summary = self._format_daily_summary(stats)

            # Wyślij do wszystkich użytkowników
            result = await self.broadcast_message(summary)

            logger.info(f"Daily summary sent: {result}")
            return result

        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
            return {"success": False, "error": str(e)}

    async def send_receipt_analysis_notification(
        self, user_id: int, receipt_data: dict[str, Any]
    ) -> bool:
        """Wysyła powiadomienie o analizie paragonu."""
        try:
            message = self._format_receipt_notification(receipt_data)

            result = await self._send_notification(user_id, message)

            if result:
                logger.info(f"Receipt analysis notification sent to user {user_id}")
                return True
            else:
                logger.error(f"Failed to send receipt notification to user {user_id}")
                return False

        except Exception as e:
            logger.error(f"Error sending receipt notification: {e}")
            return False

    async def send_expense_alert(
        self, user_id: int, expense_data: dict[str, Any]
    ) -> bool:
        """Wysyła alert o wydatkach."""
        try:
            message = self._format_expense_alert(expense_data)

            result = await self._send_notification(user_id, message)

            if result:
                logger.info(f"Expense alert sent to user {user_id}")
                return True
            else:
                logger.error(f"Failed to send expense alert to user {user_id}")
                return False

        except Exception as e:
            logger.error(f"Error sending expense alert: {e}")
            return False

    async def send_weather_alert(
        self, user_id: int, weather_data: dict[str, Any]
    ) -> bool:
        """Wysyła alert pogodowy."""
        try:
            message = self._format_weather_alert(weather_data)

            result = await self._send_notification(user_id, message)

            if result:
                logger.info(f"Weather alert sent to user {user_id}")
                return True
            else:
                logger.error(f"Failed to send weather alert to user {user_id}")
                return False

        except Exception as e:
            logger.error(f"Error sending weather alert: {e}")
            return False

    async def _send_notification(self, user_id: int, message: str) -> bool:
        """Wysyła powiadomienie do konkretnego użytkownika."""
        try:
            # Użyj istniejącej metody wysyłania wiadomości
            await self.bot_handler._send_message(user_id, message)
            return True

        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
            return False

    def _format_alert_message(
        self, alert_type: str, message: str, priority: str
    ) -> str:
        """Formatuje wiadomość alertu."""
        priority_icons = {"low": "ℹ️", "normal": "⚠️", "high": "🚨", "critical": "🚨🚨"}

        icon = priority_icons.get(priority, "⚠️")

        return f"""{icon} **Alert Systemowy - {alert_type.upper()}**

{message}

⏰ **Czas:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔔 **Priorytet:** {priority.upper()}"""

    def _format_daily_summary(self, stats: dict[str, Any]) -> str:
        """Formatuje dzienne podsumowanie."""
        return f"""📊 **Dzienne Podsumowanie - {datetime.now().strftime('%Y-%m-%d')}**

🤖 **Aktywność AI:**
• Wiadomości przetworzone: {stats.get('messages_processed', 0)}
• Paragony przeanalizowane: {stats.get('receipts_analyzed', 0)}
• Przepisy wyszukane: {stats.get('recipes_searched', 0)}

💰 **Finanse:**
• Wydatki dzisiaj: {stats.get('daily_expenses', 0):.2f} zł
• Oszczędności: {stats.get('savings', 0):.2f} zł

👥 **Użytkownicy:**
• Aktywni użytkownicy: {stats.get('active_users', 0)}
• Nowi użytkownicy: {stats.get('new_users', 0)}

💡 **Sugestie:**
{stats.get('suggestions', 'Brak sugestii na dziś')}"""

    def _format_receipt_notification(self, receipt_data: dict[str, Any]) -> str:
        """Formatuje powiadomienie o analizie paragonu."""
        return f"""📷 **Analiza paragonu zakończona!**

🏪 **Sklep:** {receipt_data.get('store_name', 'Nieznany')}
💰 **Suma:** {receipt_data.get('total_amount', 0):.2f} zł
📅 **Data:** {receipt_data.get('date', 'Nieznana')}

📋 **Produkty:** {len(receipt_data.get('items', []))} pozycji

💡 **Sugestie oszczędności:**
{receipt_data.get('suggestions', 'Brak sugestii')}"""

    def _format_expense_alert(self, expense_data: dict[str, Any]) -> str:
        """Formatuje alert o wydatkach."""
        return f"""💰 **Alert Wydatków**

⚠️ **Wykryto wysokie wydatki!**

🏪 **Sklep:** {expense_data.get('store_name', 'Nieznany')}
💰 **Kwota:** {expense_data.get('amount', 0):.2f} zł
📅 **Data:** {expense_data.get('date', 'Nieznana')}

💡 **Sugestie oszczędności:**
{expense_data.get('suggestions', 'Brak sugestii')}"""

    def _format_weather_alert(self, weather_data: dict[str, Any]) -> str:
        """Formatuje alert pogodowy."""
        return f"""🌤️ **Alert Pogodowy**

📍 **Lokalizacja:** {weather_data.get('location', 'Nieznana')}
🌡️ **Temperatura:** {weather_data.get('temperature', 'Nieznana')}°C
🌧️ **Opady:** {weather_data.get('precipitation', 'Nieznane')}

⚠️ **Ostrzeżenia:**
{weather_data.get('warnings', 'Brak ostrzeżeń')}"""

    def _get_users_for_alert(self, priority: str) -> list[int]:
        """Zwraca listę użytkowników dla alertu na podstawie priorytetu."""
        if priority == "critical":
            # Wszyscy użytkownicy dla krytycznych alertów
            return list(self.subscribed_users)
        elif priority == "high":
            # 80% użytkowników dla wysokich alertów
            users = list(self.subscribed_users)
            return users[: int(len(users) * 0.8)]
        else:
            # 50% użytkowników dla normalnych alertów
            users = list(self.subscribed_users)
            return users[: int(len(users) * 0.5)]

    async def _get_daily_stats(self) -> dict[str, Any]:
        """Pobiera dzienne statystyki."""
        # TODO: Implementacja pobierania statystyk z bazy danych
        return {
            "messages_processed": 150,
            "receipts_analyzed": 25,
            "recipes_searched": 30,
            "daily_expenses": 245.67,
            "savings": 45.23,
            "active_users": 45,
            "new_users": 3,
            "suggestions": "• Rozważ zakupy w Lidl dla lepszych cen\n• Sprawdź promocje w Biedronce\n• Planuj posiłki na cały tydzień",
        }

    def _log_notification(
        self, notification_type: str, message: str, success_count: int, error_count: int
    ) -> None:
        """Loguje powiadomienie."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": notification_type,
            "message": message[:100] + "..." if len(message) > 100 else message,
            "success_count": success_count,
            "error_count": error_count,
        }

        self.notification_history.append(log_entry)

        # Zachowaj tylko ostatnie 100 wpisów
        if len(self.notification_history) > 100:
            self.notification_history = self.notification_history[-100:]

    def _log_alert(
        self, alert_type: str, message: str, priority: str, result: dict[str, Any]
    ) -> None:
        """Loguje alert."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "alert",
            "alert_type": alert_type,
            "priority": priority,
            "message": message[:100] + "..." if len(message) > 100 else message,
            "result": result,
        }

        self.notification_history.append(log_entry)

    def add_subscriber(self, user_id: int) -> None:
        """Dodaje użytkownika do listy subskrybentów."""
        self.subscribed_users.add(user_id)
        logger.info(f"User {user_id} subscribed to notifications")

    def remove_subscriber(self, user_id: int) -> None:
        """Usuwa użytkownika z listy subskrybentów."""
        self.subscribed_users.discard(user_id)
        logger.info(f"User {user_id} unsubscribed from notifications")

    def get_subscribers_count(self) -> int:
        """Zwraca liczbę subskrybentów."""
        return len(self.subscribed_users)

    def get_notification_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Zwraca historię powiadomień."""
        return self.notification_history[-limit:]

    def update_settings(self, settings: dict[str, bool]) -> None:
        """Aktualizuje ustawienia powiadomień."""
        self.notification_settings.update(settings)
        logger.info(f"Notification settings updated: {settings}")
