"""
Logger utilities for the Macro Engine
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Log directory
LOG_DIR = Path(__file__).parent.parent / "logs"


def setup_logger(level: int = logging.INFO):
    """Setup logging configuration"""
    LOG_DIR.mkdir(exist_ok=True)
    
    # Create log filename with date
    log_file = LOG_DIR / f"macro_engine_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("pynput").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)
