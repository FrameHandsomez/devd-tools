"""
Snippet Manager - Handles loading, saving, and processing of code snippets
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import re
from utils.logger import get_logger

logger = get_logger(__name__)

class SnippetManager:
    """
    Manages code snippets stored in JSON configuration.
    Handles variable substitution and clipboard interaction.
    """
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._snippets: List[Dict] = []
        self.load()
        
    def load(self):
        """Load snippets from config file"""
        if not self.config_path.exists():
            logger.warning(f"Snippet config not found: {self.config_path}")
            self._save_defaults()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._snippets = data.get("snippets", [])
            logger.info(f"Loaded {len(self._snippets)} snippets")
        except Exception as e:
            logger.error(f"Error loading snippets: {e}")
            self._snippets = []

    def save(self):
        """Save snippets to config file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({"snippets": self._snippets}, f, indent=2)
            logger.info("Snippets saved")
        except Exception as e:
            logger.error(f"Error saving snippets: {e}")

    def _save_defaults(self):
        """Create default snippets file"""
        defaults = [
            {
                "trigger": "log", 
                "description": "Console Log", 
                "content": "console.log('{{cursor}}');", 
                "tags": ["js", "debug"]
            }
        ]
        self._snippets = defaults
        self.save()

    def get_snippets(self, filter_text: str = "") -> List[Dict]:
        """Get snippets matching filter text (trigger, formatting, tags)"""
        if not filter_text:
            return self._snippets
            
        filter_lower = filter_text.lower()
        results = []
        for s in self._snippets:
            # Search in trigger, description, or tags
            if (filter_lower in s.get("trigger", "").lower() or
                filter_lower in s.get("description", "").lower() or
                any(filter_lower in t.lower() for t in s.get("tags", []))):
                results.append(s)
        return results
    
    def add_snippet(self, trigger: str, content: str, description: str = "", tags: List[str] = None):
        """Add a new snippet"""
        self._snippets.append({
            "trigger": trigger,
            "content": content,
            "description": description,
            "tags": tags or []
        })
        self.save()

    def process_snippet(self, snippet: Dict, placeholders: Dict[str, str] = None) -> str:
        """
        Process snippet content: replace {{variables}}.
        Auto-handles {{clipboard}}.
        """
        content = snippet.get("content", "")
        if not content:
            return ""
            
        # Default placeholders
        if placeholders is None:
            placeholders = {}
            
        # Handle clipboard
        if "{{clipboard}}" in content:
            import pyperclip
            try:
                clip_text = pyperclip.paste()
                content = content.replace("{{clipboard}}", clip_text)
            except Exception as e:
                logger.warning(f"Clipboard access failed: {e}")
        
        # Replace provided variables
        for key, value in placeholders.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
            
        return content

    def get_required_variables(self, snippet: Dict) -> List[str]:
        """Extract variable names required by the snippet"""
        content = snippet.get("content", "")
        # Find all {{var}} patterns
        matches = re.findall(r"{{(\w+)}}", content)
        # Filter out built-ins
        return [m for m in set(matches) if m not in ("cursor", "clipboard")]
