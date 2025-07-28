# w pliku backend/schemas/shopping_schemas.py
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date

# --- Schematy dla Produktu ---


# Pola wspólne dla tworzenia i odczytu
class ProductBase(BaseModel):
    name: str
    category: str | None = None
    quantity: float = 1.0
    unit: str | None = None
    unit_price: float | None = None
    expiration_date: date | None = None
    notes: str | None = None
    is_consumed: bool = False


# Schemat używany przy tworzeniu nowego produktu (nie znamy jeszcze jego ID)
class ProductCreate(ProductBase):
    pass


# Schemat używany przy aktualizacji produktu
class ProductUpdate(BaseModel):
    """
    Model Pydantic dla aktualizacji istniejącego produktu.
    Wszystkie pola są opcjonalne.
    """

    name: str | None = None
    category: str | None = None
    quantity: float | None = None
    unit: str | None = None
    unit_price: float | None = None
    expiration_date: date | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


# Schemat używany przy odczytywaniu produktu z bazy danych
class ProductSchema(ProductBase):
    id: int
    trip_id: int

    # Konfiguracja pozwalająca tworzyć schemat z obiektu SQLAlchemy
    model_config = {"from_attributes": True}


# --- Schematy dla Paragonu (ShoppingTrip) ---


class ShoppingTripBase(BaseModel):
    trip_date: date
    store_name: str
    total_amount: float | None = None


# Schemat do tworzenia nowego paragonu - zawiera listę produktów do stworzenia
class ShoppingTripCreate(ShoppingTripBase):
    products: list[ProductCreate] = []


# Schemat do aktualizacji paragonu
class ShoppingTripUpdate(BaseModel):
    """
    Model Pydantic dla aktualizacji istniejącego paragonu.
    Wszystkie pola są opcjonalne.
    """

    trip_date: date | None = None
    store_name: str | None = None
    total_amount: float | None = None

    model_config = {"from_attributes": True}


# Schemat do odczytu paragonu z bazy - zawiera listę wczytanych produktów
class ShoppingTrip(ShoppingTripBase):
    id: int
    products: list[ProductSchema] = []

    model_config = {"from_attributes": True}


class ShoppingTripSummary(BaseModel):
    """
    Schema for the summary of a shopping trip.
    """

    total_products: int
    total_cost: float

    model_config = {"from_attributes": True}


# Rebuild all models to resolve forward references
ShoppingTripCreate.model_rebuild()
ShoppingTrip.model_rebuild()
