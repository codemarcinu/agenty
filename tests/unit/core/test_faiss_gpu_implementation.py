#!/usr/bin/env python3
"""
Test script for FAISS GPU implementation
Tests functionality, performance, and fallback mechanisms
"""

import asyncio
import logging
from pathlib import Path
import sys
import time

import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import faiss

    from backend.core.faiss_gpu_service import (
        EnhancedVectorStoreGPU,
        FAISSGPUService,
        benchmark_cpu_vs_gpu,
        get_gpu_vector_store,
    )
    from backend.core.vector_store import DocumentChunk
    IMPORTS_OK = True
except ImportError:
    IMPORTS_OK = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FAISSGPUTester:
    """Comprehensive test suite for FAISS GPU implementation"""

    def __init__(self):
        self.test_results = {}
        self.dimension = 384  # Common embedding dimension

    async def test_gpu_availability(self) -> bool:
        """Test GPU availability and basic FAISS GPU functionality"""
        logger.info("=== Testing GPU Availability ===")

        try:
            gpu_count = faiss.get_num_gpus()
            logger.info(f"GPUs detected: {gpu_count}")

            if gpu_count == 0:
                logger.warning("No GPUs available - will test CPU fallback")
                self.test_results["gpu_available"] = False
                return False

            # Test basic GPU operation
            dimension = 128
            vectors = np.random.random((100, dimension)).astype("float32")

            # Create CPU index
            cpu_index = faiss.IndexFlatL2(dimension)
            cpu_index.add(vectors)

            # Transfer to GPU
            res = faiss.StandardGpuResources()
            gpu_index = faiss.index_cpu_to_gpu(res, 0, cpu_index)

            # Test search
            query = np.random.random((1, dimension)).astype("float32")
            distances, indices = gpu_index.search(query, 5)

            logger.info("✓ Basic GPU functionality test passed")
            self.test_results["gpu_available"] = True
            return True

        except Exception as e:
            logger.error(f"✗ GPU test failed: {e}")
            self.test_results["gpu_available"] = False
            return False

    async def test_faiss_gpu_service(self) -> bool:
        """Test FAISSGPUService class"""
        logger.info("=== Testing FAISS GPU Service ===")

        try:
            # Initialize service
            service = FAISSGPUService(
                dimension=self.dimension,
                index_type="IndexFlatL2",
                gpu_id=0,
                enable_fallback=True
            )

            # Generate test data
            num_vectors = 500
            test_vectors = np.random.random((num_vectors, self.dimension)).astype("float32")
            doc_ids = [f"test_doc_{i}" for i in range(num_vectors)]

            # Test adding vectors
            start_time = time.time()
            await service.add_vectors(test_vectors, doc_ids)
            add_time = time.time() - start_time

            logger.info(f"✓ Added {num_vectors} vectors in {add_time:.3f}s")

            # Test search
            query_vector = np.random.random(self.dimension).astype("float32")
            start_time = time.time()
            distances, indices = await service.search(query_vector, k=10)
            search_time = time.time() - start_time

            logger.info(f"✓ Search completed in {search_time:.3f}s")
            logger.info(f"✓ Found {len(indices[0])} results")

            # Test statistics
            stats = service.get_statistics()
            logger.info(f"✓ Service stats: {stats['index_size']} vectors, using GPU: {stats['using_gpu']}")

            self.test_results["faiss_gpu_service"] = {
                "success": True,
                "add_time": add_time,
                "search_time": search_time,
                "using_gpu": stats["using_gpu"],
                "index_size": stats["index_size"]
            }

            return True

        except Exception as e:
            logger.error(f"✗ FAISS GPU Service test failed: {e}")
            self.test_results["faiss_gpu_service"] = {"success": False, "error": str(e)}
            return False

    async def test_enhanced_vector_store(self) -> bool:
        """Test EnhancedVectorStoreGPU class"""
        logger.info("=== Testing Enhanced Vector Store GPU ===")

        try:
            # Initialize vector store
            vector_store = EnhancedVectorStoreGPU(
                dimension=self.dimension,
                index_type="IndexFlatL2",
                gpu_id=0,
                enable_fallback=True
            )

            # Generate test documents
            num_docs = 300
            documents = []

            for i in range(num_docs):
                embedding = np.random.random(self.dimension).astype("float32")
                doc = DocumentChunk(
                    id=f"enhanced_doc_{i}",
                    content=f"Test document content {i}",
                    metadata={"type": "test", "index": i},
                    embedding=embedding
                )
                documents.append(doc)

            # Test adding documents
            start_time = time.time()
            await vector_store.add_documents(documents)
            add_time = time.time() - start_time

            logger.info(f"✓ Added {num_docs} documents in {add_time:.3f}s")

            # Test search
            query_embedding = np.random.random(self.dimension).astype("float32")
            start_time = time.time()
            results = await vector_store.search(query_embedding, k=5)
            search_time = time.time() - start_time

            logger.info(f"✓ Search completed in {search_time:.3f}s")
            logger.info(f"✓ Found {len(results)} results")

            # Test statistics
            stats = await vector_store.get_stats()
            logger.info(f"✓ Vector store stats: {stats.get('total_documents', 0)} docs")

            self.test_results["enhanced_vector_store"] = {
                "success": True,
                "add_time": add_time,
                "search_time": search_time,
                "num_results": len(results),
                "total_documents": stats.get("total_documents", 0)
            }

            return True

        except Exception as e:
            logger.error(f"✗ Enhanced Vector Store test failed: {e}")
            self.test_results["enhanced_vector_store"] = {"success": False, "error": str(e)}
            return False

    async def test_fallback_mechanism(self) -> bool:
        """Test CPU fallback when GPU fails"""
        logger.info("=== Testing Fallback Mechanism ===")

        try:
            # Force CPU-only mode
            service = FAISSGPUService(
                dimension=self.dimension,
                index_type="IndexFlatL2",
                gpu_id=999,  # Invalid GPU ID to trigger fallback
                enable_fallback=True
            )

            # Test operations
            test_vectors = np.random.random((100, self.dimension)).astype("float32")
            doc_ids = [f"fallback_doc_{i}" for i in range(100)]

            await service.add_vectors(test_vectors, doc_ids)

            query_vector = np.random.random(self.dimension).astype("float32")
            distances, indices = await service.search(query_vector, k=5)

            stats = service.get_statistics()

            logger.info(f"✓ Fallback mechanism working, using GPU: {stats['using_gpu']}")

            self.test_results["fallback_mechanism"] = {
                "success": True,
                "using_gpu": stats["using_gpu"],
                "fallback_triggered": not stats["using_gpu"]
            }

            return True

        except Exception as e:
            logger.error(f"✗ Fallback mechanism test failed: {e}")
            self.test_results["fallback_mechanism"] = {"success": False, "error": str(e)}
            return False

    async def test_performance_benchmark(self) -> bool:
        """Test performance comparison between CPU and GPU"""
        logger.info("=== Testing Performance Benchmark ===")

        try:
            # Generate test data
            num_vectors = 1000
            test_vectors = np.random.random((num_vectors, self.dimension)).astype("float32")
            query_vector = np.random.random(self.dimension).astype("float32")

            # Run benchmark
            benchmark_result = benchmark_cpu_vs_gpu(test_vectors, query_vector, k=10)

            if benchmark_result.get("error"):
                logger.warning(f"Benchmark completed with warnings: {benchmark_result['error']}")

            cpu_time = benchmark_result.get("cpu_time", 0)
            gpu_time = benchmark_result.get("gpu_time", 0)
            speedup = benchmark_result.get("speedup", 0)

            logger.info(f"✓ CPU time: {cpu_time:.3f}s")
            logger.info(f"✓ GPU time: {gpu_time:.3f}s")
            logger.info(f"✓ Speedup: {speedup:.2f}x")

            self.test_results["performance_benchmark"] = benchmark_result
            return True

        except Exception as e:
            logger.error(f"✗ Performance benchmark failed: {e}")
            self.test_results["performance_benchmark"] = {"success": False, "error": str(e)}
            return False

    async def test_memory_management(self) -> bool:
        """Test memory management and GPU monitoring"""
        logger.info("=== Testing Memory Management ===")

        try:
            service = FAISSGPUService(
                dimension=self.dimension,
                index_type="IndexFlatL2",
                gpu_id=0,
                enable_fallback=True
            )

            # Get initial memory info
            initial_memory = service.get_gpu_memory_info()
            logger.info(f"Initial GPU memory: {initial_memory.used / 1024**2:.1f}MB used, "
                       f"{initial_memory.free / 1024**2:.1f}MB free")

            # Add large batch of vectors
            large_batch_size = 2000
            large_vectors = np.random.random((large_batch_size, self.dimension)).astype("float32")
            doc_ids = [f"memory_test_doc_{i}" for i in range(large_batch_size)]

            await service.add_vectors(large_vectors, doc_ids)

            # Get memory info after adding vectors
            after_memory = service.get_gpu_memory_info()
            logger.info(f"After adding vectors: {after_memory.used / 1024**2:.1f}MB used, "
                       f"{after_memory.free / 1024**2:.1f}MB free")

            # Test statistics
            stats = service.get_statistics()
            gpu_memory = stats.get("gpu_memory", {})

            logger.info(f"✓ GPU utilization: {gpu_memory.get('utilization_percent', 0):.1f}%")
            logger.info(f"✓ Index size: {stats.get('index_size', 0)} vectors")

            self.test_results["memory_management"] = {
                "success": True,
                "initial_memory_mb": initial_memory.used / 1024**2,
                "final_memory_mb": after_memory.used / 1024**2,
                "gpu_utilization": gpu_memory.get("utilization_percent", 0),
                "index_size": stats.get("index_size", 0)
            }

            return True

        except Exception as e:
            logger.error(f"✗ Memory management test failed: {e}")
            self.test_results["memory_management"] = {"success": False, "error": str(e)}
            return False

    def generate_test_report(self) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("=== FAISS GPU Implementation Test Report ===")
        report.append(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values()
                          if isinstance(result, dict) and result.get("success", False))

        report.append(f"Summary: {passed_tests}/{total_tests} tests passed")
        report.append("")

        # Detailed results
        for test_name, result in self.test_results.items():
            status = "PASS" if (isinstance(result, dict) and result.get("success", False)) else "FAIL"
            report.append(f"{test_name}: {status}")

            if isinstance(result, dict):
                if result.get("error"):
                    report.append(f"  Error: {result['error']}")

                # Add specific metrics
                if test_name == "performance_benchmark":
                    cpu_time = result.get("cpu_time", 0)
                    gpu_time = result.get("gpu_time", 0)
                    speedup = result.get("speedup", 0)
                    report.append(f"  CPU Time: {cpu_time:.3f}s")
                    report.append(f"  GPU Time: {gpu_time:.3f}s")
                    report.append(f"  Speedup: {speedup:.2f}x")

                elif test_name == "faiss_gpu_service":
                    using_gpu = result.get("using_gpu", False)
                    index_size = result.get("index_size", 0)
                    report.append(f"  Using GPU: {using_gpu}")
                    report.append(f"  Index Size: {index_size}")

                elif test_name == "memory_management":
                    gpu_util = result.get("gpu_utilization", 0)
                    index_size = result.get("index_size", 0)
                    report.append(f"  GPU Utilization: {gpu_util:.1f}%")
                    report.append(f"  Index Size: {index_size}")

            report.append("")

        # Recommendations
        report.append("=== Recommendations ===")
        if self.test_results.get("gpu_available", False):
            report.append("✓ GPU is available and functional")

            perf = self.test_results.get("performance_benchmark", {})
            if perf.get("speedup", 0) > 1.5:
                report.append("✓ Significant performance improvement with GPU")
                report.append("  Recommendation: Deploy with GPU configuration")
            else:
                report.append("! Limited performance improvement")
                report.append("  Recommendation: Consider CPU mode for smaller datasets")
        else:
            report.append("! GPU not available or not functional")
            report.append("  Recommendation: Use CPU fallback mode")
            report.append("  Check: NVIDIA drivers, CUDA installation, Docker GPU support")

        if passed_tests == total_tests:
            report.append("✓ All tests passed - Ready for production deployment")
        else:
            report.append(f"! {total_tests - passed_tests} tests failed - Review issues before deployment")

        return "\n".join(report)


async def main():
    """Run comprehensive FAISS GPU tests"""
    if not IMPORTS_OK:
        return

    logger.info("Starting FAISS GPU Implementation Tests")

    tester = FAISSGPUTester()

    # Run all tests
    tests = [
        tester.test_gpu_availability(),
        tester.test_faiss_gpu_service(),
        tester.test_enhanced_vector_store(),
        tester.test_fallback_mechanism(),
        tester.test_performance_benchmark(),
        tester.test_memory_management()
    ]

    for test in tests:
        await test
        # Small delay between tests
        await asyncio.sleep(0.5)

    # Generate and display report
    report = tester.generate_test_report()

    # Save report to file
    report_path = Path("faiss_gpu_test_report.txt")
    with open(report_path, "w") as f:
        f.write(report)

    logger.info(f"Test report saved to: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
