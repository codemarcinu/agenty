from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

from sqlalchemy import text

from core.database import engine


async def run_migrations() -> None:
    """Run database migrations."""
    async with engine.begin() as conn:
        # Create products table if it doesn't exist
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                price FLOAT DEFAULT 0.0,
                unit VARCHAR,
                category VARCHAR,
                discount FLOAT DEFAULT 0.0,
                notes TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """
            )
        )
        logger.info("Products table created/verified")

        # Create shopping_trips table if it doesn't exist
        await conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS shopping_trips (
                id SERIAL PRIMARY KEY,
                trip_date TIMESTAMP,
                store_name VARCHAR,
                total_amount FLOAT DEFAULT 0.0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """
            )
        )
        logger.info("Shopping_trips table created/verified")

        # Now add columns if they don't exist (safe operations)
        # Check if the discount column exists
        result = await conn.execute(
            text(
                """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'products' AND column_name = 'discount'
        """
            )
        )
        if not result.scalar():
            # Add the discount column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN discount FLOAT DEFAULT 0.0
            """
                )
            )
            logger.info("Added discount column to products table")
        else:
            logger.info("Discount column already exists")

        # Check if the category column exists
        result = await conn.execute(
            text(
                """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'products' AND column_name = 'category'
        """
            )
        )
        if not result.scalar():
            # Add the category column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN category VARCHAR
            """
                )
            )
            logger.info("Added category column to products table")
        else:
            logger.info("Category column already exists")

        # Check if created_at column exists in shopping_trips table
        result = await conn.execute(
            text(
                """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'shopping_trips' AND column_name = 'created_at'
        """
            )
        )
        if not result.scalar():
            # Add the created_at column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE shopping_trips
                ADD COLUMN created_at TIMESTAMP
            """
                )
            )
            logger.info("Added created_at column to shopping_trips table")
        else:
            logger.info("Created_at column already exists in shopping_trips")

        # Check if updated_at column exists in shopping_trips table
        result = await conn.execute(
            text(
                """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'shopping_trips' AND column_name = 'updated_at'
        """
            )
        )
        if not result.scalar():
            # Add the updated_at column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE shopping_trips
                ADD COLUMN updated_at TIMESTAMP
            """
                )
            )
            logger.info("Added updated_at column to shopping_trips table")
        else:
            logger.info("Updated_at column already exists in shopping_trips")

        # Check if created_at column exists in products table
        result = await conn.execute(
            text(
                """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'products' AND column_name = 'created_at'
        """
            )
        )
        if not result.scalar():
            # Add the created_at column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN created_at TIMESTAMP
            """
                )
            )
            logger.info("Added created_at column to products table")
        else:
            logger.info("Created_at column already exists in products")

        # Check if updated_at column exists in products table
        result = await conn.execute(
            text(
                """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'products' AND column_name = 'updated_at'
        """
            )
        )
        if not result.scalar():
            # Add the updated_at column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN updated_at TIMESTAMP
            """
                )
            )
            logger.info("Added updated_at column to products table")
        else:
            logger.info("Updated_at column already exists in products")

        # Check if price column exists in products table
        result = await conn.execute(
            text(
                """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'products' AND column_name = 'price'
        """
            )
        )
        if not result.scalar():
            # Add the price column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN price FLOAT DEFAULT 0.0
            """
                )
            )
            logger.info("Added price column to products table")
        else:
            logger.info("Price column already exists in products")

        # Check if unit column exists in products table
        result = await conn.execute(
            text(
                """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'products' AND column_name = 'unit'
        """
            )
        )
        if not result.scalar():
            # Add the unit column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN unit VARCHAR
            """
                )
            )
            logger.info("Added unit column to products table")
        else:
            logger.info("Unit column already exists in products")

        # Check if notes column exists in products table
        result = await conn.execute(
            text(
                """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'products' AND column_name = 'notes'
        """
            )
        )
        if not result.scalar():
            # Add the notes column if it doesn't exist
            await conn.execute(
                text(
                    """
                ALTER TABLE products
                ADD COLUMN notes TEXT
            """
                )
            )
            logger.info("Added notes column to products table")
        else:
            logger.info("Notes column already exists in products")

        logger.info("Database migrations completed successfully")
