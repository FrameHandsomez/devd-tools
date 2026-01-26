"""
Context Collector - Gathers project context for AI-enhanced prompts
Collects: Terminal errors, project structure, git status, recent files
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class ContextCollector:
    """
    Collects various context information from the project
    to enhance AI prompts with relevant information.
    """
    
    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
    
    def set_project(self, path: Path):
        """Set the current project path"""
        self.project_path = path
    
    def get_project_structure(self, max_depth: int = 3, max_files: int = 50) -> str:
        """
        Get a tree-like structure of the project.
        
        Returns:
            String representation of project structure
        """
        try:
            lines = []
            file_count = 0
            
            # Folders to ignore
            ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 
                          'env', '.idea', '.vscode', 'dist', 'build', '.next'}
            ignore_extensions = {'.pyc', '.pyo', '.exe', '.dll', '.so'}
            
            def walk_dir(path: Path, prefix: str = "", depth: int = 0):
                nonlocal file_count
                
                if depth > max_depth or file_count > max_files:
                    return
                
                try:
                    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
                except PermissionError:
                    return
                
                # Filter items
                items = [i for i in items if i.name not in ignore_dirs 
                        and i.suffix not in ignore_extensions
                        and not i.name.startswith('.')]
                
                for i, item in enumerate(items):
                    if file_count > max_files:
                        lines.append(f"{prefix}... (truncated)")
                        return
                    
                    is_last = i == len(items) - 1
                    current_prefix = "└── " if is_last else "├── "
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    
                    if item.is_dir():
                        lines.append(f"{prefix}{current_prefix}📁 {item.name}/")
                        walk_dir(item, next_prefix, depth + 1)
                    else:
                        lines.append(f"{prefix}{current_prefix}{item.name}")
                        file_count += 1
            
            lines.append(f"📂 {self.project_path.name}/")
            walk_dir(self.project_path)
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"Error getting project structure: {e}")
            return f"Error: Could not read project structure"
    
    def get_git_status(self) -> str:
        """Get current git status (changed files)"""
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return f"Modified files:\n{result.stdout.strip()}"
            return "No uncommitted changes"
            
        except Exception as e:
            logger.error(f"Error getting git status: {e}")
            return "Git status unavailable"
    
    def get_recent_commits(self, count: int = 5) -> str:
        """Get recent git commits"""
        try:
            result = subprocess.run(
                ["git", "log", f"-{count}", "--oneline"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return f"Recent commits:\n{result.stdout.strip()}"
            return "No commits found"
            
        except Exception as e:
            logger.error(f"Error getting commits: {e}")
            return "Git log unavailable"
    
    def get_current_branch(self) -> str:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            return "unknown"
            
        except Exception:
            return "unknown"
    
    def get_package_info(self) -> str:
        """Get package.json or pyproject.toml info"""
        try:
            # Check for package.json (Node.js)
            package_json = self.project_path / "package.json"
            if package_json.exists():
                import json
                with open(package_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    name = data.get('name', 'unknown')
                    deps = list(data.get('dependencies', {}).keys())[:10]
                    return f"Node.js project: {name}\nDependencies: {', '.join(deps)}"
            
            # Check for pyproject.toml (Python)
            pyproject = self.project_path / "pyproject.toml"
            if pyproject.exists():
                with open(pyproject, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Simple extraction
                    if 'name = ' in content:
                        return f"Python project (pyproject.toml found)"
            
            # Check for requirements.txt
            requirements = self.project_path / "requirements.txt"
            if requirements.exists():
                with open(requirements, 'r', encoding='utf-8') as f:
                    deps = [line.split('==')[0].strip() for line in f.readlines()[:10] if line.strip()]
                    return f"Python project\nDependencies: {', '.join(deps)}"
            
            return "Project type: Unknown"
            
        except Exception as e:
            logger.error(f"Error reading package info: {e}")
            return "Package info unavailable"
    
    def get_recent_logs(self, max_lines: int = 50) -> str:
        """Find and read recent log files in the project"""
        try:
            log_patterns = ["*.log", "logs/*.log", "logs/**/*.log", "error.log", "debug.log"]
            log_files = []
            
            for pattern in log_patterns:
                log_files.extend(list(self.project_path.glob(pattern)))
            
            # Sort by modification time (newest first)
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            if not log_files:
                return "No log files found in project"
            
            # Read newest log file
            target_log = log_files[0]
            with open(target_log, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.readlines()
                # Get last N lines
                recent_lines = content[-max_lines:]
                return f"Recent logs from {target_log.relative_to(self.project_path)}:\n```\n{''.join(recent_lines)}\n```"
                
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            return f"Error reading logs: {e}"

    def collect_full_context(self) -> Dict[str, Any]:
        """
        Collect all available context information.
        
        Returns:
            Dictionary with all context data
        """
        return {
            "project_name": self.project_path.name,
            "branch": self.get_current_branch(),
            "structure": self.get_project_structure(max_depth=2, max_files=30),
            "git_status": self.get_git_status(),
            "recent_commits": self.get_recent_commits(3),
            "package_info": self.get_package_info(),
            "logs": self.get_recent_logs(30)
        }

    def format_context_for_prompt(self, include_structure: bool = True, include_logs: bool = False) -> str:
        """
        Format collected context into a string for AI prompts.
        
        Args:
            include_structure: Whether to include project structure (can be long)
            include_logs: Whether to include recent logs
        
        Returns:
            Formatted context string
        """
        ctx = self.collect_full_context()
        
        lines = [
            "## Project Context",
            f"**Project:** {ctx['project_name']}",
            f"**Branch:** {ctx['branch']}",
            f"**{ctx['package_info']}**",
            "",
            f"### Git Status",
            ctx['git_status'],
            "",
            f"### {ctx['recent_commits']}",
        ]
        
        if include_logs:
            lines.extend([
                "",
                "### Error Logs",
                ctx['logs']
            ])
        
        if include_structure:
            lines.extend([
                "",
                "### Project Structure",
                "```",
                ctx['structure'],
                "```"
            ])
        
        return "\n".join(lines)


# Global instance
_collector = None


def get_collector(project_path: Optional[Path] = None) -> ContextCollector:
    """Get or create the global context collector"""
    global _collector
    if _collector is None or project_path:
        _collector = ContextCollector(project_path)
    return _collector
