"""
Query Classification and Detection Module

Moduł zawierający logikę klasyfikacji i detekcji różnych typów zapytań
dla GeneralConversationAgent.
"""

import re
import logging

logger = logging.getLogger(__name__)


class QueryClassifier:
    """Klasyfikator zapytań użytkownika"""

    @staticmethod
    def is_simple_query(query: str) -> bool:
        """Determine if a query is simple based on length and complexity.
        
        Args:
            query: The user's query string to analyze.
            
        Returns:
            True if the query is considered simple, False otherwise.
        """
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

    @staticmethod
    def is_date_query(query: str) -> bool:
        """Sprawdza czy zapytanie dotyczy daty/czasu.
        
        Args:
            query: Zapytanie użytkownika do analizy.
            
        Returns:
            True jeśli zapytanie dotyczy daty/czasu, False w przeciwnym razie.
        """
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

    @staticmethod
    def is_pantry_query(query: str) -> bool:
        """Check if query is about pantry/inventory.
        
        Args:
            query: The user's query string to analyze.
            
        Returns:
            True if the query is about pantry/inventory, False otherwise.
        """
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

    @staticmethod
    def is_weather_query(query: str) -> bool:
        """Check if query is weather-related.
        
        Args:
            query: The user's query string to analyze.
            
        Returns:
            True if the query is weather-related, False otherwise.
        """
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

    @staticmethod
    def is_greeting(query: str) -> bool:
        """Check if query is a greeting.
        
        Args:
            query: The user's query string to analyze.
            
        Returns:
            True if the query is a greeting, False otherwise.
        """
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

    @staticmethod
    def is_product_query(query_text: str) -> bool:
        """Sprawdza czy query dotyczy produktu.
        
        Args:
            query_text: Tekst zapytania do analizy.
            
        Returns:
            True jeśli zapytanie dotyczy produktu, False w przeciwnym razie.
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

    @staticmethod
    def is_person_query(query_text: str) -> bool:
        """Sprawdza czy query dotyczy osoby - ulepszona logika kontekstowa.
        
        Args:
            query_text: Tekst zapytania do analizy.
            
        Returns:
            True jeśli zapytanie dotyczy osoby, False w przeciwnym razie.
        """
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

    @staticmethod
    def is_recipe_query(query_text: str) -> bool:
        """Sprawdza czy query dotyczy przepisu.
        
        Args:
            query_text: Tekst zapytania do analizy.
            
        Returns:
            True jeśli zapytanie dotyczy przepisu, False w przeciwnym razie.
        """
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

    @staticmethod
    def is_event_query(query_text: str) -> bool:
        """Sprawdza czy query dotyczy wydarzenia.
        
        Args:
            query_text: Tekst zapytania do analizy.
            
        Returns:
            True jeśli zapytanie dotyczy wydarzenia, False w przeciwnym razie.
        """
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

    @staticmethod
    def is_future_event(query_text: str) -> bool:
        """Sprawdza czy query dotyczy wydarzenia z przyszłości.
        
        Args:
            query_text: Tekst zapytania do analizy.
            
        Returns:
            True jeśli zapytanie dotyczy przyszłego wydarzenia, False w przeciwnym razie.
        """
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

    @staticmethod
    def is_known_person(query_text: str) -> bool:
        """Sprawdza czy query dotyczy znanej, zweryfikowanej osoby.
        
        Args:
            query_text: Tekst zapytania do analizy.
            
        Returns:
            True jeśli zapytanie dotyczy znanej osoby, False w przeciwnym razie.
        """
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


class SimpleResponseGenerator:
    """Generator prostych odpowiedzi na podstawowe zapytania"""

    @staticmethod
    def generate_simple_response(query: str) -> str:
        """Generate appropriate response for simple queries like greetings.
        
        Args:
            query: The user's query string to respond to.
            
        Returns:
            A simple, appropriate response string for the query.
        """
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