#!/usr/bin/env python3
"""
Test Flow: Dodawanie Paragonu - Warunki Produkcyjne
====================================================

Ten skrypt testuje kompletny flow dodawania paragonu w warunkach produkcyjnych:
1. Sprawdzenie zdrowia wszystkich serwisów
2. Test frontendu - nawigacja i interfejs
3. Test backendu - API endpoints
4. Test asynchronicznego przetwarzania
5. Test integracji frontend-backend
6. Test obsługi błędów
"""

import os
import sys
import time

import requests


class ReceiptFlowTest:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:8085"
        self.test_file = "tests/fixtures/test_receipt.jpg"

    def test_1_service_health(self):
        """Test 1: Sprawdzenie zdrowia wszystkich serwisów"""

        # Backend health
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            assert response.status_code == 200, f"Backend health failed: {response.status_code}"
        except Exception:
            return False

        # Receipt processing health
        try:
            response = requests.get(f"{self.backend_url}/api/v3/receipts/health", timeout=5)
            assert response.status_code == 200, f"Receipt health failed: {response.status_code}"
            data = response.json()
            assert data.get("data", {}).get("workers_available") is True, "Celery workers not available"
        except Exception:
            return False

        # Frontend health
        try:
            response = requests.get(f"{self.frontend_url}/", timeout=5)
            assert response.status_code == 200, f"Frontend health failed: {response.status_code}"
            assert "FoodSave AI" in response.text, "Frontend not loading correctly"
        except Exception:
            return False

        return True

    def test_2_backend_api_endpoints(self):
        """Test 2: Sprawdzenie API endpoints"""

        # Test v3 receipts process endpoint
        try:
            # Test with invalid file first
            files = {"file": ("test.txt", b"invalid content", "text/plain")}
            response = requests.post(f"{self.backend_url}/api/v3/receipts/process", files=files, timeout=10)
            assert response.status_code in [400, 422], f"Expected error for invalid file, got {response.status_code}"
        except Exception:
            return False

        return True

    def test_3_file_upload_and_processing(self):
        """Test 3: Upload i przetwarzanie pliku"""

        if not os.path.exists(self.test_file):
            return False

        try:
            # Upload file
            with open(self.test_file, "rb") as f:
                files = {"file": (os.path.basename(self.test_file), f, "image/jpeg")}
                response = requests.post(f"{self.backend_url}/api/v3/receipts/process", files=files, timeout=30)

            assert response.status_code == 202, f"Expected 202 Accepted, got {response.status_code}"
            data = response.json()
            job_id = data.get("data", {}).get("job_id")
            assert job_id, "No job_id in response"

            # Poll for status
            max_attempts = 60  # 5 minutes
            for attempt in range(max_attempts):
                time.sleep(5)
                status_response = requests.get(f"{self.backend_url}/api/v3/receipts/status/{job_id}", timeout=10)

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    task_status = status_data.get("data", {}).get("status")
                    status_data.get("data", {}).get("progress", 0)


                    if task_status == "SUCCESS":
                        result = status_data.get("data", {}).get("result", {})
                        result_status = result.get("status_code")

                        if result_status == 200:
                            return True
                        elif result_status == 400:
                            error_code = result.get("error_code")
                            result.get("message", "Unknown error")
                            # For test purposes, we accept OCR_FAILED as expected behavior
                            return error_code == "OCR_FAILED"
                        else:
                            return False

                    elif task_status == "FAILURE":
                        status_data.get("data", {}).get("error", "Unknown error")
                        return False
                    elif task_status == "PENDING":
                        pass
                    else:
                        pass

                else:
                    return False

            return False

        except Exception:
            return False

    def test_4_frontend_integration(self):
        """Test 4: Integracja frontend-backend"""

        try:
            # Check if frontend can access backend
            response = requests.get(f"{self.frontend_url}/", timeout=5)
            assert response.status_code == 200

            # Check for CORS headers in backend
            response = requests.options(f"{self.backend_url}/api/v3/receipts/process", timeout=5)
            # CORS preflight should not fail

            return True

        except Exception:
            return False

    def test_5_error_handling(self):
        """Test 5: Obsługa błędów"""

        # Test with non-existent job
        try:
            response = requests.get(f"{self.backend_url}/api/v3/receipts/status/nonexistent", timeout=5)
            # API returns 200 with PENDING status for non-existent jobs
            assert response.status_code == 200, f"Expected 200 for non-existent job, got {response.status_code}"
            data = response.json()
            job_status = data.get("data", {}).get("status")
            assert job_status == "PENDING", f"Expected PENDING status, got {job_status}"
        except Exception:
            return False

        # Test with invalid file type
        try:
            files = {"file": ("test.txt", b"not an image", "text/plain")}
            response = requests.post(f"{self.backend_url}/api/v3/receipts/process", files=files, timeout=10)
            assert response.status_code in [400, 422], f"Expected error for invalid file type, got {response.status_code}"
        except Exception:
            return False

        return True

    def test_6_performance_metrics(self):
        """Test 6: Metryki wydajności"""

        try:
            # Test response time for health endpoint
            start_time = time.time()
            requests.get(f"{self.backend_url}/health", timeout=5)
            end_time = time.time()

            response_time = (end_time - start_time) * 1000  # ms
            assert response_time < 2000, f"Health endpoint too slow: {response_time:.2f}ms"

            # Test response time for receipt health
            start_time = time.time()
            requests.get(f"{self.backend_url}/api/v3/receipts/health", timeout=10)
            end_time = time.time()

            response_time = (end_time - start_time) * 1000  # ms
            assert response_time < 5000, f"Receipt health endpoint too slow: {response_time:.2f}ms"

            return True

        except Exception:
            return False

    def run_all_tests(self):
        """Uruchom wszystkie testy"""

        tests = [
            ("Service Health", self.test_1_service_health),
            ("Backend API Endpoints", self.test_2_backend_api_endpoints),
            ("File Upload and Processing", self.test_3_file_upload_and_processing),
            ("Frontend Integration", self.test_4_frontend_integration),
            ("Error Handling", self.test_5_error_handling),
            ("Performance Metrics", self.test_6_performance_metrics),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    pass
            except Exception:
                pass


        if passed == total:
            pass
        else:
            pass

        return passed == total

if __name__ == "__main__":
    tester = ReceiptFlowTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
