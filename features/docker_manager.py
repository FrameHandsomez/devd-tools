"""
Docker Manager Feature - Manage Docker Compose projects
"""

import threading
import subprocess
import sys
import json
import shutil
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
             if self._is_dialog_open:
                 return FeatureResult(status=FeatureStatus.SUCCESS, message="Selecting project...")
             return FeatureResult(status=FeatureStatus.CANCELLED, message="No project selected")

        if action == "select":
             return self._show_project_selector_async()
             
        # If we are here, we have a project path
        project_path = active_project
        
        if action == "menu":
            return self._show_docker_menu_async()
        
        # Actions that require run
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
        import os
        try:
            # Expand vars like %USERPROFILE%
            expanded = os.path.expandvars(path_str)
            normalized = expanded.replace('/', '\\')
            path = Path(normalized)
            if path.exists():
                return path.resolve()
            return path
        except Exception as e:
            logger.error(f"Path normalization error: {e}")
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
                    return path

        # No active project found, show selector
        # Only show selector if we are NOT already in a dialog (like menu)
        # to avoid confusing user or double-dialogs
        if not self._is_dialog_open:
            self._show_project_selector_async()
            
    def _run_terminal_command(self, path_str: str, wsl_command: str = None, cmd_command: str = None) -> bool:
        """Helper to run a terminal command in a new window (preferring Windows Terminal)"""
        try:
            wt_path = shutil.which("wt")
            
            # Escape inner quotes for command arguments
            if wsl_command:
                # wsl_command is something like: -e bash -c "..."
                # We need to be careful with escaping
                pass 
                
            if wt_path:
                if wsl_command:
                     # wt.exe -d "path" -- wsl.exe [args]
                     cmd_str = f'wt.exe -d "{path_str}" -- wsl.exe {wsl_command}'
                else:
                     # wt.exe -d "path" cmd /k "..."
                     cmd_str = f'wt.exe -d "{path_str}" cmd /k "{cmd_command}"'
                
                subprocess.Popen(cmd_str, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                if wsl_command:
                    # Direct wsl
                    cmd_str = f'start wsl.exe --cd "{path_str}" {wsl_command}'
                else:
                    # Direct cmd
                    cmd_str = f'start cmd /k "cd /d {path_str} && {cmd_command}"'
                
                subprocess.Popen(cmd_str, shell=True)
            return True
        except Exception as e:
            logger.error(f"Failed to launch terminal: {e}")
            return False

    def _run_compose(self, project_path: Path, args: str, title: str) -> FeatureResult:
        """Run docker-compose command"""
        if not (project_path / "docker-compose.yml").exists() and not (project_path / "docker-compose.yaml").exists():
             return FeatureResult(
                status=FeatureStatus.ERROR,
                message="No docker-compose.yml found"
            )
            
        path_str = str(project_path)
        docker_cmd = f"docker compose {args}"
        
        logger.info(f"Running: {docker_cmd} in {path_str}")
        
        # Use && and || to avoid semicolon issue in wt.exe
        wsl_args = f'-e bash -c "{docker_cmd} && exec bash || exec bash"'
        
        if self._run_terminal_command(path_str, wsl_command=wsl_args):
            return FeatureResult(status=FeatureStatus.SUCCESS, message=f"Executed {title}")
        else:
            return FeatureResult(status=FeatureStatus.ERROR, message=f"Failed: {title}")

    def _get_docker_services(self, project_path: Path) -> list[str]:
        """Get list of services from docker-compose"""
        path_str = str(project_path)
        try:
             # Run docker compose config --services to get list
             # Use wsl if on windows and not using docker desktop natively?
             # Assuming wsl environment as established
             
             cmd = f'wsl.exe --cd "{path_str}" -e bash -c "docker compose config --services"'
             
             result = subprocess.run(
                 cmd, 
                 capture_output=True, 
                 text=True, 
                 creationflags=subprocess.CREATE_NO_WINDOW
             )
             
             if result.returncode == 0:
                 services = [s.strip() for s in result.stdout.splitlines() if s.strip()]
                 return services
             else:
                 logger.error(f"Failed to get services: {result.stderr}")
                 return []
        except Exception as e:
            logger.error(f"Error getting services: {e}")
            return []

    def _select_service_and_open_logs(self, project_path: Path):
        """Show dialog to select service then open logs"""
        services = self._get_docker_services(project_path)
        if not services:
            self._run_notification_subprocess("❌ Error", "No services found or failed to list services")
            return

        result_data = self._run_dialog_subprocess("ask_choice", {
            "title": "Select Service",
            "message": "Choose service to view logs:",
            "choices": services
        })
        
        if result_data and result_data.get("result") is not None:
            idx = result_data.get("result")
            if 0 <= idx < len(services):
                self._open_logs(project_path, service_name=services[idx])

    def _open_logs(self, project_path: Path, service_name: str = None) -> FeatureResult:
        """Open logs in terminal"""
        path_str = str(project_path)
        
        if service_name:
            docker_cmd = f"docker compose logs -f --tail 100 {service_name}"
            msg = f"Opening logs for {service_name}..."
        else:
            docker_cmd = "docker compose logs -f --tail 100"
            msg = "Opening all logs..."
        
        # Use && and || to ensure bash runs after (keeps window open), preventing 'wt' from splitting at semicolon
        wsl_args = f'-e bash -c "{docker_cmd} && exec bash || exec bash"'
        
        # Consistent with _run_compose, run in WSL
        if self._run_terminal_command(path_str, wsl_command=wsl_args):
            return FeatureResult(status=FeatureStatus.SUCCESS, message=msg)
        else:
            return FeatureResult(status=FeatureStatus.ERROR, message="Failed to open logs")

    def _show_docker_menu_async(self) -> FeatureResult:
        """Show docker menu in separate thread"""
        def run_dialog():
            self._is_dialog_open = True
            try:
                self._show_docker_menu()
            finally:
                self._is_dialog_open = False
        import threading
        threading.Thread(target=run_dialog, daemon=True).start()
        return FeatureResult(status=FeatureStatus.SUCCESS, message="Opening Docker menu...")

    def _show_docker_menu(self):
        """Show docker actions menu"""
        try:
            active = self._get_or_select_project()
            
            # Friendly project display
            if active:
                project_display = f"▸ Working on: {active.name}"
            else:
                project_display = "⚠ No project selected"
            
            options = [
                "🚀 Docker Up",
                "🛑 Docker Down", 
                "🔄 Restart",
                "📊 Status (ps)",

                "🔍 View Service Logs",
                "📂 Select Project",
                "🧹 System Prune (Danger)"
            ]
            
            result_data = self._run_dialog_subprocess("ask_choice", {
                "title": "Docker Menu",
                "message": f"{project_display}\n\nWhat would you like to do?",
                "choices": options
            })
            
            if not result_data:
                return
                
            choice_idx = result_data.get("result")
            
            if choice_idx is None:
                return
    
            # Allow Select (5) and Prune (6) without active project
            if not active and choice_idx not in [5, 6]:
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
            elif choice_idx == 4: # Service Logs
                self._select_service_and_open_logs(active)
            elif choice_idx == 5: # Select
                if self._show_project_selector():
                    # Re-open menu with new project
                    self._show_docker_menu()
            elif choice_idx == 6: # Prune
                self._prune_system(active)
        except Exception as e:
            logger.error(f"Menu error: {e}")
            self._run_notification_subprocess("❌ Menu Error", str(e))

    def _prune_system(self, active_project):
        """Execute docker system prune with warning"""
        try:
            # 1. Warning Dialog
            res = self._run_dialog_subprocess("ask_action_custom", {
                "title": "⚠️ DANGER: System Prune",
                "message": "This command will DELETE:\n\n"
                           "• All stopped containers\n"
                           "• All unused networks\n"
                           "• All dangling images\n"
                           "• All build cache\n\n"
                           "IMPORTANT: Ensure your containers are RUNNING!\n"
                           "If they are stopped, they will be lost.\n\n"
                           "Are you absolutely sure?",
                "buttons": ["🚫 Cancel", "🔥 Prune Now"]
            })
            
            if not res or res.get("result") != "🔥 Prune Now":
                return
                
            # 2. Execute
            # Use active project path if available, else user profile
            import os
            path = str(active_project) if active_project else os.path.expandvars("%USERPROFILE%")
            
            docker_cmd = "docker system prune -a --force"
            wsl_args = f'-e bash -c "{docker_cmd} && echo -e \\"\n✅ Prune Complete\\" && read -p \\"Press Enter to close...\\" || read -p \\"Failed...\\""'
            
            self._run_terminal_command(path, wsl_args)
        except Exception as e:
            logger.error(f"Prune error: {e}")
            self._run_notification_subprocess("❌ Prune Error", str(e))

    def _show_project_selector_async(self) -> FeatureResult:
        def run_dialog():
            self._is_dialog_open = True
            try:
                self._show_project_selector()
            finally:
                self._is_dialog_open = False
        threading.Thread(target=run_dialog, daemon=True).start()
        return FeatureResult(status=FeatureStatus.SUCCESS, message="Select Project...")

    def _show_project_selector(self) -> bool:
        """Show project selector using subprocess. Returns True if a project was selected/added."""
        
        # Gather projects similar to before
        all_projects = []
        docker_projects = self.config_manager.get_projects(self.CONFIG_KEY)
        all_projects.extend(docker_projects)
        
        for key in ["frontend_project", "git_project"]:
            for p in self.config_manager.get_projects(key):
                if not any(x["path"] == p["path"] for x in all_projects):
                    all_projects.append(p)
                    
        result_data = self._run_dialog_subprocess("ask_project_selection", {
            "projects": all_projects,
            "title": "Select Docker Project",
            "allow_add": True,
            "allow_remove": True
        })
        
        if not result_data:
            return False
            
        result = result_data.get("result")
        if not result:
            return False
        
        action = result["action"]
        if action == "select":
            self.config_manager.set_active_project(self.CONFIG_KEY, result["project"]["path"])
            self._run_notification_subprocess("✅ Docker Project Set", result["project"]["name"])
            return True
        elif action == "add":
            path = result["path"]
            self.config_manager.add_project(self.CONFIG_KEY, path)
            self.config_manager.set_active_project(self.CONFIG_KEY, path)
            self._run_notification_subprocess("✅ Added & Set", Path(path).name)
            return True
        elif action == "remove":
            # Remove from relevant lists
            path_to_remove = result["project"]["path"]
            removed = False
            if self.config_manager.remove_project(self.CONFIG_KEY, path_to_remove):
                removed = True
            
            if removed:
                self._run_notification_subprocess("🗑️ Project Removed", f"Removed: {result['project']['name']}")
            return False  # Don't re-open menu after remove, let user manually re-invoke if needed
        
        return False
            
    def _run_dialog_subprocess(self, command, data):
        """Helper to run dialog subprocess"""
        import sys
        
        dialog_script = Path(__file__).parent.parent / "ui" / "dialogs.py"
        try:
            is_frozen = getattr(sys, 'frozen', False)
            if is_frozen:
                cmd = [sys.executable, "dialog", command, json.dumps(data)]
            else:
                cmd = [sys.executable, str(dialog_script), command, json.dumps(data)]

            # Run without window creation flag on Windows
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

    def _run_notification_subprocess(self, title, message):
        """Helper to show notification via subprocess"""
        # Fire and forget
        dialog_script = Path(__file__).parent.parent / "ui" / "dialogs.py"
        data = json.dumps({
            "title": title,
            "message": message,
            "duration": 2000
        })
        try:
             is_frozen = getattr(sys, 'frozen', False)
             if is_frozen:
                 cmd = [sys.executable, "dialog", "show_notification", data]
             else:
                 cmd = [sys.executable, str(dialog_script), "show_notification", data]
                 
             subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except:
            pass
