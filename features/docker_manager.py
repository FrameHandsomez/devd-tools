"""
Docker Manager Feature - Manage Docker Compose projects
"""

import threading
import subprocess
import sys
import json
import shutil
from pathlib import Path
from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType
from utils.logger import get_logger

logger = get_logger(__name__)


class DockerManagerFeature(BaseFeature):
    """
    Feature: Docker Manager
    
    - Short press: docker-compose up -d
    - Long press: docker-compose down
    """
    
    name = "docker_manager"
    description = "Manage Docker Compose"
    supported_patterns = [PressType.SHORT, PressType.LONG]
    
    CONFIG_KEY = "docker_project"
    _is_dialog_open = False
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute docker action"""
        
        if self._is_dialog_open and action == "select":
             return FeatureResult(
                status=FeatureStatus.CANCELLED,
                message="Dialog already open"
            )

        # Get active project or ask to select
        active_project = self._get_or_select_project()
        if not active_project and action != "select":
             if self._is_dialog_open:
                 return FeatureResult(status=FeatureStatus.SUCCESS, message="Selecting project...")
             return FeatureResult(status=FeatureStatus.CANCELLED, message="No project selected")

        if action == "select":
             return self._show_project_selector_async()
             
        # If we are here, we have a project path
        project_path = active_project
        
        if action == "menu":
            return self._show_docker_menu_async()
        
        # Actions that require run
        if action == "compose_up":
            return self._run_compose(project_path, "up -d", "🚀 Docker Up")
        elif action == "compose_down":
            return self._run_compose(project_path, "down", "🛑 Docker Down")
        elif action == "view_logs":
            return self._open_logs(project_path)
        elif action == "restart":
            return self._run_compose(project_path, "restart", "🔄 Docker Restart")
        elif action == "status":
            return self._run_compose(project_path, "ps -a", "📊 Docker Status")
        elif action == "build":
            return self._run_compose(project_path, "build", "🏗️ Docker Build")
        else:
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=f"Unknown action: {action}"
            )
            
    def _normalize_path(self, path_str: str) -> Path:
        """Normalize path string to proper Path object"""
        if not path_str:
            return None
        import os
        try:
            # Expand vars like %USERPROFILE%
            expanded = os.path.expandvars(path_str)
            normalized = expanded.replace('/', '\\')
            path = Path(normalized)
            if path.exists():
                return path.resolve()
            return path
        except Exception as e:
            logger.error(f"Path normalization error: {e}")
            return None

    def _get_or_select_project(self) -> Path:
        """Get active project path or trigger selector if none"""
        # Try docker specific project first
        active = self.config_manager.get_active_project(self.CONFIG_KEY)
        if active:
            path = self._normalize_path(active.get("path", ""))
            if path and path.exists():
                return path
                
        # Fallback to other active projects if they contain docker-compose.yml
        for key in ["terminal_project", "frontend_project", "git_project"]:
            p = self.config_manager.get_active_project(key)
            if p:
                path = self._normalize_path(p.get("path", ""))
                if path and path.exists() and (path / "docker-compose.yml").exists():
                    logger.info(f"Found docker-compose in {key}: {path}")
                    return path

        # No active project found, show selector
        # Only show selector if we are NOT already in a dialog (like menu)
        # to avoid confusing user or double-dialogs
        if not self._is_dialog_open:
            self._show_project_selector_async()
            
        return None

    def _show_docker_menu(self):
        """Show docker actions menu"""
        try:
            active = self._get_or_select_project()
            project_name = active.name if active else "No Project"
            
            options = [
                "🚀 Docker Up",
                "🛑 Docker Down", 
                "🔄 Restart",
                "📊 Status (ps)",
                "📝 View Logs",
                "📂 Select Project"
            ]
            
            result_data = self._run_dialog_subprocess("ask_choice", {
                "title": "Docker Menu",
                "message": f"Project: {project_name}\nSelect Action:",
                "choices": options
            })
            
            if not result_data:
                return
                
            choice_idx = result_data.get("result")
            
            if choice_idx is None:
                return
    
            if not active and choice_idx != 5:
                 self._run_notification_subprocess("❌ Error", "No project selected")
                 return
    
            if choice_idx == 0: # Up
                self._run_compose(active, "up -d", "🚀 Docker Up")
            elif choice_idx == 1: # Down
                self._run_compose(active, "down", "🛑 Docker Down")
            elif choice_idx == 2: # Restart
                self._run_compose(active, "restart", "🔄 Restart")
            elif choice_idx == 3: # Status
                self._run_compose(active, "ps -a", "📊 Status")
            elif choice_idx == 4: # Logs
                self._open_logs(active)
            elif choice_idx == 5: # Select
                self._show_project_selector()
                # Re-open menu
                # self._show_docker_menu() # Avoid recursion loop risk if selector fails
        except Exception as e:
            logger.error(f"Menu error: {e}")
            self._run_notification_subprocess("❌ Menu Error", str(e))

    def _show_project_selector_async(self) -> FeatureResult:
        def run_dialog():
            self._is_dialog_open = True
            try:
                self._show_project_selector()
            finally:
                self._is_dialog_open = False
        threading.Thread(target=run_dialog, daemon=True).start()
        return FeatureResult(status=FeatureStatus.SUCCESS, message="Select Project...")

    def _show_project_selector(self):
        """Show project selector using subprocess"""
        
        # Gather projects similar to before
        all_projects = []
        docker_projects = self.config_manager.get_projects(self.CONFIG_KEY)
        all_projects.extend(docker_projects)
        
        for key in ["frontend_project", "git_project"]:
            for p in self.config_manager.get_projects(key):
                if not any(x["path"] == p["path"] for x in all_projects):
                    all_projects.append(p)
                    
        result_data = self._run_dialog_subprocess("ask_project_selection", {
            "projects": all_projects,
            "title": "Select Docker Project",
            "allow_add": True,
            "allow_remove": True
        })
        
        if not result_data:
            return
            
        result = result_data.get("result")
        if not result:
            return
        
        action = result["action"]
        if action == "select":
            self.config_manager.set_active_project(self.CONFIG_KEY, result["project"]["path"])
            self._run_notification_subprocess("✅ Docker Project Set", result["project"]["name"])
        elif action == "add":
            path = result["path"]
            self.config_manager.add_project(self.CONFIG_KEY, path)
            self.config_manager.set_active_project(self.CONFIG_KEY, path)
            self._run_notification_subprocess("✅ Added & Set", Path(path).name)
        elif action == "remove":
            # Remove from relevant lists
            path_to_remove = result["project"]["path"]
            removed = False
            if self.config_manager.remove_project(self.CONFIG_KEY, path_to_remove):
                removed = True
            
            if removed:
                self._run_notification_subprocess("🗑️ Project Removed", f"Removed: {result['project']['name']}")
            
            # Re-open selector
            self._show_project_selector()
