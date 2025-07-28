"""
RAG Integration Module

This module integrates the existing database (receipts, pantry, meals) with the RAG system
by converting database records into searchable documents.
"""

from datetime import datetime
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud import get_available_products
from core.rag_document_processor import RAGDocumentProcessor
from models.conversation import Conversation
from services.shopping_service import get_shopping_trips

logger = logging.getLogger(__name__)


class RAGDatabaseIntegration:
    """
    Integrates database data with RAG system by converting records to searchable documents
    """

    def __init__(self, rag_processor: RAGDocumentProcessor) -> None:
        self.rag_processor = rag_processor

    async def sync_receipts_to_rag(self, db: AsyncSession) -> dict[str, Any]:
        """
        Synchronize all receipts from database to RAG system

        Args:
            db: Database session

        Returns:
            Summary of synchronization results
        """
        try:
            # Get all shopping trips with products
            trips = await get_shopping_trips(db, limit=1000)

            # Zamień ORM na dict, aby nie trzymać referencji do sesji
            trips_data = []
            for trip in trips:
                trip_dict = {
                    "id": trip.id,
                    "store_name": trip.store_name,
                    "trip_date": trip.trip_date,
                    "total_amount": trip.total_amount,
                    "products": [
                        {
                            "name": p.name,
                            "quantity": p.quantity,
                            "unit_price": p.unit_price,
                            "category": getattr(p, "category", None),
                        }
                        for p in getattr(trip, "products", [])
                    ],
                }
                trips_data.append(trip_dict)

            total_chunks = 0
            processed_trips = 0

            for trip in trips_data:
                # Create document content from trip
                content = self._format_receipt_content(trip)
                metadata = self._create_receipt_metadata(trip)

                # Process with RAG
                chunks = await self.rag_processor.process_document(
                    content=content,
                    source_id=f"receipt_{trip['id']}",
                    metadata=metadata,
                )

                total_chunks += len(chunks)
                processed_trips += 1

            return {
                "success": True,
                "processed_trips": processed_trips,
                "total_chunks": total_chunks,
                "message": f"Successfully synced {processed_trips} receipts to RAG",
            }

        except Exception as e:
            logger.error(f"Error syncing receipts to RAG: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed_trips": 0,
                "total_chunks": 0,
            }

    async def sync_pantry_to_rag(self, db: AsyncSession) -> dict[str, Any]:
        """
        Synchronize pantry state to RAG system

        Args:
            db: Database session

        Returns:
            Summary of synchronization results
        """
        try:
            products = await get_available_products(db)
            # Zamień ORM na dict
            products_data = [
                {
                    "name": p.name,
                    "quantity": p.quantity,
                    "expiration_date": getattr(p, "expiration_date", None),
                    "category": getattr(p, "category", None),
                }
                for p in products
            ]
            if not products_data:
                return {
                    "success": True,
                    "processed_products": 0,
                    "total_chunks": 0,
                    "message": "No products in pantry to sync",
                }

            # Create document content from pantry
            content = self._format_pantry_content(products_data)
            metadata = self._create_pantry_metadata(products_data)

            # Process with RAG
            chunks = await self.rag_processor.process_document(
                content=content, source_id="pantry_state", metadata=metadata
            )

            return {
                "success": True,
                "processed_products": len(products_data),
                "total_chunks": len(chunks),
                "message": f"Successfully synced {len(products_data)} products to RAG",
            }

        except Exception as e:
            logger.error(f"Error syncing pantry to RAG: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed_products": 0,
                "total_chunks": 0,
            }

    async def sync_conversations_to_rag(self, db: AsyncSession) -> dict[str, Any]:
        """
        Synchronize conversation history to RAG system

        Args:
            db: Database session

        Returns:
            Summary of synchronization results
        """
        try:
            stmt = (
                select(Conversation).order_by(Conversation.created_at.desc()).limit(100)
            )
            result = await db.execute(stmt)
            conversations = result.scalars().all()
            # Zamień ORM na dict - extract messages properly
            conversations_data = []
            for c in conversations:
                # Get user and assistant messages from messages relationship
                user_messages = [m.content for m in c.messages if m.role == "user"]
                assistant_messages = [
                    m.content for m in c.messages if m.role == "assistant"
                ]

                # Create conversation data with first user/assistant message pair
                user_message = user_messages[0] if user_messages else ""
                assistant_response = assistant_messages[0] if assistant_messages else ""

                conversations_data.append(
                    {
                        "id": c.id,
                        "created_at": c.created_at,
                        "user_message": user_message,
                        "assistant_response": assistant_response,
                        "intent_type": None,  # Not available in new model
                        "session_id": c.session_id,
                    }
                )

            total_chunks = 0
            processed_conversations = 0

            for conv in conversations_data:
                # Create document content from conversation
                content = self._format_conversation_content(conv)
                metadata = self._create_conversation_metadata(conv)

                # Process with RAG
                chunks = await self.rag_processor.process_document(
                    content=content,
                    source_id=f"conversation_{conv['id']}",
                    metadata=metadata,
                )

                total_chunks += len(chunks)
                processed_conversations += 1

            return {
                "success": True,
                "processed_conversations": processed_conversations,
                "total_chunks": total_chunks,
                "message": f"Successfully synced {processed_conversations} conversations to RAG",
            }

        except Exception as e:
            logger.error(f"Error syncing conversations to RAG: {e}")
            return {
                "success": False,
                "error": str(e),
                "processed_conversations": 0,
                "total_chunks": 0,
            }

    async def sync_all_to_rag(self, db: AsyncSession) -> dict[str, Any]:
        """
        Synchronize all database data to RAG system

        Args:
            db: Database session

        Returns:
            Summary of all synchronization results
        """
        results = {}

        # Sync receipts
        results["receipts"] = await self.sync_receipts_to_rag(db)

        # Sync pantry
        results["pantry"] = await self.sync_pantry_to_rag(db)

        # Sync conversations
        results["conversations"] = await self.sync_conversations_to_rag(db)

        # Calculate totals
        total_chunks = sum(
            r.get("total_chunks", 0) for r in results.values() if r.get("success")
        )
        all_successful = all(r.get("success", False) for r in results.values())

        return {
            "success": all_successful,
            "results": results,
            "total_chunks": total_chunks,
            "message": f"Sync completed with {total_chunks} total chunks",
        }

    async def list_rag_documents(self, db: AsyncSession) -> list[dict[str, Any]]:
        """
        List all RAG documents with their metadata

        Args:
            db: Database session

        Returns:
            List of document information
        """
        try:
            # For now, return an empty list since we don't have a proper document storage
            # In a full implementation, this would query the vector store or database
            return []
        except Exception as e:
            logger.error(f"Error listing RAG documents: {e}")
            return []

    async def search_documents_in_rag(
        self,
        query: str,
        k: int = 5,
        filter_type: str | None = None,
        min_similarity: float = 0.65,
    ) -> dict[str, Any]:
        """
        Search documents in the RAG system

        Args:
            query: Search query
            k: Number of results to return
            filter_type: Optional filter by document type
            min_similarity: Minimum similarity threshold

        Returns:
            Search results
        """
        try:
            # Use the vector store to search by text
            results = await self.rag_processor.vector_store.search_text(
                query=query,
                k=k,
                min_similarity=min_similarity,
            )
            return {"chunks": results, "total": len(results)}
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return {"chunks": [], "total": 0, "error": str(e)}

    async def delete_document_from_rag(self, source_id: str) -> bool:
        """
        Delete a document from the RAG system by source ID

        Args:
            source_id: Source identifier

        Returns:
            True if deleted successfully
        """
        try:
            # For now, return True since we don't have delete_by_metadata
            # In a full implementation, this would delete from the vector store
            logger.info(f"Would delete document with source_id: {source_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False

    async def delete_rag_document_by_id(
        self, document_id: str, db: AsyncSession
    ) -> bool:
        """
        Delete a specific RAG document by ID

        Args:
            document_id: Document ID
            db: Database session

        Returns:
            True if deleted successfully
        """
        try:
            # For now, return True since we don't have a proper document storage
            # In a full implementation, this would delete from the vector store
            return True
        except Exception as e:
            logger.error(f"Error deleting RAG document: {e}")
            return False

    async def bulk_delete_rag_documents(
        self, document_ids: list[str], db: AsyncSession
    ) -> int:
        """
        Delete multiple RAG documents by ID

        Args:
            document_ids: List of document IDs
            db: Database session

        Returns:
            Number of documents deleted
        """
        try:
            # For now, return the count since we don't have a proper document storage
            # In a full implementation, this would delete from the vector store
            return len(document_ids)
        except Exception as e:
            logger.error(f"Error bulk deleting RAG documents: {e}")
            return 0

    async def move_rag_document(
        self, document_id: str, new_directory_path: str, db: AsyncSession
    ) -> bool:
        """
        Move a RAG document to a new directory

        Args:
            document_id: Document ID
            new_directory_path: New directory path
            db: Database session

        Returns:
            True if moved successfully
        """
        try:
            # For now, return True since we don't have a proper document storage
            # In a full implementation, this would update the vector store metadata
            return True
        except Exception as e:
            logger.error(f"Error moving RAG document: {e}")
            return False

    async def bulk_move_rag_documents(
        self, document_ids: list[str], new_directory_path: str, db: AsyncSession
    ) -> int:
        """
        Move multiple RAG documents to a new directory

        Args:
            document_ids: List of document IDs
            new_directory_path: New directory path
            db: Database session

        Returns:
            Number of documents moved
        """
        try:
            # For now, return the count since we don't have a proper document storage
            # In a full implementation, this would update the vector store metadata
            return len(document_ids)
        except Exception as e:
            logger.error(f"Error bulk moving RAG documents: {e}")
            return 0

    async def list_rag_directories(self) -> list[str]:
        """
        List all known RAG directories

        Returns:
            List of directory paths
        """
        try:
            # For now, return default directory since we don't have a proper document storage
            return ["default"]
        except Exception as e:
            logger.error(f"Error listing RAG directories: {e}")
            return []

    async def create_rag_directory(self, directory_path: str) -> bool:
        """
        Create a new RAG directory

        Args:
            directory_path: Path of the directory to create

        Returns:
            True if created successfully
        """
        try:
            # For now, return True since we don't have a proper document storage
            # In a full implementation, this would create the directory structure
            return True
        except Exception as e:
            logger.error(f"Error creating RAG directory: {e}")
            return False

    async def delete_rag_directory(self, directory_path: str, db: AsyncSession) -> int:
        """
        Delete a RAG directory and all its associated documents

        Args:
            directory_path: Directory path to delete
            db: Database session

        Returns:
            Number of documents deleted
        """
        try:
            # For now, return 0 since we don't have a proper document storage
            # In a full implementation, this would delete from the vector store
            return 0
        except Exception as e:
            logger.error(f"Error deleting RAG directory: {e}")
            return 0

    async def get_rag_stats(self) -> dict[str, Any]:
        """
        Get RAG system statistics

        Returns:
            Statistics about the RAG system
        """
        try:
            # For now, return basic stats since we don't have a proper document storage
            # In a full implementation, this would query the vector store or database
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "total_embeddings": 0,
                "storage_size_mb": 0.0,
                "last_updated": datetime.now().isoformat(),
                "vector_store_type": "local",
                "embedding_model": "SpeakLeash/bielik-4.5b-v3.0-instruct: Q8_0",
            }
        except Exception as e:
            logger.error(f"Error getting RAG stats: {e}")
            return {"error": str(e)}

    async def get_rag_directory_stats(
        self, directory_path: str, db: AsyncSession
    ) -> dict[str, Any]:
        """
        Get statistics for a specific RAG directory

        Args:
            directory_path: Directory path
            db: Database session

        Returns:
            Directory statistics
        """
        try:
            # For now, return basic directory stats since we don't have a proper document storage
            # In a full implementation, this would query the vector store for documents in this directory
            return {
                "directory_path": directory_path,
                "document_count": 0,
                "total_chunks": 0,
                "total_size_mb": 0.0,
                "last_updated": datetime.now().isoformat(),
                "documents": [],
            }
        except Exception as e:
            logger.error(f"Error getting directory stats: {e}")
            return {"error": str(e)}

    async def query_rag(self, question: str, db: AsyncSession) -> dict[str, Any]:
        """
        Query the RAG system

        Args:
            question: Question to ask
            db: Database session

        Returns:
            Query response with answer and sources
        """
        try:
            # Use the vector store to search for relevant context
            search_results = await self.search_documents_in_rag(question, k=5)

            # Extract chunks safely
            chunks = (
                search_results.get("chunks", [])
                if isinstance(search_results, dict)
                else []
            )

            # For now, return a simple response
            # In a full implementation, this would use an LLM to generate an answer
            return {
                "answer": f"Odpowiedź na pytanie: {question}. (Implementacja w toku)",
                "sources": chunks,
                "confidence": 0.5,
            }
        except Exception as e:
            logger.error(f"Error querying RAG: {e}")
            # Return a safe fallback response instead of raising an exception
            return {
                "answer": "Przepraszam, wystąpił błąd podczas przetwarzania zapytania.",
                "sources": [],
                "confidence": 0.0,
            }

    def _format_receipt_content(self, trip: dict) -> str:
        """Format shopping trip as document content"""
        products_text = "\n".join(
            [
                f"- {product['name']}: {product['quantity']} szt. @ {product['unit_price']} zł"
                for product in trip["products"]
            ]
        )

        return f"""
Paragon z {trip["store_name"]} z dnia {trip["trip_date"]}

Produkty:
{products_text}

Suma: {trip["total_amount"]} zł
"""

    def _create_receipt_metadata(self, trip: dict) -> dict[str, Any]:
        """Create metadata for receipt document"""
        return {
            "type": "receipt",
            "store": trip["store_name"],
            "date": trip["trip_date"].isoformat(),
            "total_amount": trip["total_amount"],
            "products_count": len(trip["products"]),
            "categories": list(
                {
                    product["category"]
                    for product in trip["products"]
                    if product["category"]
                }
            ),
        }

    def _format_pantry_content(self, products: list[dict]) -> str:
        """Format pantry products as document content"""
        products_text = "\n".join(
            [
                f"- {product['name']}: {product['quantity']} szt. (wygasa: {product['expiration_date']})"
                for product in products
            ]
        )

        return f"""
Stan spiżarni - ostatnia aktualizacja: {datetime.now().strftime("%Y-%m-%d %H:%M")}

Dostępne produkty:
{products_text}

Łącznie: {len(products)} produktów
"""

    def _create_pantry_metadata(self, products: list[dict]) -> dict[str, Any]:
        """Create metadata for pantry document"""
        categories = list(
            {product["category"] for product in products if product["category"]}
        )
        expiry_dates = [
            product["expiration_date"]
            for product in products
            if product["expiration_date"]
        ]

        return {
            "type": "pantry",
            "last_updated": datetime.now().isoformat(),
            "total_items": len(products),
            "categories": categories,
            "expiring_soon": len(
                [d for d in expiry_dates if d and (d - datetime.now().date()).days <= 7]
            ),
        }

    def _format_conversation_content(self, conversation: dict) -> str:
        """Format conversation as document content"""
        return f"""
Rozmowa z {conversation["created_at"].strftime("%Y-%m-%d %H:%M")}

Pytanie: {conversation["user_message"]}
Odpowiedź: {conversation["assistant_response"]}

Typ: {conversation["intent_type"]}
"""

    def _create_conversation_metadata(self, conversation: dict) -> dict[str, Any]:
        """Create metadata for conversation document"""
        return {
            "type": "conversation",
            "date": conversation["created_at"].isoformat(),
            "intent_type": conversation["intent_type"],
            "session_id": conversation["session_id"],
        }


# Global instance - use the same rag_document_processor instance to ensure singleton pattern
from core.rag_document_processor import rag_document_processor

rag_integration = RAGDatabaseIntegration(rag_document_processor)
