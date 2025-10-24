"""High-level input coordination."""
from typing import Tuple

from .keyboard import KeyboardController
from .mouse import MouseController
from ..core.logger import Logger


class InputManager:
    """Coordinates keyboard and mouse input operations."""

    def __init__(self, logger: Logger, debug: bool = False):
        self.logger = logger
        self.debug = debug
        self.keyboard = KeyboardController(logger)
        self.mouse = MouseController(logger)

    def attack_target(self, coords: Tuple[int, int]) -> None:
        """
        Attack a target at specified coordinates.

        Args:
            coords: (x, y) tuple of target location
        """
        if self.debug:
            self.logger.info(f"[DEBUG MODE] Would attack target at {coords}")
            return

        self.logger.debug(f"Attacking target at {coords}")
        self.mouse.click_at(coords, move_delay=0.2)

    def pickup_items(self, key: str = "z") -> None:
        """
        Press the pickup/loot key.

        Args:
            key: Pickup key (default 'z')
        """
        if self.debug:
            self.logger.info(f"[DEBUG MODE] Would press pickup key '{key}'")
            return

        self.logger.debug("Picking up items")
        self.keyboard.press(key, delay=0.1)

    def refresh_buffs(self, buff_keys: str) -> None:
        """
        Refresh buffs using configured key combination.

        Args:
            buff_keys: Key combination for buffs (e.g., 'ctrl+v')
        """
        if self.debug:
            self.logger.info(f"[DEBUG MODE] Would refresh buffs: {buff_keys}")
            return

        self.logger.info(f"Refreshing buffs: {buff_keys}")
        self.keyboard.press_combo(buff_keys)

    def cancel_target(self) -> None:
        """Cancel current target selection."""
        self.logger.debug("Canceling target selection")
        self.keyboard.press("esc")

    def check_exit_key(self) -> bool:
        """
        Check if the exit key (ESC) is pressed.

        Returns:
            True if exit key is pressed
        """
        return self.keyboard.is_pressed("esc")
