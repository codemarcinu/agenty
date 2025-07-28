#!/usr/bin/env python3
"""
Docker-based Telegram long polling script
"""

import asyncio
import logging

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "7689926174:AAHIidXCkrH4swWEz0EW0md8A196HvFggP4"
API_URL = f"https://api.telegram.org/bot{TOKEN}"
BACKEND_URL = "http://foodsave-backend:8000"

class DockerTelegramPoller:
    def __init__(self):
        self.offset = 0
        self.running = False

    async def get_updates(self):
        """Get updates from Telegram API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_URL}/getUpdates",
                    params={
                        "offset": self.offset,
                        "limit": 100,
                        "timeout": 30
                    },
                    timeout=35.0
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return data.get("result", [])

                logger.error(f"Failed to get updates: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []

    async def process_updates(self, updates):
        """Process updates through Docker backend"""
        for update in updates:
            try:
                self.offset = update["update_id"] + 1

                logger.info(f"Processing update {update['update_id']}")

                # Send to Docker backend webhook endpoint
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{BACKEND_URL}/api/v2/telegram/webhook",
                        json=update,
                        headers={
                            "Content-Type": "application/json",
                            "X-Telegram-Bot-Api-Secret-Token": "fixed_secret_token_for_telegram_webhook"
                        },
                        timeout=30.0
                    )

                    if response.status_code == 200:
                        logger.info("Update processed successfully")
                    else:
                        logger.error(f"Backend error: {response.status_code} - {response.text}")

            except Exception as e:
                logger.error(f"Error processing update {update.get('update_id', 'unknown')}: {e}")

    async def start_polling(self):
        """Start polling loop"""
        logger.info("🤖 Starting Docker Telegram bot polling...")
        self.running = True

        while self.running:
            try:
                updates = await self.get_updates()

                if updates:
                    logger.info(f"Received {len(updates)} updates")
                    await self.process_updates(updates)
                else:
                    await asyncio.sleep(1)

            except KeyboardInterrupt:
                logger.info("Stopping polling...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)

async def main():
    """Main function"""
    logger.info("🚀 Starting Docker Telegram Bot Poller")

    poller = DockerTelegramPoller()

    try:
        await poller.start_polling()
    except KeyboardInterrupt:
        logger.info("Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
