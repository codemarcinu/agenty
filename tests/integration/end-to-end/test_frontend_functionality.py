#!/usr/bin/env python3
"""
Test script for frontend functionality and UI components
"""

import json
import sys
import time

from bs4 import BeautifulSoup
import requests


class FrontendFunctionalityTest:
    def __init__(self):
        self.frontend_url = "http://localhost:8085"
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

    def test_html_structure(self) -> bool:
        """Test if the HTML structure is correct"""
        try:
            response = requests.get(f"{self.frontend_url}/", timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            # Check for essential elements
            essential_elements = [
                "chat-messages",
                "chat-input",
                "send-message",
                "quick-suggestions",
                "widgets-section",
                "agents-container"
            ]

            missing_elements = []
            for element_id in essential_elements:
                if not soup.find(id=element_id):
                    missing_elements.append(element_id)

            success = len(missing_elements) == 0
            details = f"Missing elements: {missing_elements}" if missing_elements else "All essential elements present"
            self.log_test("HTML Structure", success, details)
            return success
        except Exception as e:
            self.log_test("HTML Structure", False, str(e))
            return False

    def test_css_loading(self) -> bool:
        """Test if CSS is properly loaded"""
        try:
            response = requests.get(f"{self.frontend_url}/style.css", timeout=10)
            success = response.status_code == 200 and len(response.content) > 1000
            self.log_test("CSS Loading", success, f"CSS size: {len(response.content)} bytes")
            return success
        except Exception as e:
            self.log_test("CSS Loading", False, str(e))
            return False

    def test_javascript_loading(self) -> bool:
        """Test if JavaScript is properly loaded"""
        try:
            response = requests.get(f"{self.frontend_url}/app.js", timeout=10)
            success = response.status_code == 200 and len(response.content) > 1000
            self.log_test("JavaScript Loading", success, f"JS size: {len(response.content)} bytes")
            return success
        except Exception as e:
            self.log_test("JavaScript Loading", False, str(e))
            return False

    def test_navigation_structure(self) -> bool:
        """Test if navigation elements are present"""
        try:
            response = requests.get(f"{self.frontend_url}/", timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            # Check navigation buttons
            nav_buttons = soup.find_all(class_="nav-btn")
            expected_pages = ["dashboard", "receipts", "pantry", "rag"]

            found_pages = []
            for button in nav_buttons:
                page = button.get("data-page")
                if page:
                    found_pages.append(page)

            missing_pages = [page for page in expected_pages if page not in found_pages]
            success = len(missing_pages) == 0
            details = f"Found pages: {found_pages}, Missing: {missing_pages}"
            self.log_test("Navigation Structure", success, details)
            return success
        except Exception as e:
            self.log_test("Navigation Structure", False, str(e))
            return False

    def test_agent_buttons(self) -> bool:
        """Test if agent buttons are present"""
        try:
            response = requests.get(f"{self.frontend_url}/", timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            agent_buttons = soup.find_all(class_="agent-btn")
            expected_agents = ["chef", "weather", "search", "rag", "mealplanner", "analytics"]

            found_agents = []
            for button in agent_buttons:
                agent = button.get("data-agent")
                if agent:
                    found_agents.append(agent)

            missing_agents = [agent for agent in expected_agents if agent not in found_agents]
            success = len(missing_agents) == 0
            details = f"Found agents: {found_agents}, Missing: {missing_agents}"
            self.log_test("Agent Buttons", success, details)
            return success
        except Exception as e:
            self.log_test("Agent Buttons", False, str(e))
            return False

    def test_chat_interface(self) -> bool:
        """Test if chat interface elements are present"""
        try:
            response = requests.get(f"{self.frontend_url}/", timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            chat_elements = [
                "chat-messages",
                "chat-input",
                "send-message",
                "quick-suggestions"
            ]

            missing_elements = []
            for element_id in chat_elements:
                if not soup.find(id=element_id):
                    missing_elements.append(element_id)

            success = len(missing_elements) == 0
            details = f"Missing chat elements: {missing_elements}" if missing_elements else "All chat elements present"
            self.log_test("Chat Interface", success, details)
            return success
        except Exception as e:
            self.log_test("Chat Interface", False, str(e))
            return False

    def test_receipt_upload_interface(self) -> bool:
        """Test if receipt upload interface is present"""
        try:
            response = requests.get(f"{self.frontend_url}/", timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            # Check for receipt upload elements
            receipt_elements = [
                "receipt-upload-area",
                "receipt-file-input",
                "file-preview"
            ]

            missing_elements = []
            for element_id in receipt_elements:
                if not soup.find(id=element_id):
                    missing_elements.append(element_id)

            success = len(missing_elements) == 0
            details = f"Missing receipt elements: {missing_elements}" if missing_elements else "All receipt elements present"
            self.log_test("Receipt Upload Interface", success, details)
            return success
        except Exception as e:
            self.log_test("Receipt Upload Interface", False, str(e))
            return False

    def test_theme_functionality(self) -> bool:
        """Test if theme functionality elements are present"""
        try:
            response = requests.get(f"{self.frontend_url}/", timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            theme_elements = [
                "theme-toggle",
                "color-picker-container",
                "color-options"
            ]

            missing_elements = []
            for element_id in theme_elements:
                if not soup.find(id=element_id):
                    missing_elements.append(element_id)

            success = len(missing_elements) == 0
            details = f"Missing theme elements: {missing_elements}" if missing_elements else "All theme elements present"
            self.log_test("Theme Functionality", success, details)
            return success
        except Exception as e:
            self.log_test("Theme Functionality", False, str(e))
            return False

    def test_responsive_design(self) -> bool:
        """Test if responsive design elements are present"""
        try:
            response = requests.get(f"{self.frontend_url}/", timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            # Check for viewport meta tag
            viewport = soup.find("meta", attrs={"name": "viewport"})
            success = viewport is not None
            details = "Viewport meta tag present" if success else "Viewport meta tag missing"
            self.log_test("Responsive Design", success, details)
            return success
        except Exception as e:
            self.log_test("Responsive Design", False, str(e))
            return False

    def test_font_loading(self) -> bool:
        """Test if Google Fonts are properly linked"""
        try:
            response = requests.get(f"{self.frontend_url}/", timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")

            # Check for Google Fonts links
            font_links = soup.find_all("link", attrs={"href": lambda x: x and "fonts.googleapis.com" in x})
            success = len(font_links) > 0
            details = f"Found {len(font_links)} Google Fonts links"
            self.log_test("Font Loading", success, details)
            return success
        except Exception as e:
            self.log_test("Font Loading", False, str(e))
            return False

    def run_all_tests(self):
        """Run all frontend functionality tests"""

        tests = [
            self.test_html_structure,
            self.test_css_loading,
            self.test_javascript_loading,
            self.test_navigation_structure,
            self.test_agent_buttons,
            self.test_chat_interface,
            self.test_receipt_upload_interface,
            self.test_theme_functionality,
            self.test_responsive_design,
            self.test_font_loading
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
    tester = FrontendFunctionalityTest()
    success = tester.run_all_tests()

    # Save results to file
    with open("frontend_functionality_test_results.json", "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": tester.test_results
        }, f, indent=2)

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
