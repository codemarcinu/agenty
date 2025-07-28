from dataclasses import dataclass
import logging
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from agents.tools.tools import get_available_products_from_pantry
from core.anti_hallucination_decorator_optimized import with_chef_validation
from core.anti_hallucination_system import ValidationLevel
from core.llm_client import llm_client
from models.shopping import Product

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


class ChefAgentInput(BaseModel):
    """Input model for ChefAgent"""

    available_ingredients: list[str] = Field(
        default_factory=list, min_length=1, description="List of available ingredients"
    )
    dietary_restrictions: str | None = Field(None, description="Dietary restrictions")
    model: str | None = Field(
        "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M", description="LLM model to use"
    )
    validation_level: ValidationLevel = Field(
        ValidationLevel.STRICT, description="Validation strictness level"
    )
    max_ingredients_allowed: int = Field(
        3, description="Maximum additional ingredients allowed beyond provided ones"
    )


class RecipeSuggestion(BaseModel):
    """Model for recipe suggestion response"""

    recipe: str
    used_ingredients: list[dict[str, Any]]


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


class ChefAgent(BaseAgent):
    """
    Agent that suggests recipes based on available pantry items with
    anti-hallucination protection
    """

    def __init__(
        self,
        name: str = "ChefAgent",
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name,
            error_handler=error_handler,
            fallback_manager=fallback_manager,
            **kwargs,
        )
        self.input_model = ChefAgentInput
        self.llm_client = llm_client
        self.validator = AntiHallucinationValidator()

    async def _check_ingredient_availability(
        self, db: AsyncSession, ingredients: list[str]
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
            # Get all available products (not consumed)
            all_available = await db.execute(
                select(Product).where(Product.is_consumed == 0)
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
                        or self._ingredients_similar(ingredient_lower, product_name)
                    ):
                        available_ingredients.append(ingredient)
                        found = True
                        break

                if not found:
                    missing_ingredients.append(ingredient)
                    # Find similar ingredients as suggestions
                    similar = self._find_similar_ingredients(
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

    def _ingredients_similar(self, ingredient1: str, ingredient2: str) -> bool:
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

    def _find_similar_ingredients(
        self, ingredient: str, available_products: list[str]
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

    @with_chef_validation(
        validation_level=ValidationLevel.STRICT
    )
    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """
        Main processing method - validates input and generates recipe with
        anti-hallucination protection
        """
        try:
            # Use Bielik-11B as the only model
            model = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"

            # Aktualizuj input_data z wybranym modelem
            input_data["model"] = model

            # Extract ingredients from query if available_ingredients is not provided
            if (
                "available_ingredients" not in input_data
                or not input_data["available_ingredients"]
            ):
                query = input_data.get("query", "")
                if query:
                    ingredients = self._extract_ingredients_from_query(query)
                    if ingredients:
                        input_data["available_ingredients"] = ingredients
                        logger.info(
                            f"[ChefAgent] Extracted ingredients from query: {ingredients}"
                        )
                    else:
                        return AgentResponse(
                            success=False,
                            error="No ingredients found in query",
                            text="Nie mogę znaleźć składników w Twoim zapytaniu. Podaj konkretne składniki, np. 'kurczak, ryż, brokuły'",
                        )

            # Validate input
            validated_input = ChefAgentInput.model_validate(input_data)

            # Check ingredient availability in database
            db_session = input_data.get("db")
            ingredient_availability = await self._check_ingredient_availability(
                db_session, validated_input.available_ingredients
            )

            logger.info(
                f"[ChefAgent] Ingredient availability check: "
                f"Available: {ingredient_availability['available']}, "
                f"Missing: {ingredient_availability['missing']}, "
                f"Suggestions: {ingredient_availability['suggestions']}"
            )

            # Get user context from session
            user_context = None
            db_session = input_data.get("db")
            if db_session and hasattr(input_data, "get"):
                input_data.get("session_id", "default")
                try:
                    from core.mmlw_embedding_client import MMLWEmbeddingClient
                    from core.rag_integration import RAGDatabaseIntegration
                    from core.user_profile_rag import UserProfileRAG

                    # Initialize RAG components (normally these would be injected)
                    embedding_client = MMLWEmbeddingClient()
                    if (
                        not hasattr(embedding_client, "_model")
                        or embedding_client._model is None
                    ):
                        await embedding_client.initialize()

                    rag_integration = RAGDatabaseIntegration(embedding_client)
                    profile_rag = UserProfileRAG(rag_integration)

                    # Get user context for recipe query
                    query = f"przepis składniki {' '.join(validated_input.available_ingredients)}"
                    user_context = await profile_rag.get_user_context_for_query(
                        user_id="gui-user", query=query  # Default user for GUI
                    )

                    logger.info(
                        f"[ChefAgent] Retrieved user context: {user_context.get('has_profile', False)}"
                    )

                except Exception as e:
                    logger.warning(f"[ChefAgent] Could not retrieve user context: {e}")
                    user_context = None

            # Generate recipe with anti-hallucination protection
            response = await self._generate_recipe_with_validation(
                ingredients=validated_input.available_ingredients,
                dietary_restrictions=validated_input.dietary_restrictions,
                model=validated_input.model
                or "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
                validation_level=validated_input.validation_level,
                max_additional_ingredients=validated_input.max_ingredients_allowed,
                user_context=user_context,
                ingredient_availability=ingredient_availability,
            )

            # Add ingredient availability information to response
            if response.success and response.data:
                response.data.update(
                    {
                        "ingredient_availability": ingredient_availability,
                        "available_ingredients": ingredient_availability["available"],
                        "missing_ingredients": ingredient_availability["missing"],
                        "suggestions": ingredient_availability["suggestions"],
                    }
                )

            return response
        except ValidationError as ve:
            # Handle validation errors with Polish message
            if "available_ingredients" in str(ve) and "too_short" in str(ve):
                return AgentResponse(
                    success=False,
                    error="No ingredients provided",
                    text="Proszę podać składniki",
                )
            return AgentResponse(
                success=False,
                error=str(ve),
                text="Nieprawidłowe dane wejściowe",
            )
        except Exception as e:
            logger.error(f"Error in ChefAgent process: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                text=f"Przepraszam, wystąpił błąd: {e!s}",
            )

    def get_metadata(self) -> dict[str, Any]:
        """Return agent metadata including capabilities"""
        return {
            "name": self.name,
            "type": "chef",
            "capabilities": [
                "recipe_generation",
                "ingredient_analysis",
                "anti_hallucination_validation",
            ],
            "description": "Generates recipes based on available ingredients with anti-hallucination protection",
        }

    def get_dependencies(self) -> list[type]:
        """List of agent types this agent depends on"""
        return []

    def is_healthy(self) -> bool:
        """Check if agent is functioning properly"""
        return True

    def _extract_ingredients_from_query(self, query: str) -> list[str]:
        """Extract ingredients from a natural language query"""
        import re

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

    async def _generate_recipe_with_validation(
        self,
        ingredients: list[str],
        dietary_restrictions: str | None = None,
        model: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
        validation_level: ValidationLevel = ValidationLevel.STRICT,
        max_additional_ingredients: int = 3,
        user_context: dict | None = None,
        ingredient_availability: dict | None = None,
    ) -> AgentResponse:
        """
        Generate recipe with comprehensive anti-hallucination validation
        """
        if not ingredients:
            return AgentResponse(
                success=False,
                error="No ingredients provided",
                text="Proszę podać składniki",
            )

        try:
            # Przygotuj prompt z zaawansowanymi anty-halucynacyjnymi instrukcjami
            prompt = self._create_anti_hallucination_prompt(
                ingredients,
                dietary_restrictions,
                validation_level,
                user_context,
                ingredient_availability,
            )

            # Generuj przepis
            response = await self.llm_client.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt(validation_level),
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )

            # Stream the response chunks with proper validation
            full_response = ""
            async for chunk in response:
                # Validate chunk structure
                if not isinstance(chunk, dict):
                    logger.warning(f"Invalid chunk type: {type(chunk)}")
                    continue

                if "message" not in chunk:
                    logger.warning(f"Chunk missing 'message' key: {chunk}")
                    continue

                message = chunk["message"]
                if not isinstance(message, dict) or "content" not in message:
                    logger.warning(f"Invalid message structure: {message}")
                    continue

                content = message["content"]
                if not isinstance(content, str):
                    logger.warning(f"Invalid content type: {type(content)}")
                    continue

                full_response += content

            # ANTY-HALUCYNACYJNA WALIDACJA PO WYGENEROWANIU
            if full_response:
                validation_result = self.validator.validate_recipe_against_ingredients(
                    full_response,
                    ingredients,
                    validation_level,
                    max_additional_ingredients,
                )

                if not validation_result.is_valid:
                    logger.warning(
                        f"Recipe validation failed: {validation_result.recommendation}"
                    )

                    # Generate safe fallback response
                    safe_response = self._generate_safe_fallback_recipe(
                        ingredients, dietary_restrictions
                    )

                    return AgentResponse(
                        success=True,
                        text=safe_response,
                        data={
                            "ingredients": ingredients,
                            "dietary_restrictions": dietary_restrictions,
                            "validation_failed": True,
                            "validation_result": validation_result.__dict__,
                            "anti_hallucination": True,
                            "confidence": validation_result.confidence,
                        },
                    )

                # Recipe passed validation
                return AgentResponse(
                    success=True,
                    text=full_response,
                    data={
                        "ingredients": ingredients,
                        "dietary_restrictions": dietary_restrictions,
                        "validation_passed": True,
                        "validation_result": validation_result.__dict__,
                        "anti_hallucination": True,
                        "confidence": validation_result.confidence,
                    },
                )

            # If no response was generated, return error
            return AgentResponse(
                success=False,
                error="No recipe generated",
                text="Przepraszam, nie udało się wygenerować przepisu. Spróbuj ponownie.",
            )

        except Exception as e:
            logger.error(f"Error generating recipe: {e}")
            return AgentResponse(
                success=False,
                error=f"Błąd generowania przepisu: {e}",
                text="Przepraszam, nie udało się wygenerować przepisu. Spróbuj ponownie.",
            )

    def _create_anti_hallucination_prompt(
        self,
        ingredients: list[str],
        dietary_restrictions: str | None,
        validation_level: ValidationLevel,
        user_context: dict | None = None,
        ingredient_availability: dict | None = None,
    ) -> str:
        """Create anti-hallucination prompt based on validation level"""

        # Dodaj personalizację na podstawie profilu użytkownika
        personalization = ""
        if user_context and user_context.get("has_profile"):
            cooking_prefs = user_context.get("cooking_preferences", {})
            user_context.get("user_preferences", {})

            # Informacje osobiste
            if cooking_prefs.get("name"):
                personalization += f"\nOTWARCAM PRZEPIS DLA: {cooking_prefs['name']}\n"

            # Preferencje kulinarne
            if cooking_prefs.get("favorite_cuisines"):
                personalization += f"PREFEROWANE KUCHNIE: {', '.join(cooking_prefs['favorite_cuisines'])}\n"

            if cooking_prefs.get("spice_tolerance"):
                spice_map = {
                    "mild": "łagodne",
                    "medium": "średnie",
                    "hot": "ostre",
                    "very_hot": "bardzo ostre",
                }
                personalization += f"TOLERANCJA NA PRZYPRAWY: {spice_map.get(cooking_prefs['spice_tolerance'], 'średnie')}\n"

            if cooking_prefs.get("cooking_time_preference"):
                time_map = {
                    "quick": "szybkie (<30 min)",
                    "medium": "średnie (30-60 min)",
                    "long": "długie (>60 min)",
                }
                personalization += f"PREFEROWANY CZAS GOTOWANIA: {time_map.get(cooking_prefs['cooking_time_preference'], 'średnie')}\n"

            if cooking_prefs.get("available_appliances"):
                personalization += f"DOSTĘPNE URZĄDZENIA: {', '.join(cooking_prefs['available_appliances'])}\n"

            if cooking_prefs.get("cooking_methods"):
                personalization += f"PREFEROWANE METODY: {', '.join(cooking_prefs['cooking_methods'])}\n"

            # Ograniczenia dietetyczne z profilu
            profile_restrictions = cooking_prefs.get("dietary_restrictions", [])
            profile_allergies = cooking_prefs.get("allergies", [])

            if profile_restrictions:
                personalization += (
                    f"OGRANICZENIA DIETETYCZNE: {', '.join(profile_restrictions)}\n"
                )
            if profile_allergies:
                personalization += f"ALERGIE: {', '.join(profile_allergies)}\n"

            # Dodatkowe preferencje
            if cooking_prefs.get("healthy_eating_focus"):
                personalization += "NACISK NA ZDROWE ODŻYWIANIE\n"
            if cooking_prefs.get("budget_conscious"):
                personalization += (
                    "ŚWIADOMY BUDŻETU - preferuj proste, ekonomiczne rozwiązania\n"
                )

        # Add ingredient availability information to prompt
        availability_info = ""
        if ingredient_availability:
            available = ingredient_availability.get("available", [])
            missing = ingredient_availability.get("missing", [])
            suggestions = ingredient_availability.get("suggestions", [])

            if available:
                availability_info += f"\nPOTWIERDZONE W BAZIE: {', '.join(available)}"
            if missing:
                availability_info += f"\nBRAKUJE W BAZIE: {', '.join(missing)}"
            if suggestions:
                availability_info += f"\nSUGESTIE ZAMIENNIKÓW: {', '.join(suggestions)}"

        base_prompt = f"""Jesteś doświadczonym szefem kuchni. Stwórz przepis na danie używając TYLKO podanych składników.
{personalization}
DOSTĘPNE SKŁADNIKI: {', '.join(ingredients)}{availability_info}

KRYTYCZNE ZASADY:
- Używaj TYLKO podanych składników
- NIE dodawaj żadnych dodatkowych składników
- Jeśli brakuje składnika, pomiń go lub zastąp dostępnym
- Bądź kreatywny z tym co masz
- Podaj prosty, praktyczny przepis
- UWZGLĘDNIJ preferencje użytkownika podane powyżej

{f"DIETARY RESTRICTIONS: {dietary_restrictions}" if dietary_restrictions else ""}"""

        if validation_level == ValidationLevel.STRICT:
            base_prompt += """

DODATKOWE ZASADY (ŚCISŁA WALIDACJA):
- NIE używaj żadnych składników poza podanymi
- Jeśli nie masz wystarczających składników, stwórz prosty przepis z tym co jest
- Nie wymyślaj dodatkowych składników
- Skup się na prostocie i dostępności"""

        elif validation_level == ValidationLevel.MODERATE:
            base_prompt += """

DODATKOWE ZASADY (UMIARKOWANA WALIDACJA):
- Możesz użyć maksymalnie 3 dodatkowych podstawowych składników (sól, pieprz, olej)
- Jeśli potrzebujesz więcej składników, wyraźnie to zaznacz
- Priorytet: użyj podanych składników"""

        else:  # LENIENT
            base_prompt += """

DODATKOWE ZASADY (ŁAGODNA WALIDACJA):
- Możesz użyć dodatkowych podstawowych składników
- Zaznacz które składniki mogą być potrzebne
- Skup się na smaku i prostocie"""

        base_prompt += "\n\nPrzepis:"
        return base_prompt

    def _get_system_prompt(self, validation_level: ValidationLevel) -> str:
        """Get system prompt based on validation level"""

        base_system = (
            "Jesteś pomocnym szefem kuchni. Generuj przepisy z podanych składników."
        )

        if validation_level == ValidationLevel.STRICT:
            return (
                base_system
                + " Przestrzegaj ścisłych zasad - używaj TYLKO podanych składników."
            )

        if validation_level == ValidationLevel.MODERATE:
            return (
                base_system
                + " Możesz użyć ograniczonej liczby dodatkowych podstawowych składników."
            )

        # LENIENT
        return (
            base_system
            + " Możesz użyć dodatkowych składników, ale zaznacz je wyraźnie."
        )

    def _generate_safe_fallback_recipe(
        self, ingredients: list[str], dietary_restrictions: str | None
    ) -> str:
        """Generate a safe fallback recipe when validation fails"""

        fallback = f"""Przepis z dostępnych składników:

SKŁADNIKI: {', '.join(ingredients)}

PRZYGOTOWANIE:
1. Przygotuj wszystkie dostępne składniki
2. Możesz je ugotować, upiec lub usmażyć według własnych preferencji
3. Użyj podstawowych przypraw (sól, pieprz) jeśli dostępne
4. Skup się na prostocie i smaku

{f"UWAGA DIETETYCZNA: {dietary_restrictions}" if dietary_restrictions else ""}

To bezpieczny przepis wykorzystujący tylko podane składniki."""

        return fallback

    async def generate_recipe_idea(
        self, db: Any, model: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
    ) -> AgentResponse:
        """
        Generates recipe ideas based on available pantry items with
        anti-hallucination protection.

        Args:
            db: Database session
            model: LLM model to use for generating the recipe
                (default: SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M)

        Returns:
            AgentResponse with recipe suggestion or error message
        """
        # Get available products from pantry
        products = await get_available_products_from_pantry(db)

        if not products:
            return AgentResponse(
                success=True,
                text="Twoja spiżarnia jest pusta!",
                message="Pantry is empty",
            )

        # Prepare list of available products for the prompt
        product_list = "\n".join(
            f"- {product.name} (ID: {product.id})" for product in products
        )

        # Create LLM prompt with anti-hallucination instructions
        prompt = (
            "Mam następujące produkty w spiżarni:\n"
            f"{product_list}\n\n"
            "Proszę zaproponuj prosty przepis wykorzystujący TYLKO te produkty. "
            "NIE dodawaj żadnych dodatkowych składników.\n"
            "Odpowiedz w formacie:\n"
            "PRZEPIS: [treść przepisu]\n"
            "UŻYTE SKŁADNIKI: [lista nazw użytych składników]"
        )

        try:
            # Call LLM with specified model and get the response
            full_response = ""
            async for chunk in await self.llm_client.generate_stream(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym szefem kuchni. Używaj TYLKO podanych składników.",
                    },
                    {"role": "user", "content": prompt},
                ],
            ):
                # Validate chunk structure
                if not isinstance(chunk, dict):
                    logger.warning(f"Invalid chunk type: {type(chunk)}")
                    continue

                if "message" not in chunk:
                    logger.warning(f"Chunk missing 'message' key: {chunk}")
                    continue

                message = chunk["message"]
                if not isinstance(message, dict) or "content" not in message:
                    logger.warning(f"Invalid message structure: {message}")
                    continue

                content = message["content"]
                if not isinstance(content, str):
                    logger.warning(f"Invalid content type: {type(content)}")
                    continue

                full_response += content

            # After streaming, validate the response
            if full_response:
                validation_result = self.validator.validate_recipe_against_ingredients(
                    full_response, [p.name for p in products], ValidationLevel.STRICT
                )

                if not validation_result.is_valid:
                    logger.warning(
                        f"Recipe idea validation failed: {validation_result.recommendation}"
                    )
                    # Generate safe fallback
                    safe_idea = self._generate_safe_recipe_idea(products)
                    full_response = (
                        f"{full_response}\n\n[UWAGA: Poprawiony przepis]\n{safe_idea}"
                    )

            # Parse the full response to extract used ingredients
            used_ingredients = []
            if "UŻYTE SKŁADNIKI:" in full_response:
                parts = full_response.split("UŻYTE SKŁADNIKI:")
                ingredient_names = [
                    name.strip() for name in parts[1].split(",") if name.strip()
                ]
                used_ingredients = [
                    {"id": p.id, "name": p.name}
                    for p in products
                    if p.name in ingredient_names
                ]
            logger.info(f"Used ingredients identified: {used_ingredients}")

            return AgentResponse(
                success=True,
                text=full_response,
                message="Recipe generated successfully.",
                data={
                    "used_ingredients": used_ingredients,
                    "validation_result": (
                        validation_result.__dict__
                        if "validation_result" in locals()
                        else None
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Error in recipe idea generation: {e}")
            return AgentResponse(
                success=False, error=str(e), text=f"Przepraszam, wystąpił błąd: {e!s}"
            )

    def _generate_safe_recipe_idea(self, products: list[Any]) -> str:
        """Generate a safe recipe idea when validation fails"""
        product_names = [p.name for p in products]

        return f"""Bezpieczny przepis z dostępnych składników:

SKŁADNIKI: {', '.join(product_names)}

PRZYGOTOWANIE:
1. Przygotuj wszystkie dostępne składniki
2. Możesz je ugotować, upiec lub usmażyć
3. Użyj podstawowych przypraw jeśli dostępne
4. Skup się na prostocie i smaku

To przepis wykorzystujący tylko podane składniki."""
