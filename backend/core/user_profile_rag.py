"""
User Profile RAG Integration
Moduł do integracji profilu użytkownika z systemem RAG dla personalizacji odpowiedzi
"""

import logging
from typing import Any

from core.rag_integration import RAGDatabaseIntegration
from models.user_profile import CookingPreferences, UserProfile

logger = logging.getLogger(__name__)


class UserProfileRAG:
    """Zarządza integracją profilu użytkownika z systemem RAG"""

    def __init__(self, rag_integration: RAGDatabaseIntegration):
        self.rag_integration = rag_integration

    async def create_user_profile_document(
        self, user_profile: UserProfile, session_id: str
    ) -> dict[str, Any]:
        """
        Tworzy dokument RAG z profilu użytkownika dla personalizacji odpowiedzi

        Args:
            user_profile: Profil użytkownika
            session_id: ID sesji dla powiązania

        Returns:
            Dict z informacją o stworzonym dokumencie
        """
        try:
            preferences = user_profile.get_preferences()
            schedule = user_profile.get_schedule()
            cooking_prefs = preferences.cooking

            # Stwórz dokument z profilem użytkownika
            profile_content = self._generate_profile_text(
                cooking_prefs, preferences, schedule
            )

            # Metadane dokumentu
            metadata = {
                "type": "user_profile",
                "user_id": user_profile.user_id,
                "session_id": session_id,
                "category": "personal_info",
                "created_by": "user_profile_rag",
                "cooking_preferences": cooking_prefs.model_dump(),
                "user_preferences": {
                    "formality": preferences.formality,
                    "topics_of_interest": user_profile.topics_of_interest,
                },
            }

            # Dodaj do systemu RAG przez rag_processor
            chunks = await self.rag_integration.rag_processor.process_document(
                content=profile_content,
                source_id=f"user_profile_{user_profile.user_id}",
                metadata=metadata,
            )

            logger.info(
                f"Created user profile RAG document for user {user_profile.user_id}"
            )
            return {"document_id": chunks[0]["chunk_id"] if chunks else None}

        except Exception as e:
            logger.error(f"Error creating user profile RAG document: {e}")
            raise

    def _generate_profile_text(
        self, cooking_prefs: CookingPreferences, preferences: Any, schedule: Any
    ) -> str:
        """Generuje tekst profilu użytkownika dla systemu RAG"""

        profile_parts = []

        # Podstawowe informacje
        if cooking_prefs.name:
            profile_parts.append(f"Imię użytkownika: {cooking_prefs.name}")
        if cooking_prefs.age:
            profile_parts.append(f"Wiek: {cooking_prefs.age} lat")
        if cooking_prefs.occupation:
            profile_parts.append(f"Zawód: {cooking_prefs.occupation}")

        # Preferencje kulinarne
        if cooking_prefs.favorite_cuisines:
            profile_parts.append(
                f"Ulubione kuchnie: {', '.join(cooking_prefs.favorite_cuisines)}"
            )

        if cooking_prefs.dietary_restrictions:
            profile_parts.append(
                f"Ograniczenia dietetyczne: {', '.join(cooking_prefs.dietary_restrictions)}"
            )

        if cooking_prefs.allergies:
            profile_parts.append(
                f"Alergie pokarmowe: {', '.join(cooking_prefs.allergies)}"
            )

        profile_parts.append(
            f"Tolerancja na ostre przyprawy: {cooking_prefs.spice_tolerance}"
        )

        # Styl gotowania
        if cooking_prefs.cooking_style:
            profile_parts.append(
                f"Styl gotowania: {', '.join(cooking_prefs.cooking_style)}"
            )

        if cooking_prefs.preferred_meal_types:
            profile_parts.append(
                f"Preferowane typy posiłków: {', '.join(cooking_prefs.preferred_meal_types)}"
            )

        profile_parts.append(
            f"Preferowany czas gotowania: {cooking_prefs.cooking_time_preference}"
        )

        # Sprzęt kuchenny
        if cooking_prefs.available_appliances:
            profile_parts.append(
                f"Dostępne urządzenia kuchenne: {', '.join(cooking_prefs.available_appliances)}"
            )

        if cooking_prefs.cooking_methods:
            profile_parts.append(
                f"Preferowane metody gotowania: {', '.join(cooking_prefs.cooking_methods)}"
            )

        # Dodatkowe preferencje
        additional_prefs = []
        if cooking_prefs.budget_conscious:
            additional_prefs.append("świadomy budżetu")
        if cooking_prefs.healthy_eating_focus:
            additional_prefs.append("skupiony na zdrowym odżywianiu")
        if cooking_prefs.environmental_conscious:
            additional_prefs.append("świadomy ekologicznie")
        if cooking_prefs.loves_trying_new_things:
            additional_prefs.append("lubi próbować nowych rzeczy")

        if additional_prefs:
            profile_parts.append(f"Dodatkowe cechy: {', '.join(additional_prefs)}")

        # Harmonogram (podstawowe info)
        profile_parts.append(f"Strefa czasowa: {schedule.time_zone}")
        profile_parts.append(f"Pora lunchu: {schedule.lunch_time}")

        return "\n".join(profile_parts)

    async def update_user_profile_document(
        self, user_profile: UserProfile, session_id: str
    ) -> dict[str, Any]:
        """
        Aktualizuje dokument RAG z profilem użytkownika

        Args:
            user_profile: Zaktualizowany profil użytkownika
            session_id: ID sesji

        Returns:
            Dict z informacją o aktualizacji
        """
        try:
            # Usuń stary dokument profilu
            await self.remove_user_profile_document(user_profile.user_id)

            # Dodaj nowy
            return await self.create_user_profile_document(user_profile, session_id)

        except Exception as e:
            logger.error(f"Error updating user profile RAG document: {e}")
            raise

    async def remove_user_profile_document(self, user_id: str) -> bool:
        """
        Usuwa dokument RAG z profilem użytkownika

        Args:
            user_id: ID użytkownika

        Returns:
            True jeśli usunięto, False jeśli nie znaleziono
        """
        try:
            # Znajdź dokumenty profilu użytkownika
            query_result = await self.rag_integration.search_documents(
                query=f"user_profile_{user_id}",
                metadata_filter={"type": "user_profile", "user_id": user_id},
            )

            removed_count = 0
            for doc in query_result.get("documents", []):
                if doc.get("metadata", {}).get("type") == "user_profile":
                    doc_id = doc.get("id")
                    if doc_id:
                        await self.rag_integration.remove_document(doc_id)
                        removed_count += 1

            logger.info(
                f"Removed {removed_count} user profile documents for user {user_id}"
            )
            return removed_count > 0

        except Exception as e:
            logger.error(f"Error removing user profile RAG document: {e}")
            return False

    async def get_user_context_for_query(
        self, user_id: str, query: str, max_results: int = 1
    ) -> dict[str, Any]:
        """
        Pobiera kontekst użytkownika dla zapytania

        Args:
            user_id: ID użytkownika
            query: Zapytanie użytkownika
            max_results: Maksymalna liczba wyników

        Returns:
            Dict z kontekstem użytkownika
        """
        try:
            # Wyszukaj dokumenty profilu użytkownika
            search_result = await self.rag_integration.search_documents(
                query=query,
                metadata_filter={"type": "user_profile", "user_id": user_id},
                max_results=max_results,
            )

            if not search_result.get("documents"):
                return {"has_profile": False, "context": ""}

            # Wyciągnij najlepiej pasujący dokument
            best_match = search_result["documents"][0]

            return {
                "has_profile": True,
                "context": best_match.get("content", ""),
                "cooking_preferences": best_match.get("metadata", {}).get(
                    "cooking_preferences", {}
                ),
                "user_preferences": best_match.get("metadata", {}).get(
                    "user_preferences", {}
                ),
                "relevance_score": best_match.get("score", 0.0),
            }

        except Exception as e:
            logger.error(f"Error getting user context for query: {e}")
            return {"has_profile": False, "context": "", "error": str(e)}


def create_sample_user_profile() -> str:
    """
    Tworzy przykładowy profil użytkownika do demonstracji

    Returns:
        JSON string z przykładowym profilem
    """
    sample_cooking_prefs = CookingPreferences(
        name="Marcin",
        age=35,
        occupation="Programista",
        favorite_cuisines=["polska", "włoska", "azjatycka"],
        dietary_restrictions=["bezlaktozowy"],
        allergies=[],
        spice_tolerance="medium",
        cooking_style=["szybko", "praktycznie"],
        preferred_meal_types=["jednogarnkowe", "dania główne", "zupy"],
        cooking_time_preference="quick",
        available_appliances=["piekarnik", "mikrofala", "patelnia", "garnek"],
        cooking_methods=["smażenie", "pieczenie", "gotowanie"],
        budget_conscious=True,
        healthy_eating_focus=True,
        environmental_conscious=False,
        loves_trying_new_things=True,
    )

    return sample_cooking_prefs.model_dump_json(indent=2)


# Funkcja pomocnicza do łatwego użycia
async def setup_user_profile_in_rag(
    user_id: str,
    session_id: str,
    cooking_preferences: dict[str, Any],
    rag_integration: RAGDatabaseIntegration,
) -> dict[str, Any]:
    """
    Łatwa funkcja do konfiguracji profilu użytkownika w RAG

    Args:
        user_id: ID użytkownika
        session_id: ID sesji
        cooking_preferences: Słownik z preferencjami kulinarnymi
        rag_integration: Instancja RAG integration

    Returns:
        Dict z wynikiem operacji
    """
    try:
        # Stwórz tymczasowy profil użytkownika
        from models.user_profile import UserPreferences, UserProfile

        # Konwertuj cooking_preferences na obiekt CookingPreferences
        cooking_prefs = CookingPreferences.model_validate(cooking_preferences)

        # Stwórz UserPreferences z cooking preferences
        user_prefs = UserPreferences(cooking=cooking_prefs)

        # Stwórz tymczasowy UserProfile (nie zapisujemy do bazy)
        temp_profile = UserProfile(
            user_id=user_id, session_id=session_id, preferences=user_prefs.model_dump()
        )

        # Dodaj do RAG
        profile_rag = UserProfileRAG(rag_integration)
        result = await profile_rag.create_user_profile_document(
            temp_profile, session_id
        )

        return {
            "success": True,
            "message": "Profil użytkownika został dodany do systemu RAG",
            "document_id": result.get("document_id"),
            "profile_summary": cooking_preferences,
        }

    except Exception as e:
        logger.error(f"Error setting up user profile in RAG: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Nie udało się dodać profilu do systemu RAG",
        }
