#!/usr/bin/env python3
"""
Kompleksowy runner testów dla ulepszonego systemu "Add → Receipt Analysis".
Uruchamia wszystkie testy: unit, integration, performance i E2E.
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any


class EnhancedTestRunner:
    """Runner testów dla ulepszonego systemu przetwarzania paragonów."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {}
        self.start_time = time.time()

    def run_command(
        self, command: list[str], cwd: Path | None = None
    ) -> dict[str, Any]:
        """Uruchamia komendę i zwraca wyniki."""
        if cwd is None:
            cwd = self.project_root

        start_time = time.time()

        try:
            result = subprocess.run(
                command,
                check=False,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minut timeout
            )

            end_time = time.time()
            duration = end_time - start_time

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": duration,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": "Test timeout after 5 minutes",
                "duration": 300,
            }
        except Exception as e:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
                "duration": 0,
            }

    def run_backend_unit_tests(self) -> dict[str, Any]:
        """Uruchamia testy jednostkowe backendu."""

        # Testy OCR z zaawansowanym preprocessingiem
        ocr_tests = self.run_command(
            [
                "python",
                "-m",
                "pytest",
                "tests/unit/test_ocr_advanced_preprocessing.py",
                "-v",
                "--tb=short",
            ]
        )

        # Testy agentów
        agent_tests = self.run_command(
            [
                "python",
                "-m",
                "pytest",
                "tests/unit/test_ocr_enhanced.py",
                "tests/unit/test_receipt_analysis_enhanced.py",
                "-v",
                "--tb=short",
            ]
        )

        return {
            "ocr_advanced_preprocessing": ocr_tests,
            "ocr_enhanced": agent_tests,
            "total_success": ocr_tests["success"] and agent_tests["success"],
        }

    def run_backend_integration_tests(self) -> dict[str, Any]:
        """Uruchamia testy integracyjne backendu."""

        # Testy workflow agentów
        workflow_tests = self.run_command(
            [
                "python",
                "-m",
                "pytest",
                "tests/integration/test_receipt_agent_workflow.py",
                "-v",
                "--tb=short",
            ]
        )

        # Testy endpointów
        endpoint_tests = self.run_command(
            [
                "python",
                "-m",
                "pytest",
                "tests/integration/test_receipt_endpoints_enhanced.py",
                "-v",
                "--tb=short",
            ]
        )

        return {
            "agent_workflow": workflow_tests,
            "endpoints": endpoint_tests,
            "total_success": workflow_tests["success"] and endpoint_tests["success"],
        }

    def run_backend_performance_tests(self) -> dict[str, Any]:
        """Uruchamia testy wydajnościowe backendu."""

        performance_tests = self.run_command(
            [
                "python",
                "-m",
                "pytest",
                "tests/performance/test_ocr_performance_enhanced.py",
                "-v",
                "--tb=short",
                "--durations=10",
            ]
        )

        return {
            "ocr_performance": performance_tests,
            "total_success": performance_tests["success"],
        }

    def run_frontend_e2e_tests(self) -> dict[str, Any]:
        """Uruchamia testy E2E frontendu."""

        frontend_dir = self.project_root / "myappassistant-chat-frontend"

        if not frontend_dir.exists():
            return {"error": "Frontend directory not found", "total_success": False}

        # Sprawdź czy Playwright jest zainstalowany
        playwright_check = self.run_command(
            ["npx", "playwright", "--version"], cwd=frontend_dir
        )

        if not playwright_check["success"]:
            install_result = self.run_command(
                ["npm", "install", "--save-dev", "@playwright/test"], cwd=frontend_dir
            )

            if install_result["success"]:
                self.run_command(["npx", "playwright", "install"], cwd=frontend_dir)

        # Uruchom testy E2E
        e2e_tests = self.run_command(
            [
                "npx",
                "playwright",
                "test",
                "tests/e2e/receipt-wizard-enhanced.spec.ts",
                "--reporter=list",
            ],
            cwd=frontend_dir,
        )

        return {"receipt_wizard_e2e": e2e_tests, "total_success": e2e_tests["success"]}

    def run_tauri_integration_tests(self) -> dict[str, Any]:
        """Uruchamia testy integracji Tauri."""

        frontend_dir = self.project_root / "myappassistant-chat-frontend"

        if not frontend_dir.exists():
            return {"error": "Frontend directory not found", "total_success": False}

        # Testy integracji Tauri
        tauri_tests = self.run_command(
            [
                "npx",
                "playwright",
                "test",
                "tests/e2e/tauri-integration-fixed.spec.ts",
                "--reporter=list",
            ],
            cwd=frontend_dir,
        )

        return {
            "tauri_integration": tauri_tests,
            "total_success": tauri_tests["success"],
        }

    def run_coverage_tests(self) -> dict[str, Any]:
        """Uruchamia testy z pokryciem kodu."""

        coverage_tests = self.run_command(
            [
                "python",
                "-m",
                "pytest",
                "tests/unit/test_ocr_advanced_preprocessing.py",
                "tests/integration/test_receipt_agent_workflow.py",
                "tests/performance/test_ocr_performance_enhanced.py",
                "--cov=backend.core.ocr",
                "--cov=backend.agents",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
                "--cov-report=json:coverage.json",
            ]
        )

        return {"coverage": coverage_tests, "total_success": coverage_tests["success"]}

    def generate_test_report(self) -> str:
        """Generuje raport z testów."""
        end_time = time.time()
        total_duration = end_time - self.start_time

        report = []
        report.append("📋 RAPORT Z TESTÓW ULEPSZONEGO SYSTEMU")
        report.append("=" * 60)
        report.append(f"⏱️  Całkowity czas: {total_duration:.2f}s")
        report.append("")

        # Podsumowanie wyników
        total_tests = 0
        passed_tests = 0

        for category, results in self.test_results.items():
            if isinstance(results, dict) and "total_success" in results:
                total_tests += 1
                if results["total_success"]:
                    passed_tests += 1
                    status = "✅"
                else:
                    status = "❌"

                report.append(
                    f"{status} {category}: {'PASSED' if results['total_success'] else 'FAILED'}"
                )

                # Dodaj szczegóły dla każdego testu w kategorii
                for test_name, test_result in results.items():
                    if test_name != "total_success":
                        test_status = "✅" if test_result["success"] else "❌"
                        duration = test_result.get("duration", 0)
                        report.append(f"  {test_status} {test_name}: {duration:.2f}s")

        report.append("")
        report.append(
            f"📈 WYNIKI: {passed_tests}/{total_tests} kategorii testów przeszło"
        )

        # Dodaj szczegółowe logi błędów
        report.append("")
        report.append("🔍 SZCZEGÓŁOWE LOGI BŁĘDÓW:")
        report.append("-" * 40)

        for category, results in self.test_results.items():
            if isinstance(results, dict) and "total_success" in results:
                if not results["total_success"]:
                    report.append(f"\n❌ {category}:")
                    for test_name, test_result in results.items():
                        if test_name != "total_success" and not test_result["success"]:
                            report.append(f"  🔥 {test_name}:")
                            if test_result["stderr"]:
                                report.append(
                                    f"    Error: {test_result['stderr'][:200]}..."
                                )

        return "\n".join(report)

    def save_test_results(self, output_file: str = "enhanced_test_results.json"):
        """Zapisuje wyniki testów do pliku JSON."""
        results_file = self.project_root / output_file

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)

    def run_all_tests(
        self, include_e2e: bool = True, include_performance: bool = True
    ) -> bool:
        """Uruchamia wszystkie testy."""

        # Backend tests
        self.test_results["backend_unit"] = self.run_backend_unit_tests()
        self.test_results["backend_integration"] = self.run_backend_integration_tests()

        if include_performance:
            self.test_results["backend_performance"] = (
                self.run_backend_performance_tests()
            )

        # Coverage tests
        self.test_results["coverage"] = self.run_coverage_tests()

        # Frontend tests
        if include_e2e:
            self.test_results["frontend_e2e"] = self.run_frontend_e2e_tests()
            self.test_results["tauri_integration"] = self.run_tauri_integration_tests()

        # Wygeneruj raport
        self.generate_test_report()

        # Zapisz wyniki
        self.save_test_results()

        # Sprawdź czy wszystkie testy przeszły
        all_passed = all(
            results.get("total_success", False)
            for results in self.test_results.values()
            if isinstance(results, dict) and "total_success" in results
        )

        return bool(all_passed)


def main():
    """Główna funkcja uruchamiająca testy."""
    parser = argparse.ArgumentParser(
        description="Runner testów dla ulepszonego systemu przetwarzania paragonów"
    )
    parser.add_argument("--no-e2e", action="store_true", help="Pomiń testy E2E")
    parser.add_argument(
        "--no-performance", action="store_true", help="Pomiń testy wydajnościowe"
    )
    parser.add_argument(
        "--unit-only", action="store_true", help="Uruchom tylko testy jednostkowe"
    )
    parser.add_argument(
        "--integration-only",
        action="store_true",
        help="Uruchom tylko testy integracyjne",
    )

    args = parser.parse_args()

    runner = EnhancedTestRunner()

    if args.unit_only:
        runner.test_results["backend_unit"] = runner.run_backend_unit_tests()
    elif args.integration_only:
        runner.test_results["backend_integration"] = (
            runner.run_backend_integration_tests()
        )
    else:
        # Uruchom wszystkie testy
        success = runner.run_all_tests(
            include_e2e=not args.no_e2e, include_performance=not args.no_performance
        )

        if success:
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
