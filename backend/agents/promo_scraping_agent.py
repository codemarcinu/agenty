"""
PromoScrapingAgent - Agent do monitoringu promocji w sklepach
Integruje się z sidecar scraperem i AI agentem
"""

from datetime import datetime, timedelta
import json
import logging
from typing import Any

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from core.hybrid_llm_client import hybrid_llm_client

logger = logging.getLogger(__name__)


class PromoScrapingAgent(BaseAgent):
    """Agent do monitoringu promocji w polskich sklepach"""

    def __init__(self):
        super().__init__()
        self.agent_name = "PromoScrapingAgent"
        self.description = "Monitoruje promocje w sklepach spożywczych"

        # Konfiguracja sklepów
        self.supported_stores = {
            "lidl": {
                "name": "Lidl",
                "url": "https://www.lidl.pl/pl/promocje",
                "enabled": True,
            },
            "biedronka": {
                "name": "Biedronka",
                "url": "https://www.biedronka.pl/pl/promocje",
                "enabled": True,
            },
        }

        # Cache dla wyników
        self.cache_duration = timedelta(hours=6)  # 6 godzin
        self.last_scrape = {}
        self.scraped_data = {}

    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """
        Przetwarza żądanie monitoringu promocji

        Args:
            request: Słownik z parametrami żądania

        Returns:
            AgentResponse z wynikami
        """
        try:
            # Analizuj intencję użytkownika
            intent = await self._detect_intent(input_data)

            if intent == "scrape_promotions":
                return await self._scrape_promotions(input_data)
            if intent == "analyze_promotions":
                return await self._analyze_promotions(input_data)
            if intent == "compare_stores":
                return await self._compare_stores(input_data)
            if intent == "get_best_deals":
                return await self._get_best_deals(input_data)
            return await self._general_promo_info(input_data)

        except Exception as e:
            logger.error(f"Błąd w PromoScrapingAgent: {e}")
            return AgentResponse(
                success=False,
                data={},
                message=f"Wystąpił błąd podczas monitoringu promocji: {e!s}",
            )

    async def _detect_intent(self, request: dict[str, Any]) -> str:
        """Wykrywa intencję użytkownika"""
        user_input = request.get("user_input", "").lower()

        if any(
            word in user_input for word in ["sprawdź", "skanuj", "scrape", "pobierz"]
        ):
            return "scrape_promotions"
        if any(word in user_input for word in ["analizuj", "przeanalizuj", "podsumuj"]):
            return "analyze_promotions"
        if any(word in user_input for word in ["porównaj", "sklepy", "który lepszy"]):
            return "compare_stores"
        if any(word in user_input for word in ["najlepsze", "okazje", "rabaty"]):
            return "get_best_deals"
        return "general_promo_info"

    async def _scrape_promotions(self, request: dict[str, Any]) -> AgentResponse:
        """Uruchamia scraping promocji"""
        try:
            # Sprawdź czy mamy świeże dane
            if await self._has_fresh_data():
                logger.info("Używam danych z cache")
                return AgentResponse(
                    success=True,
                    data=self.scraped_data,
                    message="Dane promocji (z cache)",
                )

            # Uruchom scraping przez sidecar
            scraped_data = await self._run_scraper_sidecar()

            if scraped_data:
                # Analizuj dane przez AI sidecar
                analysis = await self._run_ai_analysis(scraped_data)

                # Połącz wyniki
                result = {
                    "raw_data": scraped_data,
                    "analysis": analysis,
                    "scraped_at": datetime.now().isoformat(),
                    "stores_checked": list(self.supported_stores.keys()),
                }

                # Zapisz do cache
                self.scraped_data = result
                self.last_scrape = {
                    store: datetime.now() for store in self.supported_stores
                }

                return AgentResponse(
                    success=True,
                    data=result,
                    message=f"Pobrano promocje z {len(scraped_data.get('results', []))} sklepów",
                )
            return AgentResponse(
                success=False, data={}, message="Nie udało się pobrać promocji"
            )

        except Exception as e:
            logger.error(f"Błąd podczas scrapowania: {e}")
            return AgentResponse(
                success=False,
                data={},
                message=f"Błąd podczas pobierania promocji: {e!s}",
            )

    async def _run_scraper_sidecar(self) -> dict[str, Any] | None:
        """Uruchamia sidecar scraper"""
        try:
            # W trybie Tauri - wywołaj sidecar
            if hasattr(self, "_tauri_invoke"):
                # Symulacja wywołania sidecar w Tauri
                command = await self._tauri_invoke(
                    "run_scraper_sidecar",
                    {"stores": list(self.supported_stores.keys())},
                )
                return json.loads(command.stdout) if command.success else None
            # PRODUCTION: No mock data fallback
            logger.warning("No scraper sidecar available - using real data only")
            return None

        except Exception as e:
            logger.error(f"Błąd sidecar scraper: {e}")
            return None

    async def _run_ai_analysis(self, scraped_data: dict[str, Any]) -> dict[str, Any]:
        """Uruchamia AI analysis sidecar"""
        try:
            # W trybie Tauri - wywołaj AI sidecar
            if hasattr(self, "_tauri_invoke"):
                command = await self._tauri_invoke(
                    "run_ai_analysis_sidecar", {"data": scraped_data}
                )
                return json.loads(command.stdout) if command.success else {}
            # Fallback - analiza przez Bielik
            return await self._analyze_with_bielik(scraped_data)

        except Exception as e:
            logger.error(f"Błąd AI analysis: {e}")
            return {}

    async def _analyze_with_bielik(
        self, scraped_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Analizuje dane używając Bielik"""
        try:
            # Przygotuj prompt dla Bielik
            prompt = self._create_analysis_prompt(scraped_data)

            response = await hybrid_llm_client.chat(
                model="SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0",
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś ekspertem od analizy promocji w sklepach spożywczych. Analizuj dane i generuj przydatne insights.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
                max_tokens=1000,
            )

            if response and "message" in response:
                content = response["message"]["content"]
                # Próbuj sparsować JSON z odpowiedzi
                try:
                    return json.loads(content)
                except:
                    # Fallback - zwróć tekst
                    return {"analysis": content, "method": "bielik_fallback"}

            return {}

        except Exception as e:
            logger.error(f"Błąd analizy Bielik: {e}")
            return {}

    def _create_analysis_prompt(self, scraped_data: dict[str, Any]) -> str:
        """Tworzy prompt dla analizy"""
        results = scraped_data.get("results", [])

        prompt = "Przeanalizuj następujące promocje ze sklepów:\n\n"

        for result in results:
            if result.get("success") and result.get("promotions"):
                prompt += f"Sklep: {result['store']}\n"
                for promo in result["promotions"][:5]:  # Pierwsze 5 promocji
                    prompt += f"- {promo.get('title', 'N/A')}: {promo.get('discount', 'N/A')}\n"
                prompt += "\n"

        prompt += """
        Przeanalizuj te dane i zwróć JSON z:
        1. Podsumowaniem (liczba promocji, średni rabat)
        2. Najlepszymi ofertami
        3. Porównaniem sklepów
        4. Rekomendacjami dla użytkownika

        Odpowiedz tylko w formacie JSON.
        """

        return prompt

    # PRODUCTION: Mock data simulation removed
    # async def _simulate_scraped_data(self) -> dict[str, Any]:
    #     """Symuluje dane z scrapera dla testów"""
    #     # Method removed for production - no mock data
    #     pass

    async def _has_fresh_data(self) -> bool:
        """Sprawdza czy ma świeże dane w cache"""
        if not self.scraped_data:
            return False

        # Sprawdź czy cache nie wygasł
        for last_time in self.last_scrape.values():
            if datetime.now() - last_time > self.cache_duration:
                return False

        return True

    async def _analyze_promotions(self, request: dict[str, Any]) -> AgentResponse:
        """Analizuje istniejące promocje"""
        if not self.scraped_data:
            return await self._scrape_promotions(request)

        analysis = self.scraped_data.get("analysis", {})

        return AgentResponse(success=True, data=analysis, message="Analiza promocji")

    async def _compare_stores(self, request: dict[str, Any]) -> AgentResponse:
        """Porównuje sklepy"""
        if not self.scraped_data:
            return await self._scrape_promotions(request)

        store_comparison = self.scraped_data.get("analysis", {}).get(
            "store_comparison", {}
        )

        return AgentResponse(
            success=True,
            data={"store_comparison": store_comparison},
            message="Porównanie sklepów",
        )

    async def _get_best_deals(self, request: dict[str, Any]) -> AgentResponse:
        """Zwraca najlepsze oferty"""
        if not self.scraped_data:
            return await self._scrape_promotions(request)

        best_deals = self.scraped_data.get("analysis", {}).get("best_deals", [])

        return AgentResponse(
            success=True, data={"best_deals": best_deals}, message="Najlepsze oferty"
        )

    async def _general_promo_info(self, request: dict[str, Any]) -> AgentResponse:
        """Informacje ogólne o promocjach"""
        return AgentResponse(
            success=True,
            data={
                "supported_stores": list(self.supported_stores.keys()),
                "last_update": self.last_scrape.get("lidl", "Nigdy"),
                "cache_duration_hours": self.cache_duration.total_seconds() / 3600,
            },
            message="Informacje o monitoringu promocji",
        )

    def get_capabilities(self) -> list[str]:
        """Zwraca możliwości agenta"""
        return [
            "monitoring_promotions",
            "store_comparison",
            "price_analysis",
            "best_deals_detection",
            "trend_analysis",
        ]
