"""
Configuration Manager - Read/write macros.json with validation
"""

import json
import os
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
            logger.error(f"Invalid JSON in config file: {e}. Loading defaults.")
            self._config = self._get_default_config()
            return self._config
        except Exception as e:
            logger.error(f"Error loading config: {e}. Loading defaults.")
            self._config = self._get_default_config()
            return self._config
    
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
        path = self._config.get("saved_paths", {}).get(key)
        return self._expand_path(path)
    
    def set_saved_path(self, key: str, path: str):
        """Set a saved path"""
        if "saved_paths" not in self._config:
            self._config["saved_paths"] = {}
        self._config["saved_paths"][key] = self._collapse_path(path)
        self.save()
        logger.info(f"Saved path for {key}: {path}")
    
    # ==================== Multi-Project Support ====================
    
    def get_projects(self, key: str) -> list[dict]:
        """Get all saved projects for a feature (e.g., frontend_projects)"""
        projects_key = f"{key}_list"
        projects = self._config.get("saved_paths", {}).get(projects_key, [])
        
        # Return copy with expanded paths
        expanded_projects = []
        for p in projects:
            p_copy = p.copy()
            if "path" in p_copy:
                p_copy["path"] = self._expand_path(p_copy["path"])
            expanded_projects.append(p_copy)
            
        return expanded_projects
    
    def add_project(self, key: str, path: str, name: str = None) -> bool:
        """Add a project to the list"""
        if "saved_paths" not in self._config:
            self._config["saved_paths"] = {}
        
        projects_key = f"{key}_list"
        if projects_key not in self._config["saved_paths"]:
            self._config["saved_paths"][projects_key] = []
        
        projects = self._config["saved_paths"][projects_key]
        
        # Check if already exists (compare expanded paths)
        expanded_path_to_add = self._expand_path(path)
        
        for p in projects:
            existing_expanded = self._expand_path(p["path"])
            # Normalize for comparison
            if Path(existing_expanded).resolve() == Path(expanded_path_to_add).resolve():
                logger.info(f"Project already exists: {path}")
                return False
        
        # Auto-generate name from folder if not provided
        if not name:
            name = Path(path).name
        
        projects.append({
            "name": name,
            "path": self._collapse_path(path)
        })
        
        self.save()
        logger.info(f"Added project: {name} ({path})")
        return True
    
    def remove_project(self, key: str, path: str) -> bool:
        """Remove a project from the list"""
        projects_key = f"{key}_list"
        projects = self._config.get("saved_paths", {}).get(projects_key, [])
        
        target_expanded = self._expand_path(path)
        
        for i, p in enumerate(projects):
            current_expanded = self._expand_path(p["path"])
            # Normalize for comparison
            if Path(current_expanded).resolve() == Path(target_expanded).resolve():
                del projects[i]
                self.save()
                logger.info(f"Removed project: {path}")
                return True
        
        return False
    
    def get_active_project(self, key: str) -> dict | None:
        """Get the currently active project"""
        active_key = f"{key}_active"
        active_path = self._config.get("saved_paths", {}).get(active_key)
        
        if not active_path:
            return None
            
        expanded_active_path = self._expand_path(active_path)
        
        # Find project in list
        projects = self.get_projects(key) # This returns expanded projects
        for p in projects:
            # Simple string comparison should work as both are expanded, 
            # but resolve is safer
            if Path(p["path"]).resolve() == Path(expanded_active_path).resolve():
                return p
        
        # Fallback if not found in list but active path is set
        if expanded_active_path:
             return {"name": Path(expanded_active_path).name, "path": expanded_active_path}
             
        return None
    
    def set_active_project(self, key: str, path: str):
        """Set the active project"""
        if "saved_paths" not in self._config:
            self._config["saved_paths"] = {}
        
        active_key = f"{key}_active"
        self._config["saved_paths"][active_key] = self._collapse_path(path)
        self.save()
        logger.info(f"Active project set: {path}")
    
    def save_settings(self, settings: dict):
        """Save settings section"""
        self._config["settings"] = settings
        self.save()
        
    def _get_user_home(self) -> str:
        """Get user home directory with caching"""
        if not hasattr(self, "_cached_home"):
            # Try USERPROFILE (Windows), then HOME (Linux/Mac)
            self._cached_home = os.environ.get("USERPROFILE") or os.environ.get("HOME")
            if not self._cached_home:
                # Fallback to current directory if no env var found
                logger.warning("Neither USERPROFILE nor HOME defined, using current directory")
                self._cached_home = os.getcwd()
        return self._cached_home

    def _expand_path(self, path: str) -> str:
        """Expand environment variables and user home in path with security checks"""
        if not path:
            return path
            
        try:
            # 1. Expand variables
            expanded = os.path.expandvars(os.path.expanduser(path))
            
            # 2. Normalize path
            # Use pathlib for better normalization
            norm_path = Path(expanded).resolve()
            
            # 3. Security check: Ensure path is within safe boundaries
            # Allowed bases: User Home, Project Root
            user_home = Path(self._get_user_home()).resolve()
            
            # We allow paths under user profile or relative paths which resolve to under user profile
            # But we might also want to allow paths explicitly added by user outside profile? 
            # For now, let's just warn if it looks suspicious (e.g. System drive root)
            # A strict traversal check would prevent accessing anything outside allowed roots.
            
            # For this context (Developer Tool), we trust the user's config to some extent,
            # but we want to prevent accidental expansion of "../../" into system dirs if input was malicious
            
            if ".." in str(path) and not str(norm_path).startswith(str(user_home)):
                 logger.warning(f"Path traversal detected or path outside user home: {path} -> {norm_path}")
                 # You might want to return None or empty string here if strict
            
            return str(norm_path)
        except Exception as e:
            # Log without revealing sensitive full path if possible, or just the error
            logger.error(f"Error expanding path: {e}")
            return path

    def _collapse_path(self, path: str) -> str:
        """Replace user home with %USERPROFILE% if applicable"""
        if not path:
            return path
            
        try:
            user_profile = self._get_user_home()
            if not user_profile:
                return path
                
            path_obj = Path(path).resolve()
            profile_obj = Path(user_profile).resolve()
            
            # Strict check: path MUST start with user profile path
            if path_obj.is_relative_to(profile_obj):
                rel_path = path_obj.relative_to(profile_obj)
                # Use forward slashes for JSON consistency
                return f"%USERPROFILE%/{rel_path}".replace("\\", "/")
                
            return path
        except Exception as e:
            logger.warning(f"Error collapsing path: {e}")
            return path
    
    
    # ==================== Quick Panel Support ====================
    
    def get_quick_panel_settings(self) -> dict:
        """Get quick panel settings"""
        return self._config.get("quick_panel", {
            "visible": True,
            "x": 100,
            "y": 100
        })
    
    def set_quick_panel_settings(self, visible: bool, x: int, y: int):
        """Set quick panel settings"""
        self._config["quick_panel"] = {
            "visible": visible,
            "x": x,
            "y": y
        }
        self.save()
            
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
            "quick_panel": {
                "visible": True,
                "x": 100,
                "y": 100
            },
            "saved_paths": {}
        }
