from gui.core.backend_client import BackendClient
from gui.windows.agent_panel import AgentControlPanel
from PySide6.QtWidgets import QApplication
import pytest


@pytest.fixture(scope="module")
def app():
    app = QApplication([])
    yield app
    app.quit()


@pytest.fixture
def backend_client():
    return BackendClient(base_url="http://localhost:8000")


@pytest.fixture
def panel(backend_client, app):
    return AgentControlPanel(backend_client)


def test_initialization_and_pagination(panel):
    assert panel.total_pages >= 1
    assert panel.page_size == 8
    assert panel.current_page == 0
    visible = [
        panel.agent_list_layout.itemAt(i).widget()
        for i in range(panel.agent_list_layout.count())
        if panel.agent_list_layout.itemAt(i).widget()
    ]
    assert len(visible) <= panel.page_size


def test_next_prev_page(panel):
    start_page = panel.current_page
    panel.next_page()
    if panel.total_pages > 1:
        assert panel.current_page == start_page + 1
        panel.prev_page()
        assert panel.current_page == start_page
    else:
        assert panel.current_page == start_page


def test_select_agent(panel):
    first_agent = next(iter(panel.agent_cards))
    panel.select_agent(first_agent)
    assert panel.selected_agent == first_agent


def test_signals(qtbot, panel):
    selected = []
    status_changed = []
    panel.agent_selected.connect(lambda agent: selected.append(agent))
    panel.agent_status_changed.connect(
        lambda agent, active: status_changed.append((agent, active))
    )
    first_agent = next(iter(panel.agent_cards))
    panel.on_agent_card_selected(first_agent)
    panel.on_agent_status_toggled(first_agent, True)
    assert selected and selected[0] == first_agent
    assert (
        status_changed
        and status_changed[0][0] == first_agent
        and status_changed[0][1] is True
    )
