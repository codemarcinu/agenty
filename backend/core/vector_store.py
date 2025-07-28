"""
Vector Store Implementation with FAISS
Zgodnie z regułami MDC dla zarządzania pamięcią i optymalizacji
"""

import asyncio
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
import logging
import os
from pathlib import Path
from typing import Any

import numpy as np

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Document chunk with metadata and embedding support"""

    id: str
    content: str
    metadata: dict[str, Any]
    embedding: np.ndarray | None = None
    created_at: str | None = None

    def __post_init__(self) -> None:
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class SmartChunker:
    """Smart document chunking with overlap and metadata preservation"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: list[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",
            "\n",
            ". ",
            "! ",
            "? ",
            ";",
            ":",
            " - ",
            "\t",
            " ",
        ]

    def chunk_document(
        self, text: str, metadata: dict[str, Any]
    ) -> list[DocumentChunk]:
        """Split document into overlapping chunks"""
        chunks = []
        start = 0
        chunk_id = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to find a good break point
            if end < len(text):
                # Look for the last separator in the chunk
                for separator in self.separators:
                    last_sep = text.rfind(separator, start, end)
                    if last_sep > start:
                        end = last_sep + len(separator)
                        break

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = chunk_id
                chunk_metadata["chunk_start"] = start
                chunk_metadata["chunk_end"] = end

                chunks.append(
                    DocumentChunk(
                        id=f"{metadata.get('source', 'doc')}_{chunk_id}",
                        content=chunk_text,
                        metadata=chunk_metadata,
                    )
                )
                chunk_id += 1

            start = end - self.chunk_overlap
            if start >= len(text):
                break

        return chunks


class VectorStore:
    """FAISS-based vector store with proper memory management and optimizations"""

    def __init__(self, dimension: int = 4096, index_type: str = "IndexIVFFlat") -> None:
        self.dimension = dimension
        self.index_type = index_type
        self._actual_dimension = None  # Will be set based on first embedding

        # Check if FAISS is available
        if not FAISS_AVAILABLE or faiss is None:
            logger.warning("FAISS not available, using basic vector store")
            self.index = None
            self._is_trained = True  # Mark as trained for basic mode
            self.vectors = []  # Simple list for basic implementation
            self.metadata = []
            return

        # Initialize optimized FAISS index
        if index_type == "IndexFlatL2":
            self.index = faiss.IndexFlatL2(dimension)
        elif index_type == "IndexIVFFlat":
            # Use IVF for better memory efficiency and speed
            quantizer = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIVFFlat(quantizer, dimension, 100)
            # Train the index (will be done when vectors are added)
            self._is_trained = False
        elif index_type == "IndexIVFPQ":
            # Use Product Quantization for memory efficiency
            quantizer = faiss.IndexFlatL2(dimension)
            # 8 bits per sub-vector, 8 sub-vectors
            self.index = faiss.IndexIVFPQ(quantizer, dimension, 100, 8, 8)
            self._is_trained = False
        else:
            raise ValueError(f"Unsupported index type: {index_type}")

        # Use strong references to avoid premature garbage collection
        self._documents: dict[str, DocumentChunk] = {}
        self._document_ids: list[str] = []

        # Memory management
        self._max_documents = 10000
        self._cleanup_threshold = 8000
        self._cleanup_lock = asyncio.Lock()

        # Cache for frequently accessed vectors
        self._vector_cache: dict[str, np.ndarray] = {}
        self._cache_max_size = 1000
        self._cache_hits = 0
        self._cache_misses = 0

        # Memory mapping for large indices
        self._use_memory_mapping = False
        self._index_file_path: str | None = None

        # Performance tracking
        self._stats = {
            "total_documents": 0,
            "total_vectors": 0,
            "last_cleanup": 0.0,
            "cleanup_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # Track chunks since last save
        self.chunks_since_save = 0

    def _adjust_dimension_if_needed(self, embedding: np.ndarray) -> np.ndarray:
        """Adjust vector store dimension if needed based on actual embedding dimension"""
        actual_dim = embedding.shape[0]

        if self._actual_dimension is None:
            # First embedding - set the actual dimension
            self._actual_dimension = actual_dim
            if actual_dim != self.dimension:
                logger.info(
                    f"Adjusting vector store dimension from {self.dimension} to {actual_dim}"
                )
                self.dimension = actual_dim
                # Recreate index with correct dimension
                if self.index_type == "IndexFlatL2":
                    self.index = faiss.IndexFlatL2(actual_dim)
                elif self.index_type == "IndexIVFFlat":
                    quantizer = faiss.IndexFlatL2(actual_dim)
                    self.index = faiss.IndexIVFFlat(quantizer, actual_dim, 100)
                    self._is_trained = False
                elif self.index_type == "IndexIVFPQ":
                    quantizer = faiss.IndexFlatL2(actual_dim)
                    self.index = faiss.IndexIVFPQ(quantizer, actual_dim, 100, 8, 8)
                    self._is_trained = False
            return embedding
        elif actual_dim != self._actual_dimension:
            logger.warning(
                f"Embedding dimension mismatch: expected {self._actual_dimension}, got {actual_dim}"
            )
            # Try to reshape if possible
            if actual_dim < self._actual_dimension:
                # Pad with zeros
                padded_embedding = np.zeros(
                    self._actual_dimension, dtype=embedding.dtype
                )
                padded_embedding[:actual_dim] = embedding
                return padded_embedding
            elif actual_dim > self._actual_dimension:
                # Truncate
                return embedding[: self._actual_dimension]

        return embedding

    def _cleanup_callback(self, weak_ref) -> None:
        """Callback when document is garbage collected"""
        logger.info(f"=== CLEANUP CALLBACK TRIGGERED === weak_ref: {weak_ref}")
        for doc_id, ref in list(self._documents.items()):
            if ref is weak_ref:
                logger.info(f"=== CLEANUP CALLBACK === Removing doc_id: {doc_id}")
                del self._documents[doc_id]
                if doc_id in self._document_ids:
                    self._document_ids.remove(doc_id)
                    logger.info(
                        f"=== CLEANUP CALLBACK === Removed from _document_ids: {doc_id}"
                    )
                # Remove from cache if present
                if doc_id in self._vector_cache:
                    del self._vector_cache[doc_id]
                    logger.info(
                        f"=== CLEANUP CALLBACK === Removed from cache: {doc_id}"
                    )
                logger.info(
                    f"=== CLEANUP CALLBACK === Final state - _documents: {list(self._documents.keys())}, _document_ids: {self._document_ids}"
                )
                break

    def _get_cached_embedding(self, doc_id: str) -> np.ndarray | None:
        """Get embedding from cache"""
        if doc_id in self._vector_cache:
            self._stats["cache_hits"] = int(self._stats.get("cache_hits", 0)) + 1
            return self._vector_cache[doc_id]
        self._stats["cache_misses"] = int(self._stats.get("cache_misses", 0)) + 1
        return None

    def _cache_embedding(self, doc_id: str, embedding: np.ndarray) -> None:
        """Cache embedding with LRU eviction"""
        if len(self._vector_cache) >= self._cache_max_size:
            # Remove oldest entry (simple LRU)
            oldest_key = next(iter(self._vector_cache))
            del self._vector_cache[oldest_key]
        self._vector_cache[doc_id] = embedding

    async def add_document(
        self, text: str, metadata: dict[str, Any], auto_embed: bool = True
    ) -> None:
        """Add a single document to the vector store"""
        # Create a simple document chunk
        doc = DocumentChunk(
            id=f"doc_{len(self._documents)}", content=text, metadata=metadata
        )

        # Generate embedding if auto_embed is True
        if auto_embed:
            try:
                # Import here to avoid circular imports
                from core.hybrid_llm_client import hybrid_llm_client

                # Use hybrid LLM client for embeddings
                embedding_response = await hybrid_llm_client.embed(text=text)
                if embedding_response and isinstance(embedding_response, list):
                    doc.embedding = np.array(embedding_response, dtype=np.float32)
                    logger.debug(
                        f"Generated embedding for document: {len(embedding_response)} dimensions"
                    )
                else:
                    logger.warning(
                        f"Failed to generate embedding for document: {text[:50]}..."
                    )
                    return  # Don't add document without embedding
            except Exception as e:
                logger.warning(f"Failed to auto-generate embedding: {e}")
                return  # Don't add document without embedding

        await self.add_documents([doc])

    async def add_documents(self, documents: list[DocumentChunk]) -> None:
        """Add documents to vector store with memory management and caching"""
        if len(self._documents) + len(documents) >= self._max_documents:
            await self._cleanup_old_documents()
        embeddings = []
        for doc in documents:
            assert isinstance(
                doc.embedding, np.ndarray
            ), f"Embedding for doc {doc.id} is not np.ndarray: {type(doc.embedding)}"
            if doc.embedding is not None:
                # Adjust dimension if needed
                adjusted_embedding = self._adjust_dimension_if_needed(doc.embedding)

                embeddings.append(adjusted_embedding)
                self._cache_embedding(doc.id, doc.embedding)
                if doc.id not in self._documents:
                    self._documents[doc.id] = doc
                else:
                    logger.warning(
                        f"Document with id {doc.id} already exists in _documents, skipping overwrite."
                    )
                if doc.id not in self._document_ids:
                    self._document_ids.append(doc.id)
                else:
                    logger.warning(
                        f"Document id {doc.id} already in _document_ids, skipping append."
                    )
                self._stats["total_documents"] = (
                    int(self._stats.get("total_documents", 0)) + 1
                )
                self.chunks_since_save += 1
        if embeddings:
            embeddings_array = np.array(embeddings, dtype=np.float32)
            if hasattr(self, "_is_trained") and not self._is_trained:
                if len(embeddings_array) >= 100:
                    self.index.train(embeddings_array)
                    self._is_trained = True
                    logger.info("Trained FAISS index")
                else:
                    self.index = faiss.IndexFlatL2(self.dimension)
                    logger.info("Using FlatL2 index for small dataset")

            # Normalize embeddings before adding to FAISS for consistent similarity calculation
            faiss.normalize_L2(embeddings_array)
            logger.debug(
                f"Normalized {len(embeddings_array)} embeddings before adding to FAISS"
            )

            self.index.add(embeddings_array)
            self._stats["total_vectors"] = int(self.index.ntotal)
            logger.debug(f"Added {len(documents)} documents to vector store")

            # Auto-save if we've added enough chunks
            if self.chunks_since_save >= 10:  # Save every 10 chunks
                await self.save_index_async()

    async def search(
        self, query_embedding: np.ndarray, k: int = 5
    ) -> list[tuple[DocumentChunk, float]]:
        """Search for similar documents with caching and proper error handling"""
        try:
            # Ensure query embedding is 2D
            if query_embedding.ndim == 1:
                query_embedding = query_embedding.reshape(1, -1)

            # Check if index has any vectors
            if self.index.ntotal == 0:
                logger.warning("Vector store is empty, no search results available")
                return []

            # Search in FAISS index
            distances, indices = self.index.search(query_embedding, k)

            # Check if search returned any results
            if len(distances) == 0 or len(indices) == 0:
                logger.warning("FAISS search returned no results")
                return []

            # Ensure we have valid arrays
            if len(distances[0]) == 0 or len(indices[0]) == 0:
                logger.warning("FAISS search returned empty result arrays")
                return []

            results = []
            for i, (distance, idx) in enumerate(
                zip(distances[0], indices[0], strict=False)
            ):
                # Check if index is valid
                if idx < 0 or idx >= len(self._document_ids):
                    logger.warning(f"Invalid document index: {idx}, skipping")
                    continue

                doc_id = self._document_ids[idx]

                # Get document from storage (always use full document for content)
                doc = self._documents.get(doc_id)
                if doc is None:
                    logger.warning(f"Document {doc_id} not found in storage")
                    continue

                results.append((doc, float(distance)))

            return results

        except Exception as e:
            logger.error(f"Error in vector store search: {e!s}")
            return []

    async def search_text(
        self, query: str, k: int = 5, min_similarity: float = 0.0
    ) -> list[dict[str, Any]]:
        """Search for documents by text query"""
        try:
            # Import here to avoid circular imports
            from core.hybrid_llm_client import hybrid_llm_client

            # Generate embedding for query
            embedding_response = await hybrid_llm_client.embed(text=query)
            if not embedding_response or not isinstance(embedding_response, list):
                logger.error("Failed to generate embedding for query")
                return []

            query_embedding = np.array(embedding_response, dtype=np.float32)

            # Adjust dimension if needed
            self._adjust_dimension_if_needed(query_embedding)

            # Search for similar documents
            results = await self.search(query_embedding, k)

            # Filter by similarity threshold
            filtered_results = []
            for doc, similarity in results:
                if similarity >= min_similarity:
                    filtered_results.append(
                        {
                            "id": doc.id,
                            "content": doc.content,
                            "metadata": doc.metadata,
                            "similarity": similarity,
                        }
                    )

            return filtered_results

        except Exception as e:
            logger.error(f"Error in text search: {e!s}")
            return []

    async def get_document(self, doc_id: str) -> DocumentChunk | None:
        """Get document by ID"""
        return self._documents.get(doc_id)

    async def remove_document(self, doc_id: str) -> bool:
        """Remove document by ID"""
        if doc_id in self._documents:
            del self._documents[doc_id]
            if doc_id in self._document_ids:
                self._document_ids.remove(doc_id)
            if doc_id in self._vector_cache:
                del self._vector_cache[doc_id]
            return True
        return False

    async def _cleanup_old_documents(self) -> None:
        """Clean up old documents to free memory"""
        async with self._cleanup_lock:
            if len(self._documents) <= self._cleanup_threshold:
                return

            # Remove oldest documents
            documents_to_remove = len(self._documents) - self._cleanup_threshold
            removed_count = 0

            for doc_id in list(self._documents.keys())[:documents_to_remove]:
                if await self.remove_document(doc_id):
                    removed_count += 1

            self._stats["last_cleanup"] = datetime.now().timestamp()
            self._stats["cleanup_count"] = int(self._stats.get("cleanup_count", 0)) + 1

            logger.info(f"Cleaned up {removed_count} old documents")

    async def get_stats(self) -> dict[str, Any]:
        """Get vector store statistics"""
        return {
            "total_documents": len(self._documents),
            "total_vectors": self.index.ntotal if hasattr(self.index, "ntotal") else 0,
            "cache_size": len(self._vector_cache),
            "cache_hits": self._stats.get("cache_hits", 0),
            "cache_misses": self._stats.get("cache_misses", 0),
            "dimension": self.dimension,
            "actual_dimension": self._actual_dimension,
            "index_type": self.index_type,
        }

    async def get_statistics(self) -> dict[str, Any]:
        """Get detailed statistics"""
        return await self.get_stats()

    async def is_empty(self) -> bool:
        """Check if vector store is empty"""
        return len(self._documents) == 0

    async def clear_all(self) -> None:
        """Clear all documents and reset index"""
        self._documents.clear()
        self._document_ids.clear()
        self._vector_cache.clear()

        # Reset index
        if self.index_type == "IndexFlatL2":
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "IndexIVFFlat":
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            self._is_trained = False
        elif self.index_type == "IndexIVFPQ":
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.index = faiss.IndexIVFPQ(quantizer, self.dimension, 100, 8, 8)
            self._is_trained = False

        self._stats = {
            "total_documents": 0,
            "total_vectors": 0,
            "last_cleanup": 0.0,
            "cleanup_count": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        self.chunks_since_save = 0
        logger.info("Vector store cleared")

    async def load_index_async(self) -> None:
        """Load index asynchronously from disk"""
        try:
            data_dir = Path("data/vector_store")
            index_path = data_dir / "faiss_index.bin"
            metadata_path = data_dir / "metadata.json"

            if not index_path.exists() or not metadata_path.exists():
                logger.info("No saved vector store found, starting fresh")
                return

            # Load FAISS index
            self.index = faiss.read_index(str(index_path))

            # Load metadata
            import json

            with open(metadata_path, encoding="utf-8") as f:
                metadata = json.load(f)

            # Restore documents
            self._documents.clear()
            self._document_ids.clear()

            for doc_id, doc_data in metadata["documents"].items():
                doc = DocumentChunk(
                    id=doc_id,
                    content=doc_data["content"],
                    metadata=doc_data["metadata"],
                    created_at=doc_data["created_at"],
                )
                self._documents[doc_id] = doc

            self._document_ids = metadata["document_ids"]
            self._stats = metadata["stats"]
            self.dimension = metadata["dimension"]
            self._actual_dimension = metadata["actual_dimension"]
            self.index_type = metadata["index_type"]

            logger.info(f"Loaded vector store with {len(self._documents)} documents")

        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            # Continue with empty vector store

    async def save_index_async(self) -> None:
        """Save index asynchronously to disk"""
        try:
            if not FAISS_AVAILABLE or self.index is None:
                logger.warning(
                    "Cannot save index - FAISS not available or index is None"
                )
                return

            # Create data directory if it doesn't exist
            data_dir = Path("data/vector_store")
            data_dir.mkdir(parents=True, exist_ok=True)

            # Save FAISS index
            index_path = data_dir / "faiss_index.bin"
            faiss.write_index(self.index, str(index_path))

            # Save metadata
            metadata_path = data_dir / "metadata.json"
            metadata = {
                "documents": {
                    doc_id: {
                        "content": doc.content,
                        "metadata": doc.metadata,
                        "created_at": doc.created_at,
                    }
                    for doc_id, doc in self._documents.items()
                },
                "document_ids": self._document_ids,
                "stats": self._stats,
                "dimension": self.dimension,
                "actual_dimension": self._actual_dimension,
                "index_type": self.index_type,
                "chunks_since_save": 0,  # Reset counter
            }

            import json

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            self.chunks_since_save = 0
            logger.info(
                f"Saved vector store to {data_dir} with {len(self._documents)} documents"
            )

        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            raise

    @asynccontextmanager
    async def context_manager(self) -> AsyncGenerator["VectorStore", None]:
        """Context manager for vector store operations"""
        try:
            yield self
        finally:
            await self.save_index_async()

    async def __aenter__(self) -> "VectorStore":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.save_index_async()

    def save_index(self, filepath: str) -> None:
        """Save FAISS index to file"""
        try:
            faiss.write_index(self.index, filepath)
            logger.info(f"Saved FAISS index to {filepath}")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")

    def load_index(self, filepath: str, use_memory_mapping: bool = False) -> None:
        """Load FAISS index from file"""
        try:
            if use_memory_mapping and os.path.exists(filepath):
                self.index = faiss.read_index(filepath)
                self._use_memory_mapping = True
                self._index_file_path = filepath
                logger.info(f"Loaded FAISS index with memory mapping from {filepath}")
            else:
                self.index = faiss.read_index(filepath)
                logger.info(f"Loaded FAISS index from {filepath}")
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")

    async def list_directories(self) -> list[dict]:
        """List directories in vector store (placeholder for future implementation)"""
        return [
            {
                "name": "default",
                "document_count": len(self._documents),
                "vector_count": (
                    self.index.ntotal if hasattr(self.index, "ntotal") else 0
                ),
            }
        ]


class AsyncDocumentLoader:
    """Asynchronous document loader with progress tracking"""

    def __init__(self, vector_store: VectorStore) -> None:
        self.vector_store = vector_store

    async def load_directory(
        self,
        directory: str,
        glob_pattern: str = "**/*.*",
        metadata_fn: Callable | None = None,
    ) -> None:
        """Load documents from directory with progress tracking"""
        try:
            path = Path(directory)
            if not path.exists():
                logger.error(f"Directory {directory} does not exist")
                return

            files = list(path.glob(glob_pattern))
            total_files = len(files)
            logger.info(f"Found {total_files} files to process")

            for i, file_path in enumerate(files, 1):
                try:
                    if file_path.is_file():
                        # Read file content
                        with open(file_path, encoding="utf-8") as f:
                            content = f.read()

                        # Generate metadata
                        metadata = {
                            "source": str(file_path),
                            "filename": file_path.name,
                            "file_size": file_path.stat().st_size,
                            "file_type": file_path.suffix,
                        }

                        # Apply custom metadata function if provided
                        if metadata_fn:
                            metadata.update(metadata_fn(file_path))

                        # Add to vector store
                        await self.vector_store.add_document(
                            text=content, metadata=metadata, auto_embed=True
                        )

                        logger.info(f"Processed {i}/{total_files}: {file_path.name}")

                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")

            logger.info(f"Completed loading {total_files} files from {directory}")

        except Exception as e:
            logger.error(f"Error loading directory {directory}: {e}")

    async def start_incremental_indexing(
        self,
        directory: str,
        glob_pattern: str = "**/*.*",
        check_interval: int = 300,  # seconds
        metadata_fn: Callable | None = None,
    ) -> None:
        """Start incremental indexing of directory"""
        logger.info(f"Starting incremental indexing of {directory}")

        async def _indexing_task() -> None:
            while True:
                try:
                    await self.load_directory(directory, glob_pattern, metadata_fn)
                    await asyncio.sleep(check_interval)
                except Exception as e:
                    logger.error(f"Error in incremental indexing: {e}")
                    await asyncio.sleep(check_interval)

        # Start indexing task
        asyncio.create_task(_indexing_task())


# Global vector store instance - disabled when FAISS not available
if FAISS_AVAILABLE:
    vector_store = VectorStore()
    # Load saved index on startup
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule loading for later
            asyncio.create_task(vector_store.load_index_async())
        else:
            # Run in new event loop
            asyncio.run(vector_store.load_index_async())
    except Exception as e:
        logger.warning(f"Could not load vector store on startup: {e}")
else:
    vector_store = None
