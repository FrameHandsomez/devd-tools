"""
Clone Project Feature - Git clone with auto dependency installation

Actions:
- clone: Clone a new project from Git URL
- update: Update an existing project (git pull)
"""

from pathlib import Path
from typing import Optional
from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType
from utils.project_detector import detect_project_type, get_install_command, ProjectType
from utils.logger import get_logger

logger = get_logger(__name__)


class CloneProjectFeature(BaseFeature):
    """
    Feature 1: Clone Project Workflow
    
    - Short press: Clone new project
    - Long press: Update existing project
    """
    
    name = "clone_project"
    description = "Clone git repository and auto-install dependencies"
    supported_patterns = [PressType.SHORT, PressType.LONG]
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute the clone or update action"""
        
        if action == "clone":
            return self._clone_project()
        elif action == "update":
            return self._update_project()
        else:
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=f"Unknown action: {action}"
            )
    
    def _clone_project(self) -> FeatureResult:
        """Clone a new project from Git URL"""
        
        # Import here to avoid circular import and keep core headless
        from ui.dialogs import ask_git_clone_info
        
        # Get Git URL and path from user
        result = ask_git_clone_info(
            default_path=self.config_manager.get_settings().get("default_clone_path", "C:\\Projects")
        )
        
        if not result:
            return FeatureResult(
                status=FeatureStatus.CANCELLED,
                message="User cancelled clone operation"
            )
        
        git_url, clone_path = result
        clone_path = Path(clone_path)
        
        # Extract project name from URL
        project_name = git_url.rstrip("/").split("/")[-1]
        if project_name.endswith(".git"):
            project_name = project_name[:-4]
        
        project_path = clone_path / project_name
        
        logger.info(f"Cloning {git_url} to {project_path}")
        
        # Build commands
        commands = [
            ["git", "clone", git_url, str(project_path)]
        ]
        
        # Detect project type and add install command
        # We'll check after clone in the interactive terminal
        
        # Execute in interactive terminal
        success = self.command_executor.execute_interactive(
            commands=[
                ["git", "clone", git_url, str(project_path)],
            ],
            cwd=clone_path,
            title="Clone Project"
        )
        
        if success:
            # After cloning, detect project type and install deps
            self._post_clone_install(project_path)
            
            return FeatureResult(
                status=FeatureStatus.SUCCESS,
                message=f"Project cloned to {project_path}"
            )
        
        return FeatureResult(
            status=FeatureStatus.ERROR,
            message="Clone operation failed"
        )
    
    def _post_clone_install(self, project_path: Path):
        """Install dependencies after cloning"""
        import time
        
        # Give git clone time to finish
        time.sleep(2)
        
        if not project_path.exists():
            logger.warning(f"Project path doesn't exist yet: {project_path}")
            return
        
        project_type = detect_project_type(project_path)
        
        if project_type == ProjectType.NODEJS:
            install_cmd = get_install_command(project_type, project_path)
            if install_cmd:
                self.command_executor.execute_interactive(
                    commands=[install_cmd],
                    cwd=project_path,
                    title="Installing Dependencies"
                )
        
        elif project_type == ProjectType.PYTHON:
            # Create venv and install requirements
            commands = [
                ["python", "-m", "venv", "venv"],
                [".\\venv\\Scripts\\pip.exe", "install", "-r", "requirements.txt"]
            ]
            self.command_executor.execute_interactive(
                commands=commands,
                cwd=project_path,
                title="Setting up Python Environment"
            )
    
    def _update_project(self) -> FeatureResult:
        """Update an existing project with git pull"""
        
        from ui.dialogs import ask_folder_path
        
        # Ask for project path
        project_path = ask_folder_path("Select project to update")
        
        if not project_path:
            return FeatureResult(
                status=FeatureStatus.CANCELLED,
                message="User cancelled update operation"
            )
        
        project_path = Path(project_path)
        
        if not (project_path / ".git").exists():
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message="Not a git repository"
            )
        
        logger.info(f"Updating project at {project_path}")
        
        # Execute git pull in terminal
        self.command_executor.execute_interactive(
            commands=[["git", "pull"]],
            cwd=project_path,
            title="Update Project"
        )
        
        return FeatureResult(
            status=FeatureStatus.SUCCESS,
            message=f"Project updated at {project_path}"
        )
