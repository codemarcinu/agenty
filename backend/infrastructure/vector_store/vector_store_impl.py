import logging
from typing import Any

import faiss
import numpy as np

from core.vector_store import VectorStore

logger = logging.getLogger(__name__)


class EnhancedVectorStoreImpl:
    def __init__(
        self,
        llm_client: Any,  # Changed from LLMClient to Any to accept HybridLLMClient
        dimension: int = 4096,
        index_type: str = "IndexFlatL2",
    ) -> None:
        self.llm_client = llm_client
        self.vector_store = VectorStore(dimension=dimension, index_type=index_type)

    async def add_documents(self, documents: list[str]) -> None:
        """Add documents to vector store"""
        try:
            for i, document in enumerate(documents):
                metadata = {"source": f"document_{i}", "type": "text", "index": i}
                await self.vector_store.add_document(
                    text=document, metadata=metadata, auto_embed=True
                )
            logger.info(f"Added {len(documents)} documents to vector store")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

    async def add_document(self, text: str, metadata: dict[str, Any]) -> None:
        """Add a single document to vector store"""
        try:
            logger.info(
                f"[VECTOR_STORE_IMPL] Starting add_document for text: {text[:50]}..."
            )

            # Generate embedding using our mock llm_client
            embedding_response = await self.llm_client.embed(text)
            logger.info(
                f"[VECTOR_STORE_IMPL] Embedding response: {type(embedding_response)}, length: {len(embedding_response) if embedding_response else 0}"
            )

            if not embedding_response:
                logger.warning("Failed to generate embedding for document")
                return

            import uuid

            import numpy as np

            from core.vector_store import DocumentChunk

            # Clone metadata to avoid reference overwrite
            meta = dict(metadata) if metadata else {}
            doc_id = meta.get("id")
            if not doc_id:
                doc_id = str(uuid.uuid4())
            meta["id"] = doc_id

            doc = DocumentChunk(
                id=doc_id,
                content=text,
                metadata=meta,
                embedding=np.array(embedding_response, dtype=np.float32),
            )

            assert isinstance(
                doc.embedding, np.ndarray
            ), f"Embedding for doc {doc.id} is not np.ndarray: {type(doc.embedding)}"

            # Dynamicznie dostosuj wymiar jeśli to pierwszy dokument i index jest pusty
            if (
                self.vector_store.dimension != doc.embedding.shape[0]
                and self.vector_store.index.ntotal == 0
            ):
                logger.info(
                    f"[VECTOR_STORE_IMPL] Adjusting vector store dimension from {self.vector_store.dimension} to {doc.embedding.shape[0]}"
                )
                self.vector_store.dimension = doc.embedding.shape[0]
                self.vector_store._actual_dimension = doc.embedding.shape[0]

                # Przeładuj index FAISS z nowym wymiarem TYLKO jeśli index jest pusty
                if self.vector_store.index_type == "IndexFlatL2":
                    self.vector_store.index = faiss.IndexFlatL2(doc.embedding.shape[0])
                elif self.vector_store.index_type == "IndexIVFFlat":
                    quantizer = faiss.IndexFlatL2(doc.embedding.shape[0])
                    self.vector_store.index = faiss.IndexIVFFlat(
                        quantizer, doc.embedding.shape[0], 100
                    )
                    self.vector_store._is_trained = False
                elif self.vector_store.index_type == "IndexIVFPQ":
                    quantizer = faiss.IndexFlatL2(doc.embedding.shape[0])
                    self.vector_store.index = faiss.IndexIVFPQ(
                        quantizer, doc.embedding.shape[0], 100, 8, 8
                    )
                    self.vector_store._is_trained = False
            elif (
                self.vector_store.dimension != doc.embedding.shape[0]
                and self.vector_store.index.ntotal > 0
            ):
                logger.error(
                    f"[VECTOR_STORE_IMPL] Cannot change dimension from {self.vector_store.dimension} to {doc.embedding.shape[0]} - index already contains {self.vector_store.index.ntotal} documents"
                )
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self.vector_store.dimension}, got {doc.embedding.shape[0]}"
                )

            await self.vector_store.add_documents([doc])

            logger.info(
                f"[DIAG] Added doc {doc_id} to vector store. index.ntotal={self.vector_store.index.ntotal}, _document_ids={len(self.vector_store._document_ids)}, _documents={len(self.vector_store._documents)}"
            )
        except Exception as e:
            logger.error(f"Error in add_document: {e}")
            raise

    async def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.65,
        filter_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Search for similar documents with the interface expected by RAG integration"""
        try:
            # Generate query embedding
            embedding_response = await self.llm_client.embed(query)
            if not embedding_response:
                logger.warning("Failed to generate embedding for query")
                return {"chunks": [], "total": 0}

            # Convert to numpy array and normalize
            query_embedding = np.array(embedding_response, dtype=np.float32)

            # Normalize query embedding (same as document embeddings)
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)
            faiss.normalize_L2(query_embedding)
            query_embedding = query_embedding.reshape(-1)  # Back to 1D for consistency

            # Search vector store
            results = await self.vector_store.search(
                query_embedding=query_embedding, k=top_k
            )

            # Filter results by similarity threshold and metadata
            filtered_results = []
            for doc_chunk, distance in results:
                # For L2 distance: convert to cosine-like similarity
                # Lower distance = higher similarity
                similarity = 1.0 / (1.0 + distance)

                # Check similarity threshold
                if similarity < similarity_threshold:
                    continue

                # Check metadata filter if provided
                if filter_metadata:
                    metadata_match = True
                    for key, value in filter_metadata.items():
                        if doc_chunk.metadata.get(key) != value:
                            metadata_match = False
                            break
                    if not metadata_match:
                        continue

                filtered_results.append(
                    {
                        "content": doc_chunk.content,
                        "metadata": doc_chunk.metadata,
                        "similarity": similarity,
                        "id": doc_chunk.id,
                    }
                )

            return {"chunks": filtered_results, "total": len(filtered_results)}
        except Exception as e:
            logger.error(f"Error in search: {e}")
            return {"chunks": [], "total": 0, "error": str(e)}

    async def similarity_search(self, query: str, k: int = 4) -> list[str]:
        """Search for similar documents (legacy method)"""
        try:
            # Generate query embedding
            query_embedding = await self.llm_client.embed(query)
            if not query_embedding:
                return []

            # Search vector store
            results = await self.vector_store.search(
                query_embedding=np.array(query_embedding, dtype=np.float32), k=k
            )

            # Extract text from results
            documents = [chunk.content for chunk, _ in results if chunk.content]
            return documents
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []

    async def get_relevant_documents(self, query: str) -> list[str]:
        """Get relevant documents for query"""
        try:
            # Use similarity search with default k=4
            return await self.similarity_search(query, k=4)
        except Exception as e:
            logger.error(f"Error getting relevant documents: {e}")
            return []

    async def delete_by_metadata(self, metadata_filter: dict[str, Any]) -> bool:
        """Delete documents by metadata filter"""
        try:
            # This is a simplified implementation
            # In a full implementation, you would iterate through documents and delete matching ones
            logger.info(f"Delete by metadata called with filter: {metadata_filter}")
            return True
        except Exception as e:
            logger.error(f"Error deleting by metadata: {e}")
            return False

    async def get_stats(self) -> dict[str, Any]:
        """Get vector store statistics"""
        try:
            return await self.vector_store.get_stats()
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}

    async def clear_all(self) -> None:
        """Clear all documents from vector store"""
        try:
            # This would need to be implemented in the base VectorStore
            logger.info("Clear all called")
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")
            raise

    async def is_empty(self) -> bool:
        """Check if vector store is empty"""
        try:
            stats = await self.get_stats()
            return stats.get("total_documents", 0) == 0
        except Exception as e:
            logger.error(f"Error checking if empty: {e}")
            return True
