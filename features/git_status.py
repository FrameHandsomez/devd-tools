"""
Git Status Feature - Display git status in a popup

Actions:
- status: Show git status for a project folder
"""

from pathlib import Path
from typing import Optional
from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType
from utils.logger import get_logger

logger = get_logger(__name__)


class GitStatusFeature(BaseFeature):
    """
    Feature: Git Status Display
    
    - Short press (F9): Show git status for selected folder
    """
    
    name = "git_status"
    description = "Display git status in a popup"
    supported_patterns = [PressType.SHORT]
    
    # Remember last used path
    _last_path: Optional[Path] = None
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute the git status action"""
        
        if action == "status":
            return self._show_status()
        else:
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=f"Unknown action: {action}"
            )
    
    def _show_status(self) -> FeatureResult:
        """Show git status for selected project"""
        
        from ui.dialogs import ask_folder_path, show_git_output
        
        # Use saved path or ask for folder
        project_path = self._last_path
        
        if not project_path or not project_path.exists():
            folder = ask_folder_path("Select Git Repository")
            if not folder:
                return FeatureResult(
                    status=FeatureStatus.CANCELLED,
                    message="User cancelled folder selection"
                )
            project_path = Path(folder)
        
        # Verify it's a git repository
        if not (project_path / ".git").exists():
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=f"Not a git repository: {project_path}"
            )
        
        # Save path for next time
        self._last_path = project_path
        
        logger.info(f"Running git status in {project_path}")
        
        # Run git status
        result = self.command_executor.execute(
            command=["git", "status"],
            cwd=project_path
        )
        
        # Display output
        if result.stdout:
            show_git_output(
                title=f"📊 Git Status: {project_path.name}",
                output=result.stdout,
                is_error=False
            )
        elif result.stderr:
            show_git_output(
                title=f"❌ Git Error: {project_path.name}",
                output=result.stderr,
                is_error=True
            )
        
        return FeatureResult(
            status=FeatureStatus.SUCCESS if result.return_code == 0 else FeatureStatus.ERROR,
            message=f"Git status for {project_path.name}",
            data={"path": str(project_path)}
        )
