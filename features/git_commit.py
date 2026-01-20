"""
Git Commit Feature - Quick commit workflow

Actions:
- commit: Add, commit with message, and push
"""

from pathlib import Path
from typing import Optional
from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType
from utils.logger import get_logger

logger = get_logger(__name__)


class GitCommitFeature(BaseFeature):
    """
    Feature: Quick Git Commit Workflow
    
    - Short press (F10): git add . -> git commit -m "..." -> git push
    """
    
    name = "git_commit"
    description = "Quick commit workflow: add, commit, push"
    supported_patterns = [PressType.SHORT]
    
    # Remember last used path
    _last_path: Optional[Path] = None
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute the git commit action"""
        
        if action == "commit":
            return self._commit_workflow()
        else:
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=f"Unknown action: {action}"
            )
    
    def _commit_workflow(self) -> FeatureResult:
        """Run the full commit workflow"""
        
        from ui.dialogs import ask_folder_path, ask_commit_message, show_notification
        from utils.project_detector import get_active_project_path
        from core.commands.command_executor import find_git_path
        import threading
        
        # Check if Git is installed first
        if not find_git_path():
            show_notification(
                title="❌ Git ไม่พบในเครื่อง",
                message="กรุณาติดตั้ง Git ก่อนใช้งาน\ngit-scm.com/download/win",
                duration=5000
            )
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message="Git not found"
            )
        
        # Try to auto-detect from active window (VS Code)
        project_path = get_active_project_path()
        
        # Fall back to saved path
        if not project_path:
            project_path = self._last_path
        
        # If still no path or path doesn't exist, ask user
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
        
        # Ask for commit message
        commit_message = ask_commit_message(f"Commit to {project_path.name}")
        
        if not commit_message:
            return FeatureResult(
                status=FeatureStatus.CANCELLED,
                message="User cancelled commit"
            )
        
        logger.info(f"Committing to {project_path} with message: {commit_message}")
        
        # Run git add, commit, push in interactive terminal
        commands = [
            ["git", "add", "."],
            ["git", "commit", "-m", commit_message],
            ["git", "push"]
        ]
        
        success = self.command_executor.execute_interactive(
            commands=commands,
            cwd=project_path,
            title=f"Git Commit: {project_path.name}"
        )
        
        if success:
            # Show notification in thread
            def show_notif():
                try:
                    show_notification(
                        title="✅ Git Commit",
                        message=f"Committed: {commit_message[:50]}...",
                        duration=3000
                    )
                except Exception as e:
                    logger.warning(f"Could not show notification: {e}")
            
            threading.Thread(target=show_notif, daemon=True).start()
            
            return FeatureResult(
                status=FeatureStatus.SUCCESS,
                message=f"Committed to {project_path.name}",
                data={"path": str(project_path), "message": commit_message}
            )
        
        return FeatureResult(
            status=FeatureStatus.ERROR,
            message="Commit operation failed"
        )
