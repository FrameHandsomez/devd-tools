"""
Logger utilities for the Macro Engine
With log rotation to prevent disk space issues
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Log directory
LOG_DIR = Path(__file__).parent.parent / "logs"

# Log settings
MAX_LOG_SIZE_MB = 5  # Max size per log file
MAX_LOG_FILES = 3    # Keep only 3 backup files (total ~20MB max)


def setup_logger(level: int = logging.INFO):
    """Setup logging configuration with rotation"""
    LOG_DIR.mkdir(exist_ok=True)
    
    # Create log filename
    log_file = LOG_DIR / "macro_engine.log"
    
    # Create rotating file handler
    # Max 5MB per file, keep 3 backups (total max ~20MB)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
        backupCount=MAX_LOG_FILES,
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from external libraries
    logging.getLogger("pynput").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)


def cleanup_old_logs(days: int = 7):
    """Remove log files older than specified days"""
    if not LOG_DIR.exists():
        return
    
    import time
    from datetime import timedelta
    
    cutoff = time.time() - (days * 86400)
    removed_count = 0
    
    for log_file in LOG_DIR.glob("*.log*"):
        if log_file.stat().st_mtime < cutoff:
            try:
                log_file.unlink()
                removed_count += 1
            except Exception:
                pass
    
    if removed_count > 0:
        logger = get_logger(__name__)
        logger.info(f"Cleaned up {removed_count} old log files")
