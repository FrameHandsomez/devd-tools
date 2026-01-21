"""
Statistics Tracker - Track usage statistics for Macro Engine

Tracks:
- Feature executions
- Mode changes
- Key presses
- Session time
"""

import json
import threading
from pathlib import Path
from datetime import datetime, date
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class StatisticsTracker:
    """
    Tracks and persists usage statistics.
    
    Statistics are saved to a JSON file and can be viewed in Settings.
    """
    
    def __init__(self, stats_file: Optional[Path] = None):
        if stats_file is None:
            stats_file = Path(__file__).parent.parent / "stats.json"
        
        self.stats_file = stats_file
        self._stats = self._load_stats()
        self._session_start = datetime.now()
        self._lock = threading.Lock()
    
    def _load_stats(self) -> dict:
        """Load statistics from file"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load stats: {e}")
        
        return self._get_default_stats()
    
    def _get_default_stats(self) -> dict:
        """Return default statistics structure"""
        return {
            "total_key_presses": 0,
            "total_feature_executions": 0,
            "total_mode_changes": 0,
            "total_commits": 0,
            "total_sessions": 0,
            "total_session_minutes": 0,
            "first_use_date": datetime.now().isoformat(),
            "last_use_date": datetime.now().isoformat(),
            "feature_usage": {},
            "mode_usage": {},
            "daily_stats": {},
            "streak_days": 0
        }
    
    def _save_stats(self):
        """Save statistics to file"""
        try:
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(self._stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Could not save stats: {e}")
    
    def track_key_press(self, key: str):
        """Track a key press"""
        with self._lock:
            self._stats["total_key_presses"] += 1
            self._update_daily("key_presses")
            self._save_stats()
    
    def track_feature_execution(self, feature_name: str, action: str):
        """Track a feature execution"""
        with self._lock:
            self._stats["total_feature_executions"] += 1
            
            # Track per-feature
            if feature_name not in self._stats["feature_usage"]:
                self._stats["feature_usage"][feature_name] = 0
            self._stats["feature_usage"][feature_name] += 1
            
            # Special tracking
            if feature_name == "git_commit" and action == "commit":
                self._stats["total_commits"] += 1
            
            self._update_daily("executions")
            self._save_stats()
    
    def track_mode_change(self, from_mode: str, to_mode: str):
        """Track a mode change"""
        with self._lock:
            self._stats["total_mode_changes"] += 1
            
            # Track per-mode usage
            if to_mode not in self._stats["mode_usage"]:
                self._stats["mode_usage"][to_mode] = 0
            self._stats["mode_usage"][to_mode] += 1
            
            self._update_daily("mode_changes")
            self._save_stats()
    
    def start_session(self):
        """Start a new session"""
        with self._lock:
            self._session_start = datetime.now()
            self._stats["total_sessions"] += 1
            self._stats["last_use_date"] = datetime.now().isoformat()
            self._update_streak()
            self._save_stats()
    
    def end_session(self):
        """End the current session"""
        with self._lock:
            session_duration = (datetime.now() - self._session_start).total_seconds() / 60
            self._stats["total_session_minutes"] += int(session_duration)
            self._save_stats()
    
    def _update_daily(self, stat_type: str):
        """Update daily statistics"""
        today = date.today().isoformat()
        
        if today not in self._stats["daily_stats"]:
            self._stats["daily_stats"][today] = {
                "key_presses": 0,
                "executions": 0,
                "mode_changes": 0
            }
        
        self._stats["daily_stats"][today][stat_type] += 1
        
        # Keep only last 30 days
        if len(self._stats["daily_stats"]) > 30:
            dates = sorted(self._stats["daily_stats"].keys())
            for old_date in dates[:-30]:
                del self._stats["daily_stats"][old_date]
    
    def _update_streak(self):
        """Update usage streak"""
        today = date.today()
        last_use = self._stats.get("last_use_date", "")
        
        try:
            last_date = datetime.fromisoformat(last_use).date()
            diff = (today - last_date).days
            
            if diff == 1:
                self._stats["streak_days"] += 1
            elif diff > 1:
                self._stats["streak_days"] = 1
        except Exception:
            self._stats["streak_days"] = 1
    
    def get_stats(self) -> dict:
        """Get all statistics"""
        with self._lock:
            stats = self._stats.copy()
            
            # Calculate current session duration
            current_session = (datetime.now() - self._session_start).total_seconds() / 60
            stats["current_session_minutes"] = int(current_session)
            
            return stats
    
    def get_summary(self) -> dict:
        """Get a summary of key statistics"""
        stats = self.get_stats()
        
        return {
            "total_actions": stats["total_feature_executions"],
            "total_commits": stats["total_commits"],
            "total_sessions": stats["total_sessions"],
            "total_hours": round(stats["total_session_minutes"] / 60, 1),
            "streak_days": stats["streak_days"],
            "favorite_mode": max(stats["mode_usage"], key=stats["mode_usage"].get) if stats["mode_usage"] else "N/A",
            "favorite_feature": max(stats["feature_usage"], key=stats["feature_usage"].get) if stats["feature_usage"] else "N/A"
        }
    
    def reset_stats(self):
        """Reset all statistics"""
        with self._lock:
            self._stats = self._get_default_stats()
            self._save_stats()


# Global instance
_tracker: Optional[StatisticsTracker] = None


def get_tracker() -> StatisticsTracker:
    """Get the global statistics tracker instance"""
    global _tracker
    if _tracker is None:
        _tracker = StatisticsTracker()
    return _tracker
