import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def load_seed_data() -> dict[str, list[dict[str, Any]]]:
    """Loads seed data from a JSON file."""
    # PRODUCTION: Disabled seed data loading
    logger.info("Seed data loading disabled in production mode")
    return {"shopping_trips": []}


async def seed_database(db: AsyncSession | None = None) -> None:
    """
    Seeds the database with initial data.
    PRODUCTION: Database seeding is disabled to prevent test data contamination.

    Args:
        db: Optional database session
    """
    if db is None:
        return

    # PRODUCTION: Skip seeding to prevent test data contamination
    logger.info(
        "Database seeding disabled in production mode - using real user data only"
    )
    return

    # Original seeding logic (disabled)
    # try:
    #     # Check if database is already seeded
    #     result = await db.execute(select(ShoppingTrip).limit(1))
    #     existing_trip = result.scalars().first()

    #     if existing_trip:
    #         logger.info("Database already has data, skipping seeding.")
    #         return

    #     logger.info("Seeding database with initial shopping data...")

    #     seed_data = load_seed_data()
    #     # Insert shopping trips and their products
    #     for trip_data in seed_data["shopping_trips"]:
    #         products_data = trip_data.pop("products")
    #         trip = ShoppingTrip(**trip_data)
    #         db.add(trip)
    #         await db.flush()  # Get the trip ID

    #         for product_data in products_data:
    #             product = Product(trip_id=trip.id, **product_data)
    #             db.add(product)

    #     await db.commit()
    #     logger.info(
    #         f"Successfully seeded database with {len(seed_data['shopping_trips'])} shopping trips."
    #     )
    # except SQLAlchemyError as e:
    #     logger.error(f"Database seeding failed: {e}")
    #     await db.rollback()
    # except Exception as e:
    #     logger.error(f"An unexpected error occurred during database seeding: {e}")
    #     await db.rollback()
