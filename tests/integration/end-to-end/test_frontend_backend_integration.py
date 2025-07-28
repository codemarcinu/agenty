#!/usr/bin/env python3
"""
Test script for frontend-backend integration after refactoring
"""

import json
import sys
import time

import requests


class FrontendBackendIntegrationTest:
    def __init__(self):
        self.frontend_url = "http://localhost:8085"
        self.backend_url = "http://localhost:8000"
        self.test_results = []

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        if details:
            pass
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })

    def test_frontend_accessibility(self) -> bool:
        """Test if frontend is accessible"""
        try:
            response = requests.get(f"{self.frontend_url}/", timeout=10)
            success = response.status_code == 200
            self.log_test("Frontend Accessibility", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Frontend Accessibility", False, str(e))
            return False

    def test_backend_health(self) -> bool:
        """Test backend health endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            success = response.status_code == 200
            self.log_test("Backend Health", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Backend Health", False, str(e))
            return False

    def test_api_proxy(self) -> bool:
        """Test API proxy through frontend"""
        try:
            response = requests.get(f"{self.frontend_url}/health", timeout=10)
            success = response.status_code == 200
            self.log_test("API Proxy", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("API Proxy", False, str(e))
            return False

    def test_agents_api(self) -> bool:
        """Test agents API endpoint"""
        try:
            response = requests.get(f"{self.frontend_url}/api/agents/agents", timeout=10)
            success = response.status_code == 200
            if success:
                agents = response.json()
                self.log_test("Agents API", success, f"Found {len(agents)} agents")
            else:
                self.log_test("Agents API", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Agents API", False, str(e))
            return False

    def test_v2_api(self) -> bool:
        """Test v2 API endpoint"""
        try:
            response = requests.get(f"{self.frontend_url}/api/v2/test", timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                self.log_test("V2 API", success, f"Message: {data.get('message', 'N/A')}")
            else:
                self.log_test("V2 API", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("V2 API", False, str(e))
            return False

    def test_frontend_static_files(self) -> bool:
        """Test if frontend static files are served correctly"""
        files_to_test = [
            "/style.css",
            "/app.js",
            "/index.html"
        ]

        all_success = True
        for file_path in files_to_test:
            try:
                response = requests.get(f"{self.frontend_url}{file_path}", timeout=10)
                success = response.status_code == 200
                if not success:
                    all_success = False
                self.log_test(f"Static File: {file_path}", success, f"Status: {response.status_code}")
            except Exception as e:
                all_success = False
                self.log_test(f"Static File: {file_path}", False, str(e))

        return all_success

    def test_nginx_configuration(self) -> bool:
        """Test nginx configuration and headers"""
        try:
            response = requests.get(f"{self.frontend_url}/", timeout=10)
            headers = response.headers

            # Check for important headers
            security_headers = [
                "X-Frame-Options",
                "X-XSS-Protection",
                "X-Content-Type-Options"
            ]

            missing_headers = []
            for header in security_headers:
                if header not in headers:
                    missing_headers.append(header)

            success = len(missing_headers) == 0
            details = f"Missing headers: {missing_headers}" if missing_headers else "All security headers present"
            self.log_test("Nginx Security Headers", success, details)
            return success
        except Exception as e:
            self.log_test("Nginx Security Headers", False, str(e))
            return False

    def test_container_status(self) -> bool:
        """Test if all containers are running"""
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=10, check=False
            )

            if result.returncode != 0:
                self.log_test("Container Status", False, "Failed to get container status")
                return False

            containers = result.stdout.strip().split("\n")[1:]  # Skip header
            foodsave_containers = [c for c in containers if "foodsave" in c.lower()]

            all_running = True
            for container in foodsave_containers:
                if "Up" not in container:
                    all_running = False
                    break

            self.log_test("Container Status", all_running, f"Found {len(foodsave_containers)} FoodSave containers")
            return all_running
        except Exception as e:
            self.log_test("Container Status", False, str(e))
            return False

    def run_all_tests(self):
        """Run all integration tests"""

        tests = [
            self.test_frontend_accessibility,
            self.test_backend_health,
            self.test_api_proxy,
            self.test_agents_api,
            self.test_v2_api,
            self.test_frontend_static_files,
            self.test_nginx_configuration,
            self.test_container_status
        ]

        for test in tests:
            test()
            time.sleep(0.5)  # Small delay between tests

        # Summary

        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)


        if passed == total:
            pass
        else:
            pass

        return passed == total

def main():
    """Main test function"""
    tester = FrontendBackendIntegrationTest()
    success = tester.run_all_tests()

    # Save results to file
    with open("frontend_backend_integration_test_results.json", "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": tester.test_results
        }, f, indent=2)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
