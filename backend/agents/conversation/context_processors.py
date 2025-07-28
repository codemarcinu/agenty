"""
Context Processing Module

Moduł do przetwarzania kontekstu z różnych źródeł (RAG, internet) 
dla GeneralConversationAgent.
"""

import asyncio
import logging

import numpy as np

from core.cache_manager import cached_async, internet_cache, rag_cache
from core.mmlw_embedding_client import mmlw_client
# Perplexity API removed - using DuckDuckGo fallback
from core.vector_store import vector_store
from integrations.web_search import web_search

logger = logging.getLogger(__name__)


class ContextProcessor:
    """Procesor kontekstu z różnych źródeł"""

    @staticmethod
    @cached_async(rag_cache)
    async def get_rag_context(query: str) -> tuple[str, float]:
        """Pobiera kontekst z RAG i ocenia jego pewność.
        
        Args:
            query: Zapytanie użytkownika do wyszukania w RAG.
            
        Returns:
            Tuple zawierający kontekst (str) i ocenę pewności (float 0.0-1.0).
            
        Raises:
            Exception: W przypadku błędu podczas pobierania kontekstu.
        """
        try:
            # 1. Stwórz wektor dla zapytania
            query_embedding_list = await mmlw_client.embed_text(query)
            if not query_embedding_list:
                logger.warning("Failed to generate query embedding for RAG context.")
                return "", 0.0
            query_embedding = np.array([query_embedding_list], dtype=np.float32)

            # 2. Przeszukaj bazę wektorową (bez min_similarity)
            # Zwiększamy k, aby mieć więcej kandydatów do filtrowania
            if vector_store is not None:
                search_results = await vector_store.search(query_embedding, k=5)
            else:
                logger.warning("vector_store is not available")
                return "", 0.0

            if not search_results:
                return "", 0.0

            # 3. Ręcznie odfiltruj wyniki poniżej progu podobieństwa
            min_similarity_threshold = 0.7
            filtered_results = [
                (doc, sim)
                for doc, sim in search_results
                if sim >= min_similarity_threshold
            ]

            if not filtered_results:
                return "", 0.0

            # 4. Przetwórz i sformatuj odfiltrowane wyniki
            avg_confidence = sum(sim for _, sim in filtered_results) / len(
                filtered_results
            )

            context_parts = []
            if filtered_results:
                doc_texts = [
                    f"- {doc.content} (Źródło: {doc.metadata.get('filename', 'Brak nazwy')})"
                    for doc, sim in filtered_results
                    if doc.content
                ]
                if doc_texts:
                    context_parts.append("Dokumenty:\n" + "\n".join(doc_texts[:2]))

            return "\n\n".join(context_parts) if context_parts else "", avg_confidence

        except Exception as e:
            logger.warning(f"Error getting RAG context: {e!s}")
            return "", 0.0

    @staticmethod
    @cached_async(internet_cache)
    async def get_internet_context(query: str, use_perplexity: bool) -> str:
        """Pobiera informacje z internetu z weryfikacją wiedzy.
        
        Args:
            query: Zapytanie do wyszukania w internecie.
            use_perplexity: Czy użyć Perplexity AI zamiast zwykłego wyszukiwania.
            
        Returns:
            Sformatowany kontekst z internetu lub pusty string w przypadku błędu.
            
        Raises:
            Exception: W przypadku błędu podczas pobierania danych z internetu.
        """
        try:
            # Perplexity API removed - using web_search fallback
            if web_search is not None:
                search_results = await web_search.search(query, max_results=3)
                if search_results:
                    return "Informacje z internetu:\n" + "\n".join(
                        [
                            f"**{result.get('title', 'Brak tytułu')}**\n{result.get('snippet', 'Brak opisu')}\nŹródło: {result.get('url', 'Brak URL')}"
                            for result in search_results[:2]
                        ]
                    )
            else:
                logger.warning("web_search is not available")
            return ""

        except Exception as e:
            logger.warning(f"Error getting internet context: {e!s}")
            return ""

    @staticmethod
    @cached_async(rag_cache)  # Cache RAG results for 1 hour
    async def get_rag_results(query: str) -> list[dict[str, str]]:
        """Get results from RAG system with caching.
        
        Args:
            query: The query string to search for in the RAG system.
            
        Returns:
            List of dictionaries containing RAG results with keys like 'content', 'metadata'.
            
        Raises:
            Exception: If there's an error accessing the RAG system.
        """
        try:
            # Placeholder for actual RAG implementation
            # In a real system, this would query a vector database
            logger.info(f"Getting RAG results for: {query}")
            await asyncio.sleep(0.1)  # Simulate some processing time
            return []  # Return empty list as placeholder
        except Exception as e:
            logger.error(f"Error getting RAG results: {e!s}")
            return []

    @staticmethod
    @cached_async(internet_cache)  # Cache internet results for 30 minutes
    async def get_internet_results(query: str) -> list[dict[str, str]]:
        """Get results from internet search with caching.
        
        Args:
            query: The query string to search for on the internet.
            
        Returns:
            List of dictionaries containing search results with keys like 'title', 'content', 'url'.
            
        Raises:
            Exception: If there's an error during internet search.
        """
        try:
            logger.info(f"Getting internet results for: {query}")
            # Użyj web_search jako obiektu, nie funkcji
            if web_search is not None:
                results = await web_search.search(query, max_results=3)
                return results if results else []
            else:
                logger.warning("web_search is not available")
                return []
        except Exception as e:
            logger.error(f"Error getting internet results: {e!s}")
            return []

    @staticmethod
    def combine_context(
        rag_results: list[dict[str, str]], internet_results: list[dict[str, str]]
    ) -> list[dict[str, str]]:
        """Combine context from RAG and internet search.
        
        Args:
            rag_results: List of results from RAG system.
            internet_results: List of results from internet search.
            
        Returns:
            Combined list of context results, with RAG results prioritized first.
        """
        # Simple combination strategy: RAG results first, then internet
        combined = []

        # Add RAG results if available
        if rag_results:
            combined.extend(rag_results)

        # Add internet results if available
        if internet_results:
            combined.extend(internet_results)

        return combined

    @staticmethod
    def format_context_for_llm(context: list[dict[str, str]]) -> str:
        """Format context for LLM input.
        
        Args:
            context: List of context items with title, content, and optional url keys.
            
        Returns:
            Formatted string ready for LLM consumption, or empty string if no context.
        """
        if not context:
            return ""

        formatted = "Oto informacje, które mogą być pomocne:\n\n"

        for i, item in enumerate(context, 1):
            title = item.get("title", f"Źródło {i}")
            content = item.get("content", "")
            url = item.get("url", "")

            formatted += f"--- {title} ---\n"
            formatted += f"{content}\n"
            if url:
                formatted += f"Źródło: {url}\n"
            formatted += "\n"

        return formatted

    @staticmethod
    def prepare_messages(
        query: str, conversation_history: list[dict[str, str]], context: str
    ) -> list[dict[str, str]]:
        """Prepare messages for LLM with optimized context and conversation history.
        
        Args:
            query: Current user query.
            conversation_history: Previous conversation messages.
            context: Additional context information to include.
            
        Returns:
            List of formatted messages ready for LLM with system message, 
            recent history, and current query.
        """
        messages = []

        # Zoptymalizowany system message
        system_message = (
            "Jesteś asystentem AI FoodSave. "
            "ODPOWIADAJ ZAWSZE W JĘZYKU POLSKIM. "
            "Bądź pomocny i zwięzły. "
            "Maksymalnie 2-3 zdania. "
            "Unikaj formatowania i list."
        )

        if context:
            system_message += "\n\nKontekst:\n" + context

        messages.append({"role": "system", "content": system_message})

        # Dodaj historię konwersacji (ostatnie 3 wiadomości)
        if conversation_history:
            recent_history = conversation_history[-3:]
            for msg in recent_history:
                if msg.get("role") in ["user", "assistant"]:
                    messages.append(msg)

        # Dodaj aktualne zapytanie
        messages.append({"role": "user", "content": query})

        return messages