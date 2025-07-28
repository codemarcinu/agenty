"""
Unit tests for Chef Prompt Builders module
"""

import pytest

from backend.agents.chef.prompt_builders import PromptBuilder
from backend.core.anti_hallucination_system import ValidationLevel


class TestPromptBuilder:
    """Test cases for PromptBuilder class"""

    def test_create_anti_hallucination_prompt_basic(self):
        """Test basic anti-hallucination prompt creation"""
        ingredients = ["pomidory", "cebula", "czosnek"]
        dietary_restrictions = None
        validation_level = ValidationLevel.STRICT
        
        result = PromptBuilder.create_anti_hallucination_prompt(
            ingredients, dietary_restrictions, validation_level
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
        assert "pomidory" in result
        assert "cebula" in result
        assert "czosnek" in result

    def test_create_anti_hallucination_prompt_with_restrictions(self):
        """Test prompt creation with dietary restrictions"""
        ingredients = ["mięso", "warzywa"]
        dietary_restrictions = "wegetariańska"
        validation_level = ValidationLevel.MODERATE
        
        result = PromptBuilder.create_anti_hallucination_prompt(
            ingredients, dietary_restrictions, validation_level
        )
        
        assert "wegetariańska" in result
        assert "mięso" in result
        assert "warzywa" in result

    def test_create_anti_hallucination_prompt_with_user_context(self):
        """Test prompt creation with user context"""
        ingredients = ["makaron", "ser"]
        dietary_restrictions = None
        validation_level = ValidationLevel.LENIENT
        user_context = {
            "has_profile": True,
            "cooking_preferences": {
                "name": "Anna"
            }
        }
        
        result = PromptBuilder.create_anti_hallucination_prompt(
            ingredients, dietary_restrictions, validation_level, user_context
        )
        
        assert "makaron" in result
        assert "ser" in result
        # User context should be incorporated somehow
        assert isinstance(result, str)

    def test_create_anti_hallucination_prompt_with_availability(self):
        """Test prompt creation with ingredient availability"""
        ingredients = ["mąka", "jajka"]
        dietary_restrictions = None
        validation_level = ValidationLevel.MODERATE
        ingredient_availability = {
            "mąka": True,
            "jajka": False
        }
        
        result = PromptBuilder.create_anti_hallucination_prompt(
            ingredients, dietary_restrictions, validation_level, 
            ingredient_availability=ingredient_availability
        )
        
        assert "mąka" in result
        assert "jajka" in result

    def test_create_anti_hallucination_prompt_different_validation_levels(self):
        """Test prompt creation with different validation levels"""
        ingredients = ["składnik1", "składnik2"]
        dietary_restrictions = None
        
        # Test all validation levels
        for level in [ValidationLevel.STRICT, ValidationLevel.MODERATE, ValidationLevel.LENIENT]:
            result = PromptBuilder.create_anti_hallucination_prompt(
                ingredients, dietary_restrictions, level
            )
            
            assert isinstance(result, str)
            assert len(result) > 0
            assert "składnik1" in result
            assert "składnik2" in result

    def test_create_anti_hallucination_prompt_empty_ingredients(self):
        """Test prompt creation with empty ingredients list"""
        ingredients = []
        dietary_restrictions = None
        validation_level = ValidationLevel.STRICT
        
        result = PromptBuilder.create_anti_hallucination_prompt(
            ingredients, dietary_restrictions, validation_level
        )
        
        # Should still return a valid prompt even with no ingredients
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_system_prompt_strict(self):
        """Test system prompt for strict validation"""
        result = PromptBuilder.get_system_prompt(ValidationLevel.STRICT)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_system_prompt_moderate(self):
        """Test system prompt for moderate validation"""
        result = PromptBuilder.get_system_prompt(ValidationLevel.MODERATE)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_system_prompt_lenient(self):
        """Test system prompt for lenient validation"""
        result = PromptBuilder.get_system_prompt(ValidationLevel.LENIENT)
        
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_system_prompt_different_levels_unique(self):
        """Test that different validation levels produce different prompts"""
        strict = PromptBuilder.get_system_prompt(ValidationLevel.STRICT)
        moderate = PromptBuilder.get_system_prompt(ValidationLevel.MODERATE)
        lenient = PromptBuilder.get_system_prompt(ValidationLevel.LENIENT)
        
        # All should be different strings
        assert strict != moderate
        assert moderate != lenient
        assert strict != lenient

    def test_prompt_contains_recipe_instruction(self):
        """Test that prompts contain recipe-related instructions"""
        ingredients = ["test"]
        result = PromptBuilder.create_anti_hallucination_prompt(
            ingredients, None, ValidationLevel.STRICT
        )
        
        # Should contain some recipe-related keywords
        recipe_keywords = ["przepis", "składnik", "gotowanie", "przygotowanie"]
        contains_recipe_keyword = any(keyword in result.lower() for keyword in recipe_keywords)
        assert contains_recipe_keyword, f"Prompt should contain recipe-related keywords. Got: {result}"