"""Character and camera movement."""
import random
import time
from typing import Tuple

from ..input.keyboard import KeyboardController
from ..core.logger import Logger


class MovementController:
    """Handles character and camera movement."""

    def __init__(self, keyboard: KeyboardController, logger: Logger):
        self.keyboard = keyboard
        self.logger = logger

    def rotate_camera(self, duration: float = 1.0) -> None:
        """
        Rotate camera using Q key.

        Args:
            duration: How long to hold the rotation key
        """
        self.logger.debug(f"Rotating camera for {duration}s")
        self.keyboard.hold("q", duration)

    def move_forward(self, duration: float) -> None:
        """
        Move character forward.

        Args:
            duration: How long to move forward
        """
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

    def search_for_targets(
        self,
        num_rotations: int = 8,
        move_forward_time: float = 1.0,
        check_callback=None
    ) -> bool:
        """
        Perform a comprehensive search by rotating camera and moving character.
        Checks for targets after each rotation using callback.

        Args:
            num_rotations: Number of camera rotations to perform
            move_forward_time: Time to move forward between rotations
            check_callback: Function to call after each rotation to check for targets.
                           Should return True if targets found (stops search early).

        Returns:
            True if targets found during search, False if completed all rotations
        """
        self.logger.info(f"Starting target search: {num_rotations} rotations")

        rotation_duration = 0.5  # Duration for each rotation

        for i in range(num_rotations):
            # Rotate camera
            self.logger.debug(f"Search rotation {i+1}/{num_rotations}")
            self.rotate_camera(duration=rotation_duration)
            time.sleep(0.3)  # Let camera settle

            # Check for targets after rotation
            if check_callback is not None:
                if check_callback():
                    self.logger.info(f"Targets found after rotation {i+1}/{num_rotations}!")
                    return True

            # Every few rotations, move forward to explore
            if (i + 1) % 3 == 0:
                self.logger.debug("Moving forward to explore")
                self.move_forward(move_forward_time)
                time.sleep(0.3)

                # Check again after moving
                if check_callback is not None:
                    if check_callback():
                        self.logger.info(f"Targets found after moving (rotation {i+1}/{num_rotations})!")
                        return True

        self.logger.debug("Search completed, no targets found")
        return False

    def move_camera_and_search(self) -> None:
        """Rotate camera and move forward to search for targets."""
        self.logger.info("Moving camera to search for targets")

        # Rotate camera
        self.rotate_camera(duration=1.0)

        # Move forward
        self.move_forward_random()

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

    def unstuck_pathfinding(self) -> None:
        """
        Attempt to unstuck character from terrain using random WASD movements.
        Used when player gets stuck while pathfinding to targets.
        """
        self.logger.info("Attempting to unstuck from terrain")

        # Random movement pattern to try to escape terrain
        movements = ["w", "a", "s", "d"]

        # Try 3-5 random movements
        num_movements = random.randint(3, 5)

        for i in range(num_movements):
            # Pick a random direction
            direction = random.choice(movements)
            duration = random.uniform(0.3, 0.7)

            if self.logger.debug_enabled:
                self.logger.debug(f"Unstuck attempt {i+1}/{num_movements}: {direction.upper()} for {duration:.2f}s")

            self.keyboard.hold(direction, duration)
            time.sleep(0.1)  # Small pause between movements

        # Add a random camera rotation to change perspective
        self.rotate_camera(duration=random.uniform(0.5, 1.0))
        self.logger.info("Unstuck attempt completed")
