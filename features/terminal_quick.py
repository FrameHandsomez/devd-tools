"""
Terminal Quick Actions Feature - Open terminal at project directory

Actions:
- open_here: Open terminal at active project
- select: Select project from list
"""

import threading
import subprocess
import os
from pathlib import Path
from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType
from utils.logger import get_logger

logger = get_logger(__name__)


class TerminalQuickFeature(BaseFeature):
    """
    Feature: Terminal Quick Actions
    
    - Short press: Open terminal at active project
    - Long press: Select project from list
    """
    
    name = "terminal_quick"
    description = "Open terminal at project directory"
    supported_patterns = [PressType.SHORT, PressType.LONG]
    
    CONFIG_KEY = "terminal_project"
    _is_dialog_open = False
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute terminal action"""
        
        if self._is_dialog_open:
            return FeatureResult(
                status=FeatureStatus.CANCELLED,
                message="Dialog already open"
            )
        
        if action == "open_here":
            return self._open_terminal()
        elif action == "select":
            return self._show_project_selector_async()
        else:
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=f"Unknown action: {action}"
            )
    
    def _normalize_path(self, path_str: str) -> Path:
        """Normalize path string to proper Path object - handles all formats"""
        if not path_str:
            return None
        
        try:
            # Replace forward slashes with backslashes for Windows consistency
            normalized = path_str.replace('/', '\\')
            path = Path(normalized)
            
            # Resolve to get absolute path with consistent format
            if path.exists():
                return path.resolve()
            return path
        except Exception as e:
            logger.error(f"Path normalization failed for '{path_str}': {e}")
            return None

    def _open_terminal(self) -> FeatureResult:
        """Open terminal at active project"""
        
        # Get active project
        active = self.config_manager.get_active_project(self.CONFIG_KEY)
        
        if active:
            project_path = self._normalize_path(active.get("path", ""))
            if project_path and project_path.exists():
                logger.info(f"Using terminal_project active: {project_path}")
                return self._launch_terminal(project_path)
        
        # Try frontend project as fallback
        frontend_active = self.config_manager.get_active_project("frontend_project")
        if frontend_active:
            project_path = self._normalize_path(frontend_active.get("path", ""))
            if project_path and project_path.exists():
                logger.info(f"Using frontend_project active: {project_path}")
                return self._launch_terminal(project_path)
        
        # Try git project as fallback
        git_active = self.config_manager.get_active_project("git_project")
        if git_active:
            project_path = self._normalize_path(git_active.get("path", ""))
            if project_path and project_path.exists():
                logger.info(f"Using git_project active: {project_path}")
                return self._launch_terminal(project_path)
        
        logger.info("No active project found, showing selector")
        # No active project - show selector
        return self._show_project_selector_async()
    
    def _launch_terminal(self, project_path: Path) -> FeatureResult:
        """Launch terminal at the given path"""
        
        path_str = str(project_path)
        logger.info(f"Attempting to launch terminal at: {path_str}")
        
        try:
            # Try Windows Terminal first (wt.exe)
            import shutil
            wt_path = shutil.which("wt")
            
            if wt_path:
                # Windows Terminal is available
                logger.info(f"Found Windows Terminal at: {wt_path}")
                subprocess.Popen(
                    f'wt.exe -d "{path_str}"',
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                logger.info(f"✅ Opened Windows Terminal at: {path_str}")
            else:
                # Fallback to PowerShell
                logger.info("Windows Terminal not found, using PowerShell")
                subprocess.Popen(
                    f'start powershell -NoExit -Command "Set-Location -Path \'{path_str}\'"',
                    shell=True
                )
                logger.info(f"✅ Opened PowerShell at: {path_str}")
            
            self._show_notification_async(
                "📱 Terminal Opened",
                f"{project_path.name}"
            )
            
            return FeatureResult(
                status=FeatureStatus.SUCCESS,
                message=f"Terminal opened at {project_path.name}"
            )
            
        except Exception as e:
            logger.error(f"Failed to open terminal: {e}")
            
            # Last resort - try basic cmd
            try:
                os.system(f'start cmd /K "cd /d {path_str}"')
                logger.info(f"✅ Opened CMD at: {path_str}")
                return FeatureResult(
                    status=FeatureStatus.SUCCESS,
                    message=f"Terminal opened at {project_path.name}"
                )
            except Exception as e2:
                logger.error(f"Failed to open CMD: {e2}")
                return FeatureResult(
                    status=FeatureStatus.ERROR,
                    message=f"Failed to open terminal: {e}"
                )
    
    def _show_project_selector_async(self) -> FeatureResult:
        """Show project selector in thread"""
        
        def run_dialog():
            self._is_dialog_open = True
            try:
                self._show_project_selector()
            finally:
                self._is_dialog_open = False
        
        threading.Thread(target=run_dialog, daemon=True).start()
        
        return FeatureResult(
            status=FeatureStatus.SUCCESS,
            message="Opening project selector..."
        )
    
    def _show_project_selector(self):
        """Show project selector dialog"""
        
        from ui.dialogs import ask_project_selection, show_notification
        
        logger.info("Opening project selector dialog...")
        
        # Combine all projects
        all_projects = []
        
        # Add frontend projects
        frontend_projects = self.config_manager.get_projects("frontend_project")
        for p in frontend_projects:
            if p not in all_projects:
                all_projects.append(p)
        
        # Add git projects
        git_projects = self.config_manager.get_projects("git_project")
        for p in git_projects:
            if not any(x["path"] == p["path"] for x in all_projects):
                all_projects.append(p)
        
        # Add terminal-specific projects
        terminal_projects = self.config_manager.get_projects(self.CONFIG_KEY)
        for p in terminal_projects:
            if not any(x["path"] == p["path"] for x in all_projects):
                all_projects.append(p)
        
        logger.info(f"Found {len(all_projects)} projects")
        
        result = ask_project_selection(
            projects=all_projects,
            title="Open Terminal",
            allow_add=True,
            allow_remove=False  # Don't remove from combined list
        )
        
        if not result:
            logger.info("Project selection cancelled")
            return
        
        action = result["action"]
        logger.info(f"Project selector action: {action}")
        
        if action == "select":
            project = result["project"]
            project_path = Path(project["path"])
            logger.info(f"Selected project: {project['name']} at {project_path}")
            
            if not project_path.exists():
                logger.error(f"Path not found: {project_path}")
                show_notification(
                    title="❌ Error",
                    message=f"Path not found: {project_path}",
                    duration=3000
                )
                return
            
            # Set as active
            self.config_manager.set_active_project(self.CONFIG_KEY, str(project_path))
            logger.info(f"Set active project and launching terminal...")
            self._launch_terminal(project_path)
        
        elif action == "add":
            path = result["path"]
            logger.info(f"Adding new project: {path}")
            self.config_manager.add_project(self.CONFIG_KEY, path)
            self.config_manager.set_active_project(self.CONFIG_KEY, path)
            
            show_notification(
                title="✅ Project Added",
                message=f"Added: {Path(path).name}",
                duration=2000
            )
            
            # Launch terminal for the newly added project
            logger.info(f"Launching terminal for newly added project: {path}")
            try:
                self._launch_terminal(Path(path))
            except Exception as e:
                logger.error(f"Failed to launch terminal after add: {e}")
    
    def _show_notification_async(self, title: str, message: str):
        """Show notification in thread"""
        
        def show():
            try:
                from ui.dialogs import show_notification
                show_notification(title=title, message=message, duration=2000)
            except Exception:
                pass
        
        threading.Thread(target=show, daemon=True).start()
