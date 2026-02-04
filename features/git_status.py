"""
Git Status Feature - Display git status in a popup

Actions:
- status: Show git status for a project folder
"""

from pathlib import Path
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
    _last_path = None
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute the git status action"""
        
        if action == "status":
            return self._show_status()
        else:
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=f"Unknown action: {action}"
            )
            
    def _run_dialog_subprocess(self, command, data):
        """Helper to run dialog subprocess"""
        import subprocess
        import sys
        import json
        from pathlib import Path
        
        # Point to ui/dialogs.py relative to this file
        dialog_script = Path(__file__).parent.parent / "ui" / "dialogs.py"
        
        try:
            is_frozen = getattr(sys, 'frozen', False)
            if is_frozen:
                 cmd = [sys.executable, "dialog", command, json.dumps(data)]
            else:
                 cmd = [sys.executable, str(dialog_script), command, json.dumps(data)]
            
            # Run without window creation flag on Windows if possible, but keep simple for now
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
                
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                creationflags=creation_flags,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                logger.error(f"Dialog error ({command}): {result.stderr}")
                return None
                
            if not result.stdout.strip():
                return None
                
            return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"Subprocess failed: {e}")
            return None
    
    def _show_notification_async(self, title: str, message: str, duration: int = 5000):
        """Show notification via subprocess"""
        self._run_dialog_subprocess("show_notification", {
            "title": title,
            "message": message,
            "duration": duration
        })

    def _show_status(self) -> FeatureResult:
        """Show git status for selected project"""
        
        from utils.project_detector import get_active_project_path
        from core.commands.command_executor import find_git_path
        
        # Check if Git is installed first
        if not find_git_path():
            self._show_notification_async(
                "❌ Git ไม่พบในเครื่อง",
                "กรุณาติดตั้ง Git ก่อนใช้งาน\ngit-scm.com/download/win"
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
            result = self._run_dialog_subprocess("ask_folder_path", {
                "title": "Select Git Repository"
            })
            
            if not result or not result.get("path"):
                return FeatureResult(
                    status=FeatureStatus.CANCELLED,
                    message="User cancelled folder selection"
                )
            project_path = Path(result.get("path"))
        
        # Verify it's a git repository
        if not (project_path / ".git").exists():
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=f"Not a git repository: {project_path}"
            )
        
        # Save path for next time
        self._last_path = project_path
        
        logger.info(f"Running git status in {project_path}")
        
        # Run git status using command executor (this is fine as it's just getting output, not UI)
        result = self.command_executor.execute(
            command=["git", "status"],
            cwd=project_path
        )
        
        # Display output via subprocess dialog
        if result.stdout:
            self._run_dialog_subprocess("show_git_output", {
                "title": f"📊 Git Status: {project_path.name}",
                "output": result.stdout,
                "is_error": False
            })
        elif result.stderr:
             self._run_dialog_subprocess("show_git_output", {
                "title": f"❌ Git Error: {project_path.name}",
                "output": result.stderr,
                "is_error": True
            })
        
        return FeatureResult(
            status=FeatureStatus.SUCCESS if result.return_code == 0 else FeatureStatus.ERROR,
            message=f"Git status for {project_path.name}",
            data={"path": str(project_path)}
        )
