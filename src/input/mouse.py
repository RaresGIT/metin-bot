"""Mouse input abstraction."""
import time
from typing import Tuple, Optional

import pyautogui

from ..core.logger import Logger


class MouseController:
    """Handles mouse input operations."""

    def __init__(self, logger: Logger):
        self.logger = logger

    def move_to(self, x: int, y: int, duration: float = 0.0) -> None:
        """
        Move mouse to absolute coordinates.

        Args:
            x: Target X coordinate
            y: Target Y coordinate
            duration: Movement duration in seconds (0 for instant)
        """
        pyautogui.moveTo(x, y, duration=duration)

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left") -> None:
        """
        Click at current position or specified coordinates.

        Args:
            x: Target X coordinate (None for current position)
            y: Target Y coordinate (None for current position)
            button: Mouse button ('left', 'right', 'middle')
        """
        if x is not None and y is not None:
            pyautogui.click(x, y, button=button)
        else:
            pyautogui.click(button=button)

    def click_at(self, coords: Tuple[int, int], move_delay: float = 0.2) -> None:
        """
        Move to coordinates and click with delay.

        Args:
            coords: (x, y) tuple of target coordinates
            move_delay: Delay after moving before clicking
        """
        x, y = coords
        self.move_to(x, y)
        time.sleep(move_delay)
        self.click()

    def get_position(self) -> Tuple[int, int]:
        """
        Get current mouse position.

        Returns:
            (x, y) tuple of current position
        """
        return pyautogui.position()
