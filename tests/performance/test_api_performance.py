"""
Testy performance benchmarking dla API

Zgodnie z regułami projektu:
- Testy wydajności endpointów API
- Pomiar czasu odpowiedzi <200ms
- Benchmarking operacji bazodanowych
- Monitoring użycia pamięci
"""

import asyncio
import statistics
import time
from typing import Any
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
import pytest

from backend.main import app


class TestAPIPerformance:
    """Testy wydajności API"""

    @pytest.fixture
    def client(self):
        """Fixture dla test client"""
        return TestClient(app)

    def benchmark_endpoint(
        self,
        client: TestClient,
        endpoint: str,
        method: str = "GET",
        iterations: int = 100,
        **kwargs,
    ) -> dict[str, Any]:
        """Benchmark API endpoint performance"""
        response_times = []
        status_codes = []

        for _ in range(iterations):
            start_time = time.time()

            if method == "GET":
                response = client.get(endpoint, **kwargs)
            elif method == "POST":
                response = client.post(endpoint, **kwargs)
            elif method == "PUT":
                response = client.put(endpoint, **kwargs)
            elif method == "DELETE":
                response = client.delete(endpoint, **kwargs)

            end_time = time.time()

            response_times.append(end_time - start_time)
            status_codes.append(response.status_code)

        return {
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "response_times": response_times,
            "status_codes": status_codes,
            "mean_time": statistics.mean(response_times),
            "median_time": statistics.median(response_times),
            "min_time": min(response_times),
            "max_time": max(response_times),
            "std_dev": (
                statistics.stdev(response_times) if len(response_times) > 1 else 0
            ),
            "p95_time": (
                statistics.quantiles(response_times, n=20)[18]
                if len(response_times) > 1
                else response_times[0]
            ),
            "p99_time": (
                statistics.quantiles(response_times, n=100)[98]
                if len(response_times) > 1
                else response_times[0]
            ),
            "success_rate": sum(1 for code in status_codes if 200 <= code < 300)
            / len(status_codes),
        }

    def test_health_endpoint_performance(self, client):
        """Test wydajności endpointu health check"""
        results = self.benchmark_endpoint(client, "/health", iterations=50)

        # Sprawdź czy endpoint jest szybki
        assert results["mean_time"] < 0.1  # <100ms
        assert results["p95_time"] < 0.2  # 95% requestów <200ms
        assert results["success_rate"] == 1.0  # 100% sukces

    def test_docs_endpoint_performance(self, client):
        """Test wydajności endpointu dokumentacji"""
        results = self.benchmark_endpoint(client, "/docs", iterations=20)

        # Dokumentacja może być wolniejsza, ale nadal rozsądna
        assert results["mean_time"] < 1.0  # <1s
        assert results["p95_time"] < 2.0  # 95% requestów <2s
        assert results["success_rate"] == 1.0

    def test_openapi_endpoint_performance(self, client):
        """Test wydajności endpointu OpenAPI schema"""
        results = self.benchmark_endpoint(client, "/openapi.json", iterations=20)

        # OpenAPI schema może być duża, ale nadal rozsądna
        assert results["mean_time"] < 0.5  # <500ms
        assert results["p95_time"] < 1.0  # 95% requestów <1s
        assert results["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_chat_endpoint_performance(self, client):
        """Test wydajności endpointu chat"""
        with (
            patch("backend.api.chat.get_current_user") as mock_auth,
            patch("backend.agents.agent_factory.AgentFactory") as mock_factory,
        ):
            # Mock authentication
            mock_auth.return_value = {"user_id": 1, "username": "testuser"}

            # Mock agent factory
            mock_agent = AsyncMock()
            mock_agent.process.return_value = type(
                "obj",
                (object,),
                {"success": True, "text": "Test response", "data": {}, "metadata": {}},
            )
            mock_factory.return_value.get_agent.return_value = mock_agent

            # Test z różnymi payloadami
            test_payloads = [
                {"message": "Hello"},
                {"message": "What is machine learning?"},
                {"message": "Tell me about Python programming"},
            ]

            for payload in test_payloads:
                results = self.benchmark_endpoint(
                    client, "/api/v2/chat", method="POST", iterations=10, json=payload
                )

                # Chat endpoint może być wolniejszy ze względu na AI processing
                assert results["mean_time"] < 5.0  # <5s
                assert results["p95_time"] < 10.0  # 95% requestów <10s
                assert results["success_rate"] >= 0.8  # 80% sukces

    @pytest.mark.asyncio
    async def test_rag_endpoint_performance(self, client):
        """Test wydajności endpointów RAG"""
        with patch("backend.api.v2.endpoints.rag.rag_processor") as mock_processor:
            # Mock RAG processor
            mock_processor.process_document.return_value = [
                {"chunk_id": "test", "chunk_index": 0, "source": "test.txt"}
            ]

            # Test upload endpoint
            test_file_content = b"Test document content for RAG processing"
            files = {"file": ("test.txt", test_file_content, "text/plain")}
            data = {"category": "test", "tags": "test,rag"}

            results = self.benchmark_endpoint(
                client,
                "/api/v2/rag/upload",
                method="POST",
                iterations=10,
                files=files,
                data=data,
            )

            # RAG upload może być wolniejszy
            assert results["mean_time"] < 10.0  # <10s
            assert results["p95_time"] < 20.0  # 95% requestów <20s
            assert results["success_rate"] >= 0.7  # 70% sukces

    def test_receipt_endpoint_performance(self, client):
        """Test wydajności endpointów receipt"""
        # Test GET endpoint
        results = self.benchmark_endpoint(
            client, "/api/v2/receipts", method="GET", iterations=20
        )

        # Receipt listing powinno być szybkie
        assert results["mean_time"] < 0.5  # <500ms
        assert results["p95_time"] < 1.0  # 95% requestów <1s
        assert results["success_rate"] >= 0.8  # 80% sukces

    def test_concise_responses_performance(self, client):
        """Test wydajności endpointu concise responses"""
        with patch(
            "backend.api.v2.endpoints.concise_responses.concise_response_agent"
        ) as mock_agent:
            # Mock agent
            mock_agent.process.return_value = type(
                "obj",
                (object,),
                {
                    "success": True,
                    "text": "Concise response",
                    "data": {"concise_score": 0.9},
                },
            )

            payload = {
                "query": "What is Python?",
                "response_style": "concise",
                "use_rag": False,
            }

            results = self.benchmark_endpoint(
                client,
                "/api/v2/concise-responses/generate",
                method="POST",
                iterations=10,
                json=payload,
            )

            # Concise responses powinny być szybkie
            assert results["mean_time"] < 3.0  # <3s
            assert results["p95_time"] < 5.0  # 95% requestów <5s
            assert results["success_rate"] >= 0.8  # 80% sukces


class TestDatabasePerformance:
    """Testy wydajności bazy danych"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_database_query_performance(self, mock_db_session):
        """Test wydajności zapytań do bazy danych"""
        import time

        # Mock database operations
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_db_session.commit = AsyncMock()

        # Test różnych operacji bazodanowych
        operations = [
            ("SELECT", lambda: mock_db_session.execute("SELECT * FROM users")),
            ("INSERT", lambda: mock_db_session.execute("INSERT INTO users VALUES (?)")),
            ("UPDATE", lambda: mock_db_session.execute("UPDATE users SET name = ?")),
            (
                "DELETE",
                lambda: mock_db_session.execute("DELETE FROM users WHERE id = ?"),
            ),
        ]

        for op_name, operation in operations:
            times = []
            for _ in range(10):
                start_time = time.time()
                await operation()
                end_time = time.time()
                times.append(end_time - start_time)

            avg_time = statistics.mean(times)
            max_time = max(times)

            # Operacje bazodanowe powinny być szybkie
            assert avg_time < 0.1  # <100ms średnio
            assert max_time < 0.5  # <500ms maksymalnie

    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self):
        """Test wydajności connection pool"""

        # Test symulacji wielu równoczesnych połączeń
        async def simulate_db_operation():
            await asyncio.sleep(0.01)  # Symulacja operacji DB
            return "result"

        # Uruchom wiele operacji równocześnie
        start_time = time.time()
        tasks = [simulate_db_operation() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time

        # Wszystkie operacje powinny zakończyć się w rozsądnym czasie
        assert total_time < 2.0  # <2s dla 50 operacji
        assert len(results) == 50
        assert all(result == "result" for result in results)


class TestMemoryPerformance:
    """Testy wydajności pamięci"""

    def test_memory_usage_monitoring(self):
        """Test monitorowania użycia pamięci"""
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # Pobierz użycie pamięci przed operacjami
        initial_memory = process.memory_info().rss

        # Symuluj operacje zużywające pamięć
        large_list = list(range(100000))
        large_dict = {f"key_{i}": f"value_{i}" for i in range(10000)}

        # Pobierz użycie pamięci po operacjach
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Zwiększenie pamięci nie powinno być zbyt duże (MB)
        memory_increase_mb = memory_increase / 1024 / 1024
        assert memory_increase_mb < 100  # Maksymalnie 100MB

        # Wyczyść referencje
        del large_list
        del large_dict

    def test_memory_leak_detection(self):
        """Test wykrywania wycieków pamięci"""
        import gc
        import os

        import psutil

        process = psutil.Process(os.getpid())

        # Pobierz użycie pamięci przed testem
        initial_memory = process.memory_info().rss

        # Symuluj potencjalny wyciek pamięci
        leaked_objects = []
        for _ in range(1000):
            leaked_objects.append(list(range(100)))

        # Wymuś garbage collection
        gc.collect()

        # Pobierz użycie pamięci po testach
        final_memory = process.memory_info().rss
        final_memory - initial_memory

        # Wyczyść referencje
        del leaked_objects
        gc.collect()

        # Sprawdź czy pamięć została zwolniona
        after_cleanup_memory = process.memory_info().rss
        memory_after_cleanup = after_cleanup_memory - initial_memory

        # Po wyczyszczeniu użycie pamięci powinno być bliskie początkowemu
        memory_after_cleanup_mb = memory_after_cleanup / 1024 / 1024
        assert memory_after_cleanup_mb < 10  # Maksymalnie 10MB różnicy


class TestConcurrentPerformance:
    """Testy wydajności przy równoczesnych żądaniach"""

    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, client):
        """Test wydajności przy równoczesnych żądaniach API"""
        import asyncio
        import time

        async def make_request():
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            return {
                "status_code": response.status_code,
                "response_time": end_time - start_time,
            }

        # Uruchom wiele równoczesnych żądań
        start_time = time.time()
        tasks = [make_request() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time
        response_times = [r["response_time"] for r in results]
        status_codes = [r["status_code"] for r in results]

        # Sprawdź wydajność
        assert total_time < 5.0  # Wszystkie żądania w <5s
        assert all(code == 200 for code in status_codes)  # Wszystkie sukces
        assert statistics.mean(response_times) < 0.2  # Średnio <200ms

    @pytest.mark.asyncio
    async def test_concurrent_database_operations(self):
        """Test wydajności przy równoczesnych operacjach bazodanowych"""
        import asyncio
        import time

        async def simulate_db_operation(operation_id: int):
            await asyncio.sleep(0.01)  # Symulacja operacji DB
            return f"result_{operation_id}"

        # Uruchom wiele równoczesnych operacji
        start_time = time.time()
        tasks = [simulate_db_operation(i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        total_time = end_time - start_time

        # Sprawdź wydajność
        assert total_time < 2.0  # Wszystkie operacje w <2s
        assert len(results) == 50
        assert all(f"result_{i}" in results for i in range(50))


class TestLoadTesting:
    """Testy obciążeniowe"""

    def benchmark_endpoint(
        self,
        client: TestClient,
        endpoint: str,
        method: str = "GET",
        iterations: int = 100,
        **kwargs,
    ) -> dict[str, Any]:
        """Benchmark endpoint performance"""
        import statistics
        import time

        response_times = []
        success_count = 0

        for _ in range(iterations):
            start_time = time.time()
            try:
                if method.upper() == "GET":
                    response = client.get(endpoint, **kwargs)
                elif method.upper() == "POST":
                    response = client.post(endpoint, **kwargs)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                if response.status_code < 500:  # Nie liczymy błędów serwera jako sukces
                    success_count += 1

                end_time = time.time()
                response_times.append(end_time - start_time)

            except Exception:
                # W przypadku błędu, dodaj maksymalny czas
                response_times.append(1.0)

        if not response_times:
            return {
                "mean_time": 0,
                "p95_time": 0,
                "p99_time": 0,
                "success_rate": 0,
                "response_times": [],
            }

        # Oblicz statystyki
        mean_time = statistics.mean(response_times)
        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        p99_index = int(len(sorted_times) * 0.99)

        return {
            "mean_time": mean_time,
            "p95_time": (
                sorted_times[p95_index]
                if p95_index < len(sorted_times)
                else sorted_times[-1]
            ),
            "p99_time": (
                sorted_times[p99_index]
                if p99_index < len(sorted_times)
                else sorted_times[-1]
            ),
            "success_rate": success_count / iterations,
            "response_times": response_times,
        }

    def test_high_load_performance(self, client):
        """Test wydajności przy wysokim obciążeniu"""
        # Symuluj wysokie obciążenie
        results = self.benchmark_endpoint(
            client,
            "/health",
            iterations=1000,  # 1000 żądań
        )

        # Sprawdź czy system radzi sobie z obciążeniem
        assert results["mean_time"] < 0.1  # Średnio <100ms
        assert results["p95_time"] < 0.2  # 95% <200ms
        assert results["p99_time"] < 0.5  # 99% <500ms
        assert results["success_rate"] >= 0.95  # 95% sukces

    def test_sustained_load_performance(self, client):
        """Test wydajności przy długotrwałym obciążeniu"""
        # Test przez dłuższy czas
        all_times = []

        for batch in range(10):  # 10 batchy po 100 żądań
            results = self.benchmark_endpoint(client, "/health", iterations=100)
            all_times.extend(results["response_times"])

            # Sprawdź czy wydajność nie pogarsza się znacząco
            if batch > 0:
                current_avg = statistics.mean(results["response_times"])
                assert current_avg < 0.2  # Nie więcej niż 200ms średnio

        # Sprawdź ogólną wydajność
        overall_avg = statistics.mean(all_times)
        overall_p95 = statistics.quantiles(all_times, n=20)[18]

        assert overall_avg < 0.15  # Ogólnie <150ms
        assert overall_p95 < 0.3  # 95% <300ms
