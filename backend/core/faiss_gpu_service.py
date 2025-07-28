"""
FAISS GPU Service Implementation
Migracja na FAISS GPU z mechanizmem fallback do CPU
"""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
import logging
import time
from typing import Any

import numpy as np

try:
    import faiss

    FAISS_AVAILABLE = True

    # Try to import GPU-specific functions
    try:
        import pynvml

        NVIDIA_ML_AVAILABLE = True
    except ImportError:
        NVIDIA_ML_AVAILABLE = False
        pynvml = None

except ImportError:
    FAISS_AVAILABLE = False
    NVIDIA_ML_AVAILABLE = False
    faiss = None
    pynvml = None

from core.vector_store import DocumentChunk, VectorStore

logger = logging.getLogger(__name__)


@dataclass
class GPUMemoryInfo:
    """GPU memory information"""

    total: int = 0
    used: int = 0
    free: int = 0
    utilization: float = 0.0


class FAISSGPUService:
    """FAISS GPU service with automatic fallback to CPU"""

    def __init__(
        self,
        dimension: int = 768,
        index_type: str = "IndexIVFFlat",
        gpu_id: int = 0,
        enable_fallback: bool = True,
        batch_size: int = 1000,
    ):
        self.dimension = dimension
        self.index_type = index_type
        self.gpu_id = gpu_id
        self.enable_fallback = enable_fallback
        self.batch_size = batch_size

        # GPU state
        self.gpu_available = False
        self.gpu_initialized = False
        self.gpu_resources = None
        self.gpu_index = None

        # CPU fallback
        self.cpu_index = None
        self.using_gpu = False

        # Performance tracking
        self.stats = {
            "gpu_searches": 0,
            "cpu_searches": 0,
            "gpu_add_operations": 0,
            "cpu_add_operations": 0,
            "gpu_memory_errors": 0,
            "fallback_count": 0,
            "last_gpu_check": 0,
        }

        # Documents storage (shared between GPU and CPU)
        self._documents: dict[str, DocumentChunk] = {}
        self._document_ids: list[str] = []

        # Initialize service
        self._initialize()

    def _initialize(self) -> None:
        """Initialize FAISS GPU service with fallback"""
        logger.info("Initializing FAISS GPU service...")

        if not FAISS_AVAILABLE:
            logger.warning("FAISS not available, using CPU-only fallback")
            self._initialize_cpu_only()
            return

        # Check GPU availability
        gpu_count = faiss.get_num_gpus()
        if gpu_count == 0:
            logger.warning("No GPUs detected, using CPU fallback")
            self._initialize_cpu_only()
            return

        logger.info(f"Found {gpu_count} GPU(s), attempting GPU initialization")

        try:
            self._initialize_gpu()
            self.gpu_available = True
            self.using_gpu = True
            logger.info(f"Successfully initialized FAISS GPU on device {self.gpu_id}")
        except Exception as e:
            logger.error(f"GPU initialization failed: {e}")
            if self.enable_fallback:
                logger.info("Falling back to CPU implementation")
                self._initialize_cpu_fallback()
            else:
                raise

    def _initialize_gpu(self) -> None:
        """Initialize GPU index"""
        # Create CPU index first
        if self.index_type == "IndexFlatL2":
            cpu_index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "IndexIVFFlat":
            quantizer = faiss.IndexFlatL2(self.dimension)
            cpu_index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
        elif self.index_type == "IndexIVFPQ":
            quantizer = faiss.IndexFlatL2(self.dimension)
            cpu_index = faiss.IndexIVFPQ(quantizer, self.dimension, 100, 8, 8)
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")

        # Create GPU resources
        self.gpu_resources = faiss.StandardGpuResources()

        # Transfer to GPU
        self.gpu_index = faiss.index_cpu_to_gpu(
            self.gpu_resources, self.gpu_id, cpu_index
        )

        # Keep CPU index as backup
        self.cpu_index = cpu_index
        self.gpu_initialized = True

    def _initialize_cpu_only(self) -> None:
        """Initialize CPU-only fallback"""
        if self.index_type == "IndexFlatL2":
            self.cpu_index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "IndexIVFFlat":
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.cpu_index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
        elif self.index_type == "IndexIVFPQ":
            quantizer = faiss.IndexFlatL2(self.dimension)
            self.cpu_index = faiss.IndexIVFPQ(quantizer, self.dimension, 100, 8, 8)
        else:
            raise ValueError(f"Unsupported index type: {self.index_type}")

        self.gpu_available = False
        self.using_gpu = False
        logger.info("Initialized CPU-only FAISS index")

    def _initialize_cpu_fallback(self) -> None:
        """Initialize CPU fallback after GPU failure"""
        self._initialize_cpu_only()
        self.stats["fallback_count"] += 1
        self.gpu_available = False
        self.using_gpu = False

    def _check_gpu_health(self) -> bool:
        """Check GPU health and availability"""
        if not self.gpu_available or not NVIDIA_ML_AVAILABLE:
            return False

        current_time = time.time()
        if current_time - self.stats["last_gpu_check"] < 60:  # Check every minute
            return self.gpu_available

        try:
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(self.gpu_id)

            # Check memory
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            if info.free < 500 * 1024 * 1024:  # Less than 500MB free
                logger.warning(
                    f"GPU {self.gpu_id} has low memory: {info.free / 1024**2:.1f}MB free"
                )
                return False

            # Check utilization
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            if util.gpu > 95:  # Over 95% utilization
                logger.warning(f"GPU {self.gpu_id} is heavily utilized: {util.gpu}%")

            self.stats["last_gpu_check"] = current_time
            return True

        except Exception as e:
            logger.error(f"GPU health check failed: {e}")
            return False

    def get_gpu_memory_info(self) -> GPUMemoryInfo:
        """Get GPU memory information"""
        if not NVIDIA_ML_AVAILABLE or not self.gpu_available:
            return GPUMemoryInfo()

        try:
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(self.gpu_id)
            info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)

            return GPUMemoryInfo(
                total=info.total, used=info.used, free=info.free, utilization=util.gpu
            )
        except Exception as e:
            logger.error(f"Failed to get GPU memory info: {e}")
            return GPUMemoryInfo()

    def _should_use_gpu(self, operation_type: str = "search") -> bool:
        """Determine if GPU should be used for operation"""
        if not self.gpu_available or not self.gpu_initialized:
            return False

        # Check GPU health
        if not self._check_gpu_health():
            return False

        # For large batch operations, prefer GPU
        if operation_type == "add_batch" and self.batch_size > 500:
            return True

        # For searches, always prefer GPU if available
        if operation_type == "search":
            return True

        return self.using_gpu

    async def add_vectors(self, vectors: np.ndarray, document_ids: list[str]) -> None:
        """Add vectors to the index"""
        vectors = np.array(vectors, dtype=np.float32)

        if len(vectors) != len(document_ids):
            raise ValueError("Number of vectors must match number of document IDs")

        # Store document IDs
        for doc_id in document_ids:
            if doc_id not in self._document_ids:
                self._document_ids.append(doc_id)

        # Process in batches for memory efficiency
        total_vectors = len(vectors)
        for i in range(0, total_vectors, self.batch_size):
            batch_vectors = vectors[i : i + self.batch_size]

            try:
                if self._should_use_gpu("add_batch"):
                    # Try GPU first
                    await self._add_vectors_gpu(batch_vectors)
                    self.stats["gpu_add_operations"] += 1
                else:
                    # Use CPU
                    await self._add_vectors_cpu(batch_vectors)
                    self.stats["cpu_add_operations"] += 1

            except Exception as e:
                logger.error(f"Error adding batch {i//self.batch_size + 1}: {e}")

                # Try fallback if GPU failed
                if self.using_gpu and self.enable_fallback:
                    logger.warning("GPU operation failed, falling back to CPU")
                    await self._add_vectors_cpu(batch_vectors)
                    self.stats["gpu_memory_errors"] += 1
                    self.stats["cpu_add_operations"] += 1
                else:
                    raise

        logger.info(f"Added {total_vectors} vectors to FAISS index")

    async def _add_vectors_gpu(self, vectors: np.ndarray) -> None:
        """Add vectors using GPU"""
        if self.gpu_index is None:
            raise RuntimeError("GPU index not initialized")

        # Train index if needed
        if hasattr(self.gpu_index, "is_trained") and not self.gpu_index.is_trained:
            if len(vectors) >= 100:
                self.gpu_index.train(vectors)
                logger.info("Trained GPU FAISS index")

        self.gpu_index.add(vectors)

        # Sync CPU index for fallback
        if self.cpu_index is not None:
            self.cpu_index.add(vectors)

    async def _add_vectors_cpu(self, vectors: np.ndarray) -> None:
        """Add vectors using CPU"""
        if self.cpu_index is None:
            raise RuntimeError("CPU index not initialized")

        # Train index if needed
        if hasattr(self.cpu_index, "is_trained") and not self.cpu_index.is_trained:
            if len(vectors) >= 100:
                self.cpu_index.train(vectors)
                logger.info("Trained CPU FAISS index")

        self.cpu_index.add(vectors)

    async def search(
        self, query_vector: np.ndarray, k: int = 10
    ) -> tuple[np.ndarray, np.ndarray]:
        """Search for nearest neighbors"""
        query_vector = np.array([query_vector], dtype=np.float32)

        try:
            if self._should_use_gpu("search"):
                # Try GPU first
                distances, indices = await self._search_gpu(query_vector, k)
                self.stats["gpu_searches"] += 1
                return distances, indices
            else:
                # Use CPU
                distances, indices = await self._search_cpu(query_vector, k)
                self.stats["cpu_searches"] += 1
                return distances, indices

        except Exception as e:
            logger.error(f"Search operation failed: {e}")

            # Try fallback if GPU failed
            if self.using_gpu and self.enable_fallback:
                logger.warning("GPU search failed, falling back to CPU")
                distances, indices = await self._search_cpu(query_vector, k)
                self.stats["gpu_memory_errors"] += 1
                self.stats["cpu_searches"] += 1
                return distances, indices
            else:
                raise

    async def _search_gpu(
        self, query_vector: np.ndarray, k: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Search using GPU"""
        if self.gpu_index is None:
            raise RuntimeError("GPU index not initialized")

        return self.gpu_index.search(query_vector, k)

    async def _search_cpu(
        self, query_vector: np.ndarray, k: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """Search using CPU"""
        if self.cpu_index is None:
            raise RuntimeError("CPU index not initialized")

        return self.cpu_index.search(query_vector, k)

    def get_index_size(self) -> int:
        """Get number of vectors in index"""
        if self.using_gpu and self.gpu_index is not None:
            return self.gpu_index.ntotal
        elif self.cpu_index is not None:
            return self.cpu_index.ntotal
        return 0

    def get_statistics(self) -> dict[str, Any]:
        """Get service statistics"""
        gpu_memory = self.get_gpu_memory_info()

        return {
            "using_gpu": self.using_gpu,
            "gpu_available": self.gpu_available,
            "gpu_initialized": self.gpu_initialized,
            "index_size": self.get_index_size(),
            "dimension": self.dimension,
            "index_type": self.index_type,
            "batch_size": self.batch_size,
            "stats": self.stats.copy(),
            "gpu_memory": {
                "total_mb": gpu_memory.total / 1024**2,
                "used_mb": gpu_memory.used / 1024**2,
                "free_mb": gpu_memory.free / 1024**2,
                "utilization_percent": gpu_memory.utilization,
            },
        }

    def save_index(self, filepath: str) -> None:
        """Save index to file"""
        try:
            if self.using_gpu and self.gpu_index is not None:
                # Save GPU index by transferring to CPU first
                cpu_index = faiss.index_gpu_to_cpu(self.gpu_index)
                faiss.write_index(cpu_index, filepath)
            elif self.cpu_index is not None:
                faiss.write_index(self.cpu_index, filepath)
            else:
                raise RuntimeError("No index to save")

            logger.info(f"Saved FAISS index to {filepath}")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise

    def load_index(self, filepath: str) -> None:
        """Load index from file"""
        try:
            # Load CPU index first
            cpu_index = faiss.read_index(filepath)
            self.cpu_index = cpu_index

            # Transfer to GPU if available
            if self.gpu_available and self.gpu_resources is not None:
                try:
                    self.gpu_index = faiss.index_cpu_to_gpu(
                        self.gpu_resources, self.gpu_id, cpu_index
                    )
                    self.using_gpu = True
                    logger.info(f"Loaded FAISS index to GPU from {filepath}")
                except Exception as e:
                    logger.warning(f"Failed to load index to GPU: {e}, using CPU")
                    self.using_gpu = False
            else:
                logger.info(f"Loaded FAISS index to CPU from {filepath}")

        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise

    @asynccontextmanager
    async def batch_context(self) -> AsyncGenerator["FAISSGPUService", None]:
        """Context manager for batch operations"""
        # Could implement batch optimization here
        try:
            yield self
        finally:
            # Cleanup or finalization
            pass

    def __del__(self):
        """Cleanup GPU resources"""
        try:
            if self.gpu_resources is not None:
                # FAISS handles GPU resource cleanup automatically
                pass
        except Exception:
            pass


class EnhancedVectorStoreGPU(VectorStore):
    """Enhanced Vector Store with GPU acceleration"""

    def __init__(
        self,
        dimension: int = 768,
        index_type: str = "IndexIVFFlat",
        gpu_id: int = 0,
        enable_fallback: bool = True,
    ):
        super().__init__(dimension, index_type)

        # Replace FAISS index with GPU service
        self.faiss_gpu_service = FAISSGPUService(
            dimension=dimension,
            index_type=index_type,
            gpu_id=gpu_id,
            enable_fallback=enable_fallback,
        )

        # Override parent index
        self.index = None  # Will use GPU service instead

    async def add_documents(self, documents: list[DocumentChunk]) -> None:
        """Add documents using GPU-accelerated FAISS"""
        if len(self._documents) + len(documents) >= self._max_documents:
            await self._cleanup_old_documents()

        embeddings = []
        doc_ids = []

        for doc in documents:
            if doc.embedding is not None:
                self._adjust_dimension_if_needed(doc.embedding)
                embeddings.append(doc.embedding)
                doc_ids.append(doc.id)

                self._cache_embedding(doc.id, doc.embedding)

                if doc.id not in self._documents:
                    self._documents[doc.id] = doc

                if doc.id not in self._document_ids:
                    self._document_ids.append(doc.id)

                self._stats["total_documents"] = (
                    int(self._stats.get("total_documents", 0)) + 1
                )
                self.chunks_since_save += 1

        if embeddings:
            embeddings_array = np.array(embeddings, dtype=np.float32)
            await self.faiss_gpu_service.add_vectors(embeddings_array, doc_ids)
            self._stats["total_vectors"] = self.faiss_gpu_service.get_index_size()
            logger.debug(f"Added {len(documents)} documents to GPU vector store")

    async def add_document(
        self, text: str, metadata: dict[str, Any], auto_embed: bool = False
    ) -> None:
        """Add a single document to GPU vector store"""
        logger.info(
            f"[ENHANCED_VECTOR_STORE_GPU] Starting add_document for text: {text[:50]}..."
        )

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
                logger.info(
                    f"[ENHANCED_VECTOR_STORE_GPU] Embedding response: {type(embedding_response)}, length: {len(embedding_response) if embedding_response else 0}"
                )

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

    async def search(
        self, query_embedding: np.ndarray, k: int = 5
    ) -> list[tuple[DocumentChunk, float]]:
        """Search using GPU-accelerated FAISS"""
        try:
            # Check if index has any vectors
            if self.faiss_gpu_service.get_index_size() == 0:
                logger.warning("Vector store is empty, no search results available")
                return []

            # Search using GPU service
            distances, indices = await self.faiss_gpu_service.search(query_embedding, k)

            # Process results
            results = []
            for i, (distance, idx) in enumerate(
                zip(distances[0], indices[0], strict=False)
            ):
                if idx < 0 or idx >= len(self._document_ids):
                    continue

                doc_id = self._document_ids[idx]
                doc = self._documents.get(doc_id)
                if doc is None:
                    continue

                results.append((doc, float(distance)))

            return results

        except Exception as e:
            logger.error(f"Error in GPU vector store search: {e}")
            return []

    async def get_stats(self) -> dict[str, Any]:
        """Get enhanced statistics including GPU metrics"""
        base_stats = await super().get_stats()
        gpu_stats = self.faiss_gpu_service.get_statistics()

        return {**base_stats, "gpu_service": gpu_stats}

    def save_index(self, filepath: str) -> None:
        """Save GPU index to file"""
        self.faiss_gpu_service.save_index(filepath)

    def load_index(self, filepath: str, use_memory_mapping: bool = False) -> None:
        """Load index to GPU from file"""
        self.faiss_gpu_service.load_index(filepath)


# Global GPU vector store instance
gpu_vector_store = None


def get_gpu_vector_store(
    dimension: int = 768, index_type: str = "IndexIVFFlat", gpu_id: int = 0
) -> EnhancedVectorStoreGPU:
    """Get global GPU vector store instance"""
    global gpu_vector_store

    if gpu_vector_store is None:
        gpu_vector_store = EnhancedVectorStoreGPU(
            dimension=dimension,
            index_type=index_type,
            gpu_id=gpu_id,
            enable_fallback=True,
        )

    return gpu_vector_store


def benchmark_cpu_vs_gpu(
    vectors: np.ndarray, query_vector: np.ndarray, k: int = 10
) -> dict[str, Any]:
    """Benchmark CPU vs GPU performance"""
    results = {
        "cpu_time": 0.0,
        "gpu_time": 0.0,
        "speedup": 0.0,
        "gpu_available": False,
        "error": None,
    }

    try:
        dimension = vectors.shape[1]

        # CPU benchmark
        start_time = time.time()
        cpu_service = FAISSGPUService(dimension=dimension, enable_fallback=False)
        cpu_service._initialize_cpu_only()

        # Use asyncio.run for async methods
        async def run_cpu_test():
            await cpu_service.add_vectors(
                vectors, [f"doc_{i}" for i in range(len(vectors))]
            )
            return await cpu_service.search(query_vector, k)

        cpu_distances, cpu_indices = asyncio.run(run_cpu_test())
        results["cpu_time"] = time.time() - start_time

        # GPU benchmark (if available)
        if faiss.get_num_gpus() > 0:
            start_time = time.time()
            gpu_service = FAISSGPUService(dimension=dimension, enable_fallback=False)

            async def run_gpu_test():
                await gpu_service.add_vectors(
                    vectors, [f"doc_{i}" for i in range(len(vectors))]
                )
                return await gpu_service.search(query_vector, k)

            try:
                gpu_distances, gpu_indices = asyncio.run(run_gpu_test())
                results["gpu_time"] = time.time() - start_time
                results["gpu_available"] = True

                if results["gpu_time"] > 0:
                    results["speedup"] = results["cpu_time"] / results["gpu_time"]

            except Exception as e:
                results["error"] = f"GPU test failed: {e}"

        logger.info(
            f"Benchmark results: CPU={results['cpu_time']:.3f}s, "
            f"GPU={results['gpu_time']:.3f}s, "
            f"Speedup={results['speedup']:.2f}x"
        )

    except Exception as e:
        results["error"] = str(e)
        logger.error(f"Benchmark failed: {e}")

    return results
