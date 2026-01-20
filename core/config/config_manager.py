"""
Configuration Manager - Read/write macros.json with validation
"""

import json
from pathlib import Path
from typing import Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """
    Manages the macros.json configuration file.
    Provides read/write access with validation.
    """
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._config: dict = {}
    
    def load(self) -> dict:
        """Load configuration from file"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            self._config = self._get_default_config()
            self.save()
            return self._config
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return self._config
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def save(self):
        """Save configuration to file"""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a configuration value and save"""
        self._config[key] = value
        self.save()
    
    def get_current_mode(self) -> str:
        """Get the current mode name"""
        return self._config.get("current_mode", "DEV")
    
    def set_current_mode(self, mode: str):
        """Set the current mode"""
        if mode in self._config.get("modes", {}):
            self._config["current_mode"] = mode
            self.save()
            logger.info(f"Mode changed to: {mode}")
        else:
            logger.warning(f"Unknown mode: {mode}")
    
    def get_modes(self) -> dict:
        """Get all modes configuration"""
        return self._config.get("modes", {})
    
    def get_mode_bindings(self, mode: str) -> dict:
        """Get key bindings for a specific mode"""
        modes = self.get_modes()
        if mode in modes:
            return modes[mode].get("bindings", {})
        return {}
    
    def get_settings(self) -> dict:
        """Get settings section"""
        return self._config.get("settings", {})
    
    def get_saved_path(self, key: str) -> Optional[str]:
        """Get a saved path"""
        return self._config.get("saved_paths", {}).get(key)
    
    def set_saved_path(self, key: str, path: str):
        """Set a saved path"""
        if "saved_paths" not in self._config:
            self._config["saved_paths"] = {}
        self._config["saved_paths"][key] = path
        self.save()
        logger.info(f"Saved path for {key}: {path}")
    
    def _get_default_config(self) -> dict:
        """Return default configuration"""
        return {
            "version": "2.0",
            "current_mode": "DEV",
            "modes": {
                "DEV": {
                    "name": "Development Mode",
                    "bindings": {}
                }
            },
            "settings": {
                "long_press_ms": 800,
                "multi_press_window_ms": 500,
                "multi_press_count": 3,
                "notification_enabled": True
            },
            "saved_paths": {}
        }
