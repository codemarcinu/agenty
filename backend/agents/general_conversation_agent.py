"""
General Conversation Agent

Agent obsługujący swobodne konwersacje na dowolny temat z wykorzystaniem:
- RAG (Retrieval-Augmented Generation) dla wiedzy z dokumentów
- Wyszukiwania internetowego (DuckDuckGo, Perplexity) dla aktualnych informacji
- Bielika jako głównego modelu językowego
"""

import asyncio
from collections.abc import AsyncGenerator
import logging
import re
import time
from typing import Any

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from agents.tools import get_current_date
from core.anti_hallucination_decorator import (
    AntiHallucinationConfig,
    with_anti_hallucination,
)
from core.anti_hallucination_system import ValidationLevel
from core.cache_manager import cached_async, internet_cache, rag_cache
from core.decorators import handle_exceptions
from core.hybrid_llm_client import ModelComplexity, hybrid_llm_client
from core.performance_monitor import performance_monitor

# Lazy loading dla ciężkich importów
_rag_processor = None
_rag_integration = None
_vector_store = None
_web_search = None
_mmlw_client = None

def _get_rag_processor():
    global _rag_processor
    if _rag_processor is None:
        from core.rag_document_processor import RAGDocumentProcessor
        _rag_processor = RAGDocumentProcessor()
    return _rag_processor

def _get_rag_integration():
    global _rag_integration
    if _rag_integration is None:
        from core.rag_integration import RAGDatabaseIntegration
        _rag_integration = RAGDatabaseIntegration(_get_rag_processor())
    return _rag_integration

def _get_vector_store():
    global _vector_store
    if _vector_store is None:
        from core.vector_store import vector_store
        _vector_store = vector_store
    return _vector_store

def _get_web_search():
    global _web_search
    if _web_search is None:
        from integrations.web_search import web_search
        _web_search = web_search
    return _web_search

def _get_mmlw_client():
    global _mmlw_client
    if _mmlw_client is None:
        from core.mmlw_embedding_client import mmlw_client
        _mmlw_client = mmlw_client
    return _mmlw_client

logger = logging.getLogger(__name__)


class GeneralConversationAgent(BaseAgent):
    """Agent do obsługi swobodnych konwersacji
    z wykorzystaniem RAG i wyszukiwania internetowego."""

    def __init__(
        self,
        name: str = "GeneralConversationAgent",
        timeout=None,
        plugins=None,
        initial_state=None,
        **kwargs,
    ) -> None:
        super().__init__(name, **kwargs)
        self.timeout = timeout
        self.plugins = plugins or []
        self.initial_state = initial_state or {}
        self.rag_processor = _get_rag_processor()
        self.rag_integration = _get_rag_integration()
        self.description = "Agent do obsługi swobodnych konwersacji z wykorzystaniem RAG i wyszukiwania internetowego"

    @with_anti_hallucination(
        AntiHallucinationConfig(
            validation_level=ValidationLevel.MODERATE, log_validation=True
        )
    )
    @handle_exceptions(max_retries=2)
    async def process(
        self, input_data: dict[str, Any], db: AsyncSession | None = None
    ) -> AgentResponse:
        """Process user query with RAG and internet search in parallel"""
        start_time = time.time()
        
        try:
            query = self._extract_query_from_input(input_data)
            session_id = input_data.get("session_id", "")
            use_perplexity = input_data.get("use_perplexity", False)
            use_bielik = input_data.get("use_bielik", True)

            if not query:
                duration = time.time() - start_time
                performance_monitor.record_operation("chat_response", duration, {"error": "no_query"})
                return AgentResponse(
                    success=False,
                    error="No query provided in input_data",
                    data={"available_fields": list(input_data.keys())},
                    text="",
                )

            # 🚀 EARLY EXIT: Sprawdź czy to proste zapytanie
            if self._is_simple_query(query):
                logger.info(f"Early exit for simple query: {query}")
                performance_monitor.record_early_exit()
                simple_response = self._generate_simple_response(query)
                duration = time.time() - start_time
                performance_monitor.record_operation("chat_response", duration, {"early_exit": True})
                return AgentResponse(
                    success=True,
                    text=simple_response,
                    data={
                        "query": query,
                        "used_rag": False,
                        "used_internet": False,
                        "early_exit": True,
                        "session_id": session_id,
                    },
                    request_id=input_data.get("request_id"),
                )

            # Check if this is a pantry query and use pantry tools
            logger.info(
                f"[GeneralConversationAgent] Checking pantry detection for query: {query}"
            )
            pantry_detected = self._should_use_pantry_tools(query)
            logger.info(
                f"[GeneralConversationAgent] Pantry detection result: {pantry_detected}"
            )
            if pantry_detected and db is not None:
                logger.info(
                    f"[GeneralConversationAgent] Detected pantry query: {query}"
                )
                pantry_result = await self._execute_pantry_tools(query, db)
                if pantry_result:
                    duration = time.time() - start_time
                    performance_monitor.record_operation("chat_response", duration, {"pantry_tools": True})
                    return AgentResponse(
                        success=True,
                        text=pantry_result,
                        data={
                            "query": query,
                            "used_pantry_tools": True,
                            "used_rag": False,
                            "used_internet": False,
                            "rag_confidence": 0.0,
                            "use_perplexity": use_perplexity,
                            "use_bielik": use_bielik,
                            "session_id": session_id,
                        },
                    )

            # Continue with normal processing
            logger.info(
                f"[GeneralConversationAgent] Processing query: {query}... "
                f"use_perplexity={use_perplexity}, use_bielik={use_bielik}"
            )

            # Sprawdź czy to pytanie o datę/czas - natychmiastowa odpowiedź
            if self._is_date_query(query):
                logger.info(f"Detected date query: {query}")
                date_response = get_current_date()
                return AgentResponse(
                    success=True,
                    text=date_response,
                    data={
                        "query": query,
                        "used_rag": False,
                        "used_internet": False,
                        "rag_confidence": 0.0,
                        "use_perplexity": use_perplexity,
                        "use_bielik": use_bielik,
                        "session_id": session_id,
                        "is_date_query": True,
                    },
                )

            # Debug prints
            logger.debug(f"Input data: {input_data}")
            logger.debug(
                "Starting GeneralConversationAgent.process with parallel processing"
            )

            # Uruchom równolegle pobieranie kontekstu z RAG i internetu
            rag_task = asyncio.create_task(self._get_rag_context(query))
            internet_task = asyncio.create_task(
                self._get_internet_context(query, use_perplexity)
            )

            # Czekaj na zakończenie obu zadań
            rag_result, internet_context = await asyncio.gather(rag_task, internet_task)
            rag_context, rag_confidence = rag_result

            logger.info(f"RAG context confidence: {rag_confidence}")
            logger.info(f"Internet search completed: {bool(internet_context)}")

            # Wygeneruj odpowiedź z wykorzystaniem wszystkich źródeł
            logger.debug("Generating response with combined context")
            response = await self._generate_response(
                query, rag_context, internet_context, use_perplexity, use_bielik
            )
            logger.info(
                f"[GeneralConversationAgent] Generated response before post-processing: '{response[:100]}...'"
            )

            # Check if response contains LLM fallback message and provide better response
            llm_fallback_message = (
                "I'm sorry, but I'm currently unable to process your request. "
                "Please try again later."
            )
            if response and llm_fallback_message in response:
                logger.info(
                    "Detected LLM fallback message, providing graceful response"
                )
                response = "Przepraszam, obecnie mam trudności z przetworzeniem Twojego zapytania. Spróbuj zadać je w inny sposób."

            # If no response could be generated, provide meaningful fallback
            if not response or not response.strip():
                logger.warning(f"Empty response generated for query: {query}")
                if self._is_weather_query(query):
                    response = (
                        "Nie mogę obecnie sprawdzić pogody. Spróbuj ponownie za chwilę."
                    )
                elif self._is_greeting(query):
                    response = "Cześć! Jak mogę Ci pomóc?"
                else:
                    response = "Przepraszam, nie jestem w stanie odpowiedzieć na to pytanie w tym momencie. Możesz spróbować zadać je ponownie?"

            # --- POST-PROCESSING ANTI-HALLUCINATION FILTER ---
            # Zaawansowany filtr z fuzzy matching i detekcją wzorców halucynacji
            def contains_name_fuzzy(query_text: str, response_text: str) -> bool:
                """Sprawdza czy odpowiedź zawiera imię/nazwisko z query.
                Fuzzy match.
                Zwraca True, jeśli znaleziono dopasowanie.
                UWAGA: Zablokowane dla pytań o własne imię użytkownika.
                """
                
                # Sprawdź czy to pytanie o własne imię
                own_name_patterns = [
                    r"jak mam na imię",
                    r"jak się nazywam",
                    r"jakie jest moje imię",
                    r"mam na imię",
                    r"nazywam się"
                ]
                
                for pattern in own_name_patterns:
                    if re.search(pattern, query_text.lower()):
                        return False  # Nie blokuj odpowiedzi dla pytań o własne imię
                # Wyciągnij potencjalne imiona/nazwiska z query
                name_pattern = (
                    r"\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\b"
                )
                names_in_query = re.findall(name_pattern, query_text)

                # Lista typowych polskich imion do sprawdzenia
                polish_names = [
                    "jan",
                    "janusz",
                    "piotr",
                    "andrzej",
                    "tomasz",
                    "marek",
                    "michał",
                    "krzysztof",
                    "wojciech",
                    "anna",
                    "maria",
                    "katarzyna",
                    "małgorzata",
                    "agnieszka",
                    "barbara",
                    "ewa",
                    "elżbieta",
                    "joanna",
                    "kamil",
                    "mateusz",
                    "dawid",
                    "jakub",
                    "szymon",
                    "filip",
                    "mikołaj",
                    "bartosz",
                    "adrian",
                    "natalia",
                    "aleksandra",
                    "karolina",
                    "paulina",
                    "monika",
                    "sylwia",
                    "iwona",
                    "dorota",
                    "renata",
                ]

                for name in names_in_query:
                    # Sprawdź czy imię lub nazwisko występuje w odpowiedzi
                    first_name, last_name = name.split()
                    if (
                        first_name.lower() in response_text.lower()
                        or last_name.lower() in response_text.lower()
                    ):
                        return True

                # Sprawdź czy odpowiedź zawiera jakiekolwiek polskie imię
                # (ale tylko jeśli nie jest to odpowiedź na pytanie o własne imię)
                response_lower = response_text.lower()
                for polish_name in polish_names:
                    if polish_name in response_lower and re.search(
                        r"\b" + polish_name + r"\b", response_lower
                    ):
                        # Dodatkowe sprawdzenie - czy to nie odpowiedź typu "Nazywasz się Marcin"
                        context_patterns = [
                            "nazywasz się", "masz na imię", "twoje imię to",
                            "jesteś", "to ty"
                        ]
                        if any(pattern in response_lower for pattern in context_patterns):
                            return False  # Nie blokuj jeśli to odpowiedź o użytkowniku
                        return True

                return False

            def is_product_query(query_text: str) -> bool:
                """Sprawdza czy query dotyczy produktu.
                Zwraca True, jeśli zapytanie dotyczy produktu.
                """
                product_keywords = [
                    "telefon",
                    "smartfon",
                    "laptop",
                    "komputer",
                    "tablet",
                    "kamera",
                    "słuchawki",
                    "specyfikacja",
                    "specyfikacje",
                    "parametry",
                    "cechy",
                    "funkcje",
                    "wyposażenie",
                    "samsung",
                    "iphone",
                    "xiaomi",
                    "huawei",
                    "lenovo",
                    "dell",
                    "hp",
                    "asus",
                ]
                query_lower = query_text.lower()
                return any(keyword in query_lower for keyword in product_keywords)

            def is_person_query(query_text: str) -> bool:
                """Sprawdza czy query dotyczy osoby - ulepszona logika kontekstowa"""
                query_lower = query_text.lower()

                # Wykluczenia - pytania które na pewno NIE dotyczą osób
                exclusion_patterns = [
                    r"cena\s+\w+",  # "cena bitcoina", "cena akcji"
                    r"aktualna\s+cena",
                    r"ile\s+kosztuje",
                    r"wartość\s+\w+",
                    r"kurs\s+\w+",
                    r"notowania",
                    r"giełda",
                    r"bitcoin",
                    r"ethereum",
                    r"kryptowalut",
                    r"pogoda",
                    r"temperatura",
                    r"przepis\s+na",
                    r"jak\s+zrobić",
                    r"składniki",
                    r"technologia",
                    r"komputer",
                    r"smartfon",
                ]

                for pattern in exclusion_patterns:
                    if re.search(pattern, query_lower):
                        return False

                # Silne wskaźniki osoby - tylko te jednoznaczne
                strong_person_indicators = [
                    "kto",
                    "kim",
                    "biografia",
                    "życiorys",
                    "urodził się",
                    "urodziła się",
                    "zmarł",
                    "zmarła",
                ]

                for indicator in strong_person_indicators:
                    if indicator in query_lower:
                        return True

                # Słabsze wskaźniki - wymagają dodatkowego kontekstu
                weak_person_indicators = [
                    "naukowiec",
                    "profesor",
                    "doktor",
                    "inżynier",
                    "lekarz",
                    "artysta",
                    "polski",
                    "polska",
                    "polak",
                    "polka",
                ]

                # Sprawdź czy są imiona/nazwiska w zapytaniu
                has_name_pattern = bool(
                    re.search(
                        r"\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\b",
                        query_text,
                    )
                )

                # Słabe wskaźniki liczymy tylko jeśli jest też wzorzec imienia
                if has_name_pattern:
                    for indicator in weak_person_indicators:
                        if indicator in query_lower:
                            return True

                return False

            def contains_hallucination_patterns(response_text: str) -> bool:
                """Sprawdza czy odpowiedź zawiera typowe wzorce halucynacji
                (czyli czy odpowiedź zawiera typowe wzorce halucynacji)"""
                hallucination_patterns = [
                    # Wzorce dla osób
                    r"był\s+wybitnym",
                    r"urodził\s+się",
                    r"zmarł\s+w",
                    r"jego\s+najważniejsze\s+osiągnięcia",
                    r"był\s+polskim\s+[a-ząćęłńóśźż]+",
                    r"studia\s+na\s+uniwersytecie",
                    r"profesor\s+uniwersytetu",
                    r"członek\s+akademii",
                    r"prace\s+naukowe",
                    r"wynalazca",
                    r"chemik",
                    r"fizyk",
                    r"matematyk",
                    # Wzorce dla produktów
                    r"specyfikacja",
                    r"ekran\s+o\s+przekątnej",
                    r"procesor",
                    r"bateria\s+ma\s+pojemność",
                    r"posiada\s+procesor",
                    r"wyposażony\s+jest\s+w",
                    r"ram\s+\d+\s+gb",
                    r"pamięć\s+wewnętrzna",
                    r"rozdzielczość",
                    r"pojemność\s+baterii",
                    # KRYTYCZNE: Wzorce dla przepisów (halucynacje)
                    r"\d+\.\s*[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż\s]+[w]?\s+[a-ząćęłńóśźż\s]+[przez]\s+\d+\s+minut",
                    r"ugotuj\s+[a-ząćęłńóśźż\s]+\s+w\s+[a-ząćęłńóśźż\s]+wodzie",
                    r"dodaj\s+[a-ząćęłńóśźż\s]+\s+do\s+[a-ząćęłńóśźż\s]+patelni",
                    r"pokrój\s+[a-ząćęłńóśźż\s]+\s+w\s+[a-ząćęłńóśźż\s]+kostkę",
                    r"posyp\s+[a-ząćęłńóśźż\s]+\s+[a-ząćęłńóśźż\s]+parmezanem",
                    r"przepis:",
                    r"kroki:",
                    r"instrukcja:",
                    # KRYTYCZNE: Wzorce dla wydarzeń (halucynacje)
                    r"obchodzony\s+jest\s+[a-ząćęłńóśźż\s]+dzień",
                    r"upamiętnia\s+[a-ząćęłńóśźż\s]+wydarzenie",
                    r"główne\s+obchody\s+odbywają\s+się",
                    r"uroczystości\s+państwowych",
                    r"manifestacji\s+patriotycznych",
                    r"w\s+[a-ząćęłńóśźż\s]+na\s+placu",
                    r"z\s+udziałem\s+władz",
                    # Wzorce dla szczegółowych informacji bez źródeł
                    r"\d{4}\s+roku",
                    r"w\s+\d{4}\s+roku",
                    r"od\s+\d{4}\s+do\s+\d{4}",
                    r"w\s+latach\s+\d{4}-\d{4}",
                ]

                for pattern in hallucination_patterns:
                    if re.search(pattern, response_text, re.IGNORECASE):
                        return True
                return False

            def is_known_person(query_text: str) -> bool:
                """Sprawdza czy query dotyczy znanej, zweryfikowanej osoby
                (czyli czy zapytanie dotyczy znanej osoby)"""
                known_persons = [
                    # Politycy i osoby publiczne
                    "andrzej duda",
                    "prezydent polski",
                    "prezydent polski",
                    "donald tusk",
                    "mateusz morawiecki",
                    "władysław kosiniak-kamysz",
                    "szymon hołownia",
                    "krzysztof bosak",
                    "robert biedroń",
                    # Znane postacie historyczne
                    "józef piłsudski",
                    "lech wałęsa",
                    "jan paweł ii",
                    "mikołaj kopernik",
                    "maria skłodowska",
                    "fryderyk chopin",
                    "adam mickiewicz",
                    "juliusz słowacki",
                    "henryk sienkiewicz",
                    # Aktualne osoby publiczne
                    "robert lewandowski",
                    "iga świątek",
                    "andrzej wajda",
                    "roman polański",
                    # Dodatkowe warianty
                    "prezydent",
                    "prezydenta",
                    "prezydentem",
                    "prezydentowi",
                ]
                query_lower = query_text.lower()

                # Sprawdź czy query zawiera słowo "prezydent" + "polski/polska"
                if "prezydent" in query_lower and (
                    "polski" in query_lower or "polska" in query_lower
                ):
                    return True

                return any(person in query_lower for person in known_persons)

            def is_future_event(query_text: str) -> bool:
                """Sprawdza czy query dotyczy wydarzenia z przyszłości
                (czyli czy zapytanie dotyczy przyszłych wydarzeń)"""
                future_patterns = [
                    r"\b202[5-9]\b",  # Lata 2025-2029
                    r"\b20[3-9][0-9]\b",  # Lata 2030-2099
                    r"\bprzyszłości\b",
                    r"\bprzyszłym\b",
                    r"\bprzyszła\b",
                    r"\bzaplanowane\b",
                    r"\bodbędzie\b",
                    r"\bodbędą\b",
                ]
                query_lower = query_text.lower()
                return any(
                    re.search(pattern, query_lower) for pattern in future_patterns
                )

            def is_recipe_query(query_text: str) -> bool:
                """Sprawdza czy query dotyczy przepisu"""
                recipe_patterns = [
                    r"przepis",
                    r"przygotuj",
                    r"ugotuj",
                    r"upiecz",
                    r"zrób",
                    r"danie",
                    r"obiad",
                    r"śniadanie",
                    r"kolacja",
                    r"posiłek",
                    r"jedzenie",
                    r"kuchnia",
                    r"gotowanie",
                ]
                query_lower = query_text.lower()
                return any(
                    re.search(pattern, query_lower) for pattern in recipe_patterns
                )

            def is_event_query(query_text: str) -> bool:
                """Sprawdza czy query dotyczy wydarzenia"""
                event_patterns = [
                    r"wydarzenie",
                    r"obchody",
                    r"uroczystość",
                    r"święto",
                    r"dzień",
                    r"festiwal",
                    r"koncert",
                    r"wystawa",
                    r"konferencja",
                    r"spotkanie",
                    r"ceremonia",
                    r"parada",
                ]
                query_lower = query_text.lower()
                return any(
                    re.search(pattern, query_lower) for pattern in event_patterns
                )

            def _validate_response_against_context(
                response: str, context: str
            ) -> dict[str, Any]:
                """Waliduje odpowiedź przeciwko dostępnemu kontekstowi"""
                if not context:
                    return {"is_valid": False, "reason": "Brak kontekstu"}

                # Sprawdź czy odpowiedź zawiera szczegółowe informacje bez potwierdzenia w kontekście
                response_lower = response.lower()
                context_lower = context.lower()

                # Sprawdź czy odpowiedź zawiera przepis bez składników w kontekście
                if any(
                    word in response_lower
                    for word in ["przepis", "ugotuj", "dodaj", "pokrój"]
                ) and not any(
                    word in context_lower
                    for word in [
                        "składnik",
                        "produkt",
                        "makaron",
                        "kurczak",
                        "pomidor",
                    ]
                ):
                    return {
                        "is_valid": False,
                        "reason": "Przepis bez dostępnych składników",
                    }

                # Sprawdź czy odpowiedź zawiera wydarzenie bez daty w kontekście
                if any(
                    word in response_lower
                    for word in ["obchodzony", "upamiętnia", "główne obchody"]
                ) and not any(
                    word in context_lower
                    for word in ["data", "dzisiaj", "jutro", "wczoraj"]
                ):
                    return {
                        "is_valid": False,
                        "reason": "Wydarzenie bez potwierdzonej daty",
                    }

                # Sprawdź czy odpowiedź zawiera szczegółowe kroki bez instrukcji w kontekście
                if re.search(r"\d+\.\s*[A-ZĄĆĘŁŃÓŚŹŻ]", response):
                    if not any(
                        word in context_lower
                        for word in ["instrukcja", "krok", "sposób", "metoda"]
                    ):
                        return {
                            "is_valid": False,
                            "reason": "Szczegółowe kroki bez instrukcji w kontekście",
                        }

                return {"is_valid": True, "reason": "Odpowiedź potwierdzona kontekstem"}

            # Sprawdź czy odpowiedź zawiera halucynacje
            # rag_context to tuple (str, float), więc bierzemy tylko tekst
            rag_text = (
                rag_context[0]
                if isinstance(rag_context, tuple)
                else (rag_context or "")
            )
            context_text = rag_text + (internet_context or "")
            
            # Sprawdź czy to pytanie o osobę publiczną - jeśli tak, nie blokuj wyszukiwania
            public_figure_patterns = [
                r"karol nawrocki",
                r"wybory prezydenckie", 
                r"prezydent.*pol",
                r"kandydat.*prezydent",
                r"andrzej duda",
                r"donald tusk"
            ]
            
            is_public_figure_query = any(
                re.search(pattern, query.lower()) for pattern in public_figure_patterns
            )

            # 1. Sprawdź fuzzy matching dla nazwisk
            fuzzy_match = contains_name_fuzzy(query, response)
            logger.info(
                f"[GeneralConversationAgent] Fuzzy name check: query='{query}', response='{response[:50]}...', fuzzy_match={fuzzy_match}"
            )
            
            # Dla osób publicznych - zawsze użyj wyszukiwania internetowego
            if fuzzy_match and is_public_figure_query:
                logger.info(f"Post-processing: Wykryte pytanie o osobę publiczną: {query}")
                # Użyj search agent dla osób publicznych
                search_agent_result = await self._use_search_agent_for_query(
                    query, use_perplexity, use_bielik, session_id
                )
                if search_agent_result:
                    return search_agent_result
                    
            elif fuzzy_match:
                if is_known_person(query):
                    logger.info("Post-processing: Pomijam znaną osobę: " f"{query}")
                elif not any(
                    name in context_text
                    for name in re.findall(
                        r"\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\b",
                        query,
                    )
                ):
                    # Sprawdź czy zapytanie wymaga aktualnych danych przed zwróceniem odpowiedzi o osobie
                    current_data_indicators = [
                        "aktualna cena",
                        "najnowsza wiadomość",
                        "dzisiaj",
                        "obecnie",
                        "najnowsze informacje",
                        "aktualne dane",
                        "obecna sytuacja",
                        "ostatnie wiadomości",
                        "co się dzieje",
                        "najświeższe",
                    ]

                    query_lower = query.lower()
                    should_search_current = any(
                        indicator in query_lower
                        for indicator in current_data_indicators
                    )

                    if should_search_current:
                        logger.info(
                            f"[GeneralConversationAgent] Wykryto fuzzy name ale zapytanie o aktualną informację, przełączam na SearchAgent: {query}"
                        )
                        try:
                            from agents.search_agent import SearchAgent

                            search_agent = SearchAgent()
                            search_input = {"query": query, "max_results": 3}
                            search_response = await search_agent.process(search_input)
                            if search_response and search_response.text:
                                return AgentResponse(
                                    success=True,
                                    text=f"[Wynik wyszukiwania internetowego]\n{search_response.text}",
                                    data={
                                        "query": query,
                                        "used_rag": bool(rag_context),
                                        "used_internet": True,
                                        "used_search_agent": True,
                                        "rag_confidence": 0.0,
                                        "use_perplexity": use_perplexity,
                                        "use_bielik": use_bielik,
                                        "session_id": session_id,
                                        "anti_hallucination": True,
                                        "trigger": "fuzzy_name_with_current_data",
                                    },
                                )
                        except Exception as e:
                            logger.error(
                                f"[GeneralConversationAgent] Błąd podczas wywołania SearchAgent w fuzzy name handler: {e}"
                            )

                    logger.info(
                        "Post-processing: Wykryto halucynację nazwiska w query: "
                        f"{query}"
                    )
                    return AgentResponse(
                        success=True,
                        text="Nie mam informacji o tej osobie.",
                        data={
                            "query": query,
                            "used_rag": bool(rag_context),
                            "used_internet": False,
                            "used_search_agent": False,
                            "rag_confidence": 0.0,
                            "use_perplexity": use_perplexity,
                            "use_bielik": use_bielik,
                            "session_id": session_id,
                            "anti_hallucination": True,
                            "trigger": "fuzzy_name_match",
                        },
                    )

            # 2. Sprawdź wzorce halucynacji w odpowiedzi - NAPRAWIONA LOGIKA
            hallucination_patterns_match = contains_hallucination_patterns(response)
            logger.info(
                f"[GeneralConversationAgent] Hallucination patterns check: query='{query}', response='{response[:50]}...', patterns_match={hallucination_patterns_match}"
            )
            if hallucination_patterns_match:
                # Sprawdź czy kontekst zawiera informacje potwierdzające odpowiedź
                context_validation = _validate_response_against_context(
                    response, context_text
                )

                if not context_validation["is_valid"]:
                    logger.info(
                        f"Post-processing: Wykryto wzorce halucynacji w odpowiedzi. Brak potwierdzenia w kontekście: {context_validation['reason']}"
                    )

                    # Sprawdź czy powinniśmy przełączyć na SearchAgent zamiast zwracać ogólną odpowiedź
                    should_search = False

                    # Sprawdź czy zapytanie wymaga aktualnych danych
                    current_data_indicators = [
                        "aktualna cena",
                        "najnowsza wiadomość",
                        "dzisiaj",
                        "obecnie",
                        "najnowsze informacje",
                        "aktualne dane",
                        "obecna sytuacja",
                        "ostatnie wiadomości",
                        "co się dzieje",
                        "najświeższe",
                    ]

                    query_lower = query.lower()
                    for indicator in current_data_indicators:
                        if indicator in query_lower:
                            should_search = True
                            break

                    # Sprawdź czy to nie jest typowe zapytanie o osobę (bez danych aktualnych)
                    # Ale jeśli już wykryliśmy potrzebę wyszukiwania aktualnych danych, nie blokuj
                    if is_person_query(query) and not should_search:
                        should_search = False

                    logger.info(
                        f"[GeneralConversationAgent] Analiza zapytania: should_search={should_search}, is_person_query={is_person_query(query)}, query='{query}'"
                    )

                    if should_search:
                        logger.info(
                            "[GeneralConversationAgent] Halucynacja wykryta, ale zapytanie wymaga aktualnych danych - przełączam na SearchAgent"
                        )
                        try:
                            from agents.search_agent import SearchAgent

                            search_agent = SearchAgent()
                            search_input = {"query": query, "max_results": 3}
                            search_response = await search_agent.process(search_input)
                            if search_response and search_response.text:
                                return AgentResponse(
                                    success=True,
                                    text=f"[Wynik wyszukiwania internetowego]\n{search_response.text}",
                                    data={
                                        "query": query,
                                        "used_rag": bool(rag_context),
                                        "used_internet": True,
                                        "used_search_agent": True,
                                        "rag_confidence": 0.0,
                                        "use_perplexity": use_perplexity,
                                        "use_bielik": use_bielik,
                                        "session_id": session_id,
                                        "anti_hallucination": True,
                                        "trigger": "hallucination_patterns_with_search",
                                    },
                                )
                        except Exception as e:
                            logger.error(
                                f"[GeneralConversationAgent] Błąd podczas wywołania SearchAgent w hallucination handler: {e}"
                            )

                    # Wybierz odpowiedni komunikat w zależności od typu query
                    if is_recipe_query(query):
                        safe_message = "Nie mam dostępnych składników do tego przepisu. Sprawdź swoją spiżarnię."
                    elif is_product_query(query):
                        safe_message = "Nie mam informacji o tym produkcie."
                    elif is_person_query(query) and not is_known_person(query):
                        safe_message = "Nie mam informacji o tej osobie."
                    elif is_event_query(query):
                        safe_message = "Nie mam aktualnych informacji o tym wydarzeniu."
                    elif is_future_event(query):
                        safe_message = (
                            "Nie mam informacji o tym wydarzeniu z przyszłości."
                        )
                    else:
                        safe_message = (
                            "Nie mam zweryfikowanych informacji na ten temat."
                        )

                return AgentResponse(
                    success=True,
                    text=safe_message,
                    data={
                        "query": query,
                        "used_rag": bool(rag_context),
                        "used_internet": False,  # Nie używamy SearchAgent w tym miejscu
                        "used_search_agent": False,
                        "rag_confidence": 0.0,
                        "use_perplexity": use_perplexity,
                        "use_bielik": use_bielik,
                        "session_id": session_id,
                        "anti_hallucination": True,
                        "trigger": "hallucination_patterns",
                    },
                )

            # --- POST-PROCESSING ANTI-HALLUCINATION FILTER ---
            # Zaawansowany filtr z fuzzy matching i detekcją wzorców halucynacji
            def _should_switch_to_search(
                query: str, rag_context: str, response: str, rag_confidence: float
            ) -> bool:
                # Jeśli nie ma kontekstu RAG i nie ma odpowiedzi lub odpowiedź jest pusta/niepewna
                if not rag_context or rag_confidence < 0.3:
                    return True
                if not response or not response.strip():
                    return True

                # Typowe frazy braku wiedzy
                lower_resp = response.lower()
                knowledge_lack_phrases = [
                    "nie wiem",
                    "nie jestem pewien",
                    "nie posiadam informacji",
                    "nie mogę odpowiedzieć",
                    "nie znalazłem",
                    "nie znalazłam",
                    "nie jestem w stanie",
                    "nie mam wystarczających danych",
                    "nie potrafię odpowiedzieć",
                    "nie mam wiedzy",
                    "nie mam informacji",
                    "nie mogę znaleźć",
                    "nie mogę udzielić odpowiedzi",
                    "nie mam dostępu do aktualnych",
                    "nie mam informacji o tej osobie",
                    "nie mam aktualnych informacji",
                    "nie posiadam najnowszych danych",
                ]

                for phrase in knowledge_lack_phrases:
                    if phrase in lower_resp:
                        return True

                # Detekcja pytań wymagających aktualnych danych
                current_data_indicators = [
                    "aktualna cena",
                    "najnowsza wiadomość",
                    "dzisiaj",
                    "obecnie",
                    "najnowsze informacje",
                    "aktualne dane",
                    "obecna sytuacja",
                    "ostatnie wiadomości",
                    "co się dzieje",
                    "najświeższe",
                ]

                query_lower = query.lower()
                for indicator in current_data_indicators:
                    if indicator in query_lower:
                        return True

                # Detekcja ogólnych/wymijających odpowiedzi (krótsze niż 100 znaków lub bardzo ogólne)
                if len(response.strip()) < 100:
                    return True

                # Detekcja specyficznych wymijających odpowiedzi
                evasive_patterns = [
                    "nie mam informacji o tej osobie",
                    "test response for",
                    "nie mam dostępu do",
                    "niestety nie mam",
                ]

                return any(pattern in lower_resp for pattern in evasive_patterns)

            # Sprawdź czy powinniśmy przełączyć na SearchAgent
            used_search_agent = False
            if _should_switch_to_search(query, rag_context, response, rag_confidence):
                logger.info(
                    "[GeneralConversationAgent] Brak pewnej odpowiedzi lokalnej, przełączam na SearchAgent/web_search"
                )
                try:
                    # Wywołaj SearchAgent
                    from agents.search_agent import SearchAgent

                    search_agent = SearchAgent()
                    search_input = {"query": query, "max_results": 3}
                    search_response = await search_agent.process(search_input)
                    if search_response and search_response.text:
                        response = f"[Wynik wyszukiwania internetowego]\n{search_response.text}"
                        used_search_agent = True
                        logger.info(
                            "[GeneralConversationAgent] SearchAgent zwrócił odpowiedź"
                        )
                    else:
                        response = "Nie udało się znaleźć odpowiedzi w internecie."
                        logger.warning(
                            "[GeneralConversationAgent] SearchAgent nie zwrócił odpowiedzi"
                        )
                except Exception as e:
                    logger.error(
                        f"[GeneralConversationAgent] Błąd podczas wywołania SearchAgent: {e}"
                    )
                    response = "Wystąpił błąd podczas wyszukiwania w internecie."

            logger.debug("GeneralConversationAgent.process completed successfully")
            return AgentResponse(
                success=True,
                text=response,
                data={
                    "query": query,
                    "used_rag": bool(rag_context),
                    "used_internet": used_search_agent or bool(internet_context),
                    "used_search_agent": used_search_agent,
                    "rag_confidence": rag_confidence,
                    "use_perplexity": use_perplexity,
                    "use_bielik": use_bielik,
                    "session_id": session_id,
                },
            )

        except Exception as e:
            logger.error(f"Error in GeneralConversationAgent: {e!s}", exc_info=True)

            # Extract query for proper error response
            query = self._extract_query_from_input(input_data)

            # Provide graceful error handling based on error type
            if "ollama" in str(e).lower() or "connection" in str(e).lower():
                error_response = "Przepraszam, obecnie mam problemy z połączeniem do systemu AI. Spróbuj ponownie za chwilę."
            elif "timeout" in str(e).lower():
                error_response = "Operacja przekroczyła dozwolony czas. Spróbuj zadać prostsze pytanie."
            elif "rate" in str(e).lower() or "limit" in str(e).lower():
                error_response = "Przekroczono limit zapytań. Poczekaj chwilę przed kolejnym zapytaniem."
            else:
                error_response = "Przepraszam, wystąpił nieoczekiwany błąd podczas przetwarzania Twojego zapytania."

            return AgentResponse(
                success=False,
                text=error_response,
                error=str(e),
                data={
                    "query": query,
                    "used_rag": False,
                    "used_internet": False,
                    "used_search_agent": False,
                    "rag_confidence": 0.0,
                    "use_perplexity": input_data.get("use_perplexity", False),
                    "use_bielik": input_data.get("use_bielik", True),
                    "session_id": input_data.get("session_id", ""),
                    "error_type": type(e).__name__,
                },
            )

    def _extract_query_from_input(self, input_data: dict[str, Any]) -> str:
        """Defensively extract query from possible fields in input_data."""
        possible_fields = ["query", "task", "user_command", "command", "text"]
        for field in possible_fields:
            value = input_data.get(field)
            if value and isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    @cached_async(rag_cache)
    async def _get_rag_context(self, query: str) -> tuple[str, float]:
        """Pobiera kontekst z RAG i ocenia jego pewność."""
        rag_start_time = time.time()
        
        try:
            # 1. Stwórz wektor dla zapytania
            query_embedding_list = await _get_mmlw_client().embed_text(query)
            if not query_embedding_list:
                logger.warning("Failed to generate query embedding for RAG context.")
                duration = time.time() - rag_start_time
                performance_monitor.record_operation("rag_search", duration, {"error": "embedding_failed"})
                return "", 0.0
            query_embedding = np.array([query_embedding_list], dtype=np.float32)

            # 2. Przeszukaj bazę wektorową (bez min_similarity)
            # Zwiększamy k, aby mieć więcej kandydatów do filtrowania
            if _get_vector_store() is not None:
                search_results = await _get_vector_store().search(query_embedding, k=5)
            else:
                logger.warning("vector_store is not available")
                duration = time.time() - rag_start_time
                performance_monitor.record_operation("rag_search", duration, {"error": "vector_store_unavailable"})
                return "", 0.0

            if not search_results:
                duration = time.time() - rag_start_time
                performance_monitor.record_operation("rag_search", duration, {"no_results": True})
                return "", 0.0

            # 3. Ręcznie odfiltruj wyniki poniżej progu podobieństwa
            min_similarity_threshold = 0.7
            filtered_results = [
                (doc, sim)
                for doc, sim in search_results
                if sim >= min_similarity_threshold
            ]

            if not filtered_results:
                duration = time.time() - rag_start_time
                performance_monitor.record_operation("rag_search", duration, {"no_filtered_results": True})
                return "", 0.0

            # 4. Przetwórz i sformatuj odfiltrowane wyniki
            avg_confidence = sum(sim for _, sim in filtered_results) / len(
                filtered_results
            )

            context_parts = []
            if filtered_results:
                doc_texts = [
                    f"- {doc.content} (Źródło: {doc.metadata.get('filename', 'Brak nazwy')})"
                    for doc, sim in filtered_results
                    if doc.content
                ]
                if doc_texts:
                    context_parts.append("Dokumenty:\n" + "\n".join(doc_texts[:2]))

            duration = time.time() - rag_start_time
            performance_monitor.record_operation("rag_search", duration, {"confidence": avg_confidence, "results_count": len(filtered_results)})
            
            return "\n\n".join(context_parts) if context_parts else "", avg_confidence

        except Exception as e:
            duration = time.time() - rag_start_time
            performance_monitor.record_operation("rag_search", duration, {"error": str(e)})
            logger.warning(f"Error getting RAG context: {e!s}")
            return "", 0.0

    @cached_async(internet_cache)
    async def _get_internet_context(self, query: str, use_perplexity: bool) -> str:
        """Pobiera informacje z internetu z weryfikacją wiedzy"""
        internet_start_time = time.time()
        
        try:
            # Perplexity API removed - using web_search fallback
            if _get_web_search() is not None:
                search_results = await _get_web_search().search(query, max_results=3)
                if search_results:
                    duration = time.time() - internet_start_time
                    performance_monitor.record_operation("internet_search", duration, {"results_count": len(search_results)})
                    return "Informacje z internetu:\n" + "\n".join(
                        [
                            f"**{result.get('title', 'Brak tytułu')}**\n{result.get('snippet', 'Brak opisu')}\nŹródło: {result.get('url', 'Brak URL')}"
                            for result in search_results[:2]
                        ]
                    )
            else:
                logger.warning("web_search is not available")
                duration = time.time() - internet_start_time
                performance_monitor.record_operation("internet_search", duration, {"error": "web_search_unavailable"})
            return ""

        except Exception as e:
            duration = time.time() - internet_start_time
            performance_monitor.record_operation("internet_search", duration, {"error": str(e)})
            logger.warning(f"Error getting internet context: {e!s}")
            return ""

    async def _generate_response(
        self,
        query: str,
        rag_context: str,
        internet_context: str,
        use_perplexity: bool,
        use_bielik: bool,
    ) -> str:
        """Generuje odpowiedź z wykorzystaniem wszystkich źródeł.
        Informacji i weryfikacji wiedzy.
        """

        # Określ złożoność zapytania z ulepszoną analizą
        complexity = self._determine_query_complexity_enhanced(
            query, rag_context, internet_context
        )

        # System prompt zoptymalizowany dla modelu Bielik z polskim kontekstem kulturowym
        system_prompt = self._build_bielik_optimized_prompt(complexity, rag_context, internet_context)

        # Buduj kontekst
        context_parts = []
        if rag_context:
            context_parts.append(f"KONTEKST Z DOKUMENTÓW I BAZY DANYCH:\n{rag_context}")
        if internet_context:
            context_parts.append(f"INFORMACJE Z INTERNETU:\n{internet_context}")

        context_text = "\n\n".join(context_parts) if context_parts else ""

        # Buduj wiadomości
        messages = [{"role": "system", "content": system_prompt}]

        if context_text:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        f"DOSTĘPNE INFORMACJE:\n{context_text}\n\nKRYTYCZNE: Użyj TYLKO tych "
                        "informacji do udzielenia dokładnej odpowiedzi. NIGDY nie wymyślaj "
                        "dodatkowych faktów, szczegółów ani informacji. Jeśli informacji brakuje, "
                        "przyznaj to zamiast wymyślać. Uwzględnij informacje o weryfikacji wiedzy "
                        "jeśli są dostępne."
                    ),
                }
            )

        messages.append({"role": "user", "content": query})

        # Generuj odpowiedź używając odpowiedniego modelu
        try:
            logger.info(f"Enhanced complexity determination: {complexity}")
            logger.info(f"Enhanced complexity determination: {complexity}")

            # Wybierz optymalny model Bielik
            model_name = self._select_model(complexity, use_bielik)
            logger.info(f"Selected optimized Bielik model: {model_name}")

            # Wykryj intencję użytkownika dla lepszego dostosowania
            user_intent = self._detect_user_intent_bielik(query)
            logger.info(f"Detected user intent: {user_intent}")
            
            # Pobierz styl odpowiedzi na podstawie intencji
            response_style = self._get_bielik_response_style(user_intent, complexity)
            
            # Optymalizuj parametry dla wybranego modelu Bielik
            bielik_params = self._get_bielik_parameters(complexity, model_name)
            
            # Dostosuj parametry na podstawie stylu odpowiedzi
            if response_style:
                bielik_params.update({
                    "max_tokens": response_style.get("max_tokens", bielik_params["max_tokens"]),
                    "temperature": response_style.get("temperature", bielik_params["temperature"])
                })
            
            logger.info(f"Using optimized Bielik parameters: {bielik_params}")

            # Zastosuj tryb konwersacyjny (domyślnie przyjazny)
            messages = await self._apply_conversation_mode(messages, "friendly")
            
            # Dodaj informację o stylu odpowiedzi do system message
            if messages and messages[0]["role"] == "system" and response_style:
                messages[0]["content"] += f"\n\nSTYL ODPOWIEDZI: {response_style['approach']}"

            response = await hybrid_llm_client.chat(
                messages=messages,
                model=model_name,
                force_complexity=complexity,
                stream=False,
                **bielik_params  # Dodaj zoptymalizowane parametry
            )

            # Sprawdź czy response jest słownikiem (nie AsyncGenerator)
            if (
                isinstance(response, dict)
                and "message" in response
                and "content" in response["message"]
            ):
                response_text = response["message"]["content"]

                # Sprawdź czy odpowiedź wskazuje na brak wiedzy
                if self._indicates_lack_of_knowledge(response_text):
                    logger.info(
                        f"Response indicates lack of knowledge, switching to search mode for query: {query}"
                    )
                    return await self._switch_to_search_mode(
                        query, use_perplexity, use_bielik
                    )

                return response_text
            return "Przepraszam, nie udało się wygenerować odpowiedzi."

        except Exception as e:
            logger.error(f"Error generating response: {e!s}")

            # Jeśli to błąd LLM, spróbuj z fallback modelem
            if "LLM error" in str(e) or "timeout" in str(e).lower():
                logger.info("Attempting fallback to stable model")
                try:
                    # Użyj stabilnego modelu Bielik 4.5B jako fallback
                    fallback_response = await hybrid_llm_client.chat(
                        messages=messages,
                        model="SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0",
                        force_complexity=ModelComplexity.SIMPLE,
                        stream=False,
                    )

                    # Sprawdź czy fallback_response jest słownikiem
                    if (
                        isinstance(fallback_response, dict)
                        and "message" in fallback_response
                        and "content" in fallback_response["message"]
                    ):
                        logger.info("Fallback model response successful")
                        response_text = fallback_response["message"]["content"]

                        # Sprawdź czy odpowiedź wskazuje na brak wiedzy
                        if self._indicates_lack_of_knowledge(response_text):
                            logger.info(
                                f"Fallback response indicates lack of knowledge, switching to search mode for query: {query}"
                            )
                            return await self._switch_to_search_mode(
                                query, use_perplexity, use_bielik
                            )

                        return response_text
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error!s}")

            # Ostateczny fallback - przełącz na tryb wyszukiwania
            logger.info(
                f"All models failed, switching to search mode for query: {query}"
            )
            return await self._switch_to_search_mode(query, use_perplexity, use_bielik)

    def _indicates_lack_of_knowledge(self, response_text: str) -> bool:
        """
        Sprawdza czy odpowiedź wskazuje na brak wiedzy i powinna przełączyć na tryb wyszukiwania.

        Args:
            response_text: Tekst odpowiedzi do sprawdzenia

        Returns:
            bool: True jeśli odpowiedź wskazuje na brak wiedzy
        """
        response_lower = response_text.lower()

        # Wzorce wskazujące na brak wiedzy
        lack_of_knowledge_patterns = [
            "nie mam pewnych informacji",
            "nie mam informacji",
            "nie znam",
            "nie wiem",
            "nie mam danych",
            "nie mam wiedzy",
            "nie mogę odpowiedzieć",
            "nie potrafię odpowiedzieć",
            "nie mam dostępu do informacji",
            "nie mam odpowiedzi",
            "nie mam pewności",
            "nie jestem pewien",
            "nie jestem pewna",
            "nie mogę potwierdzić",
            "nie mam informacji o",
            "nie istnieje",
            "nie rozpoznaję",
            "nie znam takiej osoby",
            "nie znam takiego produktu",
            "nie mam danych na ten temat",
            "nie mam wiedzy na ten temat",
            "nie mogę udzielić informacji",
            "nie potrafię udzielić informacji",
            "nie mam dostępu do danych",
            "nie mam dostępu do wiedzy",
            "nie mogę znaleźć informacji",
            "nie potrafię znaleźć informacji",
            "nie mam odpowiednich informacji",
            "nie mam aktualnych informacji",
            "nie mam szczegółowych informacji",
            "nie mam pełnych informacji",
            "nie mam kompletnych informacji",
            "nie mam wystarczających informacji",
            "nie mam dokładnych informacji",
            "nie mam precyzyjnych informacji",
            "nie mam konkretnych informacji",
            "nie mam szczegółowych danych",
            "nie mam aktualnych danych",
            "nie mam odpowiednich danych",
            "nie mam kompletnych danych",
            "nie mam pełnych danych",
            "nie mam wystarczających danych",
            "nie mam dokładnych danych",
            "nie mam precyzyjnych danych",
            "nie mam konkretnych danych",
        ]

        # Sprawdź czy odpowiedź zawiera którykolwiek z wzorców
        for pattern in lack_of_knowledge_patterns:
            if pattern in response_lower:
                return True

        # Sprawdź czy odpowiedź jest bardzo krótka (może wskazywać na brak wiedzy)
        if len(response_text.strip()) < 50:
            # Sprawdź czy nie jest to prosty potwierdzenie lub zaprzeczenie
            simple_responses = [
                "tak",
                "nie",
                "ok",
                "dobrze",
                "rozumiem",
                "jasne",
                "zgoda",
            ]
            if response_lower.strip() not in simple_responses:
                return True

        return False

    async def _switch_to_search_mode(
        self, query: str, use_perplexity: bool, use_bielik: bool
    ) -> str:
        """
        Automatycznie przełącza na tryb wyszukiwania gdy model nie zna odpowiedzi.

        Args:
            query: Zapytanie użytkownika
            use_perplexity: Czy używać Perplexity
            use_bielik: Czy używać modelu Bielik

        Returns:
            str: Odpowiedź z trybu wyszukiwania
        """
        try:
            logger.info(f"Switching to search mode for query: {query}")

            # Utwórz SearchAgent
            from agents.search_agent import SearchAgent

            search_agent = SearchAgent()

            # Przygotuj dane wejściowe dla SearchAgent
            search_input = {
                "query": query,
                "model": (
                    "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M" if use_bielik else None
                ),
                "max_results": 5,
            }

            # Wykonaj wyszukiwanie
            search_response = await search_agent.process(search_input)

            if search_response.success and search_response.text:
                # Dodaj informację o przełączeniu na tryb wyszukiwania
                enhanced_response = (
                    f"🔍 **Przełączono na tryb wyszukiwania**\n\n"
                    f"{search_response.text}\n\n"
                    f"*Informacje zostały znalezione w internecie.*"
                )
                return enhanced_response
            else:
                # Jeśli wyszukiwanie nie powiodło się, zwróć informację
                return (
                    f"Przepraszam, nie udało mi się znaleźć odpowiednich informacji "
                    f"w internecie dla zapytania: '{query}'. "
                    f"Spróbuj sformułować zapytanie inaczej lub sprawdź pisownię."
                )

        except Exception as e:
            logger.error(f"Error switching to search mode: {e!s}")
            return (
                "Przepraszam, wystąpił problem podczas wyszukiwania informacji. "
                "Spróbuj ponownie za chwilę."
            )

    def _determine_query_complexity(
        self, query: str, rag_context: str, internet_context: str
    ) -> ModelComplexity:
        """
        Określa złożoność zapytania na podstawie jego treści i dostępnego kontekstu.

        Args:
            query: Zapytanie użytkownika
            rag_context: Kontekst z RAG (może być tuple (str, float) lub str)
            internet_context: Kontekst z internetu

        Returns:
            ModelComplexity: Poziom złożoności zapytania
        """
        query_lower = query.lower()

        # Jeśli zapytanie jest bardzo krótkie, to jest proste
        if len(query) < 10:
            return ModelComplexity.SIMPLE

        # Jeśli mamy dużo kontekstu, to zapytanie jest złożone
        # Obsługa przypadku gdy rag_context jest tuple (str, float)
        rag_text = rag_context[0] if isinstance(rag_context, tuple) else rag_context
        combined_context = (rag_text or "") + (internet_context or "")
        if len(combined_context) > 1000:
            return ModelComplexity.COMPLEX

        # Słowa kluczowe sugerujące złożone zapytanie
        complex_keywords = [
            "porównaj",
            "przeanalizuj",
            "wyjaśnij",
            "zinterpretuj",
            "oceń",
            "podsumuj",
            "zreferuj",
            "przedstaw argumenty",
            "uzasadnij",
            "zaprojektuj",
            "stwórz",
            "napisz",
            "wymyśl",
            "zaproponuj",
        ]

        if any(keyword in query_lower for keyword in complex_keywords):
            return ModelComplexity.COMPLEX

        # Domyślnie używamy standardowej złożoności
        return ModelComplexity.STANDARD

    def _select_model(self, complexity: ModelComplexity, use_bielik: bool) -> str:
        """
        Wybiera optymalny model Bielik na podstawie złożoności zapytania

        Args:
            complexity: Złożoność zapytania
            use_bielik: Czy używać modelu Bielik (zawsze True dla tego agenta)

        Returns:
            Nazwa modelu do użycia - zoptymalizowana wersja Bielika
        """
        # Adaptacyjny wybór modelu Bielik na podstawie złożoności
        if complexity == ModelComplexity.SIMPLE:
            # Dla prostych zapytań używaj najszybszego modelu
            return "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
        elif complexity == ModelComplexity.STANDARD:
            # Dla standardowych zapytań używaj zbalansowanego modelu
            return "SpeakLeash/bielik-7b-v2.1-instruct:Q5_K_M"
        else:  # COMPLEX
            # Dla złożonych zapytań używaj najpotężniejszego modelu
            return "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"

    async def process_stream(
        self, input_data: dict[str, Any]
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process general conversation input with streaming response"""
        try:
            query = input_data.get("query", "")
            context = input_data.get("context", [])
            use_perplexity = input_data.get("use_perplexity", False)
            use_bielik = input_data.get("use_bielik", True)

            # Determine if this is a simple query
            is_simple_query = self._is_simple_query(query)

            # For simple queries, use a smaller model
            if is_simple_query:
                force_complexity = ModelComplexity.SIMPLE
                logger.info(f"Using SIMPLE model for query: {query}")
            else:
                force_complexity = None
                logger.info(f"Using standard model selection for query: {query}")

            # Run RAG and internet search in parallel
            rag_task = asyncio.create_task(self._get_rag_results(query))
            internet_task = asyncio.create_task(self._get_internet_results(query))

            # First yield a message that we're gathering information
            yield {
                "text": "Zbieram informacje...",
                "data": {"status": "gathering_info"},
                "success": True,
            }

            # Wait for both tasks to complete
            rag_results, internet_results = await asyncio.gather(
                rag_task, internet_task
            )

            # Yield a message that we're processing the information
            yield {
                "text": "\nAnalizuję zebrane dane...",
                "data": {"status": "processing_info"},
                "success": True,
            }

            # Combine context from both sources
            combined_context = self._combine_context(rag_results, internet_results)

            # Format the context for the LLM
            formatted_context = self._format_context_for_llm(combined_context)

            # Prepare messages for the LLM
            messages = self._prepare_messages(query, context, formatted_context)

            # Generate streaming response using the LLM
            stream_response = await hybrid_llm_client.chat(
                messages=messages,
                stream=True,
                use_perplexity=use_perplexity,
                use_bielik=use_bielik,
                force_complexity=force_complexity,
            )

            # Clear the initial messages
            yield {
                "text": "",
                "data": {"status": "responding", "clear_previous": True},
                "success": True,
            }

            # Stream the response chunks
            full_text = ""
            async for chunk in stream_response:
                if (
                    isinstance(chunk, dict)
                    and "message" in chunk
                    and "content" in chunk["message"]
                ):
                    content = chunk["message"]["content"]
                    full_text += content
                    yield {
                        "text": content,
                        "data": {"status": "streaming"},
                        "success": True,
                    }

            # Final chunk with complete data
            yield {
                "text": "",  # No additional text
                "data": {
                    "status": "complete",
                    "context_used": combined_context[
                        :2
                    ],  # Include first 2 context items for transparency
                },
                "success": True,
            }

        except Exception as e:
            logger.error(f"Error in GeneralConversationAgent streaming: {e!s}")
            yield {
                "text": f"Przepraszam, wystąpił błąd: {e!s}",
                "data": {"status": "error"},
                "success": False,
            }

    def _is_simple_query(self, query: str) -> bool:
        """Determine if a query is simple based on length and complexity"""
        # Simple heuristic: short queries are likely simple
        if len(query) < 20:
            return True

        # Check for common simple phrases
        simple_phrases = [
            "dziękuję",
            "dzięki",
            "rozumiem",
            "ok",
            "dobrze",
            "tak",
            "nie",
            "może",
            "cześć",
            "hej",
            "witaj",
            "do widzenia",
            "pa",
            "żegnaj",
        ]

        query_lower = query.lower()
        return any(phrase in query_lower for phrase in simple_phrases)

    def _generate_simple_response(self, query: str) -> str:
        """Generate appropriate response for simple queries like greetings"""
        query_lower = query.lower().strip()

        # Greetings
        if any(
            greeting in query_lower
            for greeting in ["cześć", "hej", "witaj", "hi", "hello"]
        ):
            return "Cześć! Jak mogę Ci pomóc dzisiaj? 😊"

        # Thanks
        if any(
            thanks in query_lower
            for thanks in ["dziękuję", "dzięki", "thank you", "thanks"]
        ):
            return "Nie ma sprawy! 😊"

        # Agreement
        if any(agree in query_lower for agree in ["ok", "dobrze", "tak", "rozumiem"]):
            return "Świetnie! 😊"

        # Disagreement
        if any(disagree in query_lower for disagree in ["nie", "no"]):
            return "Rozumiem. Czy mogę pomóc w czymś innym?"

        # Uncertainty
        if any(uncertain in query_lower for uncertain in ["może", "maybe"]):
            return "Rozumiem Twoje wątpliwości. Daj znać, jeśli będziesz potrzebować pomocy!"

        # Goodbye
        if any(
            goodbye in query_lower
            for goodbye in ["do widzenia", "pa", "żegnaj", "bye", "goodbye"]
        ):
            return "Do widzenia! Miłego dnia! 👋"

        # Default for other short queries
        return "Rozumiem! Jak mogę Ci pomóc?"

    @cached_async(rag_cache)  # Cache RAG results for 1 hour
    async def _get_rag_results(self, query: str) -> list[dict[str, str]]:
        """Get results from RAG system with caching"""
        try:
            # Placeholder for actual RAG implementation
            # In a real system, this would query a vector database
            logger.info(f"Getting RAG results for: {query}")
            await asyncio.sleep(0.1)  # Simulate some processing time
            return []  # Return empty list as placeholder
        except Exception as e:
            logger.error(f"Error getting RAG results: {e!s}")
            return []

    @cached_async(internet_cache)  # Cache internet results for 30 minutes
    async def _get_internet_results(self, query: str) -> list[dict[str, str]]:
        """Get results from internet search with caching"""
        try:
            logger.info(f"Getting internet results for: {query}")
            # Użyj web_search jako obiektu, nie funkcji
            if _get_web_search() is not None:
                results = await _get_web_search().search(query, max_results=3)
                return results if results else []
            else:
                logger.warning("web_search is not available")
                return []
        except Exception as e:
            logger.error(f"Error getting internet results: {e!s}")
            return []

    def _combine_context(
        self, rag_results: list[dict[str, str]], internet_results: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """Combine context from RAG and internet search"""
        # Simple combination strategy: RAG results first, then internet
        combined = []

        # Add RAG results if available
        if rag_results:
            combined.extend(rag_results)

        # Add internet results if available
        if internet_results:
            combined.extend(internet_results)

        return combined

    def _format_context_for_llm(self, context: list[dict[str, str]]) -> str:
        """Format context for LLM input"""
        if not context:
            return ""

        formatted = "Oto informacje, które mogą być pomocne:\n\n"

        for i, item in enumerate(context, 1):
            title = item.get("title", f"Źródło {i}")
            content = item.get("content", "")
            url = item.get("url", "")

            formatted += f"--- {title} ---\n"
            formatted += f"{content}\n"
            if url:
                formatted += f"Źródło: {url}\n"
            formatted += "\n"

        return formatted

    def _prepare_messages(
        self, query: str, conversation_history: list[dict[str, str]], context: str
    ) -> list[dict[str, str]]:
        """Prepare messages for LLM with optimized context
        and conversation history."""
        messages = []

        # Zoptymalizowany system message dla modelu Bielik
        system_message = (
            "Jesteś inteligentnym polskim asystentem AI opartym na modelu Bielik. "
            "Specjalizujesz się w naturalnych konwersacjach w języku polskim. "
            "Odpowiadaj pomocnie, precyzyjnie i naturalnie. "
            "Dostosowuj długość odpowiedzi do potrzeb - od zwięzłych po szczegółowe wyjaśnienia. "
            "Wykorzystuj polską kulturę i kontekst lokalny w swoich odpowiedziach."
        )

        if context:
            system_message += "\n\nKontekst:\n" + context

        messages.append({"role": "system", "content": system_message})

        # Dodaj historię konwersacji (ostatnie 3 wiadomości)
        if conversation_history:
            recent_history = conversation_history[-3:]
            for msg in recent_history:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append(msg)

        # Dodaj aktualne zapytanie
        messages.append({"role": "user", "content": query})

        return messages

    def _is_date_query(self, query: str) -> bool:
        """Sprawdza czy zapytanie dotyczy daty/czasu"""
        query_lower = query.lower()

        # Wyklucz zapytania o pogodę
        weather_keywords = [
            "weather",
            "pogoda",
            "temperature",
            "temperatura",
            "rain",
            "deszcz",
            "snow",
            "śnieg",
        ]
        if any(keyword in query_lower for keyword in weather_keywords):
            return False

        # Wyklucz zapytania o inne tematy, które mogą zawierać słowa związane z czasem
        exclude_keywords = [
            "weather",
            "pogoda",
            "temperature",
            "temperatura",
            "forecast",
            "prognoza",
        ]
        if any(keyword in query_lower for keyword in exclude_keywords):
            return False

        # Specyficzne wzorce dla zapytań o datę
        date_patterns = [
            r"\b(jaki|which|what)\s+(dzisiaj|today|dzień|day)\b",
            r"\b(kiedy|when)\s+(jest|is)\b",
            r"\b(dzisiaj|today)\s+(jest|is)\b",
            r"\b(podaj|tell)\s+(mi|me|dzisiejszą|today's)?\s*(datę|date)\b",
            r"\b(jaki|what)\s+(to|is)\s+(dzień|day)\b",
            r"\b(dzień|day)\s+(tygodnia|of\s+week)\b",
            r"\b(data|date)\s+(dzisiaj|today)\b",
            r"\b(dzisiaj|today)\s+(data|date)\b",
            r"\b(jaki|what)\s+(mamy|do\s+we\s+have)\s+(dzisiaj|today)\b",
            r"\b(który|which)\s+(dzień|day)\s+(dzisiaj|today)\b",
            r"\b(podaj|tell)\s+(dzisiejszą|today's)\s+(datę|date)\b",
            r"\b(dzisiejsza|today's)\s+(data|date)\b",
        ]

        import re

        for pattern in date_patterns:
            if re.search(pattern, query_lower):
                return True

        # Dodatkowe słowa kluczowe tylko jeśli nie ma kontekstu pogodowego
        date_keywords = [
            "dzisiaj",
            "dziś",
            "today",
            "wczoraj",
            "yesterday",
            "jutro",
            "tomorrow",
            "dzień",
            "day",
            "miesiąc",
            "month",
            "rok",
            "year",
            "godzina",
            "hour",
            "czas",
            "time",
            "kiedy",
            "when",
            "który dzień",
            "what day",
            "jaki dzień",
            "which day",
            "jaki dzisiaj",
            "what today",
            "który to dzień",
            "what day is it",
            "jaki dzisiaj dzień",
            "what day is today",
            "poniedziałek",
            "monday",
            "wtorek",
            "tuesday",
            "środa",
            "wednesday",
            "czwartek",
            "thursday",
            "piątek",
            "friday",
            "sobota",
            "saturday",
            "niedziela",
            "sunday",
        ]

        # Sprawdź czy zapytanie zawiera głównie słowa związane z datą
        date_word_count = sum(1 for keyword in date_keywords if keyword in query_lower)
        total_words = len(query_lower.split())

        # Jeśli więcej niż 50% słów to słowa związane z datą,
        # to prawdopodobnie zapytanie o datę
        return bool(date_word_count > 0 and date_word_count / total_words > 0.3)

    def _is_pantry_query(self, query: str) -> bool:
        """Check if query is about pantry/inventory"""
        pantry_keywords = [
            "spiżarnia",
            "lodówka",
            "magazyn",
            "produkty",
            "jedzenie",
            "żywność",
            "co mam",
            "co jest",
            "sprawdź",
            "lista",
            "inwentarz",
            "zapasy",
            "składniki",
            "przepis",
            "gotowanie",
            "kuchnia",
            "jedzenie",
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in pantry_keywords)

    def _should_use_pantry_tools(self, query: str) -> bool:
        """Determine if pantry tools should be used"""
        return self._is_pantry_query(query)

    async def _execute_pantry_tools(self, query: str, db: AsyncSession) -> str:
        """Execute pantry-related tools"""
        try:
            from agents.tools.tools import get_pantry_summary

            # Get pantry summary
            summary = await get_pantry_summary(db)

            if "co mam" in query.lower() or "co jest" in query.lower():
                # User wants to know what's in pantry
                result = "W Twojej spiżarni masz:\n\n"
                result += f"• Łącznie produktów: {summary['total_items']}\n"
                result += f"• W magazynie: {summary['in_stock']}\n"
                result += f"• Niski stan: {summary['low_stock']}\n"
                result += f"• Brak: {summary['out_of_stock']}\n"

                if summary["expiring_soon"] > 0:
                    result += f"• Wkrótce przeterminowane: {summary['expiring_soon']}\n"

                if summary["categories"]:
                    result += "\nProdukty według kategorii:\n"
                    for category, items in summary["categories"].items():
                        result += f"• {category}: {len(items)} produktów\n"

                return result
            else:
                # General pantry info
                return f"Podsumowanie spiżarni: {summary['total_items']} produktów, {summary['in_stock']} w magazynie, {summary['low_stock']} z niskim stanem."

        except Exception as e:
            logger.error(f"Error executing pantry tools: {e}")
            return f"Przepraszam, nie udało się pobrać informacji o spiżarni: {e!s}"

    def _get_available_tools(self) -> list[str]:
        """Get list of available tools for the agent"""
        return [
            "search_web",
            "get_weather",
            "convert_units",
            "get_current_time",
            "calculate",
            "get_pantry_info",
            "check_pantry_for_ingredients",
        ]

    def _is_weather_query(self, query: str) -> bool:
        """Check if query is weather-related"""
        weather_keywords = {
            "pogoda",
            "weather",
            "temperatura",
            "temperature",
            "deszcz",
            "rain",
            "śnieg",
            "snow",
            "wiatr",
            "wind",
            "wilgotność",
            "humidity",
            "słońce",
            "sun",
            "chmury",
            "clouds",
            "burza",
            "storm",
            "mgła",
            "fog",
            "grad",
            "hail",
        }
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in weather_keywords)

    def _is_greeting(self, query: str) -> bool:
        """Check if query is a greeting"""
        greetings = {
            "cześć",
            "czesc",
            "hej",
            "witaj",
            "dzień dobry",
            "dzien dobry",
            "dobry wieczór",
            "dobry wieczor",
            "hello",
            "hi",
            "good morning",
            "good evening",
            "witam",
            "siema",
        }
        query_lower = query.lower().strip()
        return any(greeting in query_lower for greeting in greetings)

    def _build_bielik_optimized_prompt(
        self, complexity: ModelComplexity, rag_context: str, internet_context: str
    ) -> str:
        """
        Buduje zoptymalizowany system prompt dla modelu Bielik
        
        Args:
            complexity: Złożoność zapytania
            rag_context: Kontekst z RAG
            internet_context: Kontekst z internetu
            
        Returns:
            Zoptymalizowany system prompt dla Bielika
        """
        # Bazowy prompt dla modelu Bielik z polskim kontekstem
        base_prompt = (
            "Jesteś Bielik - zaawansowany polski asystent AI stworzony przez SpeakLeash. "
            "Specjalizujesz się w prowadzeniu naturalnych konwersacji w języku polskim, "
            "uwzględniając polski kontekst kulturowy, społeczny i językowy.\n\n"
        )
        
        # Dostosuj prompt do złożoności zapytania
        if complexity == ModelComplexity.SIMPLE:
            complexity_prompt = (
                "TRYB SZYBKIEJ ODPOWIEDZI:\n"
                "- Odpowiadaj zwięźle i na temat\n"
                "- Maksymalnie 1-2 zdania dla prostych pytań\n"
                "- Używaj naturalnego, przyjaznego tonu\n"
                "- Priorytetowo traktuj jasność przekazu\n\n"
            )
        elif complexity == ModelComplexity.STANDARD:
            complexity_prompt = (
                "TRYB STANDARDOWEJ KONWERSACJI:\n"
                "- Udzielaj pełnych, ale zwięzłych odpowiedzi\n"
                "- 2-4 zdania z wyjaśnieniami\n"
                "- Dodawaj przydatny kontekst gdy potrzebny\n"
                "- Zachowuj równowagę między szczegółowością a jasnością\n\n"
            )
        else:  # COMPLEX
            complexity_prompt = (
                "TRYB GŁĘBOKIEJ ANALIZY:\n"
                "- Udzielaj szczegółowych, wieloaspektowych odpowiedzi\n"
                "- Analizuj zagadnienia z różnych perspektyw\n"
                "- Używaj strukturyzowanego formatowania gdy pomocne\n"
                "- Dodawaj przykłady i kontekst kulturowy\n"
                "- Nie ograniczaj się długością - priorytetem jest kompletność\n\n"
            )
        
        # Instrukcje anty-halucynacyjne
        anti_hallucination = (
            "ZASADY WIARYGODNOŚCI:\n"
            "- NIGDY nie wymyślaj faktów, dat, nazwisk ani szczegółów\n"
            "- Jeśli nie znasz odpowiedzi, powiedz to wprost\n"
            "- Oznaczaj niepewne informacje jako 'prawdopodobnie' lub 'może'\n"
            "- Używaj tylko zweryfikowanych informacji z dostępnych źródeł\n"
            "- Dla nieznanych osób/produktów odpowiadaj: 'Nie mam informacji o...'\n\n"
        )
        
        # Instrukcje kontekstowe
        context_instructions = ""
        if rag_context or internet_context:
            context_instructions = (
                "WYKORZYSTANIE KONTEKSTU:\n"
                "- Priorytetowo używaj informacji z dostarczonych źródeł\n"
                "- Zawsze wskazuj źródło informacji gdy to możliwe\n"
                "- Łącz wiedzę z różnych źródeł w spójną całość\n"
                "- Oceniaj wiarygodność informacji przed użyciem\n\n"
            )
        
        # Specjalizacja polska
        polish_context = (
            "POLSKI KONTEKST:\n"
            "- Używaj polskiej terminologii i zwrotów\n"
            "- Uwzględniaj polskie realia kulturowe i społeczne\n"
            "- Rozpoznawaj polskie nazwiska, miejsca i instytucje\n"
            "- Zapamiętuj informacje o użytkowniku z konwersacji\n"
            "- Jeśli użytkownik przedstawi się imieniem, używaj go w dalszych odpowiedziach\n"
            "- Dostosowuj odpowiedzi do polskiego odbiorcy\n"
            "- Używaj polskich przykładów i analogii\n\n"
        )
        
        # Finalne instrukcje
        final_instructions = (
            "Odpowiadaj zawsze w języku polskim, chyba że użytkownik wyraźnie prosi o inny język. "
            "Bądź pomocny, dokładny i naturalny w komunikacji."
        )
        
        return (
            base_prompt + 
            complexity_prompt + 
            anti_hallucination + 
            context_instructions + 
            polish_context + 
            final_instructions
        )

    def _determine_query_complexity_enhanced(
        self, query: str, rag_context: str, internet_context: str
    ) -> ModelComplexity:
        """
        Ulepszona metoda określania złożoności zapytania dla modelu Bielik
        
        Args:
            query: Zapytanie użytkownika
            rag_context: Kontekst z RAG
            internet_context: Kontekst z internetu
            
        Returns:
            ModelComplexity: Poziom złożoności zapytania
        """
        query_lower = query.lower()
        query_length = len(query)
        word_count = len(query.split())
        
        # Bardzo proste zapytania (pozdrowienia, krótkie odpowiedzi)
        simple_patterns = [
            "cześć", "hej", "witaj", "dzień dobry", "tak", "nie", "ok", 
            "dziękuję", "dzięki", "do widzenia", "pa", "pomocy", "help"
        ]
        if any(pattern in query_lower for pattern in simple_patterns) and word_count <= 3:
            return ModelComplexity.SIMPLE
        
        # Bardzo krótkie zapytania
        if query_length < 15 or word_count <= 2:
            return ModelComplexity.SIMPLE
            
        # Zapytania o fakty, definicje - standardowe
        standard_keywords = [
            "co to", "kim jest", "gdzie", "kiedy", "ile", "jaki", "jaka", 
            "jakie", "czym", "dlaczego", "definicja", "znaczenie"
        ]
        if any(keyword in query_lower for keyword in standard_keywords) and word_count <= 10:
            return ModelComplexity.STANDARD
            
        # Złożone zapytania analityczne
        complex_keywords = [
            "porównaj", "przeanalizuj", "wyjaśnij szczegółowo", "oceń", 
            "przedstaw argumenty", "uzasadnij", "stwórz", "napisz",
            "zaprojektuj", "zaproponuj rozwiązanie", "strategia", 
            "plan działania", "analiza", "interpretacja"
        ]
        if any(keyword in query_lower for keyword in complex_keywords):
            return ModelComplexity.COMPLEX
            
        # Długie zapytania z wieloma pytaniami
        if query_length > 200 or word_count > 30:
            return ModelComplexity.COMPLEX
            
        # Zapytania z dużym kontekstem
        rag_text = rag_context[0] if isinstance(rag_context, tuple) else rag_context
        combined_context = (rag_text or "") + (internet_context or "")
        if len(combined_context) > 1500:
            return ModelComplexity.COMPLEX
            
        # Domyślnie standardowy poziom
        return ModelComplexity.STANDARD
    
    def _get_bielik_parameters(self, complexity: ModelComplexity, model_name: str) -> dict:
        """
        Zwraca zoptymalizowane parametry dla modelu Bielik
        
        Args:
            complexity: Złożoność zapytania
            model_name: Nazwa modelu Bielik
            
        Returns:
            Dict z parametrami dla modelu
        """
        base_params = {
            "temperature": 0.7,  # Balans między kreatywnością a precyzją
            "top_p": 0.9,
            "max_tokens": 2048,
            "stop": None,
        }
        
        # Dostosuj parametry do złożoności zapytania
        if complexity == ModelComplexity.SIMPLE:
            # Dla prostych zapytań - szybko i precyzyjnie
            base_params.update({
                "temperature": 0.3,  # Mniej kreatywności, więcej precyzji
                "top_p": 0.7,        # Bardziej konserwatywne wybory
                "max_tokens": 150,   # Krótsze odpowiedzi
            })
        elif complexity == ModelComplexity.COMPLEX:
            # Dla złożonych zapytań - więcej kreatywności i przestrzeni
            base_params.update({
                "temperature": 0.8,  # Więcej kreatywności
                "top_p": 0.95,       # Więcej różnorodności
                "max_tokens": 4096,  # Dłuższe odpowiedzi
            })
            
        # Specjalne dostosowania dla różnych wariantów Bielika
        if "4.5b" in model_name:
            # Mniejszy model - bardziej konserwatywne parametry
            base_params["temperature"] = min(base_params["temperature"], 0.6)
        elif "11b" in model_name:
            # Największy model - może pozwolić sobie na więcej kreatywności
            if complexity == ModelComplexity.COMPLEX:
                base_params["temperature"] = 0.9
                
        return base_params
    
    def _get_bielik_conversation_modes(self) -> dict[str, dict]:
        """
        Zwraca dostępne tryby konwersacyjne dla modelu Bielik
        
        Returns:
            Dict z różnymi trybami konwersacyjnymi
        """
        return {
            "friendly": {
                "name": "Przyjazny",
                "description": "Ciepły, pomocny ton z używaniem emotikonów",
                "temperature": 0.8,
                "system_suffix": "Bądź ciepły, przyjazny i używaj emotikonów gdy to naturalne. 😊"
            },
            "professional": {
                "name": "Profesjonalny", 
                "description": "Formalny, rzeczowy ton biznesowy",
                "temperature": 0.5,
                "system_suffix": "Używaj profesjonalnego, formalnego języka. Unikaj emotikonów."
            },
            "creative": {
                "name": "Kreatywny",
                "description": "Bardziej kreatywny i nietypowy sposób wyrażania",
                "temperature": 0.9,
                "system_suffix": "Bądź kreatywny w odpowiedziach. Używaj metafor, analogii i ciekawych porównań."
            },
            "analytical": {
                "name": "Analityczny",
                "description": "Szczegółowe analizy z przykładami i uzasadnieniami",
                "temperature": 0.6,
                "system_suffix": "Analizuj zagadnienia szczegółowo. Podawaj przykłady i uzasadnienia."
            },
            "concise": {
                "name": "Zwięzły",
                "description": "Krótkie, na temat odpowiedzi bez zbędnych słów",
                "temperature": 0.4,
                "system_suffix": "Odpowiadaj zwięźle i na temat. Maksymalnie 1-2 zdania."
            },
            "educational": {
                "name": "Edukacyjny",
                "description": "Wyjaśnia pojęcia krok po kroku z przykładami",
                "temperature": 0.7,
                "system_suffix": "Wyjaśniaj pojęcia krok po kroku. Używaj przykładów i prostego języka."
            }
        }
    
    async def _apply_conversation_mode(self, messages: list, mode: str = "friendly") -> list:
        """
        Aplikuje wybrany tryb konwersacyjny do wiadomości
        
        Args:
            messages: Lista wiadomości do modelu
            mode: Wybrane tryb konwersacyjny
            
        Returns:
            Lista wiadomości z zastosowanym trybem
        """
        modes = self._get_bielik_conversation_modes()
        
        if mode not in modes:
            mode = "friendly"  # Domyślny tryb
            
        mode_config = modes[mode]
        
        # Dodaj sufiks trybu do system message
        if messages and messages[0]["role"] == "system":
            messages[0]["content"] += f"\n\nTRYB KONWERSACYJNY: {mode_config['system_suffix']}"
        
        return messages
    
    def _detect_user_intent_bielik(self, query: str) -> str:
        """
        Wykrywa intencję użytkownika dla lepszego dostosowania odpowiedzi Bielika
        
        Args:
            query: Zapytanie użytkownika
            
        Returns:
            Wykryta intencja użytkownika
        """
        query_lower = query.lower()
        
        # Wykrywanie różnych intencji
        intents = {
            "question": ["co", "jak", "dlaczego", "kiedy", "gdzie", "kto", "ile", "jaki", "?"],
            "request": ["pomóż", "zrób", "stwórz", "napisz", "znajdź", "sprawdź", "proszę"],
            "conversation": ["cześć", "dzień dobry", "co słychać", "jak sprawy", "opowiedz"],
            "explanation": ["wyjaśnij", "opisz", "przedstaw", "objaśnij", "wytłumacz"],
            "comparison": ["porównaj", "różnica", "podobieństwo", "lepszy", "gorszy"],
            "advice": ["co sądzisz", "co radzisz", "polecasz", "sugeruj", "rada"],
            "creative": ["wymyśl", "stwórz", "zaproponuj", "wyobraź sobie", "kreatywnie"]
        }
        
        # Zlicz trafienia dla każdej intencji
        intent_scores = {}
        for intent, keywords in intents.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Zwróć intencję z najwyższym wynikiem
        if intent_scores:
            return max(intent_scores.items(), key=lambda x: x[1])[0]
        
        return "general"  # Domyślna intencja
    
    def _get_bielik_response_style(self, intent: str, complexity: ModelComplexity) -> dict:
        """
        Zwraca styl odpowiedzi dostosowany do intencji i złożoności dla Bielika
        
        Args:
            intent: Wykryta intencja użytkownika
            complexity: Złożoność zapytania
            
        Returns:
            Dict z ustawieniami stylu odpowiedzi
        """
        styles = {
            "question": {
                "approach": "Odpowiedz na pytanie bezpośrednio i jasno",
                "max_tokens": 300 if complexity == ModelComplexity.SIMPLE else 800,
                "temperature": 0.5
            },
            "request": {
                "approach": "Wykonaj prośbę krok po kroku",
                "max_tokens": 500 if complexity == ModelComplexity.SIMPLE else 1200,
                "temperature": 0.6
            },
            "conversation": {
                "approach": "Prowadź naturalną, przyjazną konwersację",
                "max_tokens": 150,
                "temperature": 0.8
            },
            "explanation": {
                "approach": "Wyjaśnij szczegółowo i zrozumiale",
                "max_tokens": 600 if complexity == ModelComplexity.STANDARD else 1500,
                "temperature": 0.6
            },
            "comparison": {
                "approach": "Porównaj systematycznie z przykładami",
                "max_tokens": 800,
                "temperature": 0.7
            },
            "advice": {
                "approach": "Udziel przemyślanej rady z uzasadnieniem",
                "max_tokens": 400,
                "temperature": 0.7
            },
            "creative": {
                "approach": "Bądź kreatywny i oryginalny",
                "max_tokens": 1000,
                "temperature": 0.9
            }
        }
        
        return styles.get(intent, styles["question"])  # Domyślny styl
