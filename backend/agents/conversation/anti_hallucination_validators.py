"""
Anti-Hallucination Validation Module

Moduł zawierający walidatory przeciwko halucynacjom dla GeneralConversationAgent.
"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AntiHallucinationValidators:
    """Walidatory przeciwko halucynacjom w odpowiedziach"""

    @staticmethod
    def contains_name_fuzzy(query_text: str, response_text: str) -> bool:
        """Sprawdza czy odpowiedź zawiera imię/nazwisko z query.
        Fuzzy match.
        Zwraca True, jeśli znaleziono dopasowanie.
        """
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
        # (nawet jeśli zmienione)
        response_lower = response_text.lower()
        for polish_name in polish_names:
            if polish_name in response_lower and re.search(
                r"\b" + polish_name + r"\b", response_lower
            ):
                return True

        return False

    @staticmethod
    def contains_hallucination_patterns(response_text: str) -> bool:
        """Sprawdza czy odpowiedź zawiera typowe wzorce halucynacji"""
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

    @staticmethod
    def validate_response_against_context(
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

    @staticmethod
    def should_switch_to_search(
        query: str, rag_context: str, response: str, rag_confidence: float
    ) -> bool:
        """Określa czy powinno przełączyć na tryb wyszukiwania"""
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

    @staticmethod
    def indicates_lack_of_knowledge(response_text: str) -> bool:
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