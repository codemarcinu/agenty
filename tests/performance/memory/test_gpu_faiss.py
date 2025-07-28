#!/usr/bin/env python3
"""
Test script for GPU FAISS functionality
"""

import logging

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_faiss_gpu():
    """Test FAISS GPU functionality"""
    try:
        import faiss

        logger.info(f"FAISS version: {faiss.__version__}")

        # Check GPU support
        gpu_available = hasattr(faiss, "GpuIndexIVFFlat")
        logger.info(f"GPU FAISS available: {gpu_available}")

        if gpu_available:
            try:
                import faiss.contrib.gpu_resources

                logger.info("GPU resources module available")

                # Test GPU resources initialization
                gpu_resources = faiss.contrib.gpu_resources.GpuResources()
                logger.info("GPU resources initialized successfully")

                # Test GPU index creation
                dimension = 768
                cpu_index = faiss.IndexFlatL2(dimension)

                # Create some test vectors
                vectors = np.random.random((1000, dimension)).astype("float32")
                cpu_index.add(vectors)

                # Convert to GPU index
                gpu_index = faiss.index_cpu_to_gpu(gpu_resources, 0, cpu_index)
                logger.info("GPU index created successfully")

                # Test search on GPU
                query = np.random.random((1, dimension)).astype("float32")
                distances, indices = gpu_index.search(query, 5)
                logger.info(f"GPU search successful: found {len(indices[0])} results")

                # Convert back to CPU
                faiss.index_gpu_to_cpu(gpu_index)
                logger.info("GPU to CPU conversion successful")

                logger.info("✅ GPU FAISS test PASSED")
                return True

            except Exception as e:
                logger.error(f"❌ GPU FAISS test FAILED: {e}")
                return False
        else:
            logger.warning("⚠️ GPU FAISS not available")
            return False

    except ImportError as e:
        logger.error(f"❌ FAISS not available: {e}")
        return False


def test_vector_store_gpu():
    """Test VectorStore with GPU support"""
    try:
        from backend.core.vector_store import VectorStore

        # Test VectorStore with GPU
        vs = VectorStore(dimension=768, index_type="IndexIVFFlat", use_gpu=True)

        # Check if GPU is actually being used
        stats = vs._stats
        gpu_enabled = stats.get("gpu_enabled", False)

        logger.info(f"VectorStore GPU enabled: {gpu_enabled}")

        if gpu_enabled:
            logger.info("✅ VectorStore GPU test PASSED")
        else:
            logger.warning("⚠️ VectorStore using CPU fallback")

        return gpu_enabled

    except Exception as e:
        logger.error(f"❌ VectorStore GPU test FAILED: {e}")
        return False


if __name__ == "__main__":
    logger.info("🧪 Testing GPU FAISS functionality...")

    # Test basic FAISS GPU
    faiss_gpu_ok = test_faiss_gpu()

    # Test VectorStore GPU
    vectorstore_gpu_ok = test_vector_store_gpu()

    # Summary
    logger.info("\n📊 Test Results:")
    logger.info(f"FAISS GPU: {'✅ PASS' if faiss_gpu_ok else '❌ FAIL'}")
    logger.info(f"VectorStore GPU: {'✅ PASS' if vectorstore_gpu_ok else '❌ FAIL'}")

    if faiss_gpu_ok and vectorstore_gpu_ok:
        logger.info("🎉 All GPU tests passed! GPU FAISS is working.")
    else:
        logger.info("⚠️ Some tests failed. Check the logs above for details.")
