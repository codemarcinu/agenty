"""
Quick Response Handlers for FoodSave AI

Fast-path handlers for common queries that don't require
full agent processing (greetings, time, simple weather).
"""

from datetime import datetime
import logging
from typing import Any

import httpx

from settings import settings

logger = logging.getLogger(__name__)


class QuickGreetingHandler:
    """Fast handler for greeting responses"""

    def __init__(self):
        self.responses = {
            "formal": [
                "Dzień dobry! Jak mogę Ci dzisiaj pomóc?",
                "Witam! W czym mogę być pomocny?",
                "Dzień dobry! Jestem tutaj, aby Ci pomóc.",
            ],
            "casual": [
                "Cześć! Co słychać?",
                "Hej! Jak mogę Ci pomóc?",
                "Siema! W czym mogę pomóc?",
                "Cześć! Jak się masz?",
            ],
            "goodbye": [
                "Do widzenia! Miłego dnia!",
                "Dobranoc! Śpij dobrze!",
                "Do zobaczenia! Powodzenia!",
            ],
            "general": [
                "Cześć! Jak mogę Ci pomóc?",
                "Witaj! W czym mogę być pomocny?",
                "Hej! Co mogę dla Ciebie zrobić?",
            ],
        }

    async def handle(self, query: str, context_hints: dict[str, Any] | None = None) -> str:
        """Generate quick greeting response"""
        context_hints = context_hints or {}
        greeting_type = context_hints.get("greeting_type", "general")

        responses = self.responses.get(greeting_type, self.responses["general"])

        # Simple selection based on time of day
        hour = datetime.now().hour

        if greeting_type == "formal":
            if 5 <= hour < 12:
                return "Dzień dobry! Miłego rozpoczęcia dnia. W czym mogę pomóc?"
            elif 12 <= hour < 18:
                return "Dzień dobry! Jak minął dotychczasowy dzień? Jak mogę pomóc?"
            else:
                return "Dobry wieczór! W czym mogę być pomocny?"

        # For casual greetings, use variety
        import random

        return random.choice(responses)


class QuickTimeHandler:
    """Fast handler for time and date queries"""

    async def handle(self, query: str, context_hints: dict[str, Any] | None = None) -> str:
        """Generate quick time/date response"""
        now = datetime.now()

        query_lower = query.lower()

        if any(word in query_lower for word in ["godzina", "time", "która"]):
            return f"Aktualny czas: {now.strftime('%H:%M')}"

        elif any(word in query_lower for word in ["data", "date", "dzień", "dzien"]):
            weekdays = {
                0: "poniedziałek",
                1: "wtorek",
                2: "środa",
                3: "czwartek",
                4: "piątek",
                5: "sobota",
                6: "niedziela",
            }
            weekday = weekdays[now.weekday()]
            return f"Dzisiaj jest {weekday}, {now.strftime('%d.%m.%Y')}"

        elif "dziś" in query_lower or "today" in query_lower:
            return f"Dzisiaj jest {now.strftime('%d.%m.%Y')}, godzina {now.strftime('%H:%M')}"

        else:
            return f"Aktualny czas: {now.strftime('%H:%M')}, data: {now.strftime('%d.%m.%Y')}"


class QuickWeatherHandler:
    """Fast handler for simple weather queries using Perplexica"""

    def __init__(self):
        self.base_url = settings.PERPLEXICA_BASE_URL
        self.default_location = "Warszawa"

        # Location coordinates mapping (simplified)
        self.location_coords = {
            "warszawa": {"lat": 52.2297, "lng": 21.0122},
            "kraków": {"lat": 50.0647, "lng": 19.9450},
            "wrocław": {"lat": 51.1079, "lng": 17.0385},
            "poznań": {"lat": 52.4064, "lng": 16.9252},
            "gdańsk": {"lat": 54.3520, "lng": 18.6466},
            "ząbki": {"lat": 52.2900, "lng": 21.1050},
            "marki": {"lat": 52.3200, "lng": 21.1000},
        }

    async def handle(self, query: str, context_hints: dict[str, Any] | None = None) -> str:
        """Generate quick weather response"""
        context_hints = context_hints or {}
        location = context_hints.get("location", self.default_location).lower()
        weather_type = context_hints.get("weather_type", "general")

        try:
            # Get coordinates for location
            coords = self.location_coords.get(
                location, self.location_coords["warszawa"]
            )

            # Call Perplexica weather API
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(f"{self.base_url}/weather", json=coords)

                if response.status_code == 200:
                    weather_data = response.json()
                    return self._format_weather_response(
                        weather_data, location.title(), weather_type
                    )
                else:
                    logger.warning(f"Weather API returned {response.status_code}")
                    return f"Nie mogę obecnie sprawdzić pogody dla {location.title()}. Spróbuj ponownie za chwilę."

        except Exception as e:
            logger.error(f"Error getting weather data: {e}")
            return f"Nie mogę obecnie sprawdzić pogody dla {location.title()}. Sprawdź połączenie internetowe."

    def _format_weather_response(
        self, weather_data: dict[str, Any], location: str, weather_type: str
    ) -> str:
        """Format weather data into readable response"""
        try:
            temp = weather_data.get("temperature", "N/A")
            condition = weather_data.get("condition", "N/A")
            humidity = weather_data.get("humidity", "N/A")
            wind = weather_data.get("windSpeed", "N/A")

            if weather_type == "temperature":
                return f"Temperatura w {location}: {temp}°C"

            elif weather_type == "general":
                return (
                    f"Pogoda w {location}:\n"
                    f"🌡️ Temperatura: {temp}°C\n"
                    f"☁️ Warunki: {condition}\n"
                    f"💧 Wilgotność: {humidity}%\n"
                    f"💨 Wiatr: {wind} km/h"
                )

            elif weather_type == "forecast":
                # For now, return current weather with note about forecast
                return (
                    f"Aktualna pogoda w {location}: {temp}°C, {condition}.\n"
                    f"Szczegółową prognozę znajdziesz na stronie pogodowej."
                )

            else:
                return f"Pogoda w {location}: {temp}°C, {condition}"

        except Exception as e:
            logger.error(f"Error formatting weather response: {e}")
            return f"Otrzymałem dane pogodowe dla {location}, ale nie mogę ich poprawnie przetworzyć."


class QuickHandlerRegistry:
    """Registry for all quick handlers"""

    def __init__(self):
        self.handlers = {
            "quick_greeting_handler": QuickGreetingHandler(),
            "quick_time_handler": QuickTimeHandler(),
            "perplexica_weather_handler": QuickWeatherHandler(),
        }

    async def handle_quick_query(
        self, handler_name: str, query: str, context_hints: dict[str, Any] | None = None
    ) -> str | None:
        """Execute quick handler by name"""
        handler = self.handlers.get(handler_name)
        if handler:
            try:
                return await handler.handle(query, context_hints)
            except Exception as e:
                logger.error(f"Error in quick handler {handler_name}: {e}")
                return None
        else:
            logger.warning(f"Unknown quick handler: {handler_name}")
            return None

    def is_quick_handler(self, handler_name: str) -> bool:
        """Check if handler is a quick handler"""
        return handler_name in self.handlers


# Global registry instance
quick_handler_registry = QuickHandlerRegistry()
