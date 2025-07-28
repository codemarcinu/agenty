"""
Database operations for receipt processing
"""

from datetime import date, datetime
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from core.database import get_async_session_factory
from core.receipt_exceptions import DatabaseSaveError
from models.shopping import Product, ShoppingTrip

logger = logging.getLogger(__name__)


class ReceiptDatabaseManager:
    """Manages database operations for receipt processing"""

    def __init__(self):
        self.session_factory = get_async_session_factory()

    async def save_receipt_to_database(
        self,
        analysis_data: dict[str, Any],
        user_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Save receipt analysis data to database

        Args:
            analysis_data: Structured receipt data from analysis
            user_id: User ID (optional)
            correlation_id: Correlation ID for tracing

        Returns:
            Dict with save results

        Raises:
            DatabaseSaveError: If save operation fails
        """
        async with self.session_factory() as session:
            try:
                # Parse and validate data
                trip_data = self._parse_trip_data(analysis_data)
                products_data = self._parse_products_data(analysis_data)

                # Create shopping trip
                trip = ShoppingTrip(
                    trip_date=trip_data["date"],
                    store_name=trip_data["store_name"],
                    total_amount=trip_data["total_amount"],
                )

                session.add(trip)
                await session.flush()  # Get trip.id

                logger.info(
                    f"Created shopping trip: {trip.id}",
                    extra={
                        "correlation_id": correlation_id,
                        "store_name": trip.store_name,
                        "trip_date": trip.trip_date,
                        "total_amount": trip.total_amount,
                    },
                )

                # Create products
                products_created = []
                for product_data in products_data:
                    product = Product(
                        name=product_data["name"],
                        category=product_data.get("category"),
                        unit_price=product_data.get("unit_price"),
                        quantity=product_data.get("quantity", 1.0),
                        unit=product_data.get("unit"),
                        trip_id=trip.id,
                    )
                    session.add(product)
                    products_created.append(product)

                await session.commit()

                result = {
                    "success": True,
                    "trip_id": trip.id,
                    "products_count": len(products_created),
                    "store_name": trip.store_name,
                    "trip_date": trip.trip_date.isoformat(),
                    "total_amount": trip.total_amount,
                    "created_at": datetime.now().isoformat(),
                }

                logger.info(
                    "Successfully saved receipt to database",
                    extra={
                        "correlation_id": correlation_id,
                        "trip_id": trip.id,
                        "products_count": len(products_created),
                    },
                )

                return result

            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(
                    f"Database error saving receipt: {e!s}",
                    extra={"correlation_id": correlation_id},
                )
                raise DatabaseSaveError(
                    f"Database error: {e!s}",
                    details={
                        "error_type": "SQLAlchemyError",
                        "correlation_id": correlation_id,
                    },
                )
            except Exception as e:
                await session.rollback()
                logger.error(
                    f"Unexpected error saving receipt: {e!s}",
                    extra={"correlation_id": correlation_id},
                )
                raise DatabaseSaveError(
                    f"Unexpected error saving to database: {e!s}",
                    details={
                        "error_type": type(e).__name__,
                        "correlation_id": correlation_id,
                    },
                )

    def _parse_trip_data(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Parse trip-level data from analysis results"""

        # Parse date
        trip_date = self._parse_date(analysis_data.get("date"))

        # Parse store name
        store_name = analysis_data.get("store_name", "Unknown Store")
        if not store_name or store_name.strip() == "":
            store_name = "Unknown Store"

        # Parse total amount
        total_amount = self._parse_amount(analysis_data.get("total_amount"))

        return {
            "date": trip_date,
            "store_name": store_name.strip()[:255],  # Limit length
            "total_amount": total_amount,
        }

    def _parse_products_data(
        self, analysis_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Parse products data from analysis results"""
        products = []

        # Get items from various possible keys
        items = (
            analysis_data.get("items", [])
            or analysis_data.get("products", [])
            or analysis_data.get("line_items", [])
            or []
        )

        if not items:
            # If no items found, create a single unknown item
            items = [{"name": "Unknown Item"}]

        for item in items:
            if not isinstance(item, dict):
                continue

            product_data = {
                "name": self._clean_product_name(item.get("name", "Unknown Product")),
                "category": item.get("category"),
                "unit_price": self._parse_amount(
                    item.get("unit_price") or item.get("price")
                ),
                "quantity": self._parse_quantity(item.get("quantity")),
                "unit": self._clean_unit(item.get("unit")),
            }

            products.append(product_data)

        return products

    def _parse_date(self, date_str: Any) -> date:
        """Parse date from various formats"""
        if isinstance(date_str, date):
            return date_str

        if isinstance(date_str, datetime):
            return date_str.date()

        if not date_str:
            return datetime.now().date()

        # Try to parse string date
        if isinstance(date_str, str):
            date_formats = [
                "%Y-%m-%d",
                "%d.%m.%Y",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%Y/%m/%d",
                "%d-%m-%Y",
            ]

            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt).date()
                except ValueError:
                    continue

        # Default to today if parsing fails
        logger.warning(f"Could not parse date: {date_str}, using today")
        return datetime.now().date()

    def _parse_amount(self, amount: Any) -> float | None:
        """Parse amount from various formats"""
        if amount is None:
            return None

        if isinstance(amount, int | float):
            return float(amount) if amount >= 0 else None

        if isinstance(amount, str):
            # Clean the string
            cleaned = amount.strip().replace(",", ".").replace(" ", "")

            # Remove currency symbols
            currency_symbols = ["zł", "PLN", "EUR", "$", "€", "£"]
            for symbol in currency_symbols:
                cleaned = cleaned.replace(symbol, "")

            try:
                value = float(cleaned)
                return value if value >= 0 else None
            except ValueError:
                logger.warning(f"Could not parse amount: {amount}")
                return None

        return None

    def _parse_quantity(self, quantity: Any) -> float:
        """Parse quantity from various formats"""
        if quantity is None:
            return 1.0

        if isinstance(quantity, int | float):
            return float(quantity) if quantity > 0 else 1.0

        if isinstance(quantity, str):
            # Clean the string
            cleaned = quantity.strip().replace(",", ".")

            try:
                value = float(cleaned)
                return value if value > 0 else 1.0
            except ValueError:
                logger.warning(f"Could not parse quantity: {quantity}")
                return 1.0

        return 1.0

    def _clean_product_name(self, name: Any) -> str:
        """Clean and validate product name"""
        if not name:
            return "Unknown Product"

        if isinstance(name, str):
            # Clean the name
            cleaned = name.strip()[:255]  # Limit length
            if cleaned:
                return cleaned

        return "Unknown Product"

    def _clean_unit(self, unit: Any) -> str | None:
        """Clean and validate unit"""
        if not unit:
            return None

        if isinstance(unit, str):
            cleaned = unit.strip()[:50]  # Limit length
            if cleaned:
                return cleaned

        return None

    async def get_recent_receipts(
        self, limit: int = 10, user_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get recent receipts from database"""
        async with self.session_factory() as session:
            try:
                query = (
                    select(ShoppingTrip)
                    .order_by(ShoppingTrip.created_at.desc())
                    .limit(limit)
                )

                result = await session.execute(query)
                trips = result.scalars().all()

                return [trip.to_dict() for trip in trips]

            except SQLAlchemyError as e:
                logger.error(f"Error getting recent receipts: {e!s}")
                return []

    async def get_receipt_by_id(self, trip_id: int) -> dict[str, Any] | None:
        """Get specific receipt by ID"""
        async with self.session_factory() as session:
            try:
                query = select(ShoppingTrip).where(ShoppingTrip.id == trip_id)
                result = await session.execute(query)
                trip = result.scalar_one_or_none()

                return trip.to_dict() if trip else None

            except SQLAlchemyError as e:
                logger.error(f"Error getting receipt {trip_id}: {e!s}")
                return None

    async def delete_receipt(self, trip_id: int) -> bool:
        """Delete receipt and all associated products"""
        async with self.session_factory() as session:
            try:
                query = select(ShoppingTrip).where(ShoppingTrip.id == trip_id)
                result = await session.execute(query)
                trip = result.scalar_one_or_none()

                if trip:
                    await session.delete(trip)
                    await session.commit()
                    logger.info(f"Deleted receipt {trip_id}")
                    return True

                return False

            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Error deleting receipt {trip_id}: {e!s}")
                return False


# Global instance
receipt_db_manager = ReceiptDatabaseManager()
