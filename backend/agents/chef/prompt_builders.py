"""
Prompt Building Module

Moduł do budowania promptów dla ChefAgent.
"""

from core.anti_hallucination_system import ValidationLevel


class PromptBuilder:
    """Builder promptów dla generowania przepisów"""

    @staticmethod
    def create_anti_hallucination_prompt(
        ingredients: list[str],
        dietary_restrictions: str | None,
        validation_level: ValidationLevel,
        user_context: dict | None = None,
        ingredient_availability: dict | None = None,
    ) -> str:
        """Create anti-hallucination prompt based on validation level.
        
        Args:
            ingredients: Lista dostępnych składników.
            dietary_restrictions: Ograniczenia dietetyczne użytkownika (opcjonalne).
            validation_level: Poziom walidacji przeciw halucynacjom.
            user_context: Kontekst użytkownika z preferencjami (opcjonalne).
            ingredient_availability: Dostępność składników w spiżarni (opcjonalne).
            
        Returns:
            Sformatowany prompt dla LLM z instrukcjami przeciw halucynacjom.
        """

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

    @staticmethod
    def get_system_prompt(validation_level: ValidationLevel) -> str:
        """Get system prompt based on validation level.
        
        Args:
            validation_level: Poziom walidacji przeciw halucynacjom.
            
        Returns:
            Systemowy prompt dostosowany do poziomu walidacji.
        """

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