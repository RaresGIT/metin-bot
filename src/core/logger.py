"""Centralized logging functionality."""
from datetime import datetime
from typing import Optional


class Logger:
    """Centralized logger for bot activities."""

    def __init__(self, debug: bool = False):
        self.debug_enabled = debug

    def log(self, msg: str) -> None:
        """Log a message with timestamp."""
        print(f"{datetime.now()}: {msg}")

    def debug(self, msg: str) -> None:
        """Log a debug message (only if debug enabled)."""
        if self.debug_enabled:
            self.log(f"[DEBUG] {msg}")

    def info(self, msg: str) -> None:
        """Log an info message."""
        self.log(f"[INFO] {msg}")

    def warning(self, msg: str) -> None:
        """Log a warning message."""
        self.log(f"[WARNING] {msg}")

    def error(self, msg: str) -> None:
        """Log an error message."""
        self.log(f"[ERROR] {msg}")
