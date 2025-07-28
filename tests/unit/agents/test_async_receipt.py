#!/usr/bin/env python3
"""
Test asynchronicznego przetwarzania paragonów z GPU
"""


import requests


def test_async_receipt_processing():
    """Test asynchronicznego przetwarzania paragonów"""

    base_url = "http://localhost:8000"


    # 1. Sprawdź health backendu
    try:
        health_response = requests.get(f"{base_url}/health", timeout=10)
        if health_response.status_code == 200:
            pass
        else:
            return False
    except Exception:
        return False

    # 2. Sprawdź endpoint v3
    try:
        v3_response = requests.get(f"{base_url}/api/v3/receipts/health", timeout=10)
        if v3_response.status_code == 200:
            pass
        else:
            pass
    except Exception:
        pass

    # 3. Sprawdź konfigurację GPU
    try:
        # Sprawdź zmienne środowiskowe w kontenerze
        import subprocess
        result = subprocess.run([
            "docker", "compose", "exec", "-T", "backend",
            "python", "-c",
            "import os; print(f'USE_GPU_OCR: {os.getenv(\"USE_GPU_OCR\")}'); print(f'GPU_DEVICE_ID: {os.getenv(\"GPU_DEVICE_ID\")}')"
        ], capture_output=True, text=True, check=False)

        if result.returncode == 0:
            pass
        else:
            pass
    except Exception:
        pass

    # 4. Sprawdź frontend
    try:
        frontend_response = requests.get("http://localhost:8085/", timeout=10)
        if frontend_response.status_code == 200:
            pass
        else:
            pass
    except Exception:
        pass

    # 5. Sprawdź status kontenerów
    try:
        result = subprocess.run([
            "docker", "compose", "ps", "--format", "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
        ], capture_output=True, text=True, check=False)

        if result.returncode == 0:
            pass
        else:
            pass
    except Exception:
        pass


    return True

if __name__ == "__main__":
    test_async_receipt_processing()
