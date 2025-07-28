#!/usr/bin/env python3
"""
Kompleksowy test end-to-end flow przetwarzania paragonów
Od uploadu pliku aż do zapisania w bazie danych
"""

import asyncio
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
from typing import Any
import uuid

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import aiohttp
from PIL import Image, ImageDraw, ImageFont

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class CompleteReceiptFlowTester:
    """Kompleksowy tester flow przetwarzania paragonów"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = {
            "file_creation": False,
            "file_upload": False,
            "ocr_processing": False,
            "receipt_analysis": False,
            "database_save": False,
            "data_retrieval": False
        }
        self.correlation_id = f"test_flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def create_test_receipt_image(self) -> Path:
        """Tworzy testowy obraz paragonu"""
        logger.info("=== KROK 1: Tworzenie testowego obrazu paragonu ===")

        try:
            # Utwórz obraz 800x600 z białym tłem
            img = Image.new("RGB", (800, 600), color="white")
            draw = ImageDraw.Draw(img)

            # Dodaj tekst paragonu
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except:
                font = ImageFont.load_default()

            receipt_text = [
                "LIDL POLSKA SP Z O.O.",
                "ul. Testowa 123, 00-000 Warszawa",
                "NIP: 123-456-78-90",
                "",
                "Data: 2024-01-15",
                "Godzina: 14:30",
                "",
                "MLEKO 3,2% 1L    4.99 zł",
                "CHLEB ŻYTNI 500G   3.50 zł",
                "JOGURT NATURALNY    2.99 zł",
                "",
                "SUMA: 11.48 zł",
                "VAT 23%: 2.15 zł",
                "DO ZAPŁATY: 11.48 zł",
                "",
                "Dziękujemy za zakupy!"
            ]

            y_position = 50
            for line in receipt_text:
                draw.text((50, y_position), line, fill="black", font=font)
                y_position += 30

            # Zapisz do pliku tymczasowego
            temp_file = Path(tempfile.gettempdir()) / f"test_receipt_{uuid.uuid4()}.jpg"
            img.save(temp_file, "JPEG", quality=95)

            logger.info(f"✅ Utworzono testowy obraz paragonu: {temp_file}")
            self.test_results["file_creation"] = True
            return temp_file

        except Exception as e:
            logger.error(f"❌ Błąd tworzenia obrazu: {e}")
            raise

    async def test_file_upload(self, file_path: Path) -> dict[str, Any]:
        """Test 2: Upload pliku do API"""
        logger.info("=== KROK 2: Upload pliku do API ===")

        try:
            # Przygotuj dane do uploadu
            data = aiohttp.FormData()
            data.add_field("file",
                         open(file_path, "rb"),
                         filename="test_receipt.jpg",
                         content_type="image/jpeg")

            # Wywołaj endpoint upload
            upload_url = f"{self.base_url}/api/v2/receipts/process"

            logger.info(f"Wysyłam plik do: {upload_url}")

            async with self.session.post(upload_url, data=data) as response:
                response_text = await response.text()

                logger.info(f"Status odpowiedzi: {response.status}")
                logger.info(f"Odpowiedź: {response_text}")

                if response.status == 200:
                    result = json.loads(response_text)
                    logger.info("✅ Upload pliku: SUKCES")
                    logger.info(f"Dane odpowiedzi: {json.dumps(result, indent=2)}")
                    self.test_results["file_upload"] = True
                    return result
                else:
                    logger.error(f"❌ Upload pliku: BŁĄD HTTP {response.status}")
                    logger.error(f"Treść błędu: {response_text}")
                    return {"error": f"HTTP {response.status}: {response_text}"}

        except Exception as e:
            logger.error(f"❌ Błąd uploadu: {e}")
            return {"error": str(e)}

    async def test_async_processing(self, file_path: Path) -> dict[str, Any]:
        """Test 3: Asynchroniczne przetwarzanie"""
        logger.info("=== KROK 3: Asynchroniczne przetwarzanie ===")

        try:
            # Przygotuj dane do uploadu
            data = aiohttp.FormData()
            data.add_field("file",
                         open(file_path, "rb"),
                         filename="test_receipt.jpg",
                         content_type="image/jpeg")

            # Wywołaj endpoint async
            async_url = f"{self.base_url}/api/v2/receipts/process_async"

            logger.info(f"Wysyłam plik do async endpoint: {async_url}")

            async with self.session.post(async_url, data=data) as response:
                response_text = await response.text()

                logger.info(f"Status odpowiedzi: {response.status}")
                logger.info(f"Odpowiedź: {response_text}")

                if response.status == 202:
                    result = json.loads(response_text)
                    task_id = result.get("task_id")
                    logger.info(f"✅ Async processing: SUKCES - Task ID: {task_id}")
                    self.test_results["ocr_processing"] = True
                    return result
                else:
                    logger.error(f"❌ Async processing: BŁĄD HTTP {response.status}")
                    logger.error(f"Treść błędu: {response_text}")
                    return {"error": f"HTTP {response.status}: {response_text}"}

        except Exception as e:
            logger.error(f"❌ Błąd async processing: {e}")
            return {"error": str(e)}

    async def test_task_status(self, task_id: str) -> dict[str, Any]:
        """Test 4: Sprawdzanie statusu zadania"""
        logger.info("=== KROK 4: Sprawdzanie statusu zadania ===")

        try:
            status_url = f"{self.base_url}/api/v2/receipts/status/{task_id}"

            logger.info(f"Sprawdzam status zadania: {status_url}")

            # Poll status przez maksymalnie 60 sekund
            max_attempts = 12
            attempt = 0

            while attempt < max_attempts:
                async with self.session.get(status_url) as response:
                    response_text = await response.text()

                    if response.status == 200:
                        result = json.loads(response_text)
                        status = result.get("status", "unknown")

                        logger.info(f"Status zadania (próba {attempt + 1}): {status}")

                        if status == "completed":
                            logger.info("✅ Zadanie zakończone pomyślnie")
                            logger.info(f"Wynik: {json.dumps(result, indent=2)}")
                            self.test_results["receipt_analysis"] = True
                            return result
                        elif status == "failed":
                            logger.error(f"❌ Zadanie zakończone błędem: {result.get('error')}")
                            return {"error": result.get("error")}
                        elif status in ["pending", "processing"]:
                            logger.info(f"Zadanie w trakcie: {status}")
                            await asyncio.sleep(5)  # Czekaj 5 sekund
                            attempt += 1
                        else:
                            logger.warning(f"Nieznany status: {status}")
                            await asyncio.sleep(5)
                            attempt += 1
                    else:
                        logger.error(f"❌ Błąd sprawdzania statusu: HTTP {response.status}")
                        logger.error(f"Treść błędu: {response_text}")
                        return {"error": f"HTTP {response.status}: {response_text}"}

            logger.error("❌ Timeout - zadanie nie zakończone w czasie")
            return {"error": "Task timeout"}

        except Exception as e:
            logger.error(f"❌ Błąd sprawdzania statusu: {e}")
            return {"error": str(e)}

    async def test_database_save(self, analysis_data: dict[str, Any]) -> dict[str, Any]:
        """Test 5: Zapis do bazy danych"""
        logger.info("=== KROK 5: Zapis do bazy danych ===")

        try:
            # Import database manager directly
            from backend.core.receipt_database import ReceiptDatabaseManager

            # Create database manager
            db_manager = ReceiptDatabaseManager()

            # Generate correlation ID for tracing
            correlation_id = f"test_save_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            logger.info("Zapisuję dane do bazy bezpośrednio")
            logger.info(f"Dane do zapisu: {json.dumps(analysis_data, indent=2)}")

            # Save to database directly
            save_result = await db_manager.save_receipt_to_database(
                analysis_data,
                user_id="test_user",
                correlation_id=correlation_id
            )

            logger.info(f"Status zapisu: {save_result}")

            if save_result.get("success"):
                logger.info("✅ Zapis do bazy: SUKCES")
                logger.info(f"Wynik zapisu: {json.dumps(save_result, indent=2)}")
                self.test_results["database_save"] = True
                return save_result
            else:
                logger.error(f"❌ Zapis do bazy: BŁĄD - {save_result.get('error')}")
                return {"error": save_result.get("error")}

        except Exception as e:
            logger.error(f"❌ Błąd zapisu do bazy: {e}")
            return {"error": str(e)}

    async def test_data_retrieval(self, trip_id: str) -> dict[str, Any]:
        """Test 6: Pobieranie zapisanych danych"""
        logger.info("=== KROK 6: Pobieranie zapisanych danych ===")

        try:
            # Endpoint do pobierania paragonów (jeśli istnieje)
            retrieve_url = f"{self.base_url}/api/v2/receipts"

            logger.info(f"Pobieram dane paragonów: {retrieve_url}")

            async with self.session.get(retrieve_url) as response:
                response_text = await response.text()

                logger.info(f"Status odpowiedzi: {response.status}")
                logger.info(f"Odpowiedź: {response_text}")

                if response.status == 200:
                    result = json.loads(response_text)
                    logger.info("✅ Pobieranie danych: SUKCES")
                    logger.info(f"Pobrane dane: {json.dumps(result, indent=2)}")
                    self.test_results["data_retrieval"] = True
                    return result
                else:
                    logger.warning(f"⚠️ Pobieranie danych: HTTP {response.status}")
                    logger.warning(f"Treść odpowiedzi: {response_text}")
                    return {"warning": f"HTTP {response.status}: {response_text}"}

        except Exception as e:
            logger.error(f"❌ Błąd pobierania danych: {e}")
            return {"error": str(e)}

    async def run_complete_flow(self) -> dict[str, Any]:
        """Uruchamia kompletny flow testowy"""
        logger.info("🚀 ROZPOCZYNAM KOMPLETNY TEST FLOW PRZETWARZANIA PARAGONÓW")
        logger.info(f"Correlation ID: {self.correlation_id}")

        try:
            # Krok 1: Utwórz testowy obraz
            test_file = self.create_test_receipt_image()

            # Krok 2: Upload pliku
            upload_result = await self.test_file_upload(test_file)
            if "error" in upload_result:
                logger.error(f"❌ Test przerwany na kroku upload: {upload_result['error']}")
                return {"success": False, "error": upload_result["error"], "step": "upload"}

            # Krok 3: Async processing
            async_result = await self.test_async_processing(test_file)
            if "error" in async_result:
                logger.error(f"❌ Test przerwany na kroku async: {async_result['error']}")
                return {"success": False, "error": async_result["error"], "step": "async"}

            task_id = async_result.get("task_id")
            if not task_id:
                logger.error("❌ Brak task_id z async endpoint")
                return {"success": False, "error": "No task_id received", "step": "async"}

            # Krok 4: Sprawdź status zadania
            status_result = await self.test_task_status(task_id)
            if "error" in status_result:
                logger.error(f"❌ Test przerwany na kroku status: {status_result['error']}")
                return {"success": False, "error": status_result["error"], "step": "status"}

            analysis_data = status_result.get("result", {})

            # Krok 5: Zapis do bazy
            save_result = await self.test_database_save(analysis_data)
            if "error" in save_result:
                logger.error(f"❌ Test przerwany na kroku save: {save_result['error']}")
                return {"success": False, "error": save_result["error"], "step": "save"}

            trip_id = save_result.get("trip_id")

            # Krok 6: Pobierz dane
            if trip_id:
                retrieve_result = await self.test_data_retrieval(str(trip_id))
            else:
                logger.warning("⚠️ Brak trip_id - pomijam pobieranie danych")
                retrieve_result = {"warning": "No trip_id available"}

            # Podsumowanie
            success_count = sum(1 for result in self.test_results.values() if result)
            total_steps = len(self.test_results)

            logger.info("\n" + "="*60)
            logger.info("📊 PODSUMOWANIE TESTU FLOW")
            logger.info("="*60)

            for step, result in self.test_results.items():
                status = "✅ SUKCES" if result else "❌ BŁĄD"
                logger.info(f"{step.replace('_', ' ').title()}: {status}")

            logger.info(f"\nWynik: {success_count}/{total_steps} kroków zakończonych pomyślnie")

            if success_count == total_steps:
                logger.info("🎉 KOMPLETNY FLOW ZAKOŃCZONY POMYŚLNIE!")
                return {
                    "success": True,
                    "steps_completed": success_count,
                    "total_steps": total_steps,
                    "correlation_id": self.correlation_id,
                    "trip_id": trip_id,
                    "task_id": task_id
                }
            else:
                logger.error("⚠️ FLOW ZAKOŃCZONY Z BŁĘDAMI")
                return {
                    "success": False,
                    "steps_completed": success_count,
                    "total_steps": total_steps,
                    "correlation_id": self.correlation_id
                }

        except Exception as e:
            logger.error(f"❌ Krytyczny błąd w flow: {e}")
            return {"success": False, "error": str(e), "step": "critical"}

        finally:
            # Cleanup
            if "test_file" in locals():
                try:
                    test_file.unlink()
                    logger.info(f"🧹 Usunięto plik testowy: {test_file}")
                except Exception as e:
                    logger.warning(f"⚠️ Nie udało się usunąć pliku testowego: {e}")


async def test_api_endpoints():
    """Test dostępności endpointów API"""
    logger.info("🔍 TEST DOSTĘPNOŚCI ENDPOINTÓW API")

    base_url = "http://localhost:8000"

    async with aiohttp.ClientSession() as session:
        endpoints = [
            "/docs",
            "/api/v2/receipts/",
            "/health"
        ]

        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                async with session.get(url) as response:
                    if response.status == 200:
                        logger.info(f"✅ {endpoint}: DOSTĘPNY")
                    else:
                        logger.warning(f"⚠️ {endpoint}: HTTP {response.status}")
            except Exception as e:
                logger.error(f"❌ {endpoint}: BŁĄD - {e}")


async def main():
    """Główna funkcja testowa"""
    logger.info("🚀 ROZPOCZYNAM KOMPLEKSOWY TEST FLOW PRZETWARZANIA PARAGONÓW")

    # Test 1: Sprawdź dostępność API
    await test_api_endpoints()

    # Test 2: Kompletny flow
    async with CompleteReceiptFlowTester() as tester:
        result = await tester.run_complete_flow()

        logger.info("\n" + "="*60)
        logger.info("🎯 KOŃCOWY WYNIK TESTU")
        logger.info("="*60)

        if result["success"]:
            logger.info("🎉 WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
            logger.info(f"Trip ID: {result.get('trip_id')}")
            logger.info(f"Task ID: {result.get('task_id')}")
            logger.info(f"Correlation ID: {result.get('correlation_id')}")
        else:
            logger.error("❌ TESTY ZAKOŃCZONE Z BŁĘDAMI")
            logger.error(f"Błąd: {result.get('error')}")
            logger.error(f"Krok: {result.get('step')}")

        return result["success"]


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
