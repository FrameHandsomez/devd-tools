"""
Frontend Runner Feature - Run dev server for frontend projects
With multi-project support

Actions:
- run_dev: Run the dev server (select from saved projects or add new)
- reset_path: Reset and manage projects (triggered by multi-press)
"""

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
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute the run_dev or reset_path action"""
        
        if action == "run_dev":
            return self._run_dev_server()
        elif action == "select":
            return self._show_project_selector()
        elif action == "reset_path":
            return self._show_project_selector()
        else:
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=f"Unknown action: {action}"
            )
    
    def _run_dev_server(self) -> FeatureResult:
        """Run the frontend dev server - quick launch with active project"""
        
        # Get active project first
        active = self.config_manager.get_active_project(self.CONFIG_KEY)
        
        if active and Path(active["path"]).exists():
            project_path = Path(active["path"])
            logger.info(f"Using active project: {active['name']}")
            return self._start_dev_server(project_path)
        
        # Get all projects
        projects = self.config_manager.get_projects(self.CONFIG_KEY)
        
        if not projects:
            # No projects saved, ask to add one
            return self._add_new_project()
        
        # If only one project, use it directly
        if len(projects) == 1:
            project_path = Path(projects[0]["path"])
            if project_path.exists():
                self.config_manager.set_active_project(self.CONFIG_KEY, str(project_path))
                return self._start_dev_server(project_path)
        
        # Multiple projects - show selector
        return self._show_project_selector()
    
    def _show_project_selector(self) -> FeatureResult:
        """Show project selection dialog"""
        
        from ui.dialogs import ask_project_selection, show_notification
        
        projects = self.config_manager.get_projects(self.CONFIG_KEY)
        
        result = ask_project_selection(
            projects=projects,
            title="Frontend Projects",
            allow_add=True,
            allow_remove=True
        )
        
        if not result:
            return FeatureResult(
                status=FeatureStatus.CANCELLED,
                message="User cancelled project selection"
            )
        
        action = result["action"]
        
        if action == "select":
            project = result["project"]
            project_path = Path(project["path"])
            
            if not project_path.exists():
                return FeatureResult(
                    status=FeatureStatus.ERROR,
                    message=f"Project path not found: {project_path}"
                )
            
            # Set as active and run
            self.config_manager.set_active_project(self.CONFIG_KEY, str(project_path))
            return self._start_dev_server(project_path)
        
        elif action == "add":
            path = result["path"]
            self.config_manager.add_project(self.CONFIG_KEY, path)
            
            show_notification(
                title="✅ Project Added",
                message=f"Added: {Path(path).name}",
                duration=2000
            )
            
            # Ask again to select or run immediately
            project_path = Path(path)
            self.config_manager.set_active_project(self.CONFIG_KEY, path)
            return self._start_dev_server(project_path)
        
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
                return self._show_project_selector()
            
            return FeatureResult(
                status=FeatureStatus.SUCCESS,
                message="Project removed"
            )
        
        return FeatureResult(
            status=FeatureStatus.ERROR,
            message=f"Unknown action: {action}"
        )
    
    def _add_new_project(self) -> FeatureResult:
        """Add a new project"""
        
        from ui.dialogs import ask_folder_path, show_notification
        
        project_path = ask_folder_path("Select frontend project folder")
        
        if not project_path:
            return FeatureResult(
                status=FeatureStatus.CANCELLED,
                message="User cancelled path selection"
            )
        
        # Add to project list
        self.config_manager.add_project(self.CONFIG_KEY, project_path)
        self.config_manager.set_active_project(self.CONFIG_KEY, project_path)
        
        show_notification(
            title="✅ Project Added",
            message=f"Added: {Path(project_path).name}",
            duration=2000
        )
        
        return self._start_dev_server(Path(project_path))
    
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
            show_notification(
                title="▶️ Dev Server Started",
                message=f"{project_path.name}",
                duration=2000
            )
            
            return FeatureResult(
                status=FeatureStatus.SUCCESS,
                message=f"Dev server started for {project_path.name}"
            )
        
        return FeatureResult(
            status=FeatureStatus.ERROR,
            message="Failed to start dev server"
        )
