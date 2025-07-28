"""
Unit tests for Query Classifiers module
"""

import pytest

from backend.agents.conversation.query_classifiers import QueryClassifier, SimpleResponseGenerator


class TestQueryClassifier:
    """Test cases for QueryClassifier class"""

    def test_is_simple_query_short_text(self):
        """Test if short queries are classified as simple"""
        assert QueryClassifier.is_simple_query("tak") is True
        assert QueryClassifier.is_simple_query("nie") is True
        assert QueryClassifier.is_simple_query("ok") is True
        assert QueryClassifier.is_simple_query("hi") is True

    def test_is_simple_query_phrases(self):
        """Test if simple phrases are classified as simple"""
        assert QueryClassifier.is_simple_query("dziękuję bardzo") is True
        assert QueryClassifier.is_simple_query("rozumiem to") is True
        assert QueryClassifier.is_simple_query("witaj przyjacielu") is True

    def test_is_simple_query_complex(self):
        """Test if complex queries are not classified as simple"""
        complex_query = "Czy możesz mi pomóc znaleźć przepis na ciasto z dodatkiem czekolady?"
        assert QueryClassifier.is_simple_query(complex_query) is False

    def test_is_date_query_positive(self):
        """Test date query detection for positive cases"""
        assert QueryClassifier.is_date_query("jaki dzisiaj dzień?") is True
        assert QueryClassifier.is_date_query("który dzień tygodnia?") is True
        assert QueryClassifier.is_date_query("podaj dzisiejszą datę") is True
        assert QueryClassifier.is_date_query("what day is today?") is True

    def test_is_date_query_weather_exclusion(self):
        """Test that weather queries are not classified as date queries"""
        assert QueryClassifier.is_date_query("jaka dzisiaj pogoda?") is False
        assert QueryClassifier.is_date_query("temperatura dzisiaj") is False

    def test_is_pantry_query_positive(self):
        """Test pantry query detection"""
        assert QueryClassifier.is_pantry_query("co mam w spiżarni?") is True
        assert QueryClassifier.is_pantry_query("sprawdź lodówkę") is True
        assert QueryClassifier.is_pantry_query("lista produktów") is True

    def test_is_weather_query_positive(self):
        """Test weather query detection"""
        assert QueryClassifier.is_weather_query("jaka jest pogoda?") is True
        assert QueryClassifier.is_weather_query("temperatura na zewnątrz") is True
        assert QueryClassifier.is_weather_query("czy będzie padać?") is True

    def test_is_greeting_positive(self):
        """Test greeting detection"""
        assert QueryClassifier.is_greeting("cześć") is True
        assert QueryClassifier.is_greeting("witaj") is True
        assert QueryClassifier.is_greeting("dzień dobry") is True
        assert QueryClassifier.is_greeting("hello") is True

    def test_is_product_query_positive(self):
        """Test product query detection"""
        assert QueryClassifier.is_product_query("specyfikacja iPhone'a") is True
        assert QueryClassifier.is_product_query("laptop Dell") is True
        assert QueryClassifier.is_product_query("parametry smartfona") is True

    def test_is_person_query_positive(self):
        """Test person query detection with known persons"""
        assert QueryClassifier.is_person_query("kto to Jan Kowalski?") is True
        assert QueryClassifier.is_person_query("biografia znanej osoby") is True

    def test_is_person_query_exclusions(self):
        """Test person query exclusions for financial/technical topics"""
        assert QueryClassifier.is_person_query("cena bitcoina") is False
        assert QueryClassifier.is_person_query("kurs dolara") is False
        assert QueryClassifier.is_person_query("pogoda jutro") is False

    def test_is_recipe_query_positive(self):
        """Test recipe query detection"""
        assert QueryClassifier.is_recipe_query("przepis na pierogi") is True
        assert QueryClassifier.is_recipe_query("jak ugotować makaron?") is True
        assert QueryClassifier.is_recipe_query("przygotuj obiad") is True

    def test_is_known_person_positive(self):
        """Test known person detection"""
        assert QueryClassifier.is_known_person("Andrzej Duda") is True
        assert QueryClassifier.is_known_person("prezydent Polski") is True
        assert QueryClassifier.is_known_person("Robert Lewandowski") is True


class TestSimpleResponseGenerator:
    """Test cases for SimpleResponseGenerator class"""

    def test_generate_simple_response_greetings(self):
        """Test response generation for greetings"""
        response = SimpleResponseGenerator.generate_simple_response("cześć")
        assert "Cześć!" in response
        assert "pomóc" in response

    def test_generate_simple_response_thanks(self):
        """Test response generation for thanks"""
        response = SimpleResponseGenerator.generate_simple_response("dziękuję")
        assert "Nie ma sprawy" in response

    def test_generate_simple_response_agreement(self):
        """Test response generation for agreement"""
        response = SimpleResponseGenerator.generate_simple_response("ok")
        assert "Świetnie" in response

    def test_generate_simple_response_disagreement(self):
        """Test response generation for disagreement"""
        response = SimpleResponseGenerator.generate_simple_response("nie")
        assert "Rozumiem" in response

    def test_generate_simple_response_goodbye(self):
        """Test response generation for goodbye"""
        response = SimpleResponseGenerator.generate_simple_response("do widzenia")
        assert "Do widzenia" in response
        assert "Miłego dnia" in response

    def test_generate_simple_response_default(self):
        """Test default response generation"""
        response = SimpleResponseGenerator.generate_simple_response("xyz")
        assert "Rozumiem" in response
        assert "pomóc" in response