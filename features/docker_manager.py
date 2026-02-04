"""
Docker Manager Feature - Manage Docker Compose projects
"""

import threading
import subprocess
import os
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
             # If we tried to get a project and failed (and weren't just trying to select),
             # then we can't proceed. _get_or_select_project already triggers the selector if needed.
             # but if it returns None, it means user cancelled or is selecting asynchronously.
             if self._is_dialog_open:
                 return FeatureResult(status=FeatureStatus.c, message="Selecting project...")
             return FeatureResult(status=FeatureStatus.CANCELLED, message="No project selected")

        if action == "select":
             return self._show_project_selector_async()
             
        # If we are here, we have a project path
        project_path = active_project
        
        if action == "menu":
            return self._show_docker_menu_async()
        
        # If we are here, we have a project path
        project_path = active_project
        
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
        try:
            normalized = path_str.replace('/', '\\')
            path = Path(normalized)
            if path.exists():
                return path.resolve()
            return path
        except Exception:
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
                    # Auto-set as docker project to save verify time next time? 
                    # Maybe better to just use it temporarily.
                    return path

        # No active project found, show selector
        if not self._is_dialog_open:
            self._show_project_selector_async()
        return None

    def _run_compose(self, project_path: Path, args: str, title: str) -> FeatureResult:
        """Run docker-compose command"""
        if not (project_path / "docker-compose.yml").exists() and not (project_path / "docker-compose.yaml").exists():
             return FeatureResult(
                status=FeatureStatus.ERROR,
                message="No docker-compose.yml found"
            )

        cmd = f'docker-compose -f "{project_path}/docker-compose.yml" {args}' if (project_path / "docker-compose.yml").exists() else f'docker-compose {args}'
        
        # We need to run this in a shell
        # Use a method that doesn't block the UI thread too long, 
        # but for 'up -d' it should be fast.
        
        logger.info(f"Running: {cmd} in {project_path}")
        """Run docker-compose command using WSL preference"""
        
        # User prefers WSL + Docker Compose
        # We will use the robust launching logic from terminal_quick
        
        path_str = str(project_path)
        command = f"docker compose {args}"
        
        logger.info(f"Running docker action '{args}' in {path_str}")
        
        try:
             # Construct the shell command 
            # Use && and || to avoid semicolon issue in wt.exe
            wsl_args = f'-e bash -c "{command} && exec bash || exec bash"'
            
            import shutil
            wt_path = shutil.which("wt")
            
            if wt_path:
                # wt.exe -d "path" -- wsl.exe [args]
                cmd_str = f'wt.exe -d "{path_str}" -- wsl.exe {wsl_args}'
                subprocess.Popen(cmd_str, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                # Direct wsl
                cmd_str = f'start wsl.exe --cd "{path_str}" {wsl_args}'
                subprocess.Popen(cmd_str, shell=True)
                
            return FeatureResult(status=FeatureStatus.SUCCESS, message=f"Executed {title}")
            
        except Exception as e:
            logger.error(f"Failed to run compose: {e}")
            return FeatureResult(status=FeatureStatus.ERROR, message=f"Error: {e}")

    def _open_logs(self, project_path: Path) -> FeatureResult:
        """Open logs in terminal"""
        path_str = str(project_path)
        
        # Chain for logs
        # Use docker compose logs -f --tail 100
        cmd = "docker compose logs -f --tail 100"
        
        import shutil
        wt_path = shutil.which("wt")
        
        if wt_path:
             subprocess.Popen(f'wt.exe -d "{path_str}" cmd /k "{cmd}"', shell=True)
        else:
             subprocess.Popen(f'start cmd /k "cd /d {path_str} && {cmd}"', shell=True)
             
        return FeatureResult(status=FeatureStatus.SUCCESS, message="Opening logs...")

    def _show_docker_menu_async(self) -> FeatureResult:
        """Show docker menu in separate thread"""
        def run_dialog():
            self._is_dialog_open = True
            try:
                self._show_docker_menu()
            finally:
                self._is_dialog_open = False
        threading.Thread(target=run_dialog, daemon=True).start()
        return FeatureResult(status=FeatureStatus.SUCCESS, message="Opening Docker menu...")

    def _show_docker_menu(self):
        """Show docker actions menu"""
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
        
        # Run dialog in separate process
        import subprocess
        import sys
        import json
        from pathlib import Path
        
        dialog_script = Path(__file__).parent.parent / "ui" / "dialogs.py"
        
        data = json.dumps({
            "title": "Docker Menu",
            "message": f"Project: {project_name}\nSelect Action:",
            "choices": options
        })
        
        try:
            cmd = [sys.executable, str(dialog_script), "ask_choice", data]
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0 and result.stdout.strip():
                choice_data = json.loads(result.stdout)
                choice_idx = choice_data.get("result")
                
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
                    # Re-open menu to show updated selection/context
                    self._show_docker_menu()
                    
        except Exception as e:
            logger.error(f"Error running menu dialog: {e}")
            self._run_notification_subprocess("❌ Error", f"Menu error: {e}")

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
        import subprocess
        import sys
        import json
        
        # Gather projects similar to before
        all_projects = []
        docker_projects = self.config_manager.get_projects(self.CONFIG_KEY)
        all_projects.extend(docker_projects)
        
        for key in ["frontend_project", "git_project"]:
            for p in self.config_manager.get_projects(key):
                if not any(x["path"] == p["path"] for x in all_projects):
                    all_projects.append(p)
                    
        dialog_script = Path(__file__).parent.parent / "ui" / "dialogs.py"
        
        data = json.dumps({
            "projects": all_projects,
            "title": "Select Docker Project",
            "allow_add": True,
            "allow_remove": True
        })
        
        try:
            cmd = [sys.executable, str(dialog_script), "ask_project_selection", data]
            result_proc = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result_proc.returncode == 0 and result_proc.stdout.strip():
                output = json.loads(result_proc.stdout)
                result = output.get("result")
                
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
                    self.config_manager.remove_project(self.CONFIG_KEY, result["project"]["path"])
                    # Recurse if needed or just close
                    
        except Exception as e:
            logger.error(f"Error running selector: {e}")

    def _run_notification_subprocess(self, title, message):
        """Helper to show notification via subprocess"""
        import subprocess
        import sys
        import json
        from pathlib import Path
        
        dialog_script = Path(__file__).parent.parent / "ui" / "dialogs.py"
        data = json.dumps({
            "title": title,
            "message": message,
            "duration": 2000
        })
        try:
             subprocess.Popen(
                [sys.executable, str(dialog_script), "show_notification", data],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except:
            pass

    def _show_notification_async(self, title: str, message: str):
         self._run_notification_subprocess(title, message)
