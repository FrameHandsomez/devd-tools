"""
Mode Manager - State Machine for context-based feature routing
Same key can trigger different features based on current mode
"""

from typing import Optional, Tuple, TYPE_CHECKING
from core.events.input_event import InputEvent
from core.config.config_manager import ConfigManager
from utils.logger import get_logger

if TYPE_CHECKING:
    from core.features.base_feature import BaseFeature
    from core.features.feature_registry import FeatureRegistry

logger = get_logger(__name__)


class ModeManager:
    """
    State machine for managing modes (DEV, GIT, AI, SCRIPT, etc.)
    
    The same key combination can trigger different features
    depending on the current mode.
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        feature_registry: "FeatureRegistry"
    ):
        self.config_manager = config_manager
        self.feature_registry = feature_registry
        
        # Load available modes
        self.modes = list(config_manager.get_modes().keys())
        self.current_mode = config_manager.get_current_mode()
        
        self.observers = []
        
        logger.info(f"Mode Manager initialized with modes: {self.modes}")
        logger.info(f"Current mode: {self.current_mode}")
        
    def add_observer(self, callback):
        """Add a callback function to be notified on mode change"""
        self.observers.append(callback)
    
    def get_feature_for_event(
        self,
        event: InputEvent
    ) -> Tuple[Optional["BaseFeature"], Optional[str]]:
        """
        Get the feature and action for an input event based on current mode.
        
        Returns:
            Tuple of (feature instance, action name) or (None, None) if not found
        """
        # Get bindings for current mode
        bindings = self.config_manager.get_mode_bindings(self.current_mode)
        
        if event.key_combination not in bindings:
            logger.debug(f"No binding for {event.key_combination} in mode {self.current_mode}")
            return None, None
        
        binding = bindings[event.key_combination]
        feature_name = binding.get("feature")
        
        if not feature_name:
            return None, None
        
        # Get the feature from registry
        feature = self.feature_registry.get_feature(feature_name)
        if not feature:
            logger.warning(f"Feature not found: {feature_name}")
            return None, None
        
        # Determine the action based on press pattern
        patterns = binding.get("patterns", {})
        action = None
        
        if event.action and event.action in patterns:
            action = patterns[event.action]
        elif event.press_type.value in patterns:
            action = patterns[event.press_type.value]
        else:
            # Default to first action if no pattern match
            action = list(patterns.values())[0] if patterns else "default"
        
        return feature, action
    
    def switch_mode(self, mode: str) -> bool:
        """Switch to a specific mode"""
        if mode not in self.modes:
            logger.warning(f"Unknown mode: {mode}")
            return False
        
        old_mode = self.current_mode
        self.current_mode = mode
        self.config_manager.set_current_mode(mode)
        
        logger.info(f"Mode switched: {old_mode} → {mode}")
        
        # Notify observers
        for callback in self.observers:
            try:
                callback(mode)
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")
                
        return True
    
    def next_mode(self) -> str:
        """Switch to the next mode in sequence"""
        if not self.modes:
            return self.current_mode
        
        current_index = self.modes.index(self.current_mode)
        next_index = (current_index + 1) % len(self.modes)
        next_mode = self.modes[next_index]
        
        self.switch_mode(next_mode)
        return next_mode
    
    def previous_mode(self) -> str:
        """Switch to the previous mode in sequence"""
        if not self.modes:
            return self.current_mode
        
        current_index = self.modes.index(self.current_mode)
        prev_index = (current_index - 1) % len(self.modes)
        prev_mode = self.modes[prev_index]
        
        self.switch_mode(prev_mode)
        return prev_mode
    
    def get_mode_name(self) -> str:
        """Get the display name of current mode"""
        modes = self.config_manager.get_modes()
        if self.current_mode in modes:
            return modes[self.current_mode].get("name", self.current_mode)
        return self.current_mode
