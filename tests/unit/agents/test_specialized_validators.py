"""
Tests for specialized anti-hallucination validators
"""

import pytest
from unittest.mock import AsyncMock, patch

from backend.core.specialized_validators import (
    ChefValidator,
    ReceiptAnalysisValidator,
    WeatherValidator,
    SearchValidator,
    ValidatorFactory,
    DefaultValidator,
)
from backend.core.anti_hallucination_system import ValidationLevel, HallucinationType


class TestChefValidator:
    """Test ChefValidator functionality"""

    @pytest.fixture
    def validator(self):
        return ChefValidator()

    @pytest.mark.asyncio
    async def test_validate_with_available_ingredients(self, validator):
        """Test validation with available ingredients"""
        response = "Dodaj 300g makaronu i 2 pomidory"
        context = "Przepis na spaghetti"
        available_ingredients = ["makaron", "pomidory", "cebula"]

        result = await validator.validate(
            response=response,
            context=context,
            validation_level=ValidationLevel.STRICT,
            available_ingredients=available_ingredients,
        )

        assert result.is_valid is True
        assert result.confidence > 0.7
        assert result.hallucination_score < 0.3
        assert len(result.detected_hallucinations) == 0

    @pytest.mark.asyncio
    async def test_validate_with_unavailable_ingredients(self, validator):
        """Test validation with unavailable ingredients"""
        response = "Dodaj 300g trufli i 2 pomidory"
        context = "Przepis na spaghetti"
        available_ingredients = ["makaron", "pomidory", "cebula"]

        result = await validator.validate(
            response=response,
            context=context,
            validation_level=ValidationLevel.STRICT,
            available_ingredients=available_ingredients,
        )

        assert result.is_valid is False
        assert HallucinationType.INGREDIENT_HALLUCINATION in result.detected_hallucinations
        assert "trufli" in result.suspicious_phrases

    @pytest.mark.asyncio
    async def test_validate_unrealistic_measurements(self, validator):
        """Test validation of unrealistic measurements"""
        response = "Gotuj przez 2000 minut w temperaturze 500 stopni"
        context = "Przepis na spaghetti"

        result = await validator.validate(
            response=response,
            context=context,
            validation_level=ValidationLevel.STRICT,
        )

        assert HallucinationType.MEASUREMENT_HALLUCINATION in result.detected_hallucinations
        assert result.hallucination_score > 0.3

    def test_get_validation_patterns(self, validator):
        """Test getting validation patterns"""
        patterns = validator.get_validation_patterns()
        
        assert HallucinationType.INGREDIENT_HALLUCINATION in patterns
        assert HallucinationType.MEASUREMENT_HALLUCINATION in patterns
        assert HallucinationType.FACTUAL_ERROR in patterns

    def test_get_thresholds(self, validator):
        """Test getting confidence and hallucination thresholds"""
        confidence_threshold = validator.get_confidence_threshold()
        hallucination_threshold = validator.get_hallucination_threshold()
        
        assert confidence_threshold == 0.7
        assert hallucination_threshold == 0.3


class TestReceiptAnalysisValidator:
    """Test ReceiptAnalysisValidator functionality"""

    @pytest.fixture
    def validator(self):
        return ReceiptAnalysisValidator()

    @pytest.mark.asyncio
    async def test_validate_valid_receipt(self, validator):
        """Test validation of valid receipt data"""
        response = "Paragon z 15.01.2024, kwota 45.67 zł, NIP: 123-456-78-90"
        context = "Analiza paragonu"

        result = await validator.validate(
            response=response,
            context=context,
            validation_level=ValidationLevel.STRICT,
        )

        assert result.is_valid is True
        assert result.confidence > 0.8
        assert result.hallucination_score < 0.2

    @pytest.mark.asyncio
    async def test_validate_invalid_receipt(self, validator):
        """Test validation of invalid receipt data"""
        response = "Paragon z 32.13.2024, kwota 999999.99 zł"
        context = "Analiza paragonu"

        result = await validator.validate(
            response=response,
            context=context,
            validation_level=ValidationLevel.STRICT,
        )

        assert result.is_valid is False
        assert HallucinationType.FACTUAL_ERROR in result.detected_hallucinations

    @pytest.mark.asyncio
    async def test_validate_context_violation(self, validator):
        """Test validation of context violation"""
        response = "Dzisiaj jest piękna pogoda"
        context = "Analiza paragonu"

        result = await validator.validate(
            response=response,
            context=context,
            validation_level=ValidationLevel.STRICT,
        )

        assert HallucinationType.CONTEXT_VIOLATION in result.detected_hallucinations

    def test_get_validation_patterns(self, validator):
        """Test getting validation patterns"""
        patterns = validator.get_validation_patterns()
        
        assert HallucinationType.FACTUAL_ERROR in patterns
        assert HallucinationType.PRICE_HALLUCINATION in patterns
        assert HallucinationType.DATE_TIME_HALLUCINATION in patterns

    def test_get_thresholds(self, validator):
        """Test getting confidence and hallucination thresholds"""
        confidence_threshold = validator.get_confidence_threshold()
        hallucination_threshold = validator.get_hallucination_threshold()
        
        assert confidence_threshold == 0.8
        assert hallucination_threshold == 0.2


class TestWeatherValidator:
    """Test WeatherValidator functionality"""

    @pytest.fixture
    def validator(self):
        return WeatherValidator()

    @pytest.mark.asyncio
    async def test_validate_valid_weather(self, validator):
        """Test validation of valid weather data"""
        response = "Temperatura 22°C, wilgotność 65%, wiatr 15 km/h"
        context = "Pogoda w Warszawie"

        result = await validator.validate(
            response=response,
            context=context,
            validation_level=ValidationLevel.LENIENT,
        )

        assert result.is_valid is True
        assert result.confidence > 0.5
        assert result.hallucination_score < 0.4

    @pytest.mark.asyncio
    async def test_validate_unrealistic_weather(self, validator):
        """Test validation of unrealistic weather data"""
        response = "Temperatura 200°C, wilgotność 150%"
        context = "Pogoda w Warszawie"

        result = await validator.validate(
            response=response,
            context=context,
            validation_level=ValidationLevel.LENIENT,
        )

        assert HallucinationType.MEASUREMENT_HALLUCINATION in result.detected_hallucinations

    def test_get_validation_patterns(self, validator):
        """Test getting validation patterns"""
        patterns = validator.get_validation_patterns()
        
        assert HallucinationType.FACTUAL_ERROR in patterns
        assert HallucinationType.MEASUREMENT_HALLUCINATION in patterns

    def test_get_thresholds(self, validator):
        """Test getting confidence and hallucination thresholds"""
        confidence_threshold = validator.get_confidence_threshold()
        hallucination_threshold = validator.get_hallucination_threshold()
        
        assert confidence_threshold == 0.5
        assert hallucination_threshold == 0.4


class TestSearchValidator:
    """Test SearchValidator functionality"""

    @pytest.fixture
    def validator(self):
        return SearchValidator()

    @pytest.mark.asyncio
    async def test_validate_valid_search(self, validator):
        """Test validation of valid search results"""
        response = "Według źródeł z 2024 roku, Warszawa ma około 1.8 miliona mieszkańców"
        context = "Wyszukiwanie informacji o Warszawie"

        result = await validator.validate(
            response=response,
            context=context,
            validation_level=ValidationLevel.MODERATE,
        )

        assert result.is_valid is True
        assert result.confidence > 0.7
        assert result.hallucination_score < 0.3

    @pytest.mark.asyncio
    async def test_validate_unverifiable_claims(self, validator):
        """Test validation of unverifiable claims"""
        response = "Na pewno to jest najlepszy sposób na rozwiązanie problemu"
        context = "Wyszukiwanie informacji"

        result = await validator.validate(
            response=response,
            context=context,
            validation_level=ValidationLevel.MODERATE,
        )

        assert HallucinationType.UNVERIFIABLE_CLAIM in result.detected_hallucinations

    @pytest.mark.asyncio
    async def test_validate_context_violation(self, validator):
        """Test validation of context violation"""
        response = "Dzisiaj jest piękna pogoda"
        context = "Wyszukiwanie informacji o historii Polski"

        result = await validator.validate(
            response=response,
            context=context,
            validation_level=ValidationLevel.MODERATE,
        )

        assert HallucinationType.CONTEXT_VIOLATION in result.detected_hallucinations

    def test_get_validation_patterns(self, validator):
        """Test getting validation patterns"""
        patterns = validator.get_validation_patterns()
        
        assert HallucinationType.FACTUAL_ERROR in patterns
        assert HallucinationType.UNVERIFIABLE_CLAIM in patterns

    def test_get_thresholds(self, validator):
        """Test getting confidence and hallucination thresholds"""
        confidence_threshold = validator.get_confidence_threshold()
        hallucination_threshold = validator.get_hallucination_threshold()
        
        assert confidence_threshold == 0.7
        assert hallucination_threshold == 0.3


class TestValidatorFactory:
    """Test ValidatorFactory functionality"""

    def test_get_chef_validator(self):
        """Test getting chef validator"""
        validator = ValidatorFactory.get_validator("chef")
        assert isinstance(validator, ChefValidator)

    def test_get_receipt_validator(self):
        """Test getting receipt validator"""
        validator = ValidatorFactory.get_validator("receipt_analysis")
        assert isinstance(validator, ReceiptAnalysisValidator)

    def test_get_weather_validator(self):
        """Test getting weather validator"""
        validator = ValidatorFactory.get_validator("weather")
        assert isinstance(validator, WeatherValidator)

    def test_get_search_validator(self):
        """Test getting search validator"""
        validator = ValidatorFactory.get_validator("search")
        assert isinstance(validator, SearchValidator)

    def test_get_default_validator(self):
        """Test getting default validator for unknown agent type"""
        validator = ValidatorFactory.get_validator("unknown_agent")
        assert isinstance(validator, DefaultValidator)

    def test_register_validator(self):
        """Test registering new validator"""
        class CustomValidator(ChefValidator):
            pass

        ValidatorFactory.register_validator("custom", CustomValidator)
        validator = ValidatorFactory.get_validator("custom")
        assert isinstance(validator, CustomValidator)


class TestDefaultValidator:
    """Test DefaultValidator functionality"""

    @pytest.fixture
    def validator(self):
        return DefaultValidator()

    @pytest.mark.asyncio
    async def test_validate_general_response(self, validator):
        """Test validation of general response"""
        response = "To jest ogólna odpowiedź na pytanie"
        context = "Ogólne pytanie"

        result = await validator.validate(
            response=response,
            context=context,
            validation_level=ValidationLevel.MODERATE,
        )

        assert result.is_valid is True
        assert result.confidence > 0.6
        assert result.hallucination_score < 0.4

    @pytest.mark.asyncio
    async def test_validate_with_factual_errors(self, validator):
        """Test validation with factual errors"""
        response = "W 2024 roku wydarzyło się coś ważnego"
        context = "Ogólne pytanie"

        result = await validator.validate(
            response=response,
            context=context,
            validation_level=ValidationLevel.MODERATE,
        )

        assert HallucinationType.FACTUAL_ERROR in result.detected_hallucinations

    def test_get_validation_patterns(self, validator):
        """Test getting validation patterns"""
        patterns = validator.get_validation_patterns()
        
        assert HallucinationType.FACTUAL_ERROR in patterns

    def test_get_thresholds(self, validator):
        """Test getting confidence and hallucination thresholds"""
        confidence_threshold = validator.get_confidence_threshold()
        hallucination_threshold = validator.get_hallucination_threshold()
        
        assert confidence_threshold == 0.6
        assert hallucination_threshold == 0.4


class TestValidationLevels:
    """Test validation level behavior"""

    @pytest.mark.asyncio
    async def test_strict_validation(self):
        """Test strict validation level"""
        validator = ChefValidator()
        response = "Dodaj 300g trufli"  # Unavailable ingredient
        available_ingredients = ["makaron", "pomidory"]

        result = await validator.validate(
            response=response,
            context="Przepis",
            validation_level=ValidationLevel.STRICT,
            available_ingredients=available_ingredients,
        )

        assert result.is_valid is False
        assert result.confidence < 0.7

    @pytest.mark.asyncio
    async def test_moderate_validation(self):
        """Test moderate validation level"""
        validator = ChefValidator()
        response = "Dodaj 300g trufli"  # Unavailable ingredient
        available_ingredients = ["makaron", "pomidory"]

        result = await validator.validate(
            response=response,
            context="Przepis",
            validation_level=ValidationLevel.MODERATE,
            available_ingredients=available_ingredients,
        )

        # Moderate should be more lenient than strict
        assert result.confidence > 0.5

    @pytest.mark.asyncio
    async def test_lenient_validation(self):
        """Test lenient validation level"""
        validator = ChefValidator()
        response = "Dodaj 300g trufli"  # Unavailable ingredient
        available_ingredients = ["makaron", "pomidory"]

        result = await validator.validate(
            response=response,
            context="Przepis",
            validation_level=ValidationLevel.LENIENT,
            available_ingredients=available_ingredients,
        )

        # Lenient should be most permissive
        assert result.confidence > 0.6 