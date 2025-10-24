"""Keyboard hotkey listener for bot control."""
import keyboard
from typing import Callable, Dict, Optional
from ..core.logger import Logger


class HotkeyListener:
    """Manages keyboard hotkeys for bot control."""

    def __init__(self, logger: Logger):
        self.logger = logger
        self.hotkeys: Dict[str, Callable] = {}
        self._registered_keys: list = []

    def register_hotkey(self, key: str, callback: Callable, description: str = "") -> None:
        """
        Register a hotkey with a callback function.

        Args:
            key: Hotkey string (e.g., 'f1', 'ctrl+p', 'pause')
            callback: Function to call when hotkey is pressed
            description: Optional description of what the hotkey does
        """
        try:
            # Store the callback
            self.hotkeys[key] = callback

            # Register with keyboard library
            keyboard.add_hotkey(key, callback, suppress=False)
            self._registered_keys.append(key)

            if description:
                self.logger.info(f"Registered hotkey: {key.upper()} - {description}")
            else:
                self.logger.info(f"Registered hotkey: {key.upper()}")

        except Exception as e:
            self.logger.error(f"Failed to register hotkey '{key}': {e}")

    def unregister_all(self) -> None:
        """Unregister all hotkeys."""
        for key in self._registered_keys:
            try:
                keyboard.remove_hotkey(key)
            except Exception as e:
                self.logger.warning(f"Failed to unregister hotkey '{key}': {e}")

        self._registered_keys.clear()
        self.hotkeys.clear()
        self.logger.debug("All hotkeys unregistered")

    def is_key_pressed(self, key: str) -> bool:
        """
        Check if a specific key is currently pressed.

        Args:
            key: Key name to check

        Returns:
            True if key is pressed, False otherwise
        """
        return keyboard.is_pressed(key)
