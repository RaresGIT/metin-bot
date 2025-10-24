"""Character and camera movement."""
import random
import time
from typing import Tuple

from ..input.keyboard import KeyboardController
from ..core.logger import Logger


class MovementController:
    """Handles character and camera movement."""

    def __init__(self, keyboard: KeyboardController, logger: Logger, debug: bool = False):
        self.keyboard = keyboard
        self.logger = logger
        self.debug = debug

    def rotate_camera(self, duration: float = 1.0) -> None:
        """
        Rotate camera using Q key.

        Args:
            duration: How long to hold the rotation key
        """
        if self.debug:
            self.logger.info(f"[DEBUG MODE] Would rotate camera for {duration}s")
            return

        self.logger.debug(f"Rotating camera for {duration}s")
        self.keyboard.hold("q", duration)

    def move_forward(self, duration: float) -> None:
        """
        Move character forward.

        Args:
            duration: How long to move forward
        """
        if self.debug:
            self.logger.info(f"[DEBUG MODE] Would move forward for {duration}s")
            return

        self.keyboard.hold("w", duration)

    def move_forward_random(self, min_duration: float = 0.5, max_duration: float = 0.75) -> None:
        """
        Move forward for a random duration.

        Args:
            min_duration: Minimum movement time
            max_duration: Maximum movement time
        """
        duration = random.uniform(min_duration, max_duration)
        self.move_forward(duration)

    def move_camera_and_search(self) -> None:
        """Rotate camera and move forward to search for targets."""
        if self.debug:
            self.logger.info("[DEBUG MODE] Would move camera to search for targets")
            return

        self.logger.info("Moving camera to search for targets")

        # Rotate camera
        self.rotate_camera(duration=1.0)

        # Move forward
        self.move_forward_random(min_duration=0.7, max_duration=1)

        # Wait for camera to settle
        time.sleep(0.5)

    def unstuck(self, target_coords: Tuple[int, int], center_x: int, center_y: int) -> None:
        """
        Attempt to unstuck character with random movements.

        Args:
            target_coords: Coordinates of target we're stuck on
            center_x: Screen center X
            center_y: Screen center Y
        """
        if self.debug:
            self.logger.info("[DEBUG MODE] Would attempt to unstuck character")
            return

        self.logger.info("Attempting to unstuck character")
        x, y = target_coords

        if y < center_y:
            # Target above center - move back and strafe
            self.keyboard.hold_random("s", 0.05, 0.08)
            self.keyboard.hold_random("a", 0.05, 0.08)
            self.keyboard.hold_random("d", 0.05, 0.08)
        else:
            # Target below center - move forward and strafe
            self.keyboard.hold_random("w", 0.05, 0.08)
            self.keyboard.hold_random("a", 0.05, 0.08)
            self.keyboard.hold_random("d", 0.05, 0.08)
