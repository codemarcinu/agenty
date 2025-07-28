from abc import ABC, abstractmethod
from typing import Any


class AgentPlugin(ABC):
    """Base interface for agent plugins"""

    @abstractmethod
    def initialize(self, agent: Any) -> None:
        """Initialize plugin with agent instance"""

    @abstractmethod
    def before_process(self, input_data: dict) -> dict:
        """Pre-process input data"""

    @abstractmethod
    def after_process(self, output_data: dict) -> dict:
        """Post-process output data"""

    @abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        """Get plugin metadata"""
