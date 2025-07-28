"""
Pantry Agent - Zarządzanie spiżarnią i zapasami żywności
"""

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from agents.tools.tools import get_pantry_summary
from core.anti_hallucination_decorator_optimized import with_agent_specific_validation
from core.anti_hallucination_system import ValidationLevel

logger = logging.getLogger(__name__)


class PantryAgent(BaseAgent):
    """Agent do zarządzania spiżarnią i zapasami żywności"""

    def __init__(self, name: str = "PantryAgent", **kwargs) -> None:
        super().__init__(name, **kwargs)
        self.description = "Agent do zarządzania spiżarnią i zapasami żywności"

    @with_agent_specific_validation(
        agent_type="pantry",
        validation_level=ValidationLevel.LENIENT
    )
    async def process(
        self, input_data: dict[str, Any], db: AsyncSession | None = None
    ) -> AgentResponse:
        """Process pantry-related queries"""
        try:
            logger.info("[PantryAgent] Processing pantry query")

            query = self._extract_query_from_input(input_data)
            session_id = input_data.get("session_id", "")

            if not query:
                return AgentResponse(
                    success=False,
                    error="No query provided in input_data",
                    data={"available_fields": list(input_data.keys())},
                    text="",
                    session_id=session_id,
                )

            logger.info(f"[PantryAgent] Processing query: {query}")

            if db is None:
                logger.error("[PantryAgent] No database session provided")
                return AgentResponse(
                    success=False,
                    error="Database session not available",
                    text="Przepraszam, nie mogę uzyskać dostępu do bazy danych spiżarni.",
                    session_id=session_id,
                )

            # Get pantry summary
            logger.info("[PantryAgent] Getting pantry summary")
            summary = await get_pantry_summary(db)

            # Generate response based on query type
            if any(
                phrase in query.lower()
                for phrase in ["co mam", "co jest", "sprawdź", "lista"]
            ):
                # User wants to know what's in pantry
                result = self._format_pantry_contents(summary)
            elif any(
                phrase in query.lower()
                for phrase in ["podsumowanie", "statystyki", "ile"]
            ):
                # User wants pantry statistics
                result = self._format_pantry_stats(summary)
            else:
                # General pantry info
                result = self._format_general_pantry_info(summary)

            logger.info(f"[PantryAgent] Generated response: {result[:100]}...")

            return AgentResponse(
                success=True,
                text=result,
                data={
                    "query": query,
                    "pantry_summary": summary,
                    "agent": "PantryAgent",
                    "session_id": session_id,
                },
                session_id=session_id,
            )

        except Exception as e:
            logger.error(f"[PantryAgent] Error processing query: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                text=f"Przepraszam, wystąpił błąd podczas pobierania informacji o spiżarni: {e!s}",
                session_id=input_data.get("session_id", ""),
            )

    def _extract_query_from_input(self, input_data: dict[str, Any]) -> str:
        """Extract query from input data"""
        possible_fields = ["query", "task", "user_command", "command", "text"]
        for field in possible_fields:
            value = input_data.get(field)
            if value and isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _format_pantry_contents(self, summary: dict[str, Any]) -> str:
        """Format pantry contents for user"""
        result = "🏪 **Zawartość Twojej spiżarni:**\n\n"

        if summary["total_items"] == 0:
            return "Twoja spiżarnia jest pusta. Czas na zakupy! 🛒"

        result += "📊 **Podsumowanie:**\n"
        result += f"• Łącznie produktów: {summary['total_items']}\n"
        result += f"• Dostępne: {summary['in_stock']}\n"
        result += f"• Niski stan: {summary['low_stock']}\n"
        result += f"• Brak: {summary['out_of_stock']}\n"

        if summary["expiring_soon"] > 0:
            result += f"• ⚠️ Wkrótce przeterminowane: {summary['expiring_soon']}\n"

        if summary["categories"]:
            result += "\n🗂️ **Produkty według kategorii:**\n"
            for category, count in summary["categories"].items():
                result += f"• {category}: {count} produktów\n"

        return result

    def _format_pantry_stats(self, summary: dict[str, Any]) -> str:
        """Format pantry statistics"""
        result = "📊 **Statystyki spiżarni:**\n\n"

        if summary["total_items"] == 0:
            return "Twoja spiżarnia jest pusta. Brak statystyk do wyświetlenia."

        result += f"• Łączna liczba produktów: {summary['total_items']}\n"
        result += f"• Dostępność: {summary['in_stock']} ({summary['in_stock']/summary['total_items']*100:.1f}%)\n"
        result += f"• Niski stan: {summary['low_stock']} ({summary['low_stock']/summary['total_items']*100:.1f}%)\n"
        result += f"• Brak: {summary['out_of_stock']} ({summary['out_of_stock']/summary['total_items']*100:.1f}%)\n"

        if summary["expiring_soon"] > 0:
            result += f"• ⚠️ Wkrótce przeterminowane: {summary['expiring_soon']}\n"

        return result

    def _format_general_pantry_info(self, summary: dict[str, Any]) -> str:
        """Format general pantry information"""
        if summary["total_items"] == 0:
            return "Twoja spiżarnia jest obecnie pusta. Może czas na zakupy? 🛒"

        result = f"W Twojej spiżarni znajduje się {summary['total_items']} produktów. "
        result += f"Dostępnych masz {summary['in_stock']}, "

        if summary["low_stock"] > 0:
            result += f"{summary['low_stock']} ma niski stan, "

        if summary["out_of_stock"] > 0:
            result += f"{summary['out_of_stock']} jest niedostępnych"
        else:
            result += "wszystkie są dostępne"

        result += "."

        if summary["expiring_soon"] > 0:
            result += (
                f" ⚠️ Uwaga: {summary['expiring_soon']} produktów wkrótce się przedawni."
            )

        return result
