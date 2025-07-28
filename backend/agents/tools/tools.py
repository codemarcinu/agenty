import datetime
from datetime import date
import locale
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core import crud
from core.llm_client import llm_client
from core.utils import extract_json_from_text
from models.shopping import Product, ShoppingTrip
from settings import settings

logger = logging.getLogger(__name__)


async def recognize_intent(prompt: str) -> str:
    """
    Narzędzie, które rozpoznaje intencję użytkownika na podstawie promptu.
    """
    try:
        response = await llm_client.chat(
            model=settings.DEFAULT_CODE_MODEL,  # Use faster model for this task
            messages=[
                {
                    "role": "system",
                    "content": "Jesteś precyzyjnym systemem klasyfikacji intencji. Zawsze zwracaj tylko JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
            options={"temperature": 0.0},
        )
        if isinstance(response, dict) and response.get("message"):
            content = response["message"]["content"]
            # Use extract_json_from_text to handle markdown and other formats
            json_str = extract_json_from_text(content)
            if json_str:
                return json_str
            logger.warning(
                f"No valid JSON found in intent recognition response: {content}"
            )
            return '{"intent": "UNKNOWN"}'
        return '{"intent": "UNKNOWN"}'
    except Exception as e:
        logger.error(f"Błąd podczas rozpoznawania intencji: {e}")
        return '{"intent": "UNKNOWN"}'


async def extract_entities(prompt: str) -> str:
    """
    Narzędzie, które ekstrahuje encje z promptu.
    """
    try:
        response = await llm_client.chat(
            model=settings.DEFAULT_CODE_MODEL,  # Use faster model for this task
            messages=[
                {
                    "role": "system",
                    "content": "Jesteś precyzyjnym systemem ekstrakcji encji. Zawsze zwracaj tylko JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
            options={"temperature": 0.0},
        )
        if isinstance(response, dict) and response.get("message"):
            content = response["message"]["content"]
            # Use extract_json_from_text to handle markdown and other formats
            json_str = extract_json_from_text(content)
            if json_str:
                return json_str
            logger.warning(
                f"No valid JSON found in entity extraction response: {content}"
            )
            return "{}"
        return "{}"
    except Exception as e:
        logger.error(f"Błąd podczas ekstrakcji encji: {e}")
        return "{}"


async def find_database_object(
    db: AsyncSession, intent: str, entities: dict
) -> list[Any]:
    """
    Narzędzie, które na podstawie intencji i encji wyszukuje obiekty w bazie danych.
    Zwraca listę znalezionych obiektów.
    """
    match intent:
        case "UPDATE_ITEM" | "DELETE_ITEM":
            return await crud.find_item_for_action(db, entities=entities)
        case "UPDATE_PURCHASE" | "DELETE_PURCHASE" | "ADD_PRODUCTS_TO_TRIP":
            return await crud.find_purchase_for_action(db, entities=entities)
        case "CZYTAJ_PODSUMOWANIE":
            return await crud.get_summary(db, query_params=entities)
        case _:
            return []


async def execute_database_action(
    db: AsyncSession, intent: str, target_object: Any, entities: dict
) -> bool:
    """
    Narzędzie, które wykonuje operację zapisu (UPDATE/DELETE/CREATE) lub analizy w bazie.
    """
    try:
        if intent in ["DODAJ_ZAKUPY", "CREATE_ITEM", "CREATE_PURCHASE"]:
            from agents.agent_factory import AgentFactory

            agent_factory = AgentFactory()
            categorization_agent = agent_factory.create_agent("categorization")

            for product in entities.get("produkty", []):
                if not product.get("nazwa"):
                    logger.warning(f"Skipping product without a name: {product}")
                    continue
                if not product.get("kategoria"):
                    response = await categorization_agent.process(
                        {"product_name": product["nazwa"]}
                    )
                    if response.success and response.data:
                        product["kategoria"] = response.data.get("category")

            await crud.create_shopping_trip(db, data=entities)
            return True
        if intent == "ADD_PRODUCTS_TO_TRIP":
            if not target_object or not isinstance(target_object, ShoppingTrip):
                logger.error("Nie znaleziono paragonu do którego można dodać produkty.")
                return False
            products_data = entities.get("produkty", [])
            if not products_data:
                logger.error("Brak danych o produktach do dodania.")
                return False
            await crud.add_products_to_trip(
                db, shopping_trip_id=target_object.id, products_data=products_data
            )
            return True
        if intent == "ANALYZE":
            result = await crud.get_summary(db, query_params=entities)
            return bool(result)
        # Dla UPDATE i DELETE
        operations = entities.get("operacje")
        return await crud.execute_action(db, intent, target_object, operations)
    except Exception as e:
        logger.error(f"Error executing database action: {e}")
        return False


def generate_clarification_question_text(options: list[Any]) -> str:
    """
    Narzędzie, które formatuje listę opcji na czytelne pytanie dla użytkownika.
    """
    if not options:
        return "Coś poszło nie tak, nie mam opcji do wyboru."

    formatted_options = []
    for i, obj in enumerate(options, 1):
        if isinstance(obj, ShoppingTrip):
            formatted_options.append(
                f"{i}. Paragon ze sklepu '{obj.store_name}' z dnia {obj.trip_date}."
            )
        elif isinstance(obj, Product):
            formatted_options.append(
                f"{i}. Produkt '{obj.name}' w cenie {obj.unit_price} zł."
            )
        else:  # Dla wyników z get_summary
            formatted_options.append(f"{i}. {obj}")

    return "Znalazłem kilka pasujących opcji. Proszę, wybierz jedną:\n" + "\n".join(
        formatted_options
    )


async def get_available_products_from_pantry(db: AsyncSession) -> list[Product]:
    """
    Gets all available products from pantry (not consumed and not expired).
    Returns list of Product objects.
    """
    try:
        return await crud.get_available_products(db)
    except SQLAlchemyError as e:
        logger.error(f"Error getting available products: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting available products: {e}")
        return []


async def get_pantry_items(
    db: AsyncSession, category: str | None = None, status: str | None = None
) -> list[dict[str, Any]]:
    """
    Gets pantry items with optional filtering.
    Returns list of dictionaries with pantry item information.

    Args:
        db: Database session
        category: Optional category filter
        status: Optional status filter (in-stock, low-stock, out-of-stock)

    Returns:
        List of pantry items as dictionaries
    """
    try:
        # Build query
        query = select(Product).where(Product.is_consumed == 0)

        if category:
            query = query.where(Product.category == category)

        # Execute query
        result = await db.execute(query)
        products = result.scalars().all()

        # Convert to pantry format
        pantry_items = []
        for product in products:
            # Determine status based on quantity
            status = "in-stock"
            if product.quantity is None or product.quantity <= 0:
                status = "out-of-stock"
            elif product.quantity <= (product.unit_price or 1) * 0.2:  # 20% threshold
                status = "low-stock"

            # Check expiry
            expiry_status = None
            if product.expiration_date:
                days_until_expiry = (product.expiration_date - date.today()).days
                if days_until_expiry < 0:
                    expiry_status = "expired"
                elif days_until_expiry <= 3:
                    expiry_status = "expiring-soon"
                else:
                    expiry_status = "good"

            pantry_item = {
                "id": str(product.id),
                "name": product.name,
                "category": product.category or "Uncategorized",
                "quantity": product.quantity or 0,
                "unit": product.unit or "szt",
                "expiry_date": (
                    product.expiration_date.isoformat()
                    if product.expiration_date
                    else None
                ),
                "status": status,
                "unit_price": product.unit_price,
                "notes": product.notes,
                "expiry_status": expiry_status,
            }
            pantry_items.append(pantry_item)

        # Apply status filter if provided
        if status:
            pantry_items = [item for item in pantry_items if item["status"] == status]

        return pantry_items

    except Exception as e:
        logger.error(f"Error getting pantry items: {e}")
        return []


async def get_pantry_summary(db: AsyncSession) -> dict[str, Any]:
    """
    Gets a summary of pantry items including statistics.

    Args:
        db: Database session

    Returns:
        Dictionary with pantry summary information
    """
    try:
        items = await get_pantry_items(db)

        total_items = len(items)
        in_stock = len([item for item in items if item["status"] == "in-stock"])
        low_stock = len([item for item in items if item["status"] == "low-stock"])
        out_of_stock = len([item for item in items if item["status"] == "out-of-stock"])
        expiring_soon = len(
            [item for item in items if item.get("expiry_status") == "expiring-soon"]
        )
        expired = len(
            [item for item in items if item.get("expiry_status") == "expired"]
        )

        # Group by category
        categories = {}
        for item in items:
            category = item["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(item)

        return {
            "total_items": total_items,
            "in_stock": in_stock,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
            "expiring_soon": expiring_soon,
            "expired": expired,
            "categories": categories,
            "items": items,
        }

    except Exception as e:
        logger.error(f"Error getting pantry summary: {e}")
        return {
            "total_items": 0,
            "in_stock": 0,
            "low_stock": 0,
            "out_of_stock": 0,
            "expiring_soon": 0,
            "expired": 0,
            "categories": {},
            "items": [],
        }


async def mark_products_as_consumed(db: AsyncSession, product_ids: list[int]) -> bool:
    """
    Marks specified products as consumed.
    Returns True if successful, False otherwise.
    """
    try:
        return await crud.mark_products_consumed(db, product_ids)
    except SQLAlchemyError as e:
        logger.error(f"Error marking products as consumed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error marking products as consumed: {e}")
        return False


def get_current_date() -> str:
    """
    Narzędzie, które zwraca aktualną datę i dzień tygodnia.
    """
    try:
        # Ustawienie polskiej lokalizacji dla nazw dni tygodnia
        locale.setlocale(locale.LC_TIME, "pl_PL.UTF-8")
    except locale.Error:
        logger.warning(
            "Could not set locale to pl_PL.UTF-8. Day names may be in English."
        )

    now = datetime.datetime.now()
    return now.strftime("Dzisiaj jest %A, %d %B %Y.")
