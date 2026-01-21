"""
Auto-Updater - Check for updates and pull latest from Git
"""

import subprocess
import threading
from pathlib import Path
from typing import Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

# Current version (update this when releasing)
CURRENT_VERSION = "2.0.0"

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class Updater:
    """
    Auto-updater that checks GitHub for new commits and pulls updates.
    """
    
    def __init__(self):
        self.is_checking = False
        self.update_available = False
        self.latest_version = None
        self.update_message = ""
    
    def get_current_version(self) -> str:
        """Get current application version"""
        return CURRENT_VERSION
    
    def check_for_updates(self) -> Tuple[bool, str]:
        """
        Check if updates are available by comparing local and remote commits.
        
        Returns:
            Tuple of (update_available, message)
        """
        if self.is_checking:
            return False, "Already checking for updates..."
        
        self.is_checking = True
        
        try:
            # Fetch latest from remote (without merging)
            result = subprocess.run(
                ["git", "fetch", "origin"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Git fetch failed: {result.stderr}")
                return False, "Failed to check for updates (git fetch error)"
            
            # Get local HEAD commit
            local_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            local_commit = local_result.stdout.strip()[:7]
            
            # Get remote HEAD commit
            remote_result = subprocess.run(
                ["git", "rev-parse", "origin/main"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            
            # Try origin/master if origin/main doesn't exist
            if remote_result.returncode != 0:
                remote_result = subprocess.run(
                    ["git", "rev-parse", "origin/master"],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True
                )
            
            remote_commit = remote_result.stdout.strip()[:7]
            
            if local_commit == remote_commit:
                self.update_available = False
                self.update_message = f"You're up to date! (v{CURRENT_VERSION})"
                logger.info("No updates available")
                return False, self.update_message
            
            # Get number of commits behind
            behind_result = subprocess.run(
                ["git", "rev-list", "--count", f"HEAD..origin/main"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            
            if behind_result.returncode != 0:
                behind_result = subprocess.run(
                    ["git", "rev-list", "--count", f"HEAD..origin/master"],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True
                )
            
            commits_behind = behind_result.stdout.strip()
            
            self.update_available = True
            self.update_message = f"Update available! ({commits_behind} new commits)"
            logger.info(f"Update available: {commits_behind} commits behind")
            return True, self.update_message
            
        except subprocess.TimeoutExpired:
            logger.error("Git fetch timed out")
            return False, "Connection timeout. Please check your internet."
        except Exception as e:
            logger.error(f"Update check failed: {e}")
            return False, f"Error checking for updates: {e}"
        finally:
            self.is_checking = False
    
    def pull_updates(self) -> Tuple[bool, str]:
        """
        Pull latest updates from Git.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Stash any local changes first
            subprocess.run(
                ["git", "stash"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            
            # Pull latest
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Try master if main doesn't work
            if result.returncode != 0:
                result = subprocess.run(
                    ["git", "pull", "origin", "master"],
                    cwd=PROJECT_ROOT,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            
            if result.returncode == 0:
                logger.info("Updates pulled successfully")
                return True, "Updates downloaded! Please restart the application."
            else:
                logger.error(f"Git pull failed: {result.stderr}")
                return False, f"Failed to pull updates: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Download timed out. Please try again."
        except Exception as e:
            logger.error(f"Pull failed: {e}")
            return False, f"Error downloading updates: {e}"
    
    def check_and_update_async(self, callback=None):
        """
        Check for updates in background thread.
        
        Args:
            callback: Function to call with (update_available, message)
        """
        def run():
            result = self.check_for_updates()
            if callback:
                callback(*result)
        
        threading.Thread(target=run, daemon=True).start()


# Global instance
_updater = None


def get_updater() -> Updater:
    """Get the global updater instance"""
    global _updater
    if _updater is None:
        _updater = Updater()
    return _updater


def get_version() -> str:
    """Get current version string"""
    return CURRENT_VERSION
