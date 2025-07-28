"""
Smart Query Router for FoodSave AI

Provides intelligent routing of user queries to appropriate handlers
with fast categorization and optimized processing paths.
"""

from dataclasses import dataclass
from enum import Enum
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class QueryCategory(Enum):
    """Categories for different types of queries"""

    GREETING = "greeting"
    WEATHER = "weather"
    TIME_DATE = "time_date"
    PANTRY = "pantry"
    RECIPE = "recipe"
    SEARCH = "search"
    SIMPLE_FACT = "simple_fact"
    COMPLEX_CONVERSATION = "complex_conversation"


@dataclass
class RoutingDecision:
    """Decision made by the query router"""

    category: QueryCategory
    confidence: float
    suggested_handler: str
    fast_path: bool = False
    context_hints: dict[str, Any] = None

    def __post_init__(self):
        if self.context_hints is None:
            self.context_hints = {}


class SmartQueryRouter:
    """Intelligent query router with fast categorization"""

    def __init__(self):
        self.weather_keywords = {
            "pogoda",
            "weather",
            "temperatura",
            "temperature",
            "deszcz",
            "rain",
            "śnieg",
            "snow",
            "wiatr",
            "wind",
            "wilgotność",
            "humidity",
            "słońce",
            "sun",
            "chmury",
            "clouds",
            "burza",
            "storm",
            "mgła",
            "fog",
            "grad",
            "hail",
            "prognoza",
            "forecast",
        }

        self.greeting_patterns = {
            "cześć",
            "czesc",
            "hej",
            "witaj",
            "dzień dobry",
            "dzien dobry",
            "dobry wieczór",
            "dobry wieczor",
            "hello",
            "hi",
            "good morning",
            "good evening",
            "witam",
            "siema",
            "dobranoc",
            "do widzenia",
        }

        self.time_date_patterns = {
            "która godzina",
            "ktora godzina",
            "jaka godzina",
            "ile czasu",
            "jaki dzień",
            "jaki dzien",
            "jaka data",
            "kiedy",
            "gdy",
            "time",
            "date",
            "clock",
            "today",
            "dziś",
            "dzis",
            "jutro",
            "wczoraj",
        }

        self.pantry_keywords = {
            "spiżarnia",
            "spizarnia",
            "pantry",
            "lodówka",
            "lodowka",
            "fridge",
            "co mam",
            "jakie produkty",
            "składniki",
            "skladniki",
            "ingredients",
            "zapasy",
            "magazyn",
            "przechowalnia",
            "przechowywanie",
        }

        self.recipe_keywords = {
            "przepis",
            "przepisy",
            "recipe",
            "recipes",
            "jak ugotować",
            "jak ugotowac",
            "jak przygotować",
            "jak przygotowac",
            "danie",
            "posiłek",
            "posilek",
            "obiad",
            "śniadanie",
            "sniadanie",
            "kolacja",
            "gotowanie",
            "pieczenie",
        }

        self.search_indicators = {
            "wyszukaj",
            "znajdź",
            "znajdz",
            "search",
            "find",
            "google",
            "sprawdź",
            "sprawdz",
            "check",
            "czy",
            "dlaczego",
            "jak",
            "gdzie",
            "kiedy",
            "kto",
            "co to jest",
            "what is",
            "why",
            "how",
        }

    def route_query(
        self, query: str, context: dict[str, Any] | None = None
    ) -> RoutingDecision:
        """
        Route query to appropriate handler with confidence scoring

        Args:
            query: User query string
            context: Additional context (session_id, previous queries, etc.)

        Returns:
            RoutingDecision with category, confidence, and suggested handler
        """
        query_lower = query.lower().strip()
        context = context or {}

        # Fast path checks (highest priority)

        # 1. Greeting detection
        if self._is_greeting(query_lower):
            return RoutingDecision(
                category=QueryCategory.GREETING,
                confidence=0.95,
                suggested_handler="quick_greeting_handler",
                fast_path=True,
                context_hints={"greeting_type": self._get_greeting_type(query_lower)},
            )

        # 2. Weather queries (check before time/date as weather queries often contain time words)
        weather_confidence = self._calculate_weather_confidence(query_lower)
        if weather_confidence > 0.7:
            location = self._extract_location(query)
            return RoutingDecision(
                category=QueryCategory.WEATHER,
                confidence=weather_confidence,
                suggested_handler="perplexica_weather_handler",
                fast_path=True,
                context_hints={
                    "location": location,
                    "weather_type": self._get_weather_type(query_lower),
                },
            )

        # 3. Time/Date queries (after weather to avoid conflicts)
        if self._is_time_date_query(query_lower) and weather_confidence < 0.3:
            return RoutingDecision(
                category=QueryCategory.TIME_DATE,
                confidence=0.90,
                suggested_handler="quick_time_handler",
                fast_path=True,
                context_hints={"query_type": "time_date"},
            )

        # 4. Weather queries with lower confidence (fallback)
        if weather_confidence > 0.3:
            location = self._extract_location(query)
            return RoutingDecision(
                category=QueryCategory.WEATHER,
                confidence=weather_confidence,
                suggested_handler="perplexica_weather_handler",
                fast_path=True,
                context_hints={
                    "location": location,
                    "weather_type": self._get_weather_type(query_lower),
                },
            )

        # 5. Pantry queries
        pantry_confidence = self._calculate_pantry_confidence(query_lower)
        if pantry_confidence > 0.6:
            return RoutingDecision(
                category=QueryCategory.PANTRY,
                confidence=pantry_confidence,
                suggested_handler="pantry_agent",
                fast_path=False,
                context_hints={"pantry_action": self._get_pantry_action(query_lower)},
            )

        # 6. Recipe queries
        recipe_confidence = self._calculate_recipe_confidence(query_lower)
        if recipe_confidence > 0.6:
            return RoutingDecision(
                category=QueryCategory.RECIPE,
                confidence=recipe_confidence,
                suggested_handler="chef_agent",
                fast_path=False,
                context_hints={"recipe_type": self._get_recipe_type(query_lower)},
            )

        # 7. Search queries (requires internet)
        search_confidence = self._calculate_search_confidence(query_lower)
        if search_confidence > 0.7:
            return RoutingDecision(
                category=QueryCategory.SEARCH,
                confidence=search_confidence,
                suggested_handler="perplexica_search_agent",
                fast_path=False,
                context_hints={
                    "search_type": self._get_search_type(query_lower),
                    "requires_internet": True,
                },
            )

        # 8. Simple fact queries
        if self._is_simple_fact_query(query_lower):
            return RoutingDecision(
                category=QueryCategory.SIMPLE_FACT,
                confidence=0.6,
                suggested_handler="rag_agent",
                fast_path=False,
                context_hints={"fact_type": "simple"},
            )

        # 9. Default: Complex conversation
        return RoutingDecision(
            category=QueryCategory.COMPLEX_CONVERSATION,
            confidence=0.5,
            suggested_handler="general_conversation_agent",
            fast_path=False,
            context_hints={
                "requires_rag": True,
                "requires_internet": search_confidence > 0.3,
            },
        )

    def _is_greeting(self, query_lower: str) -> bool:
        """Check if query is a greeting"""
        # Remove punctuation for better matching
        clean_query = (
            query_lower.replace("!", "").replace("?", "").replace(".", "").strip()
        )

        # Exact matches first
        if clean_query in self.greeting_patterns:
            return True

        # Check if query starts with greeting
        words = clean_query.split()
        if words and words[0] in self.greeting_patterns:
            return True

        return False

    def _get_greeting_type(self, query_lower: str) -> str:
        """Determine type of greeting"""
        if any(word in query_lower for word in ["dobry", "dzień", "dzien"]):
            return "formal"
        elif any(word in query_lower for word in ["cześć", "czesc", "hej", "siema"]):
            return "casual"
        elif any(word in query_lower for word in ["dobranoc", "do widzenia"]):
            return "goodbye"
        return "general"

    def _is_time_date_query(self, query_lower: str) -> bool:
        """Check if query is about time or date"""
        return any(pattern in query_lower for pattern in self.time_date_patterns)

    def _calculate_weather_confidence(self, query_lower: str) -> float:
        """Calculate confidence that query is weather-related"""
        keyword_matches = sum(
            1 for keyword in self.weather_keywords if keyword in query_lower
        )
        total_keywords = len(self.weather_keywords)

        base_confidence = keyword_matches / total_keywords * 4  # Scale up

        # Boost for location indicators
        if any(loc_word in query_lower for loc_word in ["w ", "we ", "na ", "do "]):
            base_confidence += 0.2

        # Boost for question words
        if any(q_word in query_lower for q_word in ["jaka", "jaki", "jak", "ile"]):
            base_confidence += 0.1

        return min(base_confidence, 1.0)

    def _extract_location(self, query: str) -> str | None:
        """Extract location from query (reuse logic from PerplexicaSearchProvider)"""
        # Simple extraction - could be enhanced with NER
        query_lower = query.lower()

        # Common Polish cities and towns
        locations = {
            "warszawa",
            "kraków",
            "wrocław",
            "poznań",
            "gdańsk",
            "ząbki",
            "marki",
            "kobyłka",
            "wołomin",
            "zielonka",
            "legionowo",
        }

        for location in locations:
            if location in query_lower:
                return location.title()

        # Pattern matching for "w X"
        import re

        pattern = r"\b(?:w|we|na)\s+([a-ząćęłńóśźż]+)\b"
        match = re.search(pattern, query_lower)
        if match:
            return match.group(1).title()

        return None

    def _get_weather_type(self, query_lower: str) -> str:
        """Determine specific weather information requested"""
        if "temperatura" in query_lower or "stopni" in query_lower:
            return "temperature"
        elif "deszcz" in query_lower or "pada" in query_lower:
            return "precipitation"
        elif "wiatr" in query_lower:
            return "wind"
        elif "prognoza" in query_lower or "jutro" in query_lower:
            return "forecast"
        return "general"

    def _calculate_pantry_confidence(self, query_lower: str) -> float:
        """Calculate confidence for pantry-related queries"""
        keyword_matches = sum(
            1 for keyword in self.pantry_keywords if keyword in query_lower
        )
        return min(keyword_matches / len(self.pantry_keywords) * 3, 1.0)

    def _get_pantry_action(self, query_lower: str) -> str:
        """Determine pantry action requested"""
        if "co mam" in query_lower or "jakie" in query_lower:
            return "list_items"
        elif "sprawdź" in query_lower or "czy mam" in query_lower:
            return "check_item"
        elif "dodaj" in query_lower or "kup" in query_lower:
            return "add_item"
        return "general_info"

    def _calculate_recipe_confidence(self, query_lower: str) -> float:
        """Calculate confidence for recipe queries"""
        keyword_matches = sum(
            1 for keyword in self.recipe_keywords if keyword in query_lower
        )
        return min(keyword_matches / len(self.recipe_keywords) * 3, 1.0)

    def _get_recipe_type(self, query_lower: str) -> str:
        """Determine recipe type requested"""
        if "obiad" in query_lower:
            return "lunch"
        elif "śniadanie" in query_lower or "sniadanie" in query_lower:
            return "breakfast"
        elif "kolacja" in query_lower:
            return "dinner"
        return "general"

    def _calculate_search_confidence(self, query_lower: str) -> float:
        """Calculate confidence for search queries"""
        indicator_matches = sum(
            1 for indicator in self.search_indicators if indicator in query_lower
        )
        base_confidence = indicator_matches / len(self.search_indicators) * 2

        # Boost for question structure
        if query_lower.endswith("?"):
            base_confidence += 0.2

        # Boost for current events indicators
        if any(
            word in query_lower for word in ["aktualnie", "obecnie", "teraz", "dziś"]
        ):
            base_confidence += 0.3

        return min(base_confidence, 1.0)

    def _get_search_type(self, query_lower: str) -> str:
        """Determine search type needed"""
        if any(
            word in query_lower for word in ["aktualnie", "obecnie", "teraz", "dziś"]
        ):
            return "current_events"
        elif any(word in query_lower for word in ["gdzie", "location", "miejsce"]):
            return "location"
        elif any(word in query_lower for word in ["jak", "how", "tutorial"]):
            return "how_to"
        return "general"

    def _is_simple_fact_query(self, query_lower: str) -> bool:
        """Check if query is a simple factual question"""
        # Simple heuristics for factual queries
        fact_patterns = [
            r"co to (jest|znaczy)",
            r"kim (jest|był|była)",
            r"ile (ma|waży|kosztuje)",
            r"gdzie (jest|znajduje się)",
            r"kiedy (był|była|powstało)",
        ]

        return any(re.search(pattern, query_lower) for pattern in fact_patterns)


# Global router instance
query_router = SmartQueryRouter()
