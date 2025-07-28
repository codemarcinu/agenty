import logging
from typing import Any

from sqlalchemy import text

from core.database import AsyncSessionLocal, engine

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """
    Provides database statistics and optimization insights for monitoring dashboard.
    """

    def __init__(self) -> None:
        pass

    async def get_database_stats(self) -> dict[str, Any]:
        """
        Gather database statistics: number of records in key tables, connection pool stats, slow queries, etc.
        Returns:
            dict: Database statistics for dashboard
        """
        stats = {}
        try:
            async with AsyncSessionLocal() as session:
                # Example: count records in key tables
                table_counts = {}
                for table in [
                    "conversations",
                    "messages",
                    "shopping_trips",
                    "products",
                    "user_profiles",
                    "user_activities",
                    "rag_documents",
                ]:
                    try:
                        result = await session.execute(
                            text(f"SELECT COUNT(*) FROM {table}")
                        )
                        count = result.scalar_one()
                        table_counts[table] = count
                    except Exception as e:
                        table_counts[table] = f"error: {e}"
                stats["table_counts"] = table_counts

                # Connection pool stats
                pool = engine.pool
                pool_stats = {
                    "checked_in": getattr(pool, "checked_in", lambda: None)(),
                    "checked_out": getattr(pool, "checked_out", lambda: None)(),
                    "overflow": getattr(pool, "overflow", lambda: None)(),
                    "size": getattr(pool, "size", lambda: None)(),
                }
                stats["connection_pool"] = pool_stats

        except Exception as e:
            logger.warning(f"Could not get database stats: {e}")
            stats["error"] = str(e)
        return stats
