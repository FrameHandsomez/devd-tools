"""
Event Router - Detects press patterns and routes to appropriate features
Supports: short press, long press, double press, multi press
"""

import time
import threading
from typing import Callable, Optional
from core.events.input_event import InputEvent, PressType, KeyState
from core.modes.mode_manager import ModeManager
from core.config.config_manager import ConfigManager
from utils.logger import get_logger

logger = get_logger(__name__)


class EventRouter:
    """
    Routes input events to features based on:
    1. Press pattern (short/long/double/multi)
    2. Current mode
    3. Key binding configuration
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        mode_manager: ModeManager
    ):
        self.config_manager = config_manager
        self.mode_manager = mode_manager
        
        # Track key states for pattern detection
        self.key_states: dict[str, KeyState] = {}
        
        # Timers for delayed action execution
        self.pending_timers: dict[str, threading.Timer] = {}
        
        # Load settings
        settings = config_manager.get_settings()
        self.long_press_ms = settings.get("long_press_ms", 800)
        self.multi_press_window_ms = settings.get("multi_press_window_ms", 500)
        self.multi_press_count = settings.get("multi_press_count", 3)
    
    def route_event(self, event: InputEvent):
        """
        Main entry point - route an input event to the appropriate feature.
        This is called by input providers when a key event occurs.
        """
        logger.debug(f"Routing event: {event}")
        
        # Get or create key state
        if event.key_combination not in self.key_states:
            self.key_states[event.key_combination] = KeyState(
                key_combination=event.key_combination
            )
        
        key_state = self.key_states[event.key_combination]
        
        # Determine what action to take based on the event
        self._process_event(event, key_state)
    
    def _process_event(self, event: InputEvent, key_state: KeyState):
        """Process an event and determine the action"""
        
        current_time = time.time()
        
        # Check for multi-press pattern
        if key_state.last_press_time > 0:
            time_since_last = (current_time - key_state.last_press_time) * 1000
            
            if time_since_last < self.multi_press_window_ms:
                # Within multi-press window
                key_state.press_count += 1
                key_state.last_press_time = current_time
                
                # Cancel any pending timer
                self._cancel_timer(event.key_combination)
                
                # Check if we hit the multi-press threshold
                if key_state.press_count >= self.multi_press_count:
                    logger.info(f"Multi-press detected: {event.key_combination} x{key_state.press_count}")
                    event.press_type = PressType.MULTI
                    event.press_count = key_state.press_count
                    event.action = f"multi_{key_state.press_count}"
                    self._execute_event(event)
                    key_state.reset()
                else:
                    # Wait for more presses or timeout
                    self._schedule_delayed_execution(event, key_state)
                return
        
        # First press or outside multi-press window
        key_state.press_count = 1
        key_state.last_press_time = current_time
        
        # Determine press type based on duration
        if event.press_duration_ms >= self.long_press_ms:
            event.press_type = PressType.LONG
            event.action = "long"
            logger.info(f"Long press detected: {event.key_combination}")
            self._execute_event(event)
            key_state.reset()
        else:
            # Schedule delayed execution to wait for potential multi-press
            self._schedule_delayed_execution(event, key_state)
    
    def _schedule_delayed_execution(self, event: InputEvent, key_state: KeyState):
        """Schedule execution after multi-press window expires"""
        
        def delayed_action():
            # Execute as short press if no more presses came
            if key_state.press_count == 1:
                event.press_type = PressType.SHORT
                event.action = "short"
                logger.info(f"Short press detected: {event.key_combination}")
            elif key_state.press_count == 2:
                event.press_type = PressType.DOUBLE
                event.action = "double"
                event.press_count = 2
                logger.info(f"Double press detected: {event.key_combination}")
            else:
                event.press_type = PressType.MULTI
                event.action = f"multi_{key_state.press_count}"
                event.press_count = key_state.press_count
                logger.info(f"Multi-press detected: {event.key_combination} x{key_state.press_count}")
            
            self._execute_event(event)
            key_state.reset()
        
        # Cancel existing timer
        self._cancel_timer(event.key_combination)
        
        # Schedule new timer
        delay = self.multi_press_window_ms / 1000.0
        timer = threading.Timer(delay, delayed_action)
        timer.start()
        self.pending_timers[event.key_combination] = timer
    
    def _cancel_timer(self, key_combination: str):
        """Cancel a pending timer"""
        if key_combination in self.pending_timers:
            self.pending_timers[key_combination].cancel()
            del self.pending_timers[key_combination]
    
    def _execute_event(self, event: InputEvent):
        """Execute the event by finding and running the appropriate feature"""
        
        # Get the feature for this event from the mode manager
        feature, action = self.mode_manager.get_feature_for_event(event)
        
        if feature is None:
            logger.warning(f"No feature found for: {event}")
            # Show notification for no feature bound
            self._show_error_notification(
                title="⚠️ ไม่พบ Feature",
                message=f"ปุ่ม {event.key_combination.upper()} ไม่มี binding ใน mode นี้"
            )
            return
        
        # Execute the feature
        try:
            logger.info(f"Executing feature: {feature.name}, action: {action}")
            result = feature.execute(event, action)
            
            # Check if feature returned an error
            if result and hasattr(result, 'status'):
                from core.features.base_feature import FeatureStatus
                if result.status == FeatureStatus.ERROR:
                    self._show_error_notification(
                        title=f"❌ {feature.name} Error",
                        message=result.message or "Unknown error"
                    )
                    
        except Exception as e:
            logger.error(f"Error executing feature {feature.name}: {e}", exc_info=True)
            self._show_error_notification(
                title=f"❌ {feature.name} Crashed",
                message=str(e)[:100]
            )
    
    def _show_error_notification(self, title: str, message: str):
        """Show error notification in a thread to avoid blocking"""
        import threading
        def show():
            try:
                from ui.dialogs import show_notification
                show_notification(title=title, message=message, duration=4000)
            except Exception:
                pass
        threading.Thread(target=show, daemon=True).start()
    
    def cleanup(self):
        """Cancel all pending timers"""
        for timer in self.pending_timers.values():
            timer.cancel()
        self.pending_timers.clear()
