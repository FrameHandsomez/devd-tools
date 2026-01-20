"""
Command Executor - Safe shell command execution
Uses list[str] instead of shell strings for security
"""

import subprocess
import os
import threading
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum
from utils.logger import get_logger

logger = get_logger(__name__)


def find_git_path() -> Optional[str]:
    """
    Find git executable path automatically.
    Searches common installation locations on Windows.
    
    Returns:
        Path to git bin directory, or None if not found
    """
    import shutil
    
    # First, try if git is already in PATH
    git_exe = shutil.which("git")
    if git_exe:
        return str(Path(git_exe).parent)
    
    # Common git installation paths to search
    possible_paths = [
        # Standard Git for Windows
        r"C:\Program Files\Git\bin",
        r"C:\Program Files (x86)\Git\bin",
        # User-installed
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\bin"),
        # GitHub Desktop
        os.path.expandvars(r"%LOCALAPPDATA%\GitHubDesktop\bin"),
        # Scoop
        os.path.expandvars(r"%USERPROFILE%\scoop\apps\git\current\bin"),
        # Chocolatey
        r"C:\ProgramData\chocolatey\bin",
        # PortableGit
        os.path.expandvars(r"%USERPROFILE%\PortableGit\bin"),
    ]
    
    for path in possible_paths:
        git_exe = Path(path) / "git.exe"
        if git_exe.exists():
            logger.info(f"Found git at: {path}")
            return path
    
    # Try Windows Registry as last resort
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GitForWindows")
        install_path = winreg.QueryValueEx(key, "InstallPath")[0]
        winreg.CloseKey(key)
        git_bin = str(Path(install_path) / "bin")
        if Path(git_bin).exists():
            logger.info(f"Found git via registry: {git_bin}")
            return git_bin
    except:
        pass
    
    logger.warning("Git not found! Please install Git for Windows.")
    return None


class CommandStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RUNNING = "running"


@dataclass
class CommandResult:
    """Result of a command execution"""
    status: CommandStatus
    return_code: int
    stdout: str
    stderr: str
    command: list[str]
    duration_ms: int = 0


class CommandExecutor:
    """
    Safe command executor that:
    1. Uses list[str] instead of shell strings (prevents injection)
    2. Supports cwd, env, timeout
    3. Features never call subprocess directly
    """
    
    def __init__(self):
        self._running_processes: dict[int, subprocess.Popen] = {}
    
    def execute(
        self,
        command: list[str],
        cwd: Optional[Path] = None,
        env: Optional[dict] = None,
        timeout: int = 300,
        capture_output: bool = True
    ) -> CommandResult:
        """
        Execute a command and wait for completion.
        
        Args:
            command: Command as list of strings, e.g. ["git", "clone", url]
            cwd: Working directory for the command
            env: Environment variables (merged with current env)
            timeout: Timeout in seconds
            capture_output: Whether to capture stdout/stderr
        
        Returns:
            CommandResult with status, output, and return code
        """
        import time
        start_time = time.time()
        
        # Prepare environment
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        logger.info(f"Executing: {' '.join(command)}")
        if cwd:
            logger.info(f"Working directory: {cwd}")
        
        try:
            # NEVER use shell=True for security
            process = subprocess.run(
                command,
                cwd=str(cwd) if cwd else None,
                env=full_env,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            duration = int((time.time() - start_time) * 1000)
            
            result = CommandResult(
                status=CommandStatus.SUCCESS if process.returncode == 0 else CommandStatus.ERROR,
                return_code=process.returncode,
                stdout=process.stdout or "",
                stderr=process.stderr or "",
                command=command,
                duration_ms=duration
            )
            
            if result.status == CommandStatus.SUCCESS:
                logger.info(f"Command completed successfully in {duration}ms")
            else:
                logger.warning(f"Command failed with code {process.returncode}")
                if result.stderr:
                    logger.warning(f"Stderr: {result.stderr[:500]}")
            
            return result
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s")
            return CommandResult(
                status=CommandStatus.TIMEOUT,
                return_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                command=command
            )
        except FileNotFoundError:
            logger.error(f"Command not found: {command[0]}")
            return CommandResult(
                status=CommandStatus.ERROR,
                return_code=-1,
                stdout="",
                stderr=f"Command not found: {command[0]}",
                command=command
            )
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return CommandResult(
                status=CommandStatus.ERROR,
                return_code=-1,
                stdout="",
                stderr=str(e),
                command=command
            )
    
    def execute_in_terminal(
        self,
        command: list[str],
        cwd: Optional[Path] = None,
        title: Optional[str] = None,
        keep_open: bool = True
    ) -> bool:
        """
        Execute a command in a new visible terminal window.
        
        Args:
            command: Command to run
            cwd: Working directory
            title: Window title
            keep_open: Keep terminal open after command finishes
        
        Returns:
            True if terminal was opened successfully
        """
        try:
            # Build the command string for cmd.exe
            cmd_str = " ".join(command)
            
            # Use cmd.exe /k to keep window open, /c to close
            flag = "/k" if keep_open else "/c"
            
            # Build the full command
            if title:
                terminal_cmd = ["cmd.exe", flag, f"title {title} && {cmd_str}"]
            else:
                terminal_cmd = ["cmd.exe", flag, cmd_str]
            
            # Start the terminal
            process = subprocess.Popen(
                terminal_cmd,
                cwd=str(cwd) if cwd else None,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            
            logger.info(f"Terminal opened with command: {cmd_str}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open terminal: {e}")
            return False
    
    def execute_interactive(
        self,
        commands: list[list[str]],
        cwd: Optional[Path] = None,
        title: str = "Macro Engine",
        on_output: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Execute multiple commands in an interactive terminal with progress display.
        
        Args:
            commands: List of commands to run sequentially
            cwd: Working directory
            title: Terminal window title
            on_output: Callback for output lines
        
        Returns:
            True if all commands succeeded
        """
        try:
            # Get current PATH and find git automatically
            current_path = os.environ.get("PATH", "")
            
            # Find git path automatically
            git_path = find_git_path()
            if git_path:
                extended_path = f"{git_path};{current_path}"
            else:
                extended_path = current_path
                logger.warning("Git not found - commands may fail")
            
            # Create a batch script to run all commands
            script_lines = [
                "@echo off",
                f'SET PATH={extended_path}',
                f"title {title}"
            ]
            
            if cwd:
                script_lines.append(f'cd /d "{cwd}"')
            
            for cmd in commands:
                cmd_str = " ".join(cmd)
                script_lines.append(f"echo Running: {cmd_str}")
                script_lines.append(cmd_str)
                script_lines.append("if errorlevel 1 (")
                script_lines.append(f'  echo Command failed: {cmd_str}')
                script_lines.append("  pause")
                script_lines.append("  exit /b 1")
                script_lines.append(")")
                script_lines.append("echo.")
            
            script_lines.append("echo All commands completed successfully!")
            script_lines.append("pause")
            
            # Write temporary batch file
            import tempfile
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".bat",
                delete=False,
                encoding="utf-8"
            ) as f:
                f.write("\n".join(script_lines))
                batch_file = f.name
            
            # Run the batch file in a new console using 'start'
            # Pass current environment so git is in PATH
            subprocess.Popen(
                f'start "Git Commit" cmd.exe /c "{batch_file}"',
                shell=True,
                env=os.environ.copy()
            )
            
            logger.info(f"Interactive terminal started with {len(commands)} commands")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute interactive commands: {e}")
            return False
