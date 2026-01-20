"""
Project type detection utilities
"""

from pathlib import Path
from enum import Enum
from utils.logger import get_logger

logger = get_logger(__name__)


class ProjectType(Enum):
    NODEJS = "nodejs"
    PYTHON = "python"
    UNKNOWN = "unknown"


def detect_project_type(project_path: Path) -> ProjectType:
    """Detect project type based on files present"""
    
    if not project_path.exists():
        logger.warning(f"Project path does not exist: {project_path}")
        return ProjectType.UNKNOWN
    
    # Check for Node.js
    if (project_path / "package.json").exists():
        logger.info(f"Detected Node.js project at {project_path}")
        return ProjectType.NODEJS
    
    # Check for Python
    python_markers = ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"]
    for marker in python_markers:
        if (project_path / marker).exists():
            logger.info(f"Detected Python project at {project_path}")
            return ProjectType.PYTHON
    
    logger.info(f"Unknown project type at {project_path}")
    return ProjectType.UNKNOWN


def get_install_command(project_type: ProjectType, project_path: Path) -> list[str] | None:
    """Get the install command for a project type"""
    
    if project_type == ProjectType.NODEJS:
        # Check for package-lock.json (npm) or yarn.lock
        if (project_path / "yarn.lock").exists():
            return ["yarn", "install"]
        elif (project_path / "pnpm-lock.yaml").exists():
            return ["pnpm", "install"]
        else:
            return ["npm", "install"]
    
    elif project_type == ProjectType.PYTHON:
        # Return None - Python needs venv setup first
        return None
    
    return None


def get_dev_command(project_path: Path) -> list[str] | None:
    """Get the dev server command for a project"""
    
    package_json = project_path / "package.json"
    if package_json.exists():
        import json
        try:
            with open(package_json, "r", encoding="utf-8") as f:
                pkg = json.load(f)
                scripts = pkg.get("scripts", {})
                
                # Prefer dev, then start
                if "dev" in scripts:
                    return ["npm", "run", "dev"]
                elif "start" in scripts:
                    return ["npm", "start"]
        except Exception as e:
            logger.error(f"Error reading package.json: {e}")
    
    return None
