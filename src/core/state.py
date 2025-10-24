"""Bot state management."""
import random
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple


@dataclass
class SelectedTarget:
    """Represents a selected combat target."""
    coords: Tuple[int, int]
    distance: float
    selected_at: float


class BotState:
    """Manages bot runtime state."""

    def __init__(self, buff_interval_min: int = 30, buff_interval_max: int = 60):
        self.is_running = True
        self.is_paused = False
        self.start_time = time.time()

        # Combat state
        self.last_selected: Optional[SelectedTarget] = None
        self.stuck_for_iterations = 0

        # Buff state
        self.last_buff_time = time.time()
        self.next_buff_interval = random.uniform(buff_interval_min, buff_interval_max)

    def stop(self) -> None:
        """Stop the bot."""
        self.is_running = False

    def pause(self) -> None:
        """Pause the bot."""
        self.is_paused = True

    def resume(self) -> None:
        """Resume the bot."""
        self.is_paused = False

    def toggle_pause(self) -> None:
        """Toggle pause state."""
        self.is_paused = not self.is_paused

    def elapsed_hours(self) -> float:
        """Get elapsed time in hours."""
        return (time.time() - self.start_time) / 3600

    def select_target(self, coords: Tuple[int, int], distance: float) -> None:
        """Mark a target as selected."""
        self.last_selected = SelectedTarget(
            coords=coords,
            distance=distance,
            selected_at=time.time()
        )
        self.stuck_for_iterations = 0

    def clear_target(self) -> None:
        """Clear the selected target."""
        self.last_selected = None

    def is_target_selected(self) -> bool:
        """Check if a target is currently selected."""
        return self.last_selected is not None

    def time_since_target_selected(self) -> float:
        """Get time elapsed since target was selected."""
        if self.last_selected is None:
            return 0.0
        return time.time() - self.last_selected.selected_at

    def increment_stuck_iterations(self) -> None:
        """Increment stuck iteration counter."""
        self.stuck_for_iterations += 1

    def reset_stuck_iterations(self) -> None:
        """Reset stuck iteration counter."""
        self.stuck_for_iterations = 0

    def should_refresh_buffs(self) -> bool:
        """Check if it's time to refresh buffs."""
        time_since_last_buff = time.time() - self.last_buff_time
        return time_since_last_buff >= self.next_buff_interval

    def mark_buffs_refreshed(self, interval_min: int, interval_max: int) -> None:
        """Mark buffs as refreshed and schedule next refresh."""
        self.last_buff_time = time.time()
        self.next_buff_interval = random.uniform(interval_min, interval_max)
