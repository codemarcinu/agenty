"""
Enhanced receipt validation module with business logic validation.
"""

from datetime import datetime, timedelta
import logging
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ReceiptItem(BaseModel):
    """Model for receipt item with validation"""

    name: str = Field(..., min_length=1, max_length=200)
    quantity: float = Field(..., gt=0, le=999)
    unit_price: float = Field(..., ge=0, le=999999)
    total_price: float = Field(..., ge=0, le=999999)
    tax_category: str = Field(..., pattern=r"^[ABC]$")

    @field_validator("total_price")
    @classmethod
    def validate_total_price(cls, v, info):
        """Validate that total_price = quantity * unit_price"""
        if info.data and "quantity" in info.data and "unit_price" in info.data:
            expected_total = round(info.data["quantity"] * info.data["unit_price"], 2)
            if abs(v - expected_total) > 0.01:  # Allow 1 cent tolerance
                logger.warning(
                    f"Total price mismatch: {v} vs expected {expected_total}"
                )
        return v


class ReceiptDiscount(BaseModel):
    """Model for receipt discount"""

    description: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0, le=999999)


class ReceiptData(BaseModel):
    """Enhanced receipt data model with validation"""

    store: str = Field(..., min_length=1, max_length=100)
    address: str = Field(default="", max_length=200)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    time: str = Field(default="", pattern=r"^(\d{2}:\d{2})?$")
    items: list[ReceiptItem] = Field(default=[])
    discounts: list[ReceiptDiscount] = Field(default=[])
    total: float = Field(..., ge=0, le=999999)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        """Validate date format and reasonableness"""
        try:
            parsed_date = datetime.strptime(v, "%Y-%m-%d")
            # Check if date is not in the future
            if parsed_date.date() > datetime.now().date():
                raise ValueError("Receipt date cannot be in the future")
            # Check if date is not older than 2 years
            if parsed_date.date() < (datetime.now() - timedelta(days=730)).date():
                logger.warning(f"Receipt date is older than 2 years: {v}")
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")
        return v

    @field_validator("total")
    @classmethod
    def validate_total(cls, v, info):
        """Validate total matches sum of items minus discounts"""
        if info.data and "items" in info.data and "discounts" in info.data:
            items_total = sum(item.total_price for item in info.data["items"])
            discounts_total = sum(discount.amount for discount in info.data["discounts"])
            expected_total = items_total - discounts_total

            if abs(v - expected_total) > 0.01:  # Allow 1 cent tolerance
                logger.warning(f"Total mismatch: {v} vs expected {expected_total}")
        return v


class ReceiptValidator:
    """Enhanced receipt validator with business logic validation"""

    def __init__(self):
        self.polish_stores = {
            "lidl",
            "biedronka",
            "kaufland",
            "tesco",
            "auchan",
            "carrefour",
            "żabka",
            "netto",
            "lewiatan",
            "euro",
            "dino",
            "polomarket",
            "freshmarket",
            "piotr i paweł",
            "alma",
            "selgros",
            "makro",
        }

        self.tax_rates = {
            "A": 0.23,  # 23% VAT
            "B": 0.08,  # 8% VAT
            "C": 0.05,  # 5% VAT
            "D": 0.0,  # 0% VAT
        }

    def validate_receipt_data(
        self, data: dict[str, Any]
    ) -> tuple[bool, list[str], dict[str, Any]]:
        """
        Comprehensive receipt validation with business logic

        Returns:
            tuple: (is_valid, errors, cleaned_data)
        """
        errors = []

        try:
            # Normalize and clean data
            cleaned_data = self._normalize_receipt_data(data)

            # Validate with Pydantic model
            receipt = ReceiptData(**cleaned_data)

            # Additional business logic validation
            self._validate_store_name(receipt.store, errors)
            self._validate_price_reasonableness(receipt.items, errors)
            self._validate_tax_consistency(receipt.items, errors)
            self._validate_quantity_reasonableness(receipt.items, errors)

            # Convert back to dict
            validated_data = receipt.dict()

            return len(errors) == 0, errors, validated_data

        except Exception as e:
            errors.append(f"Validation error: {e!s}")
            return False, errors, data

    def _normalize_receipt_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize receipt data for consistency"""
        normalized = data.copy()

        # Normalize store name
        store_name = normalized.get("store", "").strip()
        normalized["store"] = self._normalize_store_name_value(store_name)

        # Normalize date format
        date_str = normalized.get("date", "")
        if date_str:
            normalized["date"] = self._normalize_date(date_str)

        # Normalize items
        items = normalized.get("items", [])
        normalized["items"] = [self._normalize_item(item) for item in items]

        # Ensure numeric values
        if "total" in normalized:
            normalized["total"] = self._safe_float(normalized["total"])

        return normalized

    def _normalize_store_name_value(self, store_name: str) -> str:
        """Normalize store name to standard format"""
        if not store_name:
            return "Nieznany sklep"

        # Remove common suffixes
        store_name = re.sub(
            r"\s*(SP\.?\s*Z\.?\s*O\.?\s*O\.?|S\.?\s*A\.?|SP\.?\s*K\.?).*$",
            "",
            store_name,
            flags=re.IGNORECASE,
        )

        # Normalize common stores
        store_lower = store_name.lower().strip()

        store_mapping = {
            "lidl": "Lidl",
            "biedronka": "Biedronka",
            "kaufland": "Kaufland",
            "tesco": "Tesco",
            "auchan": "Auchan",
            "carrefour": "Carrefour",
            "żabka": "Żabka",
            "netto": "Netto",
            "lewiatan": "Lewiatan",
            "euro": "Euro",
            "dino": "Dino",
            "polomarket": "Polomarket",
        }

        # Check for partial matches
        for key, value in store_mapping.items():
            if key in store_lower:
                return value

        # Return title case if no match
        return store_name.title()

    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format"""
        if not date_str:
            return ""

        # Common date patterns
        patterns = [
            (
                r"^(\d{2})[.\-/](\d{2})[.\-/](\d{4})$",
                lambda m: f"{m.group(3)}-{m.group(2)}-{m.group(1)}",
            ),  # DD.MM.YYYY
            (
                r"^(\d{4})[.\-/](\d{2})[.\-/](\d{2})$",
                lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}",
            ),  # YYYY.MM.DD
            (
                r"^(\d{2})[.\-/](\d{2})[.\-/](\d{2})$",
                lambda m: f"20{m.group(3)}-{m.group(2)}-{m.group(1)}",
            ),  # DD.MM.YY
        ]

        for pattern, formatter in patterns:
            match = re.match(pattern, date_str.strip())
            if match:
                return formatter(match)

        return date_str

    def _normalize_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """Normalize receipt item"""
        normalized = item.copy()

        # Normalize name
        name = normalized.get("name", "").strip().upper()
        normalized["name"] = name

        # Ensure numeric values
        normalized["quantity"] = self._safe_float(normalized.get("quantity", 1.0))
        normalized["unit_price"] = self._safe_float(normalized.get("unit_price", 0.0))
        normalized["total_price"] = self._safe_float(normalized.get("total_price", 0.0))

        # Normalize tax category
        tax_category = normalized.get("tax_category", "A").upper()
        if tax_category not in ["A", "B", "C", "D"]:
            tax_category = "A"
        normalized["tax_category"] = tax_category

        return normalized

    def _safe_float(self, value: Any) -> float:
        """Safely convert value to float"""
        if isinstance(value, int | float):
            return float(value)

        if isinstance(value, str):
            # Replace comma with dot for Polish decimal notation
            value = value.replace(",", ".")
            try:
                return float(value)
            except ValueError:
                return 0.0

        return 0.0

    def _validate_store_name(self, store_name: str, errors: list[str]) -> None:
        """Validate store name"""
        if not store_name or store_name == "Nieznany sklep":
            errors.append("Store name is missing or unknown")

        # Check if it's a known Polish store
        if store_name.lower() not in self.polish_stores:
            logger.info(f"Unknown store: {store_name}")

    def _validate_price_reasonableness(
        self, items: list[ReceiptItem], errors: list[str]
    ) -> None:
        """Validate price reasonableness"""
        for item in items:
            # Check for unreasonably high prices
            if item.unit_price > 1000:
                errors.append(
                    f"Unreasonably high price for {item.name}: {item.unit_price}"
                )

            # Check for zero prices (might be valid for promotions)
            if item.unit_price == 0:
                logger.warning(f"Zero price for {item.name}")

    def _validate_tax_consistency(
        self, items: list[ReceiptItem], errors: list[str]
    ) -> None:
        """Validate tax category consistency"""
        for item in items:
            tax_category = item.tax_category
            if tax_category not in self.tax_rates:
                errors.append(f"Invalid tax category {tax_category} for {item.name}")

    def _validate_quantity_reasonableness(
        self, items: list[ReceiptItem], errors: list[str]
    ) -> None:
        """Validate quantity reasonableness"""
        for item in items:
            # Check for unreasonably high quantities
            if item.quantity > 100:
                logger.warning(f"High quantity for {item.name}: {item.quantity}")

            # Check for very small quantities (might be weight-based)
            if item.quantity < 0.01:
                errors.append(
                    f"Unreasonably small quantity for {item.name}: {item.quantity}"
                )


# Global validator instance
receipt_validator = ReceiptValidator()
