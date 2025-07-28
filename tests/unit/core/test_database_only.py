#!/usr/bin/env python3
"""
Test tylko zapisu do bazy danych z naprawionym async SQLite
"""

import asyncio
import os
from pathlib import Path
import sys

# Dodaj src do PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_database_save():
    """Test zapisu do bazy danych"""

    # Ustaw środowisko testowe
    os.environ["ENVIRONMENT"] = "test"
    os.environ["DATABASE_URL"] = "sqlite:///test_foodsave.db"

    try:
        from datetime import datetime

        from backend.core.receipt_database import receipt_db_manager


        # Przygotuj testowe dane analizy
        test_analysis_data = {
            "store_name": "Test Sklep",
            "date": "2024-06-23",
            "total_amount": 15.99,
            "items": [
                {
                    "name": "Mleko 3.2% 1L",
                    "unit_price": 4.99,
                    "quantity": 1.0,
                    "category": "Nabiał"
                },
                {
                    "name": "Chleb pszenny",
                    "unit_price": 3.50,
                    "quantity": 2.0,
                    "category": "Pieczywo"
                }
            ]
        }

        # Test zapisu
        test_correlation_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        result = await receipt_db_manager.save_receipt_to_database(
            test_analysis_data,
            user_id="test_user",
            correlation_id=test_correlation_id
        )


        return bool(result.get("success"))

    except Exception:
        return False

if __name__ == "__main__":
    success = asyncio.run(test_database_save())
    sys.exit(0 if success else 1)
