"""
Windows Utilities - Registry and System operations
"""

import sys
import winreg
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)

# Registry path for auto-start
REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "JRDevMacroEngine"


def get_app_command() -> str:
    """Get the command to run the application"""
    # Assuming this is called from within the project structure
    # We need the path to main.py
    # This might need adjustment effectively if packaged, but for now we us sys.executable and main.py
    
    # Try to find main.py relative to this file
    # utils/windows_utils.py -> ../main.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    main_script = project_root / "main.py"
    
    python_exe = sys.executable
    
    # Use pythonw.exe if available to avoid console window for background task
    if "python.exe" in python_exe:
        pythonw = python_exe.replace("python.exe", "pythonw.exe")
        if Path(pythonw).exists():
            python_exe = pythonw
            
    return f'"{python_exe}" "{main_script}"'


def enable_auto_start() -> bool:
    """Add application to Windows startup via Registry"""
    try:
        command = get_app_command()
        
        # Open registry key
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_KEY,
            0,
            winreg.KEY_SET_VALUE
        )
        
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        
        logger.info(f"Auto-start enabled: {command}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to enable auto-start: {e}")
        return False


def disable_auto_start() -> bool:
    """Remove application from Windows startup"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_KEY,
            0,
            winreg.KEY_SET_VALUE
        )
        
        try:
            winreg.DeleteValue(key, APP_NAME)
            logger.info("Auto-start disabled")
        except FileNotFoundError:
            # Key doesn't exist, already disabled
            pass
        
        winreg.CloseKey(key)
        return True
        
    except Exception as e:
        logger.error(f"Failed to disable auto-start: {e}")
        return False


def is_auto_start_enabled() -> bool:
    """Check if auto-start is currently enabled"""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REGISTRY_KEY,
            0,
            winreg.KEY_READ
        )
        
        try:
            winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
            
    except Exception:
        return False
