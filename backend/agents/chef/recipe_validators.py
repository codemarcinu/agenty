"""
Recipe Validation Module

Moduł zawierający walidatory przepisów dla ChefAgent.
"""

import re
import logging
from dataclasses import dataclass
from typing import Any

from core.anti_hallucination_system import ValidationLevel

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of anti-hallucination validation"""

    is_valid: bool
    confidence: float
    suspicious_ingredients: list[str]
    missing_ingredients: list[str]
    validation_errors: list[str]
    recommendation: str


class AntiHallucinationValidator:
    """Advanced anti-hallucination validator for recipe generation"""

    def __init__(self):
        # Common ingredients that should be validated
        self.common_ingredients = {
            "podstawowe": [
                "makaron",
                "ryż",
                "ziemniaki",
                "cebula",
                "czosnek",
                "pomidory",
                "papryka",
                "marchew",
                "ogórek",
                "sałata",
                "kapusta",
                "kalafior",
                "brokuły",
                "szpinak",
                "jarmuż",
                "fasola",
                "groch",
                "soczewica",
            ],
            "mięsne": [
                "kurczak",
                "wieprzowina",
                "wołowina",
                "indyk",
                "jagnięcina",
                "kaczka",
                "gęś",
                "królik",
                "dziczyzna",
            ],
            "nabiał": [
                "jajka",
                "ser",
                "mleko",
                "śmietana",
                "masło",
                "jogurt",
                "twaróg",
                "kefir",
                "maślanka",
            ],
            "przyprawy": [
                "sól",
                "pieprz",
                "bazylia",
                "oregano",
                "tymianek",
                "rozmaryn",
                "majeranek",
                "papryka",
                "curry",
                "imbir",
                "cynamon",
                "gałka muszkatołowa",
                "kminek",
                "kolendra",
                "kurkuma",
                "chili",
            ],
            "tłuszcze": ["olej", "oliwa", "masło", "smalec", "margaryna"],
        }

        # Ingredients that are usually available in most kitchens
        self.basic_kitchen_items = [
            "sól",
            "pieprz",
            "olej",
            "masło",
            "cebula",
            "czosnek",
        ]

        # Validation patterns
        self.measurement_patterns = [
            r"\d+\s*(g|kg|ml|l|łyżka|łyżeczka|szklanka|sztuka)",
            r"\d+\s*(gram|kilogram|mililitr|litr|łyżek|łyżeczek|szklanek|sztuk)",
        ]

    def validate_recipe_against_ingredients(
        self,
        recipe_text: str,
        available_ingredients: list[str],
        validation_level: ValidationLevel = ValidationLevel.STRICT,
        max_additional_ingredients: int = 3,
    ) -> ValidationResult:
        """
        Comprehensive validation of recipe against available ingredients

        Args:
            recipe_text: The generated recipe text
            available_ingredients: List of ingredients provided by user
            validation_level: How strict the validation should be
            max_additional_ingredients: Maximum additional ingredients allowed

        Returns:
            ValidationResult with validation details
        """
        ingredients_lower = [ing.lower().strip() for ing in available_ingredients]

        # Extract all ingredients mentioned in recipe
        mentioned_ingredients = self._extract_ingredients_from_recipe(recipe_text)

        # Find suspicious ingredients (mentioned but not provided)
        suspicious_ingredients = []
        missing_ingredients = []
        validation_errors = []

        for ingredient in mentioned_ingredients:
            if ingredient not in ingredients_lower:
                # Check if it's a basic kitchen item (usually available)
                if ingredient in self.basic_kitchen_items:
                    continue

                # Check if it's a common ingredient that should be validated
                is_common = any(
                    ingredient in category
                    for category in self.common_ingredients.values()
                )

                if is_common:
                    suspicious_ingredients.append(ingredient)
                    missing_ingredients.append(ingredient)

        # Calculate confidence score
        confidence = self._calculate_confidence_score(
            suspicious_ingredients, mentioned_ingredients, validation_level
        )

        # Determine if recipe is valid based on validation level
        is_valid = self._determine_validity(
            suspicious_ingredients,
            max_additional_ingredients,
            validation_level,
            confidence,
        )

        # Generate recommendation
        recommendation = self._generate_recommendation(
            suspicious_ingredients, missing_ingredients, validation_level
        )

        return ValidationResult(
            is_valid=is_valid,
            confidence=confidence,
            suspicious_ingredients=suspicious_ingredients,
            missing_ingredients=missing_ingredients,
            validation_errors=validation_errors,
            recommendation=recommendation,
        )

    def _extract_ingredients_from_recipe(self, recipe_text: str) -> list[str]:
        """Extract all ingredients mentioned in recipe text"""
        ingredients = []

        # Look for ingredients in recipe steps
        for items in self.common_ingredients.values():
            for item in items:
                if item in recipe_text.lower():
                    ingredients.append(item)

        # Look for ingredients with measurements
        for pattern in self.measurement_patterns:
            matches = re.findall(pattern, recipe_text, re.IGNORECASE)
            for match in matches:
                # Extract ingredient name from measurement
                ingredient = self._extract_ingredient_from_measurement(match)
                if ingredient:
                    ingredients.append(ingredient.lower())

        return list(set(ingredients))  # Remove duplicates

    def _extract_ingredient_from_measurement(self, measurement: str) -> str | None:
        """Extract ingredient name from measurement text"""
        # Simple extraction - could be enhanced with NLP
        measurement_lower = measurement.lower()

        # Look for common measurement words and extract what comes before
        measurement_words = [
            "g",
            "kg",
            "ml",
            "l",
            "łyżka",
            "łyżeczka",
            "szklanka",
            "sztuka",
        ]

        for word in measurement_words:
            if word in measurement_lower:
                # Extract text before measurement
                parts = measurement_lower.split(word)
                if parts:
                    ingredient = parts[0].strip()
                    if ingredient:
                        return ingredient

        return None

    def _calculate_confidence_score(
        self,
        suspicious_ingredients: list[str],
        mentioned_ingredients: list[str],
        validation_level: ValidationLevel,
    ) -> float:
        """Calculate confidence score based on validation results"""
        if not mentioned_ingredients:
            return 0.0

        # Base confidence
        base_confidence = 1.0

        # Penalty for suspicious ingredients
        suspicious_ratio = len(suspicious_ingredients) / len(mentioned_ingredients)
        penalty = suspicious_ratio * 0.5

        # Adjust based on validation level
        if validation_level == ValidationLevel.STRICT:
            penalty_multiplier = 1.0
        elif validation_level == ValidationLevel.MODERATE:
            penalty_multiplier = 0.7
        else:  # LENIENT
            penalty_multiplier = 0.4

        confidence = base_confidence - (penalty * penalty_multiplier)
        return max(0.0, min(1.0, confidence))

    def _determine_validity(
        self,
        suspicious_ingredients: list[str],
        max_additional_ingredients: int,
        validation_level: ValidationLevel,
        confidence: float,
    ) -> bool:
        """Determine if recipe is valid based on validation criteria"""

        if validation_level == ValidationLevel.STRICT:
            # Strict: No suspicious ingredients allowed
            return len(suspicious_ingredients) == 0 and confidence >= 0.8

        if validation_level == ValidationLevel.MODERATE:
            # Moderate: Limited suspicious ingredients allowed
            return (
                len(suspicious_ingredients) <= max_additional_ingredients
                and confidence >= 0.6
            )

        # LENIENT
        # Lenient: More suspicious ingredients allowed
        return (
            len(suspicious_ingredients) <= max_additional_ingredients * 2
            and confidence >= 0.4
        )

    def _generate_recommendation(
        self,
        suspicious_ingredients: list[str],
        missing_ingredients: list[str],
        validation_level: ValidationLevel,
    ) -> str:
        """Generate recommendation based on validation results"""

        if not suspicious_ingredients:
            return "Przepis jest poprawny i używa tylko dostępnych składników."

        if validation_level == ValidationLevel.STRICT:
            return f"Przepis zawiera niedostępne składniki: {', '.join(suspicious_ingredients)}. Zalecam regenerację przepisu."

        if validation_level == ValidationLevel.MODERATE:
            return f"Przepis zawiera {len(suspicious_ingredients)} dodatkowych składników. Sprawdź czy masz: {', '.join(suspicious_ingredients)}"

        # LENIENT
        return f"Przepis może wymagać dodatkowych składników: {', '.join(suspicious_ingredients)}. Sprawdź dostępność przed przygotowaniem."


class IngredientProcessor:
    """Procesor składników dla ChefAgent"""

    @staticmethod
    def extract_ingredients_from_query(query: str) -> list[str]:
        """Extract ingredients from a natural language query"""
        # Convert to lowercase for better matching
        query_lower = query.lower()

        # Common Polish ingredients with their variations
        ingredient_patterns = {
            "kurczak": [
                "kurczak",
                "kurczaka",
                "kurczakiem",
                "chicken",
                "drób",
                "drobiu",
            ],
            "ryż": ["ryż", "ryżu", "ryżem", "rice"],
            "brokuły": ["brokuły", "brokuł", "brokułami", "broccoli"],
            "cebula": ["cebula", "cebuli", "cebulą", "onion"],
            "czosnek": ["czosnek", "czosnku", "czosnkiem", "garlic"],
            "marchew": ["marchew", "marchewka", "marchewki", "marchewką", "carrot"],
            "ziemniaki": [
                "ziemniaki",
                "ziemniak",
                "ziemniakami",
                "kartofle",
                "kartofel",
                "potato",
            ],
            "pomidory": ["pomidory", "pomidor", "pomidorem", "tomato"],
            "papryka": ["papryka", "papryką", "papryki", "pepper"],
            "mięso": ["mięso", "mięsa", "mięsem", "meat"],
            "wołowina": ["wołowina", "wołowiny", "wołowiną", "beef"],
            "wieprzowina": ["wieprzowina", "wieprzowiny", "wieprzowiną", "pork"],
            "makaron": ["makaron", "makaronu", "makaronem", "pasta"],
            "jajka": ["jajka", "jajko", "jajkiem", "egg", "eggs"],
            "ser": ["ser", "sera", "serem", "cheese"],
            "masło": ["masło", "masła", "masłem", "butter"],
            "mleko": ["mleko", "mleka", "mlekiem", "milk"],
            "jogurt": ["jogurt", "jogurem", "jogurtu", "yogurt"],
            "śmietana": ["śmietana", "śmietany", "śmietaną", "cream"],
        }

        found_ingredients = []

        # Look for each ingredient pattern in the query
        for ingredient, patterns in ingredient_patterns.items():
            for pattern in patterns:
                if re.search(r"\b" + re.escape(pattern) + r"\b", query_lower):
                    if ingredient not in found_ingredients:
                        found_ingredients.append(ingredient)
                    break

        # Also try to extract comma-separated ingredients
        # Look for patterns like "mam X, Y i Z"
        comma_match = re.search(r"mam\s+(.*?)(?:\.|$|\?)", query_lower)
        if comma_match:
            ingredients_text = comma_match.group(1)
            # Split by commas and "i"
            potential_ingredients = re.split(r"[,\s]+i\s+|[,]+", ingredients_text)
            for item in potential_ingredients:
                item = item.strip()
                if len(item) > 2 and item not in found_ingredients:
                    # Clean up the item (remove articles etc.)
                    item = re.sub(r"^(z|ze|od|do|na|w|we|o|po|przez)\s+", "", item)
                    found_ingredients.append(item)

        logger.info(
            f"[ChefAgent] Extracted ingredients from '{query}': {found_ingredients}"
        )
        return found_ingredients


class IngredientAvailabilityChecker:
    """Sprawdzacz dostępności składników w bazie danych"""

    @staticmethod
    async def check_ingredient_availability(
        db: Any, ingredients: list[str]
    ) -> dict:
        """
        Check which ingredients are available in the user's pantry database

        Args:
            db: Database session
            ingredients: List of ingredient names to check

        Returns:
            Dict with 'available', 'missing', and 'suggestions' keys
        """
        if not db:
            return {"available": [], "missing": ingredients, "suggestions": []}

        try:
            from models.shopping import Product

            # Get all available products (not consumed)
            all_available = await db.execute(
                Product.is_consumed == 0
            )
            available_product_names = [
                p.name.lower() for p in all_available.scalars().all()
            ]

            available_ingredients = []
            missing_ingredients = []
            suggestions = []

            for ingredient in ingredients:
                ingredient_lower = ingredient.lower()

                # Check exact or partial matches
                found = False
                for product_name in available_product_names:
                    if (
                        ingredient_lower in product_name
                        or product_name in ingredient_lower
                        or IngredientAvailabilityChecker._ingredients_similar(ingredient_lower, product_name)
                    ):
                        available_ingredients.append(ingredient)
                        found = True
                        break

                if not found:
                    missing_ingredients.append(ingredient)
                    # Find similar ingredients as suggestions
                    similar = IngredientAvailabilityChecker._find_similar_ingredients(
                        ingredient_lower, available_product_names
                    )
                    if similar:
                        suggestions.extend(similar)

            return {
                "available": available_ingredients,
                "missing": missing_ingredients,
                "suggestions": list(set(suggestions)),  # Remove duplicates
            }

        except Exception as e:
            logger.error(f"Error checking ingredient availability: {e}")
            return {"available": [], "missing": ingredients, "suggestions": []}

    @staticmethod
    def _ingredients_similar(ingredient1: str, ingredient2: str) -> bool:
        """Check if two ingredients are similar (basic similarity check)"""
        # Simple similarity check - could be enhanced with more sophisticated matching
        ingredient1_clean = ingredient1.strip().lower()
        ingredient2_clean = ingredient2.strip().lower()

        # Check if one is contained in the other
        if (
            ingredient1_clean in ingredient2_clean
            or ingredient2_clean in ingredient1_clean
        ):
            return True

        # Check for common ingredient variations
        variations = {
            "kurczak": ["chicken", "drób", "drobiu"],
            "pomidory": ["pomidor", "tomato"],
            "ziemniaki": ["ziemniak", "kartofle", "kartofel", "potato"],
            "brokuły": ["brokuł", "broccoli"],
            "cebula": ["onion"],
            "czosnek": ["garlic"],
            "marchew": ["marchewka", "carrot"],
            "papryka": ["pepper"],
        }

        for base, variants in variations.items():
            if (
                (ingredient1_clean == base and ingredient2_clean in variants)
                or (ingredient2_clean == base and ingredient1_clean in variants)
                or (ingredient1_clean in variants and ingredient2_clean in variants)
            ):
                return True

        return False

    @staticmethod
    def _find_similar_ingredients(
        ingredient: str, available_products: list[str]
    ) -> list[str]:
        """Find similar ingredients from available products"""
        similar = []
        ingredient_lower = ingredient.lower()

        # Category-based suggestions
        category_suggestions = {
            "kurczak": ["indyk", "wołowina", "wieprzowina", "ryba"],
            "wołowina": ["kurczak", "wieprzowina", "indyk"],
            "wieprzowina": ["kurczak", "wołowina", "indyk"],
            "ryż": ["makaron", "kasza", "ziemniaki"],
            "makaron": ["ryż", "kasza", "ziemniaki"],
            "ziemniaki": ["ryż", "makaron", "kasza"],
            "pomidory": ["papryka", "ogórek", "cebula"],
            "brokuły": ["kalafior", "szpinak", "kapusta"],
            "mleko": ["śmietana", "jogurt", "kefir"],
            "masło": ["olej", "oliwa", "margaryna"],
        }

        suggestions = category_suggestions.get(ingredient_lower, [])

        # Find which suggestions are actually available
        for suggestion in suggestions:
            for product in available_products:
                if suggestion in product.lower() or product.lower() in suggestion:
                    similar.append(product)
                    break

        return similar[:3]  # Limit to 3 suggestions