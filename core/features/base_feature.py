"""
Base Feature - Abstract class that all features must implement
Features are plugins that:
1. Don't know about input source (keyboard, Arduino, etc.)
2. Don't know about current mode
3. Just receive an event and execute their logic
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from enum import Enum
from core.events.input_event import InputEvent, PressType

if TYPE_CHECKING:
    from core.commands.command_executor import CommandExecutor
    from core.config.config_manager import ConfigManager


class FeatureStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"
    PENDING = "pending"


@dataclass
class FeatureResult:
    """Result of a feature execution"""
    status: FeatureStatus
    message: str = ""
    data: Optional[dict] = None


class BaseFeature(ABC):
    """
    Abstract base class for all features.
    
    All features must:
    1. Inherit from this class
    2. Implement the execute() method
    3. Define supported_patterns
    
    Features should NOT:
    1. Import from ui/ (headless core)
    2. Know about input source
    3. Call subprocess directly (use command_executor)
    """
    
    # Feature name (used in config bindings)
    name: str = "base_feature"
    
    # Description for UI/logging
    description: str = "Base feature"
    
    # Supported press patterns
    supported_patterns: list[PressType] = [PressType.SHORT]
    
    def __init__(
        self,
        config_manager: "ConfigManager",
        command_executor: "CommandExecutor"
    ):
        self.config_manager = config_manager
        self.command_executor = command_executor
    
    @abstractmethod
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """
        Execute the feature with the given event and action.
        
        Args:
            event: The input event that triggered this feature
            action: The action name from the binding (e.g., "clone", "update")
        
        Returns:
            FeatureResult with status and message
        """
        pass
    
    def supports_pattern(self, pattern: PressType) -> bool:
        """Check if this feature supports a press pattern"""
        return pattern in self.supported_patterns
