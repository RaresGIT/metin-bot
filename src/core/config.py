"""Configuration management with validation."""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class BotConfig:
    """Bot configuration with validation."""

    # Screen configuration (center_x, center_y, and aspect_ratio are calculated automatically)
    offset_x: int = 70
    offset_y: int = 45

    # Combat configuration
    wait_after_stone_destroyed: float = 5.0
    max_permitted_stuck_iterations: int = 3
    max_seconds_stuck: float = 1.0

    # Stone settings
    stone_names: List[str] = field(default_factory=lambda: ["blue", "red", "gold"])

    # Features
    pickup_drop: bool = True
    lure_key: str = ""
    deadline: int = 10  # hours

    # Multi-monitor
    monitor_index: Optional[int] = None

    # Buff management
    keep_buff_uptime: bool = False
    buff_interval_min: int = 30
    buff_interval_max: int = 60
    buff_keys: str = "ctrl+v"

    # Hotkeys
    hotkey_pause: str = "f1"
    hotkey_resume: str = "f2"
    hotkey_toggle_pause: str = "f3"
    hotkey_stop: str = "esc"

    # Debug
    debug: bool = False

    @classmethod
    def from_json(cls, file_path: str) -> "BotConfig":
        """Load configuration from JSON file."""
        with open(file_path, "r") as file:
            data = json.load(file)

        return cls(
            offset_x=data.get("OFFSET_X", 70),
            offset_y=data.get("OFFSET_Y", 45),
            wait_after_stone_destroyed=data.get("WAIT_AFTER_STONE_DESTROYED", 5.0),
            stone_names=data.get("STONE_NAMES", ["blue", "red", "gold"]),
            pickup_drop=data.get("PICKUP_DROP", True),
            lure_key=data.get("LURE_KEY", ""),
            deadline=data.get("DEADLINE", 10),
            monitor_index=data.get("MONITOR_INDEX", None),
            keep_buff_uptime=data.get("KEEP_BUFF_UPTIME", False),
            buff_interval_min=data.get("BUFF_INTERVAL_MIN", 30),
            buff_interval_max=data.get("BUFF_INTERVAL_MAX", 60),
            buff_keys=data.get("BUFF_KEYS", "ctrl+v"),
            hotkey_pause=data.get("HOTKEY_PAUSE", "f1"),
            hotkey_resume=data.get("HOTKEY_RESUME", "f2"),
            hotkey_toggle_pause=data.get("HOTKEY_TOGGLE_PAUSE", "f3"),
            hotkey_stop=data.get("HOTKEY_STOP", "esc"),
            debug=data.get("DEBUG", False),
        )

    def validate(self) -> None:
        """Validate configuration values."""
        if self.wait_after_stone_destroyed < 0:
            raise ValueError("Wait time cannot be negative")

        if self.deadline <= 0:
            raise ValueError("Deadline must be positive")

        if self.buff_interval_min < 0 or self.buff_interval_max < 0:
            raise ValueError("Buff intervals must be non-negative")

        if self.buff_interval_min > self.buff_interval_max:
            raise ValueError("Buff interval min cannot be greater than max")

        if not self.stone_names:
            raise ValueError("Must specify at least one stone name")
