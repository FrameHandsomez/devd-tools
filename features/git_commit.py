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
        elif action == "menu":
            return self._show_git_menu_async()
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

    def _show_project_selector_async(self) -> FeatureResult:
        """Show project selection dialog in a separate thread"""
        def run_dialog():
            self._is_dialog_open = True
            try:
                self._show_project_selector()
            finally:
                self._is_dialog_open = False
        
        threading.Thread(target=run_dialog, daemon=True).start()
        return FeatureResult(status=FeatureStatus.SUCCESS, message="Opening project selector...")
    
    def _show_project_selector(self):
        """Show project selection dialog (runs in thread)"""
        projects = self.config_manager.get_projects(self.CONFIG_KEY)
        
        result_data = self._run_dialog_subprocess("ask_project_selection", {
            "projects": projects,
            "title": "Git Projects",
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
            project = result["project"]
            project_path = Path(project["path"])
            
            if not project_path.exists():
                self._show_notification_async("❌ Error", f"Path not found: {project_path}")
                return
            
            if not (project_path / ".git").exists():
                self._show_notification_async("❌ Error", "Not a git repository")
                return
            
            # Set as active and commit
            self.config_manager.set_active_project(self.CONFIG_KEY, str(project_path))
            self._run_commit(project_path)
        
        elif action == "add":
            path = result["path"]
            # Verify it's a git repo
            if not (Path(path) / ".git").exists():
                self._show_notification_async("❌ Not a Git Repository", "Please select a folder with .git")
                return
            
            self.config_manager.add_project(self.CONFIG_KEY, path)
            self._show_notification_async("✅ Git Project Added", f"Added: {Path(path).name}")
            
            # Set as active and commit
            self.config_manager.set_active_project(self.CONFIG_KEY, path)
            self._run_commit(Path(path))
        
        elif action == "remove":
            project = result["project"]
            self.config_manager.remove_project(self.CONFIG_KEY, project["path"])
            self._show_notification_async("🗑️ Project Removed", f"Removed: {project['name']}")
            
            # Show selector again if there are more projects
            remaining = self.config_manager.get_projects(self.CONFIG_KEY)
            if remaining:
                self._show_project_selector()
            else:
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
        return FeatureResult(status=FeatureStatus.SUCCESS, message="Opening folder selector...")
    
    def _add_new_project(self):
        """Add a new git project (runs in thread)"""
        result = self._run_dialog_subprocess("ask_folder_path", {
            "title": "Select Git Repository"
        })
        
        if not result or not result.get("path"):
            logger.info("User cancelled folder selection")
            return
            
        project_path = result.get("path")
        path = Path(project_path)
        
        # Verify it's a git repo
        if not (path / ".git").exists():
            self._show_notification_async("❌ Not a Git Repository", "Please select a folder with .git")
            return
        
        # Add to project list
        self.config_manager.add_project(self.CONFIG_KEY, project_path)
        self.config_manager.set_active_project(self.CONFIG_KEY, project_path)
        
        self._show_notification_async("✅ Git Project Added", f"Added: {path.name}")
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
        return FeatureResult(status=FeatureStatus.SUCCESS, message=f"Opening commit dialog for {project_path.name}...")
    
    def _check_git_config(self, project_path: Path) -> bool:
        """Check if user.name and user.email are configured"""
        import subprocess
        try:
            name = subprocess.check_output(
                ["git", "config", "user.name"],
                cwd=project_path,
                text=True,
                encoding='utf-8', errors='replace'
            ).strip()
            email = subprocess.check_output(
                ["git", "config", "user.email"],
                cwd=project_path,
                text=True,
                encoding='utf-8', errors='replace'
            ).strip()
            return bool(name and email)
        except subprocess.CalledProcessError:
            return False
            
    def _run_commit(self, project_path: Path):
        """Run the actual commit workflow (runs in thread)"""
        logger.info(f"Checking git config for: {project_path}")
        if not self._check_git_config(project_path):
            logger.warning("Git config check failed")
            self._show_notification_async("❌ Git Config Missing", "Please configure user.name/email first")
            return
        logger.info("Git config check passed")

        # Ask for commit message
        result = self._run_dialog_subprocess("ask_commit_message", {
            "title": f"Commit to {project_path.name}",
            "initial_value": ""
        })
        
        if not result or not result.get("message"):
            logger.info("User cancelled commit")
            return
            
        commit_message = result.get("message")
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
            self._show_notification_async("✅ Git Commit", f"Committed: {commit_message[:50]}...")
    
    def _show_git_menu_async(self) -> FeatureResult:
        """Show git menu in thread"""
        def run_menu():
            self._is_dialog_open = True
            try:
                self._show_git_menu()
            finally:
                self._is_dialog_open = False
                
        threading.Thread(target=run_menu, daemon=True).start()
        return FeatureResult(status=FeatureStatus.SUCCESS, message="Opening Git Menu...")

    def _show_git_menu(self):
        active = self.config_manager.get_active_project(self.CONFIG_KEY)
        project_name = active.get("name", "Unknown") if active else "No Project"
        
        options = [
            "✅ Commit & Push",
            "✨ AI Auto-Commit",
            "📊 Check Status",
            "🔄 Pull Changes",
            "🗑️ Discard Changes",
            "📂 Switch Project"
        ]
        
        result_data = self._run_dialog_subprocess("ask_choice", {
            "title": "Git Manager",
            "message": f"Repo: {project_name}\nSelect Action:",
            "choices": options
        })
        
        if not result_data:
            return
        
        choice_idx = result_data.get("result")
        if choice_idx is None:
            return
            
        if choice_idx == 5: # Switch Project
            self._show_project_selector()
            return
            
        # Ensure active project
        if not active:
             if self._show_project_selector(): 
                 active = self.config_manager.get_active_project(self.CONFIG_KEY)
             
        if not active:
            return

        project_path = Path(active["path"])
        
        if choice_idx == 0: # Commit
            self._run_commit(project_path)
            
        elif choice_idx == 1: # AI Auto-Commit
            self._run_ai_commit(project_path)
            
        elif choice_idx == 2: # Status
            self.command_executor.execute_interactive(
                commands=[["git", "status"]],
                cwd=project_path,
                title="Git Status",
                keep_open=True
            )
            
        elif choice_idx == 3: # Pull
            self.command_executor.execute_interactive(
                commands=[["git", "pull"]],
                cwd=project_path,
                title="Git Pull"
            )
            
        elif choice_idx == 4: # Discard
            yes_no = self._run_dialog_subprocess("ask_yes_no", {
                "title": "Confirm Discard",
                "message": "⚠️ Are you sure you want to discard ALL changes?"
            })
            if yes_no and yes_no.get("result"):
                self.command_executor.execute_interactive(
                    commands=[["git", "restore", "."]],
                    cwd=project_path,
                    title="Discard Changes"
                )

    def _run_ai_commit(self, project_path: Path):
        """Prepare AI prompt for commit message"""
        import subprocess
        import pyperclip
        import webbrowser
        
        try:
            # 1. Get git status/diff
            staged_diff = subprocess.check_output(
                ["git", "diff", "--cached"], 
                cwd=project_path, text=True,
                encoding='utf-8', errors='replace'
            )
            
            diff_output = staged_diff
            if not staged_diff.strip():
                diff_output = subprocess.check_output(
                    ["git", "diff"],
                    cwd=project_path, text=True,
                    encoding='utf-8', errors='replace'
                )
                
            if not diff_output.strip():
                diff_output = subprocess.check_output(
                    ["git", "status"],
                    cwd=project_path, text=True,
                    encoding='utf-8', errors='replace'
                )
            
            # 2. Prepare Prompt
            prompt_header = "You are a senior developer. Write a clear, concise git commit message for the following changes.\\n"
            prompt_header += "Format:\\n<type>: <subject>\\n\\n<body>\\n\\nChanges:\\n```\\n"
            
            prompt_footer = "\\n```\\n\\nConstraints:\\n"
            prompt_footer += "- Use Conventional Commits (feat, fix, docs, style, refactor, test, chore)\\n"
            prompt_footer += "- Keep subject under 50 chars\\n- English language"
            
            prompt = prompt_header + diff_output[:3000] + prompt_footer
            
            # 3. Copy to clipboard
            pyperclip.copy(prompt)
            
            # 4. Open ChatGPT
            webbrowser.open("https://chat.openai.com/")
            
            self._show_notification_async(
                "✨ AI Prompt Ready",
                "Prompt copied! Paste in ChatGPT to get commit message."
            )
            
        except Exception as e:
            logger.error(f"AI Commit Error: {e}")
            self._show_notification_async("❌ Error", f"Failed: {str(e)}")
            
    def _show_notification_async(self, title: str, message: str):
        """Show notification in a separate thread"""
        self._run_dialog_subprocess("show_notification", {
            "title": title,
            "message": message,
            "duration": 3000
        })
