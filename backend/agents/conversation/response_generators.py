"""
Response Generation Module

Moduł do generowania odpowiedzi dla GeneralConversationAgent.
"""

import logging

from core.hybrid_llm_client import ModelComplexity, hybrid_llm_client

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """Generator odpowiedzi z wykorzystaniem LLM"""

    @staticmethod
    async def generate_response(
        query: str,
        rag_context: str,
        internet_context: str,
        use_perplexity: bool,
        use_bielik: bool,
    ) -> str:
        """Generuje odpowiedź z wykorzystaniem wszystkich źródeł.
        Informacji i weryfikacji wiedzy.
        """

        # Buduj system prompt z uwzględnieniem weryfikacji wiedzy
        # i zapobiegania hallucinacjom
        system_prompt = (
            "Jesteś pomocnym asystentem AI prowadzącym swobodne konwersacje. "
            "Twoim zadaniem jest udzielanie dokładnych, pomocnych i aktualnych odpowiedzi na pytania użytkownika.\n\n"
            "KRYTYCZNE ZASADY PRZECIWKO HALLUCINACJOM:\n"
            "- NIGDY nie wymyślaj faktów, dat, liczb, nazw, miejsc ani szczegółów\n"
            "- NIGDY nie twórz fikcyjnych przykładów, historii ani informacji\n"
            "- NIGDY nie podawaj niepewnych informacji jako faktów\n"
            "- Jeśli nie znasz odpowiedzi, powiedz: 'Nie mam pewnych informacji na ten temat'\n"
            "- Jeśli informacje są niepewne, oznacz je jako 'nie jestem pewien' lub 'może'\n"
            "- Używaj TYLKO informacji z podanych źródeł lub swojej sprawdzonej wiedzy ogólnej\n"
            "- Gdy brakuje informacji, przyznaj to zamiast wymyślać\n"
            "- Nie twórz fikcyjnych źródeł, cytatów ani referencji\n\n"
            "JEŚLI UŻYTKOWNIK PYTA O OSOBĘ LUB PRODUKT, KTÓREGO NIE ROZPOZNAJESZ (np. 'Jan Kowalski', 'Samsung Galaxy XYZ 2025'), ZAWSZE ODPOWIEDZ:\n"
            "- 'Nie mam informacji o osobie Jan Kowalski.'\n"
            "- 'Nie istnieje produkt Samsung Galaxy XYZ 2025.'\n"
            "NAWET JEŚLI NAZWA BRZMI PRAWDOPODOBNIE, NIE WYMYŚLAJ BIOGRAFII ANI SPECYFIKACJI.\n\n"
            "Przykłady:\n"
            "- Pytanie: 'Opowiedz o Janie Kowalskim, polskim naukowcu z XIX wieku'. Odpowiedź: 'Nie mam informacji o osobie Jan Kowalski.'\n"
            "- Pytanie: 'Jakie są specyfikacje telefonu Samsung Galaxy XYZ 2025?'. Odpowiedź: 'Nie istnieje produkt Samsung Galaxy XYZ 2025.'\n\n"
            "Wykorzystuj dostępne źródła informacji w kolejności priorytetu:\n"
            "1. Informacje z dokumentów (jeśli dostępne)\n"
            "2. Dane z bazy (jeśli dostępne)\n"
            "3. Informacje z internetu (jeśli dostępne)\n"
            "4. Sprawdzoną wiedzę ogólną (tylko fakty)\n\n"
            "Weryfikacja wiedzy:\n"
            "- Jeśli informacje zawierają wskaźniki wiarygodności, uwzględnij je w odpowiedzi\n"
            "- Oznacz informacje jako zweryfikowane (✅) lub niezweryfikowane (⚠️)\n"
            "- Jeśli wskaźnik wiarygodności jest niski (< 0.4), zalecaj ostrożność\n"
            "- Zawsze podawaj źródła informacji gdy to możliwe\n"
            "- Odróżniaj fakty od opinii\n\n"
            "Odpowiadaj w języku polskim, chyba że użytkownik prosi o inną wersję językową."
        )

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
            # Określ złożoność zapytania
            complexity = ResponseGenerator._determine_query_complexity(
                query, rag_context, internet_context
            )
            logger.info(f"Determined query complexity: {complexity}")

            # Wybierz model na podstawie złożoności i flagi use_bielik
            model_name = ResponseGenerator._select_model(complexity, use_bielik)
            logger.info(f"Selected model: {model_name}")

            response = await hybrid_llm_client.chat(
                messages=messages,
                model=model_name,
                force_complexity=complexity,
                stream=False,
            )

            # Sprawdź czy response jest słownikiem (nie AsyncGenerator)
            if (
                isinstance(response, dict)
                and "message" in response
                and "content" in response["message"]
            ):
                response_text = response["message"]["content"]

                # Sprawdź czy odpowiedź wskazuje na brak wiedzy
                if ResponseGenerator._indicates_lack_of_knowledge(response_text):
                    logger.info(
                        f"Response indicates lack of knowledge, switching to search mode for query: {query}"
                    )
                    return await ResponseGenerator._switch_to_search_mode(
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
                        if ResponseGenerator._indicates_lack_of_knowledge(response_text):
                            logger.info(
                                f"Fallback response indicates lack of knowledge, switching to search mode for query: {query}"
                            )
                            return await ResponseGenerator._switch_to_search_mode(
                                query, use_perplexity, use_bielik
                            )

                        return response_text
                except Exception as fallback_error:
                    logger.error(f"Fallback model also failed: {fallback_error!s}")

            # Ostateczny fallback - przełącz na tryb wyszukiwania
            logger.info(
                f"All models failed, switching to search mode for query: {query}"
            )
            return await ResponseGenerator._switch_to_search_mode(query, use_perplexity, use_bielik)

    @staticmethod
    def _indicates_lack_of_knowledge(response_text: str) -> bool:
        """
        Sprawdza czy odpowiedź wskazuje na brak wiedzy i powinna przełączyć na tryb wyszukiwania.
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

    @staticmethod
    async def _switch_to_search_mode(
        query: str, use_perplexity: bool, use_bielik: bool
    ) -> str:
        """
        Automatycznie przełącza na tryb wyszukiwania gdy model nie zna odpowiedzi.
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

    @staticmethod
    def _determine_query_complexity(
        query: str, rag_context: str, internet_context: str
    ) -> ModelComplexity:
        """
        Określa złożoność zapytania na podstawie jego treści i dostępnego kontekstu.
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

    @staticmethod
    def _select_model(complexity: ModelComplexity, use_bielik: bool) -> str:
        """
        Wybiera model na podstawie złożoności zapytania i preferencji użytkownika
        """
        # Use only Bielik-11B for all tasks
        return "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"