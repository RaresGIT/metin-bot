"""Keyboard input abstraction."""
import time
import random
from typing import List

import keyboard as kb
import pydirectinput

from ..core.logger import Logger


class KeyboardController:
    """Handles keyboard input operations."""

    def __init__(self, logger: Logger):
        self.logger = logger

    def press(self, key: str, delay: float = 0.0) -> None:
        """
        Press a key.

        Args:
            key: Key to press (e.g., 'w', 'space', 'esc')
            delay: Delay after pressing in seconds
        """
        pydirectinput.press(key)
        if delay > 0:
            time.sleep(delay)

    def tap(self, key: str, delay: float = 0.0) -> None:
        """
        Tap a key (alias for press).

        Args:
            key: Key to tap (e.g., 'w', 'space', 'esc')
            delay: Delay after tapping in seconds
        """
        self.press(key, delay)

    def hold(self, key: str, duration: float) -> None:
        """
        Hold a key down for a duration.

        Args:
            key: Key to hold
            duration: How long to hold in seconds
        """
        pydirectinput.keyDown(key)
        time.sleep(duration)
        pydirectinput.keyUp(key)

    def hold_random(self, key: str, min_duration: float, max_duration: float) -> None:
        """
        Hold a key for a random duration.

        Args:
            key: Key to hold
            min_duration: Minimum duration in seconds
            max_duration: Maximum duration in seconds
        """
        duration = random.uniform(min_duration, max_duration)
        self.hold(key, duration)

    def press_combo(self, keys: str, delay_between: float = 0.05) -> None:
        """
        Press a key combination (e.g., 'ctrl+v').

        Args:
            keys: Key combination string (e.g., 'ctrl+v', 'alt+f1', 'f5')
            delay_between: Delay between key presses in seconds
        """
        key_list = keys.lower().split("+")

        if len(key_list) == 1:
            # Single key
            self.press(key_list[0])
            self.logger.debug(f"Pressed key: {key_list[0]}")
        else:
            # Key combination - hold modifiers, press final key
            for key in key_list[:-1]:
                pydirectinput.keyDown(key)
                time.sleep(delay_between)

            pydirectinput.press(key_list[-1])
            time.sleep(delay_between)

            # Release modifiers in reverse order
            for key in reversed(key_list[:-1]):
                pydirectinput.keyUp(key)
                time.sleep(delay_between)

            self.logger.debug(f"Pressed key combo: {keys}")

    def is_pressed(self, key: str) -> bool:
        """
        Check if a key is currently pressed.

        Args:
            key: Key to check

        Returns:
            True if key is pressed
        """
        return kb.is_pressed(key)

    def press_sequence(self, keys: List[str], delay: float = 0.1) -> None:
        """
        Press a sequence of keys with delay between each.

        Args:
            keys: List of keys to press
            delay: Delay between presses in seconds
        """
        for key in keys:
            self.press(key, delay)
