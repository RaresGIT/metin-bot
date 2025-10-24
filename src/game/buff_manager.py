"""Buff management and timing."""
import time

from ..core.state import BotState
from ..core.logger import Logger
from ..input.input_manager import InputManager


class BuffManager:
    """Manages buff refresh timing."""

    def __init__(
        self,
        state: BotState,
        input_manager: InputManager,
        logger: Logger,
        enabled: bool = False,
        interval_min: int = 30,
        interval_max: int = 60,
        buff_keys: str = "ctrl+v",
    ):
        self.state = state
        self.input_manager = input_manager
        self.logger = logger
        self.enabled = enabled
        self.interval_min = interval_min
        self.interval_max = interval_max
        self.buff_keys = buff_keys

    def check_and_refresh(self) -> None:
        """Check if buffs need refreshing and refresh them."""
        if not self.enabled:
            return

        # Skip buff refresh in debug mode
        if self.input_manager.debug:
            if self.state.should_refresh_buffs():
                self.logger.info("[DEBUG MODE] Would refresh buffs but skipping")
                # Still mark as refreshed to avoid spam
                self.state.mark_buffs_refreshed(self.interval_min, self.interval_max)
            return

        if self.state.should_refresh_buffs():
            time_since_last = time.time() - self.state.last_buff_time
            self.logger.info(f"Refreshing buffs (last buff was {time_since_last:.1f}s ago)")

            self.input_manager.refresh_buffs(self.buff_keys)
            self.state.mark_buffs_refreshed(self.interval_min, self.interval_max)

            self.logger.debug(f"Next buff refresh in {self.state.next_buff_interval:.1f}s")
            time.sleep(0.2)  # Small delay after pressing buff keys
