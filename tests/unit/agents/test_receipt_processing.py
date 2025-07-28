#!/usr/bin/env python3
"""
Test script for receipt processing workflow
"""

from pathlib import Path
import time

import requests

# Configuration
BASE_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "tests/fixtures/test_receipt.jpg"


def test_receipt_processing():
    """Test the complete receipt processing workflow"""


    # Step 1: Check system health
    health_response = requests.get(f"{BASE_URL}/api/v3/receipts/health")
    if health_response.status_code == 200:
        health_response.json()
    else:
        return False

    # Step 2: Upload receipt
    if not Path(TEST_IMAGE_PATH).exists():
        return False

    with open(TEST_IMAGE_PATH, "rb") as f:
        files = {"file": ("test_receipt.jpg", f, "image/jpeg")}
        data = {"session_id": "test_session_123"}

        upload_response = requests.post(
            f"{BASE_URL}/api/v3/receipts/process", files=files, data=data
        )

    if upload_response.status_code == 202:
        upload_data = upload_response.json()
        job_id = upload_data["data"]["job_id"]
    else:
        return False

    # Step 3: Monitor task progress
    max_attempts = 30  # 30 seconds
    attempt = 0

    while attempt < max_attempts:
        status_response = requests.get(f"{BASE_URL}/api/v3/receipts/status/{job_id}")

        if status_response.status_code == 200:
            status_data = status_response.json()
            task_status = status_data["data"]["status"]


            if task_status == "SUCCESS":
                status_data["data"].get("result", {})
                return True
            if task_status == "FAILURE":
                status_data["data"].get("error", "Unknown error")
                return False
            if task_status == "PROGRESS":
                progress_info = status_data["data"]
                progress_info.get("step", "Unknown")
                progress_info.get("progress", 0)
                progress_info.get("message", "")
            elif task_status in ["PENDING", "STARTED"]:
                pass

        else:
            return False

        time.sleep(1)
        attempt += 1

    return False


def test_frontend_integration():
    """Test frontend accessibility"""

    try:
        frontend_response = requests.get("http://localhost:3000", timeout=5)
        return frontend_response.status_code == 200
    except requests.exceptions.RequestException:
        return False


if __name__ == "__main__":

    # Test receipt processing
    receipt_success = test_receipt_processing()

    # Test frontend
    frontend_success = test_frontend_integration()

    # Summary

    if receipt_success and frontend_success:
        pass
    else:
        pass
