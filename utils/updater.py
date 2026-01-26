"""
Auto-Updater Module
Checks for updates from the local Git repository and applies them.
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

# Get project root (works both for .py and .exe)
if getattr(sys, 'frozen', False):
    # Running as .exe
    PROJECT_ROOT = Path(sys.executable).parent
else:
    # Running as .py
    PROJECT_ROOT = Path(__file__).parent.parent


class Updater:
    """
    Git-based auto-updater.
    Checks if there are new commits on the remote and pulls them.
    """
    
    def __init__(self, repo_path: Optional[Path] = None, branch: str = "main"):
        self.repo_path = repo_path or PROJECT_ROOT
        self.branch = branch
        self._git_available = self._check_git()
    
    def _check_git(self) -> bool:
        """Check if git is available"""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _run_git(self, *args) -> Tuple[bool, str]:
        """Run a git command and return (success, output)"""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                capture_output=True,
                text=True,
                cwd=self.repo_path
            )
            output = result.stdout.strip() or result.stderr.strip()
            return result.returncode == 0, output
        except Exception as e:
            return False, str(e)
    
    def check_for_updates(self) -> Tuple[bool, str, int]:
        """
        Check if updates are available.
        
        Returns:
            (has_updates: bool, message: str, commits_behind: int)
        """
        if not self._git_available:
            return False, "Git is not available", 0
        
        # Fetch latest from remote
        logger.info("Fetching updates from remote...")
        success, output = self._run_git("fetch", "origin", self.branch)
        if not success:
            return False, f"Failed to fetch: {output}", 0
        
        # Check how many commits behind
        success, output = self._run_git(
            "rev-list", "--count", f"HEAD..origin/{self.branch}"
        )
        
        if not success:
            return False, f"Failed to check commits: {output}", 0
        
        try:
            commits_behind = int(output.strip())
        except ValueError:
            commits_behind = 0
        
        if commits_behind > 0:
            # Get commit messages for display
            success, log_output = self._run_git(
                "log", "--oneline", f"HEAD..origin/{self.branch}"
            )
            message = f"มี {commits_behind} อัพเดตใหม่!\n\n{log_output[:500]}"
            return True, message, commits_behind
        else:
            return False, "คุณใช้เวอร์ชันล่าสุดแล้ว ✅", 0
    
    def apply_update(self) -> Tuple[bool, str]:
        """
        Pull the latest changes from the remote.
        
        Returns:
            (success: bool, message: str)
        """
        if not self._git_available:
            return False, "Git is not available"
        
        logger.info(f"Pulling updates from origin/{self.branch}...")
        success, output = self._run_git("pull", "origin", self.branch)
        
        if success:
            logger.info("Update applied successfully")
            return True, f"อัพเดตสำเร็จ! 🎉\n\n{output[:300]}"
        else:
            logger.error(f"Update failed: {output}")
            return False, f"อัพเดตล้มเหลว: {output[:200]}"
    
    def get_current_version(self) -> str:
        """Get current commit hash (short)"""
        success, output = self._run_git("rev-parse", "--short", "HEAD")
        if success:
            return output.strip()
        return "unknown"
    
    def get_remote_version(self) -> str:
        """Get remote HEAD commit hash (short)"""
        success, output = self._run_git("rev-parse", "--short", f"origin/{self.branch}")
        if success:
            return output.strip()
        return "unknown"


def restart_application():
    """Restart the application after an update"""
    logger.info("Restarting application...")
    
    if getattr(sys, 'frozen', False):
        # Running as .exe - restart the executable
        exe_path = sys.executable
        os.execl(exe_path, exe_path, *sys.argv[1:])
    else:
        # Running as .py - restart Python with the same script
        python = sys.executable
        script = sys.argv[0]
        os.execl(python, python, script, *sys.argv[1:])


# Singleton instance
_updater = None

def get_updater() -> Updater:
    global _updater
    if _updater is None:
        _updater = Updater()
    return _updater
