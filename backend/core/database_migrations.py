"""
Migracje bazy danych dla systemu agentowego
"""

import logging

from sqlalchemy import text

from core.database import engine, get_db

logger = logging.getLogger(__name__)


def is_sqlite():
    return engine.url.get_backend_name() == "sqlite"


async def create_conversation_sessions_table():
    """Twórz tabelę conversation_sessions jeśli nie istnieje"""
    try:
        async for db in get_db():
            if is_sqlite():
                # SQLite: check sqlite_master
                result = await db.execute(
                    text(
                        """
                        SELECT name FROM sqlite_master WHERE type='table' AND name='conversation_sessions'
                        """
                    )
                )
                if result.fetchone():
                    logger.info("Table conversation_sessions already exists (SQLite)")
                    return
            else:
                # PostgreSQL: check information_schema
                result = await db.execute(
                    text(
                        """
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = 'conversation_sessions'
                        """
                    )
                )
                if result.fetchone():
                    logger.info(
                        "Table conversation_sessions already exists (PostgreSQL)"
                    )
                    return
            # Create table (minimal cross-db SQL)
            await db.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS conversation_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id VARCHAR NOT NULL UNIQUE,
                        user_id VARCHAR,
                        summary TEXT,
                        key_points TEXT,
                        topics_discussed TEXT,
                        user_preferences TEXT,
                        conversation_style VARCHAR DEFAULT 'friendly',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_message_count INTEGER DEFAULT 0
                    )
                    """
                )
            )
            # Indexes
            await db.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_conversation_sessions_session_id ON conversation_sessions(session_id)"
                )
            )
            await db.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_conversation_sessions_user_id ON conversation_sessions(user_id)"
                )
            )
            await db.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_conversation_sessions_updated_at ON conversation_sessions(updated_at)"
                )
            )
            await db.commit()
            logger.info("Table conversation_sessions created successfully")
    except Exception as e:
        logger.error(f"Error creating conversation_sessions table: {e}")
        if "db" in locals():
            await db.rollback()
        raise


async def update_existing_tables():
    """Aktualizuj istniejące tabele jeśli potrzeba"""
    try:
        async for db in get_db():
            if is_sqlite():
                # SQLite: pragma table_info
                result = await db.execute(text("PRAGMA table_info(messages)"))
                columns = [row[1] for row in result.fetchall()]
                if "message_metadata" not in columns:
                    await db.execute(
                        text(
                            "ALTER TABLE messages ADD COLUMN message_metadata TEXT DEFAULT '{}'"
                        )
                    )
                    logger.info(
                        "Added message_metadata column to messages table (SQLite)"
                    )
                result = await db.execute(text("PRAGMA table_info(conversations)"))
                columns = [row[1] for row in result.fetchall()]
                if "is_active" not in columns:
                    await db.execute(
                        text(
                            "ALTER TABLE conversations ADD COLUMN is_active BOOLEAN DEFAULT 1"
                        )
                    )
                    logger.info(
                        "Added is_active column to conversations table (SQLite)"
                    )
            else:
                # PostgreSQL: information_schema
                result = await db.execute(
                    text(
                        """
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name='messages' AND table_schema='public'
                        """
                    )
                )
                columns = [row[0] for row in result.fetchall()]
                if "message_metadata" not in columns:
                    await db.execute(
                        text(
                            "ALTER TABLE messages ADD COLUMN message_metadata JSONB DEFAULT '{}'"
                        )
                    )
                    logger.info(
                        "Added message_metadata column to messages table (PostgreSQL)"
                    )
                result = await db.execute(
                    text(
                        """
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name='conversations' AND table_schema='public'
                        """
                    )
                )
                columns = [row[0] for row in result.fetchall()]
                if "is_active" not in columns:
                    await db.execute(
                        text(
                            "ALTER TABLE conversations ADD COLUMN is_active BOOLEAN DEFAULT TRUE"
                        )
                    )
                    logger.info(
                        "Added is_active column to conversations table (PostgreSQL)"
                    )
            await db.commit()
    except Exception as e:
        logger.error(f"Error updating existing tables: {e}")
        if "db" in locals():
            await db.rollback()
        raise


async def create_all_tables():
    """Utwórz wszystkie tabele jeśli nie istnieją"""
    try:
        from core.database import engine

        # Create all tables using SQLAlchemy metadata
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from models.conversation import Base as ConversationBase

            # Create tables
            await conn.run_sync(ConversationBase.metadata.create_all)

        logger.info("All tables created successfully")

    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise


async def run_all_migrations():
    """Uruchom wszystkie migracje"""
    logger.info("Starting database migrations...")

    try:
        # Utwórz wszystkie tabele
        await create_all_tables()

        # Aktualizuj istniejące tabele
        await update_existing_tables()

        # Utwórz nową tabelę (jeśli nie istnieje)
        await create_conversation_sessions_table()

        logger.info("All migrations completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


async def verify_database_schema():
    """Sprawdź czy schemat bazy danych jest poprawny"""
    try:
        async for db in get_db():
            # Sprawdź tabele (PostgreSQL)
            result = await db.execute(
                text(
                    """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name NOT LIKE 'pg_%'
                ORDER BY table_name
            """
                )
            )
            tables = [row[0] for row in result.fetchall()]

            required_tables = ["conversations", "messages", "conversation_sessions"]
            missing_tables = [table for table in required_tables if table not in tables]

            if missing_tables:
                logger.warning(f"Missing tables: {missing_tables}")
                return False

            # Sprawdź kolumny w tabeli messages
            result = await db.execute(
                text(
                    """
                SELECT column_name FROM information_schema.columns
                WHERE table_name='messages' AND table_schema='public'
            """
                )
            )
            message_columns = [row[0] for row in result.fetchall()]
            required_message_columns = [
                "id",
                "content",
                "role",
                "created_at",
                "message_metadata",
                "conversation_id",
            ]
            missing_columns = [
                col for col in required_message_columns if col not in message_columns
            ]
            if missing_columns:
                logger.warning(f"Missing columns in messages table: {missing_columns}")
                return False

            logger.info("Database schema verification passed")
            return True

    except Exception as e:
        logger.error(f"Database schema verification failed: {e}")
        return False


if __name__ == "__main__":
    import asyncio

    async def main():
        await run_all_migrations()
        await verify_database_schema()

    asyncio.run(main())
