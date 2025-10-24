"""Configuration management with validation."""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class BotConfig:
    """Bot configuration with validation."""

    # Screen configuration (center_x, center_y, and aspect_ratio are calculated automatically)
    center_x: Optional[int] = None
    center_y: Optional[int] = None
    aspect_ratio: Optional[float] = None
    offset_x: int = 70
    offset_y: int = 45

    # Combat configuration
    wait_after_select: float = 3.0  # Pause after clicking target
    max_permitted_stuck_iterations: int = 3
    max_seconds_stuck: float = 1.0
    unstuck_timeout: float = 10.0  # Seconds before attempting unstuck if clusters don't change

    # Target tracking
    screen_edge_margin: int = 150  # Ignore targets within this distance from screen edges
    center_exclusion_radius: int = 50  # Ignore targets within this radius from screen center (player position)
    target_destroyed_check_interval: float = 0.5  # How often to check if target still exists

    # Search behavior
    search_camera_rotations: int = 8  # Number of camera rotations when searching
    search_move_forward_time: float = 1.0  # Seconds to move forward during search

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

    # Vision method
    vision_method: str = "v2"  # "v1" = template matching, "v2" = color detection

    # Vision v2 shape filtering
    min_circularity: float = 0.4  # Minimum circularity for v2 (0-1, 0.4 = somewhat round)
    min_shape_score: float = 0.5  # Minimum overall shape score for v2 (0-1)

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
            wait_after_select=data.get("WAIT_AFTER_SELECT", 3.0),
            unstuck_timeout=data.get("UNSTUCK_TIMEOUT", 10.0),
            screen_edge_margin=data.get("SCREEN_EDGE_MARGIN", 150),
            center_exclusion_radius=data.get("CENTER_EXCLUSION_RADIUS", 50),
            target_destroyed_check_interval=data.get("TARGET_DESTROYED_CHECK_INTERVAL", 0.5),
            search_camera_rotations=data.get("SEARCH_CAMERA_ROTATIONS", 8),
            search_move_forward_time=data.get("SEARCH_MOVE_FORWARD_TIME", 1.0),
            stone_names=data.get("STONE_NAMES", ["blue", "red", "gold"]),
            pickup_drop=data.get("PICKUP_DROP", True),
            lure_key=data.get("LURE_KEY", ""),
            deadline=data.get("DEADLINE", 10),
            monitor_index=data.get("MONITOR_INDEX", None),
            keep_buff_uptime=data.get("KEEP_BUFF_UPTIME", False),
            buff_interval_min=data.get("BUFF_INTERVAL_MIN", 30),
            buff_interval_max=data.get("BUFF_INTERVAL_MAX", 60),
            buff_keys=data.get("BUFF_KEYS", "ctrl+v"),
            vision_method=data.get("VISION_METHOD", "v2"),
            min_circularity=data.get("MIN_CIRCULARITY", 0.4),
            min_shape_score=data.get("MIN_SHAPE_SCORE", 0.5),
            debug=data.get("DEBUG", False),
        )

    def validate(self) -> None:
        """Validate configuration values."""
        if self.wait_after_select < 0:
            raise ValueError("Wait time cannot be negative")

        if self.deadline <= 0:
            raise ValueError("Deadline must be positive")

        if self.buff_interval_min < 0 or self.buff_interval_max < 0:
            raise ValueError("Buff intervals must be non-negative")

        if self.buff_interval_min > self.buff_interval_max:
            raise ValueError("Buff interval min cannot be greater than max")

        if not self.stone_names:
            raise ValueError("Must specify at least one stone name")

        if self.vision_method not in ["v1", "v2"]:
            raise ValueError("Vision method must be either 'v1' or 'v2'")
