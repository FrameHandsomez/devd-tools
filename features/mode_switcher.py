"""
Mode Switcher Feature - Switch between different mode profiles

Actions:
- next_mode: Switch to the next mode in sequence
- prev_mode: Switch to the previous mode
- select_mode: Show a dialog to select mode
"""

from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType
from utils.logger import get_logger

logger = get_logger(__name__)


class ModeSwitcherFeature(BaseFeature):
    """
    Feature 3: Mode Switching
    
    - Short press: Switch to next mode (DEV → GIT → AI → SCRIPT → DEV)
    - Long press: Show mode selection dialog
    """
    
    name = "mode_switcher"
    description = "Switch between different mode profiles"
    supported_patterns = [PressType.SHORT, PressType.LONG]
    
    # Will be set by bootstrap
    mode_manager = None
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute the mode switching action"""
        
        if action == "next_mode":
            return self._next_mode()
        elif action == "prev_mode":
            return self._prev_mode()
        elif action == "select_mode":
            return self._select_mode()
        else:
            # Default to next_mode
            return self._next_mode()
    
    def _get_mode_manager(self):
        """Get mode manager from feature registry"""
        # Import here to avoid circular import
        from runtime.bootstrap import _engine
        if _engine and _engine.mode_manager:
            return _engine.mode_manager
        return None
    
    def _next_mode(self) -> FeatureResult:
        """Switch to the next mode"""
        
        mode_manager = self._get_mode_manager()
        
        if not mode_manager:
            logger.error("Mode manager not available!")
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message="Mode manager not available"
            )
        
        old_mode = mode_manager.current_mode
        new_mode = mode_manager.next_mode()
        new_mode_name = mode_manager.get_mode_name()
        
        logger.info(f"🔄 Mode switched: {old_mode} → {new_mode} ({new_mode_name})")
        
        # Update system tray icon color
        try:
            from runtime.bootstrap import _engine
            if _engine and _engine.system_tray:
                _engine.system_tray.update_icon()
        except Exception as e:
            logger.warning(f"Could not update tray icon: {e}")
        
        # Show notification in a thread to avoid blocking
        import threading
        def show_notif():
            try:
                from ui.dialogs import show_notification
                show_notification(
                    title="🔄 Mode Changed",
                    message=f"{old_mode} → {new_mode}\n{new_mode_name}",
                    duration=2000
                )
            except Exception as e:
                logger.warning(f"Could not show notification: {e}")
        
        threading.Thread(target=show_notif, daemon=True).start()
        
        return FeatureResult(
            status=FeatureStatus.SUCCESS,
            message=f"Switched to {new_mode_name}",
            data={"mode": new_mode}
        )
    
    def _prev_mode(self) -> FeatureResult:
        """Switch to the previous mode"""
        
        mode_manager = self._get_mode_manager()
        
        if not mode_manager:
            logger.error("Mode manager not available!")
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message="Mode manager not available"
            )
        
        old_mode = mode_manager.current_mode
        new_mode = mode_manager.previous_mode()
        new_mode_name = mode_manager.get_mode_name()
        
        logger.info(f"🔄 Mode switched: {old_mode} → {new_mode} ({new_mode_name})")
        
        return FeatureResult(
            status=FeatureStatus.SUCCESS,
            message=f"Switched to {new_mode_name}",
            data={"mode": new_mode}
        )
    
    def _select_mode(self) -> FeatureResult:
        """Show a dialog to select mode"""
        
        mode_manager = self._get_mode_manager()
        
        if not mode_manager:
            logger.error("Mode manager not available!")
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message="Mode manager not available"
            )
        
        try:
            from ui.dialogs import ask_choice
            
            modes = mode_manager.modes
            mode_names = []
            for mode in modes:
                mode_config = self.config_manager.get_modes().get(mode, {})
                name = mode_config.get("name", mode)
                mode_names.append(f"{mode}: {name}")
            
            selected = ask_choice(
                title="Select Mode",
                message="Choose a mode:",
                choices=mode_names
            )
            
            if selected is not None:
                selected_mode = modes[selected]
                mode_manager.switch_mode(selected_mode)
                
                return FeatureResult(
                    status=FeatureStatus.SUCCESS,
                    message=f"Switched to {selected_mode}",
                    data={"mode": selected_mode}
                )
            
            return FeatureResult(
                status=FeatureStatus.CANCELLED,
                message="Mode selection cancelled"
            )
            
        except Exception as e:
            logger.error(f"Error in mode selection: {e}")
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=str(e)
            )

