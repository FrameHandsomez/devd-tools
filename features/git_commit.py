"""
Git Commit Feature - Quick commit workflow with multi-project support

Actions:
- commit: Add, commit with message, and push (uses active project)
- select: Show project selector
- manage: Manage git projects (add/remove)
"""

import threading
from pathlib import Path
from typing import Optional
from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType
from utils.logger import get_logger

logger = get_logger(__name__)


class GitCommitFeature(BaseFeature):
    """
    Feature: Quick Git Commit Workflow with Multi-Project Support
    
    - Short press: Commit to active project
    - Long press: Select project from list
    - Multi-press (3x): Manage projects (add/remove)
    """
    
    name = "git_commit"
    description = "Quick commit workflow with multi-project support"
    supported_patterns = [PressType.SHORT, PressType.LONG, PressType.MULTI]
    
    CONFIG_KEY = "git_project"
    _is_dialog_open = False
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute the git commit action"""
        
        # Prevent multiple dialogs
        if self._is_dialog_open:
            logger.warning("Dialog already open, ignoring request")
            return FeatureResult(
                status=FeatureStatus.CANCELLED,
                message="Dialog already open"
            )
        
        if action == "commit":
            return self._commit_workflow()
        elif action == "select":
            return self._show_project_selector_async()
        elif action == "manage":
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
        
        # Convert to Path object and resolve to absolute path
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

    def _commit_workflow(self) -> FeatureResult:
        """Run the full commit workflow with active project"""
        
        from core.commands.command_executor import find_git_path
        
        # Check if Git is installed first
        if not find_git_path():
            self._show_notification_async(
                "❌ Git ไม่พบในเครื่อง",
                "กรุณาติดตั้ง Git ก่อนใช้งาน"
            )
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message="Git not found"
            )
        
        # Get active project
        active = self.config_manager.get_active_project(self.CONFIG_KEY)
        logger.info(f"Active project from config: {active}")
        
        if active:
            # Normalize the path for cross-platform compatibility
            project_path = self._normalize_path(active.get("path", ""))
            logger.info(f"Normalized project path: {project_path}")
            
            if project_path and project_path.exists():
                logger.info(f"Project path exists: {project_path}")
                
                # Check for .git folder (try multiple ways)
                git_folder = project_path / ".git"
                git_exists = git_folder.exists() or git_folder.is_dir()
                logger.info(f"Git folder check: {git_folder} -> exists={git_exists}")
                
                if git_exists:
                    logger.info(f"Using active git project: {active.get('name', project_path.name)}")
                    return self._run_commit_async(project_path)
                else:
                    logger.warning(f".git folder not found at {git_folder}")
                    # Try to find .git in parent directories (in case user selected subfolder)
                    for parent in project_path.parents:
                        if (parent / ".git").exists():
                            logger.info(f"Found .git in parent: {parent}")
                            return self._run_commit_async(parent)
            else:
                logger.warning(f"Active project path does not exist: {project_path}")
        
        # Get all projects
        projects = self.config_manager.get_projects(self.CONFIG_KEY)
        logger.info(f"All projects: {len(projects) if projects else 0}")
        
        if not projects:
            # No projects saved, ask to add one
            logger.info("No projects found, prompting to add one")
            return self._add_new_project_async()
        
        # If only one project, use it directly
        if len(projects) == 1:
            project_path = self._normalize_path(projects[0].get("path", ""))
            if project_path and project_path.exists():
                git_folder = project_path / ".git"
                if git_folder.exists():
                    self.config_manager.set_active_project(self.CONFIG_KEY, str(project_path))
                    return self._run_commit_async(project_path)
        
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
            title="Git Projects",
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
            
            if not (project_path / ".git").exists():
                show_notification(
                    title="❌ Error",
                    message=f"Not a git repository",
                    duration=3000
                )
                return
            
            # Set as active and commit
            self.config_manager.set_active_project(self.CONFIG_KEY, str(project_path))
            self._run_commit(project_path)
        
        elif action == "add":
            path = result["path"]
            
            # Verify it's a git repo
            if not (Path(path) / ".git").exists():
                show_notification(
                    title="❌ Not a Git Repository",
                    message="Please select a folder with .git",
                    duration=3000
                )
                return
            
            self.config_manager.add_project(self.CONFIG_KEY, path)
            
            show_notification(
                title="✅ Git Project Added",
                message=f"Added: {Path(path).name}",
                duration=2000
            )
            
            # Set as active and commit
            self.config_manager.set_active_project(self.CONFIG_KEY, path)
            self._run_commit(Path(path))
        
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
                # No projects left, reset flag so user can add new ones
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
        """Add a new git project (runs in thread)"""
        
        from ui.dialogs import ask_folder_path, show_notification
        
        project_path = ask_folder_path("Select Git Repository")
        
        if not project_path:
            logger.info("User cancelled folder selection")
            return
        
        path = Path(project_path)
        
        # Verify it's a git repo
        if not (path / ".git").exists():
            show_notification(
                title="❌ Not a Git Repository",
                message="Please select a folder with .git",
                duration=3000
            )
            return
        
        # Add to project list
        self.config_manager.add_project(self.CONFIG_KEY, project_path)
        self.config_manager.set_active_project(self.CONFIG_KEY, project_path)
        
        show_notification(
            title="✅ Git Project Added",
            message=f"Added: {path.name}",
            duration=2000
        )
        
        self._run_commit(path)
    
    def _run_commit_async(self, project_path: Path) -> FeatureResult:
        """Run commit workflow asynchronously"""
        
        def run():
            self._is_dialog_open = True
            try:
                self._run_commit(project_path)
            finally:
                self._is_dialog_open = False
        
        threading.Thread(target=run, daemon=True).start()
        
        return FeatureResult(
            status=FeatureStatus.SUCCESS,
            message=f"Opening commit dialog for {project_path.name}..."
        )
    
    def _check_git_config(self, project_path: Path) -> bool:
        """Check if user.name and user.email are configured"""
        import subprocess
        
        try:
            # Check user.name
            name = subprocess.check_output(
                ["git", "config", "user.name"],
                cwd=project_path,
                text=True
            ).strip()
            
            # Check user.email
            email = subprocess.check_output(
                ["git", "config", "user.email"],
                cwd=project_path,
                text=True
            ).strip()
            
            return bool(name and email)
            
        except subprocess.CalledProcessError:
            return False
            
    def _run_commit(self, project_path: Path):
        """Run the actual commit workflow (runs in thread)"""
        
        from ui.dialogs import ask_commit_message, show_notification
        
        # Check git config
        logger.info(f"Checking git config for: {project_path}")
        if not self._check_git_config(project_path):
            logger.warning("Git config check failed - user.name or user.email missing")
            self._show_notification_async(
                "❌ Git Config Missing",
                "Please configure user.name and user.email first"
            )
            return
        logger.info("Git config check passed")

        # Ask for commit message
        commit_message = ask_commit_message(f"Commit to {project_path.name}")
        
        if not commit_message:
            logger.info("User cancelled commit")
            return
        
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
            self._show_notification_async(
                "✅ Git Commit",
                f"Committed: {commit_message[:50]}..."
            )
    
    def _show_notification_async(self, title: str, message: str):
        """Show notification in a separate thread"""
        
        def show():
            try:
                from ui.dialogs import show_notification
                show_notification(title=title, message=message, duration=3000)
            except Exception as e:
                logger.warning(f"Could not show notification: {e}")
        
        threading.Thread(target=show, daemon=True).start()
