"""
Pantry Tools Module

Moduł do obsługi narzędzi spiżarni dla GeneralConversationAgent.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PantryTools:
    """Narzędzia do obsługi spiżarni"""

    @staticmethod
    def should_use_pantry_tools(query: str) -> bool:
        """Determine if pantry tools should be used"""
        return PantryTools.is_pantry_query(query)

    @staticmethod
    def is_pantry_query(query: str) -> bool:
        """Check if query is about pantry/inventory"""
        pantry_keywords = [
            "spiżarnia",
            "lodówka",
            "magazyn",
            "produkty",
            "jedzenie",
            "żywność",
            "co mam",
            "co jest",
            "sprawdź",
            "lista",
            "inwentarz",
            "zapasy",
            "składniki",
            "przepis",
            "gotowanie",
            "kuchnia",
            "jedzenie",
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in pantry_keywords)

    @staticmethod
    async def execute_pantry_tools(query: str, db: AsyncSession) -> str:
        """Execute pantry-related tools"""
        try:
            from agents.tools.tools import get_pantry_summary

            # Get pantry summary
            summary = await get_pantry_summary(db)

            if "co mam" in query.lower() or "co jest" in query.lower():
                # User wants to know what's in pantry
                result = "W Twojej spiżarni masz:\n\n"
                result += f"• Łącznie produktów: {summary['total_items']}\n"
                result += f"• W magazynie: {summary['in_stock']}\n"
                result += f"• Niski stan: {summary['low_stock']}\n"
                result += f"• Brak: {summary['out_of_stock']}\n"

                if summary["expiring_soon"] > 0:
                    result += f"• Wkrótce przeterminowane: {summary['expiring_soon']}\n"

                if summary["categories"]:
                    result += "\nProdukty według kategorii:\n"
                    for category, items in summary["categories"].items():
                        result += f"• {category}: {len(items)} produktów\n"

                return result
            else:
                # General pantry info
                return f"Podsumowanie spiżarni: {summary['total_items']} produktów, {summary['in_stock']} w magazynie, {summary['low_stock']} z niskim stanem."

        except Exception as e:
            logger.error(f"Error executing pantry tools: {e}")
            return f"Przepraszam, nie udało się pobrać informacji o spiżarni: {e!s}"

    @staticmethod
    def get_available_tools() -> list[str]:
        """Get list of available tools for the agent"""
        return [
            "search_web",
            "get_weather",
            "convert_units",
            "get_current_time",
            "calculate",
            "get_pantry_info",
            "check_pantry_for_ingredients",
        ]