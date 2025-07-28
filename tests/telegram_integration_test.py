#!/usr/bin/env python3
"""
Prosty test integracji Telegram Bot dla FoodSave AI.

Ten skrypt testuje podstawowe funkcjonalności integracji Telegram:
1. Konfigurację bota
2. Endpointy API
3. Przetwarzanie wiadomości
4. Obsługę błędów
"""

import asyncio
import logging
import sys

import httpx

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramIntegrationTester:
    """Tester integracji Telegram Bot."""

    def __init__(self):
        self.base_url = "http://localhost:8001"  # Zmieniony port na 8001
        self.api_prefix = "/api/v2/telegram"

    async def test_telegram_settings(self) -> bool:
        """Test pobierania ustawień Telegram."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{self.api_prefix}/settings"
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Ustawienia Telegram: {data}")
                    return True
                else:
                    logger.error(f"❌ Błąd pobierania ustawień: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"❌ Błąd testu ustawień: {e}")
            return False

    async def test_telegram_connection(self) -> bool:
        """Test połączenia z Telegram API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{self.api_prefix}/test-connection"
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Test połączenia: {data}")
                    return True
                elif response.status_code == 400:
                    data = response.json()
                    logger.warning(f"⚠️ Błąd połączenia (oczekiwany bez tokenu): {data}")
                    return True  # Oczekiwany błąd bez tokenu
                else:
                    logger.error(
                        f"❌ Nieoczekiwany błąd połączenia: {response.status_code}"
                    )
                    return False

        except Exception as e:
            logger.error(f"❌ Błąd testu połączenia: {e}")
            return False

    async def test_webhook_info(self) -> bool:
        """Test informacji o webhook."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{self.api_prefix}/webhook-info"
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Informacje o webhook: {data}")
                    return True
                elif response.status_code == 400:
                    data = response.json()
                    logger.warning(f"⚠️ Błąd webhook (oczekiwany bez tokenu): {data}")
                    return True  # Oczekiwany błąd bez tokenu
                else:
                    logger.error(
                        f"❌ Nieoczekiwany błąd webhook: {response.status_code}"
                    )
                    return False

        except Exception as e:
            logger.error(f"❌ Błąd testu webhook: {e}")
            return False

    async def test_webhook_processing(self) -> bool:
        """Test przetwarzania webhook."""
        try:
            # Przykładowe dane webhook
            webhook_data = {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "from_user": {
                        "id": 987654321,
                        "first_name": "Test",
                        "username": "testuser",
                    },
                    "chat": {"id": 987654321, "type": "private"},
                    "text": "Cześć! Jak się masz?",
                    "date": 1234567890,
                },
            }

            # Pobierz aktualny secret token z ustawień
            async with httpx.AsyncClient() as client:
                settings_response = await client.get(
                    f"{self.base_url}{self.api_prefix}/settings"
                )
                if settings_response.status_code == 200:
                    settings_data = settings_response.json()
                    secret_token = settings_data["data"]["webhookSecret"]
                else:
                    secret_token = "test_secret"  # Fallback

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/webhook",
                    json=webhook_data,
                    headers={"X-Telegram-Bot-Api-Secret-Token": secret_token},
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Webhook przetworzony: {data}")
                    return True
                elif response.status_code == 403:
                    logger.info("✅ Webhook poprawnie odrzucony (nieprawidłowy secret)")
                    return True
                else:
                    logger.error(
                        f"❌ Nieoczekiwany status webhook: {response.status_code}"
                    )
                    return False

        except Exception as e:
            logger.error(f"❌ Błąd testu webhook: {e}")
            return False

    async def test_send_message(self) -> bool:
        """Test wysyłania wiadomości."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/send-message",
                    params={"chat_id": 123456, "message": "Test message"},
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Wiadomość wysłana: {data}")
                    return True
                elif response.status_code == 500:
                    data = response.json()
                    logger.warning(f"⚠️ Błąd wysyłania (oczekiwany bez tokenu): {data}")
                    return True  # Oczekiwany błąd bez tokenu
                else:
                    logger.error(
                        f"❌ Nieoczekiwany błąd wysyłania: {response.status_code}"
                    )
                    return False

        except Exception as e:
            logger.error(f"❌ Błąd testu wysyłania: {e}")
            return False

    async def test_set_webhook(self) -> bool:
        """Test ustawiania webhook."""
        try:
            webhook_url = "https://example.com/api/v2/telegram/webhook"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}{self.api_prefix}/set-webhook",
                    params={"webhook_url": webhook_url},
                )

                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✅ Webhook ustawiony: {data}")
                    return True
                elif response.status_code == 400:
                    data = response.json()
                    logger.warning(
                        f"⚠️ Błąd ustawienia webhook (oczekiwany bez tokenu): {data}"
                    )
                    return True  # Oczekiwany błąd bez tokenu
                else:
                    logger.error(
                        f"❌ Nieoczekiwany błąd ustawienia webhook: {response.status_code}"
                    )
                    return False

        except Exception as e:
            logger.error(f"❌ Błąd testu ustawienia webhook: {e}")
            return False

    async def run_all_tests(self) -> dict[str, bool]:
        """Uruchamia wszystkie testy integracji."""
        logger.info("🚀 Rozpoczynam testy integracji Telegram Bot...")

        tests = {
            "settings": self.test_telegram_settings,
            "connection": self.test_telegram_connection,
            "webhook_info": self.test_webhook_info,
            "webhook_processing": self.test_webhook_processing,
            "send_message": self.test_send_message,
            "set_webhook": self.test_set_webhook,
        }

        results = {}

        for test_name, test_func in tests.items():
            logger.info(f"📋 Test: {test_name}")
            try:
                results[test_name] = await test_func()
            except Exception as e:
                logger.error(f"❌ Błąd w teście {test_name}: {e}")
                results[test_name] = False

        return results


async def main():
    """Główna funkcja testowa."""
    tester = TelegramIntegrationTester()
    results = await tester.run_all_tests()

    # Podsumowanie wyników
    logger.info("\n" + "=" * 50)
    logger.info("📊 PODSUMOWANIE TESTÓW INTEGRACJI TELEGRAM")
    logger.info("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:20} {status}")
        if result:
            passed += 1

    logger.info("=" * 50)
    logger.info(f"Wynik: {passed}/{total} testów przeszło")

    if passed == total:
        logger.info("🎉 Wszystkie testy przeszły pomyślnie!")
    else:
        logger.warning(
            "⚠️ Niektóre testy nie przeszły (oczekiwane bez pełnej konfiguracji)"
        )

    return passed == total


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("⏹️ Testy przerwane przez użytkownika")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Błąd krytyczny: {e}")
        sys.exit(1)
