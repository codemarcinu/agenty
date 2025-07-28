#!/usr/bin/env python3
"""
Test script for frontend-backend connectivity
Tests the main API endpoints that frontend would use
"""

import asyncio
import json
import logging
from typing import Any

import aiohttp

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FrontendBackendConnectivityTest:
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.test_results = {}

    async def test_health_endpoint(self) -> dict[str, Any]:
        """Test the health endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data, "status": response.status}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}", "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e), "status": None}

    async def test_agents_endpoint(self) -> dict[str, Any]:
        """Test the agents endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/agents/agents") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data, "status": response.status}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}", "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e), "status": None}

    async def test_chat_endpoint(self) -> dict[str, Any]:
        """Test the chat endpoint"""
        try:
            payload = {
                "message": "Hello, this is a test message",
                "agent_type": "general_conversation",
                "session_id": "test_session"
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.backend_url}/api/chat/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data, "status": response.status}
                    else:
                        text = await response.text()
                        return {"success": False, "error": f"HTTP {response.status}: {text}", "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e), "status": None}

    async def test_pantry_endpoint(self) -> dict[str, Any]:
        """Test the pantry endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/pantry/list") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data, "status": response.status}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}", "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e), "status": None}

    async def test_rag_stats_endpoint(self) -> dict[str, Any]:
        """Test the RAG statistics endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/v2/rag/stats") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data, "status": response.status}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}", "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e), "status": None}

    async def test_rag_v3_stats_endpoint(self) -> dict[str, Any]:
        """Test the RAG v3 statistics endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/api/v3/rag/stats") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data, "status": response.status}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}", "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e), "status": None}

    async def test_rag_search_endpoint(self) -> dict[str, Any]:
        """Test the RAG search endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.backend_url}/api/v2/rag/search",
                    params={"query": "test search", "top_k": 5}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data, "status": response.status}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}", "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e), "status": None}

    async def test_cors_headers(self) -> dict[str, Any]:
        """Test CORS headers for frontend compatibility"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.options(
                    f"{self.backend_url}/api/chat/chat",
                    headers={
                        "Origin": "http://localhost:1420",
                        "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "Content-Type"
                    }
                ) as response:
                    cors_headers = {
                        "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                        "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                        "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
                    }
                    return {"success": True, "cors_headers": cors_headers, "status": response.status}
        except Exception as e:
            return {"success": False, "error": str(e), "status": None}

    async def run_all_tests(self) -> dict[str, Any]:
        """Run all connectivity tests"""
        logger.info("Starting frontend-backend connectivity tests...")

        tests = [
            ("health", self.test_health_endpoint()),
            ("agents", self.test_agents_endpoint()),
            ("chat", self.test_chat_endpoint()),
            ("pantry", self.test_pantry_endpoint()),
            ("rag_stats_v2", self.test_rag_stats_endpoint()),
            ("rag_stats_v3", self.test_rag_v3_stats_endpoint()),
            ("rag_search", self.test_rag_search_endpoint()),
            ("cors_headers", self.test_cors_headers())
        ]

        results = {}
        for test_name, test_coro in tests:
            logger.info(f"Running {test_name} test...")
            try:
                result = await test_coro
                results[test_name] = result
                if result["success"]:
                    logger.info(f"✓ {test_name} test: PASSED")
                else:
                    logger.error(f"✗ {test_name} test: FAILED - {result.get('error', 'Unknown error')}")
            except Exception as e:
                logger.error(f"✗ {test_name} test: ERROR - {e}")
                results[test_name] = {"success": False, "error": str(e)}

        return results

    def generate_report(self, results: dict[str, Any]) -> str:
        """Generate a test report"""
        report = []
        report.append("=== Frontend-Backend Connectivity Test Report ===")
        report.append(f"Backend URL: {self.backend_url}")
        report.append("")

        passed = sum(1 for r in results.values() if r.get("success", False))
        total = len(results)
        report.append(f"Summary: {passed}/{total} tests passed")
        report.append("")

        for test_name, result in results.items():
            status = "PASS" if result.get("success", False) else "FAIL"
            report.append(f"{test_name}: {status}")

            if result.get("success", False):
                if "data" in result:
                    data = result["data"]
                    if isinstance(data, dict):
                        # Show key information
                        if "status" in data:
                            report.append(f"  Status: {data['status']}")
                        if "message" in data:
                            report.append(f"  Message: {data['message']}")
                        if "data" in data and isinstance(data["data"], dict):
                            inner_data = data["data"]
                            if "total_documents" in inner_data:
                                report.append(f"  Documents: {inner_data['total_documents']}")
                            if "total_vectors" in inner_data:
                                report.append(f"  Vectors: {inner_data['total_vectors']}")
                elif "cors_headers" in result:
                    headers = result["cors_headers"]
                    report.append(f"  CORS Origin: {headers.get('Access-Control-Allow-Origin', 'None')}")
                    report.append(f"  CORS Methods: {headers.get('Access-Control-Allow-Methods', 'None')}")
            else:
                report.append(f"  Error: {result.get('error', 'Unknown error')}")
                if "status" in result:
                    report.append(f"  HTTP Status: {result['status']}")

            report.append("")

        # Recommendations
        report.append("=== Recommendations ===")

        health_result = results.get("health", {})
        if health_result.get("success", False):
            report.append("✓ Backend is healthy and responding")
        else:
            report.append("✗ Backend health check failed - check if backend is running")
            return "\n".join(report)

        cors_result = results.get("cors_headers", {})
        if cors_result.get("success", False):
            cors_headers = cors_result.get("cors_headers", {})
            if cors_headers.get("Access-Control-Allow-Origin"):
                report.append("✓ CORS headers are configured")
            else:
                report.append("! CORS headers may need configuration for frontend access")

        chat_result = results.get("chat", {})
        if chat_result.get("success", False):
            report.append("✓ Chat functionality is working")
        else:
            report.append("! Chat functionality may need testing")

        rag_v3_result = results.get("rag_stats_v3", {})
        if rag_v3_result.get("success", False):
            report.append("✓ RAG v3 system is accessible")
        else:
            report.append("! RAG v3 system may need configuration")

        if passed == total:
            report.append("✓ All tests passed - Frontend-backend connectivity is ready")
        else:
            report.append(f"! {total - passed} tests failed - Review issues above")

        return "\n".join(report)


async def main():
    """Run the connectivity tests"""
    tester = FrontendBackendConnectivityTest()
    results = await tester.run_all_tests()

    report = tester.generate_report(results)

    # Save results to file
    with open("frontend_backend_connectivity_test.json", "w") as f:
        json.dump(results, f, indent=2)

    # Save report to file
    with open("frontend_backend_connectivity_report.txt", "w") as f:
        f.write(report)

    logger.info("Test results saved to frontend_backend_connectivity_test.json")
    logger.info("Test report saved to frontend_backend_connectivity_report.txt")


if __name__ == "__main__":
    asyncio.run(main())
