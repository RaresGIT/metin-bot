"""Screen capture and monitor management."""
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

import pyautogui
from PIL import Image
from screeninfo import get_monitors

from ..core.logger import Logger


class MonitorManager:
    """Manages monitor detection and region calculation."""

    def __init__(self, logger: Logger):
        self.logger = logger
        self._monitors = None

    def get_monitors(self) -> List:
        """Get list of all available monitors."""
        if self._monitors is None:
            self._monitors = list(get_monitors())
        return self._monitors

    def list_monitors(self) -> None:
        """Log information about all monitors."""
        monitors = self.get_monitors()
        self.logger.info(f"Found {len(monitors)} monitor(s):")
        for i, monitor in enumerate(monitors):
            self.logger.info(
                f"  Monitor {i}: {monitor.width}x{monitor.height} at ({monitor.x}, {monitor.y})"
            )
            if monitor.is_primary:
                self.logger.info("    ^ PRIMARY monitor")

    def get_monitor_region(self, monitor_index: Optional[int] = None) -> Optional[Tuple[int, int, int, int]]:
        """
        Get the screen region for a specific monitor.

        Args:
            monitor_index: Index of monitor (0 = primary, 1 = second, etc.)
                          None = use all monitors (default PyAutoGUI behavior)

        Returns:
            tuple: (x, y, width, height) or None for all monitors
        """
        if monitor_index is None:
            return None

        try:
            monitors = self.get_monitors()
            if monitor_index < 0 or monitor_index >= len(monitors):
                self.logger.warning(
                    f"Monitor index {monitor_index} out of range. Available monitors: {len(monitors)}"
                )
                self.logger.warning("Falling back to all monitors")
                return None

            monitor = monitors[monitor_index]
            return (monitor.x, monitor.y, monitor.width, monitor.height)
        except Exception as e:
            self.logger.error(f"Error getting monitor info: {e}")
            self.logger.warning("Falling back to all monitors")
            return None

    def get_screen_center(self, monitor_index: Optional[int] = None) -> Tuple[int, int]:
        """
        Calculate the center coordinates of a monitor.

        Args:
            monitor_index: Index of monitor (0 = primary, 1 = second, etc.)
                          None = use primary monitor

        Returns:
            tuple: (center_x, center_y) absolute screen coordinates
        """
        try:
            monitors = self.get_monitors()

            # If no monitor specified, use primary monitor
            if monitor_index is None:
                for monitor in monitors:
                    if monitor.is_primary:
                        center_x = monitor.x + monitor.width // 2
                        center_y = monitor.y + monitor.height // 2
                        self.logger.info(
                            f"Using primary monitor center: ({center_x}, {center_y}) "
                            f"[Resolution: {monitor.width}x{monitor.height}]"
                        )
                        return (center_x, center_y)
                # Fallback to first monitor if no primary found
                monitor = monitors[0]
            else:
                if monitor_index < 0 or monitor_index >= len(monitors):
                    self.logger.warning(
                        f"Monitor index {monitor_index} out of range. Using primary monitor."
                    )
                    return self.get_screen_center(None)
                monitor = monitors[monitor_index]

            center_x = monitor.x + monitor.width // 2
            center_y = monitor.y + monitor.height // 2

            self.logger.info(
                f"Using monitor {monitor_index} center: ({center_x}, {center_y}) "
                f"[Resolution: {monitor.width}x{monitor.height}]"
            )

            return (center_x, center_y)
        except Exception as e:
            self.logger.error(f"Error calculating screen center: {e}")
            self.logger.warning("Falling back to default center (960, 540)")
            return (960, 540)

    def get_aspect_ratio(self, monitor_index: Optional[int] = None) -> float:
        """
        Calculate the aspect ratio of a monitor.

        Args:
            monitor_index: Index of monitor (0 = primary, 1 = second, etc.)
                          None = use primary monitor

        Returns:
            float: Aspect ratio (width / height)
        """
        try:
            monitors = self.get_monitors()

            # If no monitor specified, use primary monitor
            if monitor_index is None:
                for monitor in monitors:
                    if monitor.is_primary:
                        aspect_ratio = monitor.width / monitor.height
                        self.logger.debug(
                            f"Primary monitor aspect ratio: {aspect_ratio:.2f} "
                            f"({monitor.width}x{monitor.height})"
                        )
                        return aspect_ratio
                # Fallback to first monitor if no primary found
                monitor = monitors[0]
            else:
                if monitor_index < 0 or monitor_index >= len(monitors):
                    self.logger.warning(
                        f"Monitor index {monitor_index} out of range. Using primary monitor."
                    )
                    return self.get_aspect_ratio(None)
                monitor = monitors[monitor_index]

            aspect_ratio = monitor.width / monitor.height
            self.logger.debug(
                f"Monitor {monitor_index} aspect ratio: {aspect_ratio:.2f} "
                f"({monitor.width}x{monitor.height})"
            )

            return aspect_ratio
        except Exception as e:
            self.logger.error(f"Error calculating aspect ratio: {e}")
            self.logger.warning("Falling back to default aspect ratio (1.78)")
            return 1.78


class ScreenCapture:
    """Handles screen capture and debug screenshot saving."""

    def __init__(self, logger: Logger, debug: bool = False):
        self.logger = logger
        self.debug = debug
        self.debug_folder = Path("debug")

    def ensure_debug_folder(self) -> None:
        """Create debug folder if it doesn't exist."""
        if not self.debug_folder.exists():
            self.debug_folder.mkdir(parents=True)
            self.logger.debug("Created debug folder")

    def save_debug_screenshot(self, image: Image.Image, filename: str) -> None:
        """Save screenshot to debug folder with timestamp."""
        if not self.debug:
            return

        self.ensure_debug_folder()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filepath = self.debug_folder / f"{timestamp}_{filename}"
        image.save(filepath)
        self.logger.debug(f"Saved debug screenshot: {filepath}")

    def capture_region(self, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        """
        Capture a screenshot of a specific region.

        Args:
            region: (x, y, width, height) or None for full screen

        Returns:
            PIL Image of the captured region
        """
        return pyautogui.screenshot(region=region)
