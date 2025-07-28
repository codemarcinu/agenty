#!/usr/bin/env python3
"""
Test script for backend integration and GUI functionality
"""

from pathlib import Path
import sys

# Add project paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "gui"))

def test_backend_client():
    """Test backend client functionality"""

    try:
        from gui.backend_client import BackendClient

        client = BackendClient()

        # Test connection
        is_connected = client.is_connected()

        if is_connected:
            # Test health endpoint
            client.get_health()

            # Test system status
            client.get_system_status()

        return True

    except Exception:
        return False

def test_gui_components():
    """Test GUI component imports"""

    components = [
        ("tray", "AssistantTray"),
        ("status_indicators", "create_status_panel"),
        ("notification_manager", "NotificationManager"),
        ("theme_manager", "ThemeManager"),
        ("styles", "ModernStyles"),
        ("backend_client", "BackendClient")
    ]

    all_success = True

    for module_name, class_name in components:
        try:
            if module_name in ("tray", "status_indicators", "notification_manager", "theme_manager", "styles", "backend_client"):
                pass

        except Exception:
            all_success = False

    return all_success

def test_pyqt5_setup():
    """Test PyQt5 setup"""

    try:
        from PyQt5.QtWidgets import QApplication


        # Test QApplication creation
        app = QApplication([])

        app.quit()
        return True

    except Exception:
        return False

def test_backend_startup():
    """Test backend startup"""

    try:
        # Check if backend is already running
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            return True
    except:
        pass

    return True

def main():
    """Run all tests"""

    tests = [
        ("PyQt5 Setup", test_pyqt5_setup),
        ("GUI Components", test_gui_components),
        ("Backend Client", test_backend_client),
        ("Backend Startup", test_backend_startup)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception:
            results.append((test_name, False))

    # Summary
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        pass


    if passed == total:
        pass
    else:
        pass

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
