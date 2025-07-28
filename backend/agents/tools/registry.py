"""
Centralny rejestr narzędzi dla systemu agentowego
Zgodnie z planem ewolucji - Faza 1: Refaktoryzacja na Narzędzia
"""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definicja narzędzia w rejestrze"""

    name: str
    description: str
    function: Callable
    required_args: list[str]
    optional_args: list[str]
    return_type: str
    examples: list[dict[str, Any]]


class ToolRegistry:
    """Centralny rejestr narzędzi"""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._initialized = False

    def register_tool(self, tool_def: ToolDefinition) -> None:
        """Zarejestruj narzędzie w rejestrze"""
        if tool_def.name in self._tools:
            logger.warning(f"Tool {tool_def.name} already registered, overwriting")

        self._tools[tool_def.name] = tool_def
        logger.info(f"Registered tool: {tool_def.name}")

    def get_tool(self, name: str) -> ToolDefinition | None:
        """Pobierz narzędzie po nazwie"""
        return self._tools.get(name)

    def get_all_tools(self) -> dict[str, ToolDefinition]:
        """Pobierz wszystkie zarejestrowane narzędzia"""
        return self._tools.copy()

    def get_tool_descriptions(self) -> list[dict[str, str]]:
        """Pobierz opisy wszystkich narzędzi dla planisty"""
        descriptions = []
        for tool_name, tool_def in self._tools.items():
            descriptions.append(
                {
                    "name": tool_name,
                    "description": tool_def.description,
                    "required_args": tool_def.required_args,
                    "optional_args": tool_def.optional_args,
                    "return_type": tool_def.return_type,
                }
            )
        return descriptions

    def format_tools_for_planner(self) -> str:
        """Formatuj narzędzia dla planisty LLM"""
        formatted_tools = []
        for tool_name, tool_def in self._tools.items():
            args_str = ", ".join([f"{arg}" for arg in tool_def.required_args])
            if tool_def.optional_args:
                optional_str = ", ".join(
                    [f"{arg} (optional)" for arg in tool_def.optional_args]
                )
                args_str += f", {optional_str}"

            formatted_tools.append(
                f"""
Tool: {tool_name}
Description: {tool_def.description}
Arguments: {args_str}
Returns: {tool_def.return_type}
"""
            )

        return "\n".join(formatted_tools)

    def execute_tool(self, name: str, **kwargs) -> Any:
        """Wykonaj narzędzie z podanymi argumentami"""
        tool_def = self.get_tool(name)
        if not tool_def:
            raise ValueError(f"Tool {name} not found in registry")

        # Sprawdź wymagane argumenty
        missing_args = [arg for arg in tool_def.required_args if arg not in kwargs]
        if missing_args:
            raise ValueError(
                f"Missing required arguments for tool {name}: {missing_args}"
            )

        try:
            result = tool_def.function(**kwargs)
            logger.debug(f"Executed tool {name} with result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            raise


# Globalna instancja rejestru
tool_registry = ToolRegistry()


# Dekorator do łatwego rejestrowania narzędzi
def register_tool(
    name: str,
    description: str,
    required_args: list[str],
    optional_args: list[str] | None = None,
    return_type: str = "Any",
    examples: list[dict[str, Any]] | None = None,
):
    """Dekorator do rejestrowania narzędzi"""

    def decorator(func: Callable) -> Callable:
        tool_def = ToolDefinition(
            name=name,
            description=description,
            function=func,
            required_args=required_args,
            optional_args=optional_args or [],
            return_type=return_type,
            examples=examples or [],
        )
        tool_registry.register_tool(tool_def)
        return func

    return decorator


# Przykładowe narzędzia (będą przeniesione z agentów)
@register_tool(
    name="get_weather_forecast",
    description="Get current or future weather forecast for a specific location",
    required_args=["location"],
    optional_args=["date"],
    return_type="str",
    examples=[{"location": "Warsaw", "date": "tomorrow"}, {"location": "Krakow"}],
)
async def get_weather_forecast(location: str, date: str | None = None) -> str:
    """Narzędzie do pobierania prognozy pogody"""
    # TODO: Implementacja z weather_agent
    return f"Weather forecast for {location} on {date or 'today'}"


@register_tool(
    name="search_knowledge_base",
    description="Search the knowledge base for relevant information",
    required_args=["query"],
    optional_args=["max_results"],
    return_type="str",
    examples=[
        {"query": "przepis na kurczaka", "max_results": 5},
        {"query": "zdrowe śniadanie"},
    ],
)
async def search_knowledge_base(query: str, max_results: int = 3) -> str:
    """Narzędzie do wyszukiwania w bazie wiedzy"""
    # TODO: Implementacja z rag_agent
    return f"Search results for: {query} (max {max_results} results)"


@register_tool(
    name="find_recipes",
    description="Find recipes based on ingredients and constraints",
    required_args=["ingredients"],
    optional_args=["constraints", "max_results"],
    return_type="List[Dict]",
    examples=[
        {"ingredients": ["chicken", "rice"], "constraints": "quick"},
        {"ingredients": ["tomatoes"], "max_results": 10},
    ],
)
async def find_recipes(
    ingredients: list[str], constraints: str | None = None, max_results: int = 5
) -> list[dict[str, Any]]:
    """Narzędzie do wyszukiwania przepisów"""
    # TODO: Implementacja z chef_agent
    return [
        {
            "name": f"Recipe with {', '.join(ingredients)}",
            "ingredients": ingredients,
            "constraints": constraints,
            "difficulty": "medium",
        }
    ]


@register_tool(
    name="get_pantry_items",
    description="Get available items from user's pantry",
    required_args=[],
    optional_args=["category"],
    return_type="List[Dict]",
    examples=[{"category": "vegetables"}, {}],
)
async def get_pantry_items(category: str | None = None) -> list[dict[str, Any]]:
    """Narzędzie do pobierania produktów ze spiżarni"""
    # TODO: Implementacja z pantry_tools
    return [{"name": "Sample item", "category": category or "general", "quantity": 1}]


@register_tool(
    name="web_search",
    description="Search the web for current information",
    required_args=["query"],
    optional_args=["max_results"],
    return_type="str",
    examples=[
        {"query": "latest news about AI", "max_results": 3},
        {"query": "weather in Paris"},
    ],
)
async def web_search(query: str, max_results: int = 3) -> str:
    """Narzędzie do wyszukiwania w internecie"""
    # TODO: Implementacja z search_agent
    return f"Web search results for: {query} (max {max_results} results)"


def initialize_tool_registry() -> ToolRegistry:
    """Inicjalizuj rejestr narzędzi"""
    if not tool_registry._initialized:
        logger.info("Initializing tool registry")
        tool_registry._initialized = True

    return tool_registry
