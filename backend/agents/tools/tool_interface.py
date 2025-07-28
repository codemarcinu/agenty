"""
Tool Interface for general chat with web access and external tools
"""

from datetime import datetime
import json
import logging
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import BaseModel

# Perplexity API removed - using DuckDuckGo fallback
from settings import settings

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    """Result from tool execution"""

    success: bool
    result: str
    data: dict[str, Any] | None = None
    error: str | None = None
    execution_time: float = 0.0
    tool_name: str
    timestamp: str


class ToolInterface:
    """Interface for executing tools in general chat"""

    def __init__(self):
        self.available_tools = {
            "search_web": self._search_web,
            "get_weather": self._get_weather,
            "convert_units": self._convert_units,
            "get_current_time": self._get_current_time,
            "calculate": self._calculate,
            "get_pantry_info": self._get_pantry_info,
            "check_pantry_for_ingredients": self._check_pantry_for_ingredients,
        }
        self.tool_cache: dict[str, ToolResult] = {}

    async def execute_tool(
        self, tool_name: str, parameters: dict[str, Any], session_id: str
    ) -> dict[str, Any]:
        """
        Execute a tool with given parameters

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            session_id: Session ID for caching

        Returns:
            Tool execution result
        """
        start_time = datetime.now()

        try:
            if tool_name not in self.available_tools:
                return {
                    "success": False,
                    "result": f'Narzędzie "{tool_name}" nie jest dostępne',
                    "error": f"Unknown tool: {tool_name}",
                    "tool_name": tool_name,
                    "timestamp": datetime.now().isoformat(),
                }

            # Check cache
            cache_key = f"{session_id}:{tool_name}:{hash(json.dumps(parameters, sort_keys=True))}"
            if cache_key in self.tool_cache:
                cached_result = self.tool_cache[cache_key]
                # Cache for 5 minutes
                if (
                    datetime.now() - datetime.fromisoformat(cached_result.timestamp)
                ).seconds < 300:
                    logger.info(f"Using cached result for tool {tool_name}")
                    return cached_result.model_dump()

            # Execute tool
            tool_func = self.available_tools[tool_name]
            result = await tool_func(parameters, session_id)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            # Create result
            tool_result = ToolResult(
                success=result.get("success", True),
                result=result.get("result", ""),
                data=result.get("data"),
                error=result.get("error"),
                execution_time=execution_time,
                tool_name=tool_name,
                timestamp=datetime.now().isoformat(),
            )

            # Cache result
            self.tool_cache[cache_key] = tool_result

            logger.info(
                f"Tool {tool_name} executed successfully in {execution_time:.2f}s"
            )
            return tool_result.model_dump()

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "success": False,
                "result": f"Błąd podczas wykonywania narzędzia: {e!s}",
                "error": str(e),
                "tool_name": tool_name,
                "timestamp": datetime.now().isoformat(),
            }

    async def _search_web(
        self, parameters: dict[str, Any], session_id: str
    ) -> dict[str, Any]:
        """Search the web using Perplexity API"""
        try:
            query = parameters.get("query", "")
            if not query:
                return {
                    "success": False,
                    "result": "Zapytanie wyszukiwania jest wymagane",
                    "error": "Missing query parameter",
                }

            # Perplexity API removed - using basic web search
            return await self._basic_web_search(query)

        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return {
                "success": False,
                "result": f"Błąd podczas wyszukiwania: {e!s}",
                "error": str(e),
            }

    async def _basic_web_search(self, query: str) -> dict[str, Any]:
        """Basic web search fallback"""
        try:
            # Simple search using a search API
            search_url = f"https://api.duckduckgo.com/?q={quote(query)}&format=json"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(search_url)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get("AbstractText", "Brak wyników wyszukiwania")
                    return {
                        "success": True,
                        "result": f'Wyniki wyszukiwania dla "{query}":\n\n{results}',
                        "data": {"query": query, "search_results": results},
                    }
                return {
                    "success": False,
                    "result": "Nie udało się wykonać wyszukiwania",
                    "error": f"HTTP {response.status_code}",
                }
        except Exception as e:
            return {
                "success": False,
                "result": f"Błąd podczas wyszukiwania: {e!s}",
                "error": str(e),
            }

    async def _get_weather(
        self, parameters: dict[str, Any], session_id: str
    ) -> dict[str, Any]:
        """Get weather information for a location"""
        try:
            location = parameters.get("location", "Warszawa")

            # Use OpenWeatherMap API (you'll need to add API key to settings)
            api_key = getattr(settings, "OPENWEATHER_API_KEY", None)
            if api_key:
                weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={quote(location)}&appid={api_key}&units=metric&lang=pl"

                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(weather_url)
                    if response.status_code == 200:
                        data = response.json()
                        weather_info = {
                            "location": location,
                            "temperature": data["main"]["temp"],
                            "description": data["weather"][0]["description"],
                            "humidity": data["main"]["humidity"],
                            "wind_speed": data["wind"]["speed"],
                        }

                        result_text = f"Pogoda w {location}:\n"
                        result_text += f"Temperatura: {weather_info['temperature']}°C\n"
                        result_text += f"Opis: {weather_info['description']}\n"
                        result_text += f"Wilgotność: {weather_info['humidity']}%\n"
                        result_text += (
                            f"Prędkość wiatru: {weather_info['wind_speed']} m/s"
                        )

                        return {
                            "success": True,
                            "result": result_text,
                            "data": weather_info,
                        }
                    return {
                        "success": False,
                        "result": f"Nie udało się pobrać pogody dla {location}",
                        "error": f"HTTP {response.status_code}",
                    }
            else:
                return {
                    "success": False,
                    "result": "API klucz dla pogody nie jest skonfigurowany",
                    "error": "Missing OpenWeather API key",
                }

        except Exception as e:
            logger.error(f"Error getting weather: {e}")
            return {
                "success": False,
                "result": f"Błąd podczas pobierania pogody: {e!s}",
                "error": str(e),
            }

    async def _convert_units(
        self, parameters: dict[str, Any], session_id: str
    ) -> dict[str, Any]:
        """Convert units using a simple conversion system"""
        try:
            value = parameters.get("value")
            from_unit = parameters.get("from_unit", "").lower()
            to_unit = parameters.get("to_unit", "").lower()

            if value is None or not from_unit or not to_unit:
                return {
                    "success": False,
                    "result": "Wymagane parametry: value, from_unit, to_unit",
                    "error": "Missing required parameters",
                }

            # Simple conversion system
            conversions = {
                "temperature": {
                    "celsius_to_fahrenheit": lambda x: (x * 9 / 5) + 32,
                    "fahrenheit_to_celsius": lambda x: (x - 32) * 5 / 9,
                    "celsius_to_kelvin": lambda x: x + 273.15,
                    "kelvin_to_celsius": lambda x: x - 273.15,
                },
                "length": {
                    "meters_to_feet": lambda x: x * 3.28084,
                    "feet_to_meters": lambda x: x / 3.28084,
                    "kilometers_to_miles": lambda x: x * 0.621371,
                    "miles_to_kilometers": lambda x: x / 0.621371,
                },
                "weight": {
                    "kilograms_to_pounds": lambda x: x * 2.20462,
                    "pounds_to_kilograms": lambda x: x / 2.20462,
                    "grams_to_ounces": lambda x: x * 0.035274,
                    "ounces_to_grams": lambda x: x / 0.035274,
                },
            }

            # Find conversion
            conversion_key = f"{from_unit}_to_{to_unit}"
            result_value = None

            for category_conversions in conversions.values():
                if conversion_key in category_conversions:
                    result_value = category_conversions[conversion_key](float(value))
                    break

            if result_value is not None:
                return {
                    "success": True,
                    "result": f"{value} {from_unit} = {result_value:.2f} {to_unit}",
                    "data": {
                        "original_value": value,
                        "original_unit": from_unit,
                        "converted_value": round(result_value, 2),
                        "converted_unit": to_unit,
                    },
                }
            return {
                "success": False,
                "result": f"Konwersja z {from_unit} na {to_unit} nie jest obsługiwana",
                "error": "Unsupported conversion",
            }

        except Exception as e:
            logger.error(f"Error converting units: {e}")
            return {
                "success": False,
                "result": f"Błąd podczas konwersji jednostek: {e!s}",
                "error": str(e),
            }

    async def _get_current_time(
        self, parameters: dict[str, Any], session_id: str
    ) -> dict[str, Any]:
        """Get current time and date"""
        try:
            now = datetime.now()
            time_info = {
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "day_of_week": now.strftime("%A"),
                "timezone": "Europe/Warsaw",
            }

            result_text = f"Aktualny czas: {time_info['time']}\n"
            result_text += f"Data: {time_info['date']}\n"
            result_text += f"Dzień tygodnia: {time_info['day_of_week']}"

            return {"success": True, "result": result_text, "data": time_info}

        except Exception as e:
            logger.error(f"Error getting current time: {e}")
            return {
                "success": False,
                "result": f"Błąd podczas pobierania czasu: {e!s}",
                "error": str(e),
            }

    async def _calculate(
        self, parameters: dict[str, Any], session_id: str
    ) -> dict[str, Any]:
        """Perform mathematical calculations"""
        try:
            expression = parameters.get("expression", "")
            if not expression:
                return {
                    "success": False,
                    "result": "Wyrażenie matematyczne jest wymagane",
                    "error": "Missing expression parameter",
                }

            # Safe evaluation of mathematical expressions
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return {
                    "success": False,
                    "result": "Wyrażenie zawiera niedozwolone znaki",
                    "error": "Invalid characters in expression",
                }

            try:
                result = eval(expression)
                return {
                    "success": True,
                    "result": f"Wynik: {result}",
                    "data": {"expression": expression, "result": result},
                }
            except Exception as calc_error:
                return {
                    "success": False,
                    "result": f"Błąd w obliczeniach: {calc_error!s}",
                    "error": str(calc_error),
                }

        except Exception as e:
            logger.error(f"Error in calculation: {e}")
            return {
                "success": False,
                "result": f"Błąd podczas obliczeń: {e!s}",
                "error": str(e),
            }

    async def _get_pantry_info(
        self, parameters: dict[str, Any], session_id: str
    ) -> dict[str, Any]:
        """Get information about products in pantry"""
        try:
            from agents.tools.tools import get_pantry_items, get_pantry_summary
            from infrastructure.database.database import get_db

            query = parameters.get("query", "")
            category = parameters.get("category", "")
            status = parameters.get("status", "")

            db = get_db()
            async with db as session:
                if query or category or status:
                    # Get specific products
                    items = await get_pantry_items(
                        session, category=category, status=status
                    )

                    if not items:
                        return {
                            "success": True,
                            "result": "Nie znaleziono produktów w spiżarni spełniających kryteria.",
                            "data": {
                                "items": [],
                                "query": query,
                                "category": category,
                                "status": status,
                            },
                        }

                    # Filter by query if provided
                    if query:
                        query_lower = query.lower()
                        items = [
                            item
                            for item in items
                            if query_lower in item["name"].lower()
                        ]

                    if not items:
                        return {
                            "success": True,
                            "result": f"Nie znaleziono produktów zawierających '{query}' w spiżarni.",
                            "data": {"items": [], "query": query},
                        }

                    result = f"Znaleziono {len(items)} produktów w spiżarni:\n\n"
                    for item in items:
                        result += (
                            f"• {item['name']} - {item['quantity']} {item['unit']}"
                        )
                        if item.get("expiry_date"):
                            result += f" (do: {item['expiry_date'][:10]})"
                        result += f" - Status: {item['status']}\n"

                    return {
                        "success": True,
                        "result": result,
                        "data": {
                            "items": items,
                            "query": query,
                            "category": category,
                            "status": status,
                        },
                    }
                else:
                    # Get summary
                    summary = await get_pantry_summary(session)

                    result = "Podsumowanie spiżarni:\n"
                    result += f"• Łącznie produktów: {summary['total_items']}\n"
                    result += f"• W magazynie: {summary['in_stock']}\n"
                    result += f"• Niski stan: {summary['low_stock']}\n"
                    result += f"• Brak: {summary['out_of_stock']}\n"
                    result += f"• Wkrótce przeterminowane: {summary['expiring_soon']}\n"
                    result += f"• Przeterminowane: {summary['expired']}\n\n"

                    if summary["categories"]:
                        result += "Produkty według kategorii:\n"
                        for category, items in summary["categories"].items():
                            result += f"• {category}: {len(items)} produktów\n"

                    return {
                        "success": True,
                        "result": result,
                        "data": summary,
                    }

        except Exception as e:
            logger.error(f"Error getting pantry info: {e}")
            return {
                "success": False,
                "result": f"Błąd podczas pobierania informacji o spiżarni: {e!s}",
                "error": str(e),
            }

    async def _check_pantry_for_ingredients(
        self, parameters: dict[str, Any], session_id: str
    ) -> dict[str, Any]:
        """Check if given ingredients are available in pantry"""
        try:
            from agents.tools.tools import get_pantry_items
            from infrastructure.database.database import get_db

            ingredients = parameters.get("ingredients", [])
            if not ingredients:
                return {
                    "success": False,
                    "result": "Lista składników jest wymagana",
                    "error": "Missing ingredients parameter",
                }

            db = get_db()
            async with db as session:
                all_items = await get_pantry_items(session)

                result = "Sprawdzenie dostępności składników:\n\n"
                available_ingredients = []
                missing_ingredients = []

                for ingredient in ingredients:
                    ingredient_lower = ingredient.lower()
                    matching_items = []

                    for item in all_items:
                        if ingredient_lower in item["name"].lower():
                            matching_items.append(item)

                    if matching_items:
                        result += f"✅ {ingredient}: Znaleziono {len(matching_items)} produktów\n"
                        for item in matching_items:
                            result += f"   - {item['name']} ({item['quantity']} {item['unit']})\n"
                        available_ingredients.append(ingredient)
                    else:
                        result += f"❌ {ingredient}: Brak w spiżarni\n"
                        missing_ingredients.append(ingredient)

                return {
                    "success": True,
                    "result": result,
                    "data": {
                        "ingredients": ingredients,
                        "available": available_ingredients,
                        "missing": missing_ingredients,
                        "total_available": len(available_ingredients),
                        "total_missing": len(missing_ingredients),
                    },
                }

        except Exception as e:
            logger.error(f"Error checking pantry for ingredients: {e}")
            return {
                "success": False,
                "result": f"Błąd podczas sprawdzania składników: {e!s}",
                "error": str(e),
            }

    def get_available_tools(self) -> list[str]:
        """Get list of available tools"""
        return list(self.available_tools.keys())

    def get_tool_description(self, tool_name: str) -> str:
        """Get description of a tool"""
        descriptions = {
            "search_web": "Wyszukiwanie informacji w internecie",
            "get_weather": "Pobieranie informacji o pogodzie",
            "convert_units": "Konwersja jednostek",
            "get_current_time": "Pobieranie aktualnego czasu",
            "calculate": "Wykonywanie obliczeń matematycznych",
            "get_pantry_info": "Pobieranie informacji o produktach w spiżarni",
            "check_pantry_for_ingredients": "Sprawdzanie dostępności składników w spiżarni",
        }
        return descriptions.get(tool_name, "Brak opisu")
