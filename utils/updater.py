"""
Auto-Updater Module
Supports updating via Git (for dev) and GitHub Releases (for frozen EXE).
"""

import subprocess
import sys
import os
import json
import urllib.request
import urllib.error
import time
from pathlib import Path
from typing import Optional, Tuple
from utils.logger import get_logger
from core.constants import APP_VERSION, REPO_OWNER, REPO_NAME

logger = get_logger(__name__)

# Get project root
if getattr(sys, 'frozen', False):
    PROJECT_ROOT = Path(sys.executable).parent
    IS_FROZEN = True
else:
    PROJECT_ROOT = Path(__file__).parent.parent
    IS_FROZEN = False

class Updater:
    def __init__(self, branch: str = "main"):
        self.branch = branch
        self.repo_api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        
    def check_for_updates(self) -> Tuple[bool, str, str]:
        """
        Check for updates.
        Returns: (has_update, message, latest_version)
        """
        if IS_FROZEN:
            return self._check_github_release()
        else:
            return self._check_git_repo()

    def apply_update(self) -> Tuple[bool, str]:
        """
        Apply the update.
        Returns: (success, message)
        """
        if IS_FROZEN:
            return self._update_frozen_exe()
        else:
            return self._git_pull()

    # ==========================
    # FROZEN MODE (GitHub Release)
    # ==========================
    def _check_github_release(self) -> Tuple[bool, str, str]:
        try:
            logger.info(f"Checking updates from {self.repo_api_url}")
            req = urllib.request.Request(self.repo_api_url)
            req.add_header('User-Agent', 'Devd-Tools-Updater')
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
            latest_tag = data.get("tag_name", "").strip()
            current_version = APP_VERSION.strip()
            
            # Simple string comparison (assumes vX.Y.Z format)
            if latest_tag != current_version:
                body = data.get("body", "No release notes.")
                return True, f"New version {latest_tag} available!\n\n{body[:500]}", latest_tag
            
            return False, "You are on the latest version.", current_version
            
        except Exception as e:
            logger.error(f"Update check failed: {e}")
            return False, f"Failed to check updates: {e}", APP_VERSION

    def _update_frozen_exe(self) -> Tuple[bool, str]:
        try:
            # 1. Get download URL
            req = urllib.request.Request(self.repo_api_url)
            req.add_header('User-Agent', 'Devd-Tools-Updater')
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                
            assets = data.get("assets", [])
            download_url = None
            filename = "devd-tools.exe"
            
            for asset in assets:
                name = asset.get("name", "").lower()
                if name.endswith(".exe"):
                    download_url = asset.get("browser_download_url")
                    filename = asset.get("name") # Use actual name
                    break
            
            if not download_url:
                return False, "No exe asset found in latest release."
                
            # 2. Download to .new.exe
            current_exe = Path(sys.executable)
            new_exe = current_exe.with_suffix(".new.exe")
            
            logger.info(f"Downloading update from {download_url} to {new_exe}")
            urllib.request.urlretrieve(download_url, new_exe)
            
            # 3. Create Update Script
            bat_script = PROJECT_ROOT / "update.bat"
            script_content = f"""
@echo off
timeout /t 2 /nobreak > NUL
del "{current_exe.name}"
move "{new_exe.name}" "{current_exe.name}"
start "" "{current_exe.name}"
del "%~f0"
"""
            # Write bat file
            with open(bat_script, "w") as f:
                f.write(script_content)
                
            # 4. Run script and exit
            logger.info("Starting update script...")
            subprocess.Popen([str(bat_script)], shell=True)
            sys.exit(0) # Terminate immediately
            
        except Exception as e:
            logger.error(f"EXE update failed: {e}")
            return False, f"Update failed: {e}"

    # ==========================
    # SCRIPT MODE (Git)
    # ==========================
    def _check_git_repo(self) -> Tuple[bool, str, str]:
        updater = GitUpdater(PROJECT_ROOT, self.branch)
        has_updates, msg, count = updater.check_for_updates()
        return has_updates, msg, "git-head"

    def _git_pull(self) -> Tuple[bool, str]:
        updater = GitUpdater(PROJECT_ROOT, self.branch)
        success, msg = updater.apply_update()
        if success:
            # Restart script
            self._restart_script()
        return success, msg

    def _restart_script(self):
        python = sys.executable
        os.execl(python, python, *sys.argv)


class GitUpdater:
    """Helper for Git operations (Legacy logic)"""
    def __init__(self, repo_path: Path, branch: str = "main"):
        self.repo_path = repo_path
        self.branch = branch

    def _run_git(self, *args) -> Tuple[bool, str]:
        try:
            result = subprocess.run(
                ["git"] + list(args),
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
        except:
            return False, "Git unavailable"

    def check_for_updates(self) -> Tuple[bool, str, int]:
        success, _ = self._run_git("fetch", "origin", self.branch)
        if not success: return False, "Fetch failed", 0
        
        success, output = self._run_git("rev-list", "--count", f"HEAD..origin/{self.branch}")
        try:
             count = int(output) if success else 0
        except: count = 0
             
        if count > 0:
            return True, f"{count} new commits available (Git)", count
        return False, "Up to date", 0
        
    def apply_update(self) -> Tuple[bool, str]:
        success, output = self._run_git("pull", "origin", self.branch)
        if success: return True, f"Pulled: {output}"
        return False, f"Pull failed: {output}"

# Singleton
_updater = None
def get_updater() -> Updater:
    global _updater
    if _updater is None:
        _updater = Updater()
    return _updater
