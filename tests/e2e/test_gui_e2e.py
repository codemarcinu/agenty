"""
E2E tests for FoodSave AI GUI
Tests complete application flow and user interactions
"""


from gui.core.backend_client import BackendClient
from gui.windows.main_window import AICommandCenter
from PySide6.QtWidgets import QApplication
import pytest


@pytest.fixture(scope="module")
def app():
    """Create QApplication for testing"""
    app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def backend_client():
    """Create mock backend client"""
    return BackendClient(base_url="http://localhost:8000")


@pytest.fixture
def main_window(backend_client, app):
    """Create main window for testing"""
    window = AICommandCenter()
    window.show()
    yield window
    window.close()


class TestGUIE2E:
    """E2E tests for GUI functionality"""

    def test_application_startup(self, main_window):
        """Test application startup and initialization"""
        assert main_window.isVisible()
        assert main_window.windowTitle() == "🤖 AI Command Center - FoodSave AI"
        assert main_window.agent_panel is not None
        assert main_window.chat_hub is not None
        assert main_window.system_monitor is not None

    def test_agent_panel_pagination(self, main_window):
        """Test agent panel pagination functionality"""
        panel = main_window.agent_panel
        initial_page = panel.current_page

        # Test next page
        if panel.total_pages > 1:
            panel.next_page()
            assert panel.current_page == initial_page + 1

            # Test prev page
            panel.prev_page()
            assert panel.current_page == initial_page

    def test_agent_selection(self, main_window):
        """Test agent selection flow"""
        panel = main_window.agent_panel
        if panel.agent_cards:
            first_agent = next(iter(panel.agent_cards))
            panel.select_agent(first_agent)
            assert panel.selected_agent == first_agent

    def test_chat_hub_basic_flow(self, main_window):
        """Test basic chat hub functionality"""
        chat_hub = main_window.chat_hub
        assert chat_hub.current_tab_id is not None

        # Test tab creation
        initial_tab_count = len(chat_hub.chat_tabs)
        chat_hub.create_new_tab()
        assert len(chat_hub.chat_tabs) == initial_tab_count + 1

    def test_system_monitor_display(self, main_window):
        """Test system monitor displays correctly"""
        monitor = main_window.system_monitor
        assert monitor.metrics is not None
        assert hasattr(monitor.metrics, "cpu_usage")
        assert hasattr(monitor.metrics, "memory_usage")

    def test_status_bar_updates(self, main_window):
        """Test status bar updates correctly"""
        status_bar = main_window.statusBar()
        assert status_bar is not None

        # Test status message update
        test_message = "Test status message"
        main_window.update_status(test_message)
        # Note: Direct access to status message might require additional setup

    def test_window_resize(self, main_window):
        """Test window resize functionality"""
        main_window.size()
        new_size = (1200, 800)
        main_window.resize(*new_size)
        # Compare QSize with QSize, not tuple
        from PySide6.QtCore import QSize

        assert main_window.size() == QSize(*new_size)

    def test_theme_application(self, main_window):
        """Test theme application"""
        main_window.apply_theme()
        # Theme application should not throw errors
        assert True

    def test_backend_connection_handling(self, main_window):
        """Test backend connection handling"""
        # Test connection status updates
        main_window.on_backend_connected()
        assert "🟢 Connected" in main_window.connection_label.text()

        main_window.on_backend_disconnected()
        assert "🔴 Disconnected" in main_window.connection_label.text()

    def test_error_handling(self, main_window):
        """Test error handling in GUI"""
        # Test error message display
        test_error = "Test error message"
        main_window.show_error(test_error)
        # Error dialog should be shown (might need additional setup for testing)

    def test_progress_indication(self, main_window):
        """Test progress bar functionality"""
        main_window.show_progress(True, 50)
        assert main_window.progress_bar.isVisible()
        assert main_window.progress_bar.value() == 50

        main_window.show_progress(False)
        assert not main_window.progress_bar.isVisible()

    def test_agent_status_updates(self, main_window):
        """Test agent status update flow"""
        panel = main_window.agent_panel
        if panel.agent_cards:
            first_agent = next(iter(panel.agent_cards))
            main_window.model.get_active_count()

            # Simulate agent status change
            panel.on_agent_status_toggled(first_agent, True)
            # Status should be updated in model
            assert main_window.model.agent_status.get(first_agent, False) is True

    def test_window_close_confirmation(self, main_window):
        """Test window close confirmation dialog"""
        # This test would require mocking QMessageBox
        # For now, just test that close event handler exists
        assert hasattr(main_window, "on_close_event")
        assert callable(main_window.on_close_event)


class TestGUIIntegration:
    """Integration tests for GUI components"""

    def test_agent_panel_chat_hub_integration(self, main_window):
        """Test integration between agent panel and chat hub"""
        panel = main_window.agent_panel
        chat_hub = main_window.chat_hub

        if panel.agent_cards:
            first_agent = next(iter(panel.agent_cards))
            # Test agent request from chat hub
            chat_hub.agent_requested.emit(first_agent)
            # Agent should be selected in panel
            assert panel.selected_agent == first_agent

    def test_system_monitor_integration(self, main_window):
        """Test system monitor integration with main window"""
        monitor = main_window.system_monitor
        # Test status update signal
        test_status = {"cpu": 50.0, "memory": 60.0}
        monitor.status_updated.emit(test_status)
        # Main window should handle the signal
        assert hasattr(main_window, "on_system_status_updated")

    def test_backend_client_integration(self, main_window):
        """Test backend client integration"""
        client = main_window.backend_client
        assert client.base_url is not None
        assert client.timeout > 0
        # Test client initialization
        assert hasattr(client, "connect")
        assert hasattr(client, "get_agents")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
