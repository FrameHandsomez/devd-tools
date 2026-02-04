"""
Terminal Quick Actions Feature - Open terminal at project directory

Actions:
- open_here: Open terminal at active project
- select: Select project from list
- select_and_launch: Select project and immediately choose launch mode
"""

import threading
import subprocess
import os
from pathlib import Path
from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType
from utils.logger import get_logger

logger = get_logger(__name__)


class TerminalQuickFeature(BaseFeature):
    """
    Feature: Terminal Quick Actions
    
    - Short press: Open terminal at active project
    - Long press: Select project from list
    """
    
    name = "terminal_quick"
    description = "Open terminal at project directory"
    supported_patterns = [PressType.SHORT, PressType.LONG, PressType.DOUBLE]
    
    CONFIG_KEY = "terminal_project"
    _is_dialog_open = False
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute terminal action"""
        
        if self._is_dialog_open:
            return FeatureResult(
                status=FeatureStatus.CANCELLED,
                message="Dialog already open"
            )
        
        if action == "open_here":
            return self._open_terminal()
        elif action == "select":
            return self._show_project_selector_async()
        elif action == "select_and_launch":
            return self._show_project_selector_async(launch_after=True)
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

    def _open_terminal(self) -> FeatureResult:
        """Open terminal at active project"""
        
        # Get active project
        active = self.config_manager.get_active_project(self.CONFIG_KEY)
        
        if active:
            project_path = self._normalize_path(active.get("path", ""))
            if project_path and project_path.exists():
                logger.info(f"Using terminal_project active: {project_path}")
                return self._launch_terminal(project_path)
        
        # Try frontend project as fallback
        frontend_active = self.config_manager.get_active_project("frontend_project")
        if frontend_active:
            project_path = self._normalize_path(frontend_active.get("path", ""))
            if project_path and project_path.exists():
                logger.info(f"Using frontend_project active: {project_path}")
                return self._launch_terminal(project_path)
        
        # Try git project as fallback
        git_active = self.config_manager.get_active_project("git_project")
        if git_active:
            project_path = self._normalize_path(git_active.get("path", ""))
            if project_path and project_path.exists():
                logger.info(f"Using git_project active: {project_path}")
                return self._launch_terminal(project_path)
        
        logger.info("No active project found, showing selector")
        # No active project - show selector
        return self._show_project_selector_async()
    
    def _launch_terminal(self, project_path: Path) -> FeatureResult:
        """Launch standard terminal at the given path"""
        
        path_str = str(project_path)
        logger.info(f"Attempting to launch terminal at: {path_str}")
        
        try:
            # Try Windows Terminal first (wt.exe)
            import shutil
            wt_path = shutil.which("wt")
            
            if wt_path:
                # Windows Terminal is available
                logger.info(f"Found Windows Terminal at: {wt_path}")
                subprocess.Popen(
                    f'wt.exe -d "{path_str}"',
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                logger.info(f"✅ Opened Windows Terminal at: {path_str}")
            else:
                # Fallback to PowerShell
                logger.info("Windows Terminal not found, using PowerShell")
                subprocess.Popen(
                    f'start powershell -NoExit -Command "Set-Location -Path \'{path_str}\'"',
                    shell=True
                )
                logger.info(f"✅ Opened PowerShell at: {path_str}")
            
            self._show_notification_async(
                "📱 Terminal Opened",
                f"{project_path.name}"
            )
            
            return FeatureResult(
                status=FeatureStatus.SUCCESS,
                message=f"Terminal opened at {project_path.name}"
            )
            
        except Exception as e:
            logger.error(f"Failed to open terminal: {e}")
            
            # Last resort - try basic cmd
            try:
                os.system(f'start cmd /K "cd /d {path_str}"')
                logger.info(f"✅ Opened CMD at: {path_str}")
                return FeatureResult(
                    status=FeatureStatus.SUCCESS,
                    message=f"Terminal opened at {project_path.name}"
                )
            except Exception as e2:
                logger.error(f"Failed to open CMD: {e2}")
                return FeatureResult(
                    status=FeatureStatus.ERROR,
                    message=f"Failed to open terminal: {e}"
                )
    
    def _launch_wsl(self, project_path: Path, command: str = None) -> FeatureResult:
        """Launch WSL terminal at the given path, optionally running a command"""
        
        try:
            # Convert Windows path to WSL path manually if needed, 
            # but wt.exe and wsl.exe often handle Windows paths with --cd argument correctly now.
            # Let's try the most robust way: using `wsl --cd "path"` directly via wt or separate console.
            
            logger.info(f"Launching WSL at: {project_path} with command: {command}")
            
            # Construct the shell command if provided
            # We use "bash -c 'command; exec bash'" to keep the shell open after command
            wsl_args = ""
            if command:
                # Use -e instead of --exec, usually safer with some versions
                # Also quote the inner command carefully.
                # Use && and || to avoid semicolon ';' which wt.exe interprets as a command separator
                wsl_args = f'-e bash -c "{command} && exec bash || exec bash"'
            
            # Use Windows Terminal if available (Targeting "Ubuntu" or default profile)
            import shutil
            wt_path = shutil.which("wt")
            
            if wt_path:
                # Option 1: WT with wsl command (Force wsl shell)
                # wt.exe -d "path" -- wsl.exe [args]
                
                # Use -- to separate wt args from command args explicitly
                cmd_str = f'wt.exe -d "{project_path}" -- wsl.exe {wsl_args}'
                
                subprocess.Popen(
                   cmd_str, 
                   shell=True,
                   creationflags=subprocess.CREATE_NO_WINDOW
                )
                logger.info(f"✅ Opened WSL in Windows Terminal")
            else:
                # Direct start wsl
                # "start wsl" launches the default distro
                # --cd currently requires a windows path in quotes
                
                # Note: 'start' treats the first quoted string as window title, so we need an empty pair of quotes first if we quote the executable or args?
                # Actually 'start wsl.exe ...' is fine.
                
                cmd_str = f'start wsl.exe --cd "{project_path}" {wsl_args}'
                
                subprocess.Popen(
                    cmd_str,
                    shell=True
                )
                logger.info(f"✅ Opened WSL Direct")
                
            self._show_notification_async("🐧 WSL Opened", f"{project_path.name}")
            
            return FeatureResult(
                status=FeatureStatus.SUCCESS,
                message=f"WSL opened at {project_path.name}"
            )
            
        except Exception as e:
            logger.error(f"Failed to open WSL: {e}")
            return FeatureResult(status=FeatureStatus.ERROR, message=f"WSL Error: {e}")

    def _show_project_selector_async(self, launch_after: bool = False) -> FeatureResult:
        """Show project selector in thread"""
        
        def run_dialog():
            self._is_dialog_open = True
            try:
                self._show_project_selector(launch_after)
            finally:
                self._is_dialog_open = False
        
        threading.Thread(target=run_dialog, daemon=True).start()
        
        return FeatureResult(
            status=FeatureStatus.SUCCESS,
            message="Opening project selector..."
        )
    
    def _show_project_selector(self, launch_after: bool):
        """Show project selector dialog using subprocess"""
        import subprocess
        import sys
        import json
        from pathlib import Path
        
        logger.info("Opening project selector dialog...")
        
        # Combine all projects
        all_projects = []
        
        # Add frontend projects
        frontend_projects = self.config_manager.get_projects("frontend_project")
        for p in frontend_projects:
            if p not in all_projects:
                all_projects.append(p)
        
        # Add git projects
        git_projects = self.config_manager.get_projects("git_project")
        for p in git_projects:
            if not any(x["path"] == p["path"] for x in all_projects):
                all_projects.append(p)
        
        # Add terminal/docker projects
        docker_projects = self.config_manager.get_projects("docker_project")
        for p in docker_projects:
             if not any(x["path"] == p["path"] for x in all_projects):
                all_projects.append(p)
        
        terminal_projects = self.config_manager.get_projects(self.CONFIG_KEY)
        for p in terminal_projects:
            if not any(x["path"] == p["path"] for x in all_projects):
                all_projects.append(p)
        
        logger.info(f"Found {len(all_projects)} projects")
        
        dialog_script = Path(__file__).parent.parent / "ui" / "dialogs.py"
        
        data = json.dumps({
            "projects": all_projects,
            "title": "Select Project" + (" & Launch" if launch_after else ""),
            "allow_add": True,
            "allow_remove": True 
        })
        
        try:
            cmd = [sys.executable, str(dialog_script), "ask_project_selection", data]
            result_proc = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result_proc.returncode != 0:
                logger.error(f"Selector subprocess error: {result_proc.stderr}")
                return
            
            if not result_proc.stdout.strip():
                logger.info("Project selection cancelled")
                return

            output = json.loads(result_proc.stdout)
            result = output.get("result")
            
            if not result:
                logger.info("Project selection cancelled (parsed)")
                return
            
            action = result["action"]
            project = None
            project_path = None
            project_name = None
            
            if action == "add":
                 path = result["path"]
                 project_path = Path(path)
                 project_name = project_path.name
                 self.config_manager.add_project(self.CONFIG_KEY, str(project_path))
            elif action == "remove":
                 project = result["project"]
                 path_to_remove = project["path"]
                 
                 # Try to remove from all possible lists
                 removed_from = []
                 keys_to_check = ["frontend_project", "git_project", "docker_project", self.CONFIG_KEY]
                 
                 for key in keys_to_check:
                     if self.config_manager.remove_project(key, path_to_remove):
                         removed_from.append(key)
                 
                 if removed_from:
                     self._run_notification_subprocess("🗑️ Project Removed", f"Removed: {project['name']}")
                 else:
                     logger.warning(f"Project not found in any list: {path_to_remove}")
                     
                 # Always re-open to show updated list
                 self._show_project_selector(launch_after=launch_after)
                 return
            else:
                 project = result["project"]
                 project_path = Path(project["path"])
                 project_name = project["name"]

            # Save as active regardless
            self.config_manager.set_active_project(self.CONFIG_KEY, str(project_path))
            
            if not launch_after:
                self._run_notification_subprocess("✅ Active Project Set", project_name)
                return

            # Launch Mode Selection using subprocess as well!
            options = [
                "🚀 Standard Terminal", 
                "🐧 WSL Terminal", 
                "🐳 Docker Logs", 
                "⚡ WSL + Docker Compose Up",
                "🔻 WSL + Docker Compose Down",
                "🔄 WSL + Docker Compose Restart",
                "📊 WSL + Docker Status",
                "🏗️ WSL + Docker Build"
            ]
            
            launch_data = json.dumps({
                "title": "Launch Mode",
                "message": f"Open '{project_name}' in:",
                "choices": options
            })
            
            cmd_launch = [sys.executable, str(dialog_script), "ask_choice", launch_data]
            launch_res = subprocess.run(cmd_launch, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if launch_res.returncode == 0 and launch_res.stdout.strip():
                launch_out = json.loads(launch_res.stdout)
                choice_idx = launch_out.get("result")
                
                if choice_idx is None:
                    return # Cancelled
                
                if choice_idx == 0: # Standard
                    self._launch_terminal(project_path)
                elif choice_idx == 1: # WSL
                    self._launch_wsl(project_path)
                elif choice_idx == 2: # Docker Logs
                    path_str = str(project_path)
                    cmd = "docker compose logs -f --tail 100"
                    try:
                        import shutil
                        wt_path = shutil.which("wt")
                        if wt_path:
                            subprocess.Popen(f'wt.exe -d "{path_str}" cmd /k "{cmd}"', shell=True)
                        else:
                            subprocess.Popen(f'start cmd /k "cd /d {path_str} && {cmd}"', shell=True)
                    except:
                        pass
                elif choice_idx == 3: # WSL + Docker Compose Up
                    self._launch_wsl(project_path, command="docker compose up -d")
                elif choice_idx == 4: # WSL + Docker Compose Down
                    self._launch_wsl(project_path, command="docker compose down")
                elif choice_idx == 5: # WSL + Docker Compose Restart
                    self._launch_wsl(project_path, command="docker compose restart")
                elif choice_idx == 6: # WSL + Docker Status
                    self._launch_wsl(project_path, command="docker compose ps -a")
                elif choice_idx == 7: # WSL + Docker Build
                    self._launch_wsl(project_path, command="docker compose build")

        except Exception as e:
            logger.error(f"Error running selector: {e}")
            self._run_notification_subprocess("❌ Error", f"Selector error: {e}")
    
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
        """Show notification via subprocess"""
        self._run_notification_subprocess(title, message)
