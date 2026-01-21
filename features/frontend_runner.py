"""
Frontend Runner Feature - Run dev server for frontend projects
With multi-project support and non-blocking dialogs

Actions:
- run_dev: Run the dev server (select from saved projects or add new)
- select: Show project selector
- reset_path: Reset and manage projects (triggered by multi-press)
"""

import threading
from pathlib import Path
from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType
from utils.project_detector import get_dev_command
from utils.logger import get_logger

logger = get_logger(__name__)


class FrontendRunnerFeature(BaseFeature):
    """
    Feature 2: Frontend Project Runner with Multi-Project Support
    
    - Short press: Run dev server (select from list or use last active)
    - Long press: Show project selector (add/remove/select)
    - Multi-press (3x): Manage projects (add/remove)
    """
    
    name = "frontend_runner"
    description = "Run frontend dev server with multi-project support"
    supported_patterns = [PressType.SHORT, PressType.LONG, PressType.MULTI]
    
    CONFIG_KEY = "frontend_project"
    _dialog_lock = threading.Lock()
    _is_dialog_open = False
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute the run_dev or reset_path action"""
        
        # Prevent multiple dialogs
        if self._is_dialog_open:
            logger.warning("Dialog already open, ignoring request")
            return FeatureResult(
                status=FeatureStatus.CANCELLED,
                message="Dialog already open"
            )
        
        if action == "run_dev":
            return self._run_dev_server()
        elif action == "select":
            return self._show_project_selector_async()
        elif action == "reset_path":
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

    def _run_dev_server(self) -> FeatureResult:
        """Run the frontend dev server - quick launch with active project"""
        
        # Get active project first
        active = self.config_manager.get_active_project(self.CONFIG_KEY)
        
        if active:
            project_path = self._normalize_path(active.get("path", ""))
            if project_path and project_path.exists():
                logger.info(f"Using active project: {active.get('name', project_path.name)}")
                return self._start_dev_server(project_path)
        
        # Get all projects
        projects = self.config_manager.get_projects(self.CONFIG_KEY)
        
        if not projects:
            # No projects saved, ask to add one
            return self._add_new_project_async()
        
        # If only one project, use it directly
        if len(projects) == 1:
            project_path = self._normalize_path(projects[0].get("path", ""))
            if project_path and project_path.exists():
                self.config_manager.set_active_project(self.CONFIG_KEY, str(project_path))
                return self._start_dev_server(project_path)
        
        # Multiple projects - show selector
        return self._show_project_selector_async()
    
    def _show_project_selector_async(self) -> FeatureResult:
        """Show project selection dialog in a separate thread"""
        
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
        """Show project selection dialog (runs in thread)"""
        
        from ui.dialogs import ask_project_selection, show_notification
        
        projects = self.config_manager.get_projects(self.CONFIG_KEY)
        
        result = ask_project_selection(
            projects=projects,
            title="Frontend Projects",
            allow_add=True,
            allow_remove=True
        )
        
        if not result:
            logger.info("User cancelled project selection")
            return
        
        action = result["action"]
        
        if action == "select":
            project = result["project"]
            project_path = Path(project["path"])
            
            if not project_path.exists():
                show_notification(
                    title="❌ Error",
                    message=f"Path not found: {project_path}",
                    duration=3000
                )
                return
            
            # Set as active and run
            self.config_manager.set_active_project(self.CONFIG_KEY, str(project_path))
            self._start_dev_server(project_path)
        
        elif action == "add":
            path = result["path"]
            self.config_manager.add_project(self.CONFIG_KEY, path)
            
            show_notification(
                title="✅ Project Added",
                message=f"Added: {Path(path).name}",
                duration=2000
            )
            
            # Set as active and run
            project_path = Path(path)
            self.config_manager.set_active_project(self.CONFIG_KEY, path)
            self._start_dev_server(project_path)
        
        elif action == "remove":
            project = result["project"]
            self.config_manager.remove_project(self.CONFIG_KEY, project["path"])
            
            show_notification(
                title="🗑️ Project Removed",
                message=f"Removed: {project['name']}",
                duration=2000
            )
            
            # Show selector again if there are more projects
            remaining = self.config_manager.get_projects(self.CONFIG_KEY)
            if remaining:
                self._show_project_selector()
            else:
                # No projects left, reset flag
                self._is_dialog_open = False
    
    def _add_new_project_async(self) -> FeatureResult:
        """Add a new project (runs in thread)"""
        
        def run_dialog():
            self._is_dialog_open = True
            try:
                self._add_new_project()
            finally:
                self._is_dialog_open = False
        
        threading.Thread(target=run_dialog, daemon=True).start()
        
        return FeatureResult(
            status=FeatureStatus.SUCCESS,
            message="Opening folder selector..."
        )
    
    def _add_new_project(self):
        """Add a new project (runs in thread)"""
        
        from ui.dialogs import ask_folder_path, show_notification
        
        project_path = ask_folder_path("Select frontend project folder")
        
        if not project_path:
            logger.info("User cancelled folder selection")
            return
        
        # Add to project list
        self.config_manager.add_project(self.CONFIG_KEY, project_path)
        self.config_manager.set_active_project(self.CONFIG_KEY, project_path)
        
        show_notification(
            title="✅ Project Added",
            message=f"Added: {Path(project_path).name}",
            duration=2000
        )
        
        self._start_dev_server(Path(project_path))
    
    def _start_dev_server(self, project_path: Path) -> FeatureResult:
        """Start the dev server for the given project"""
        
        from ui.dialogs import show_notification
        
        # Detect dev command
        dev_cmd = get_dev_command(project_path)
        
        if not dev_cmd:
            # Default to npm run dev
            dev_cmd = ["npm", "run", "dev"]
            logger.info("No dev script detected, using 'npm run dev'")
        
        logger.info(f"Running dev server: {' '.join(dev_cmd)}")
        
        # Execute in new terminal
        success = self.command_executor.execute_in_terminal(
            command=dev_cmd,
            cwd=project_path,
            title=f"Dev Server - {project_path.name}",
            keep_open=True
        )
        
        if success:
            # Show notification in thread to avoid blocking
            def notify():
                show_notification(
                    title="▶️ Dev Server Started",
                    message=f"{project_path.name}",
                    duration=2000
                )
            threading.Thread(target=notify, daemon=True).start()
            
            return FeatureResult(
                status=FeatureStatus.SUCCESS,
                message=f"Dev server started for {project_path.name}"
            )
        
        return FeatureResult(
            status=FeatureStatus.ERROR,
            message="Failed to start dev server"
        )
