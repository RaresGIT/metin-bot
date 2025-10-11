"""Game window management."""
from typing import Optional, Tuple

import win32api
import win32con
import win32gui

from ..core.logger import Logger


class GameWindow:
    """Manages game window detection and interaction."""

    def __init__(self, window_title: str, logger: Logger):
        self.window_title = window_title
        self.logger = logger
        self._hwnd: Optional[int] = None

    @property
    def hwnd(self) -> int:
        """Get window handle, finding it if necessary."""
        if self._hwnd is None:
            self._hwnd = win32gui.FindWindow(None, self.window_title)
            if self._hwnd:
                self.logger.debug(f"Found game window: {self.window_title}")
            else:
                self.logger.warning(f"Could not find game window: {self.window_title}")
        return self._hwnd

    def global_to_client(self, x: int, y: int) -> Tuple[int, int]:
        """
        Convert global screen coordinates to client area coordinates.

        Args:
            x: Global X coordinate
            y: Global Y coordinate

        Returns:
            (client_x, client_y) tuple
        """
        return win32gui.ScreenToClient(self.hwnd, (x, y))

    def send_click(self, global_x: int, global_y: int) -> None:
        """
        Send a click to the window at global coordinates.

        Args:
            global_x: Global screen X coordinate
            global_y: Global screen Y coordinate
        """
        client_x, client_y = self.global_to_client(global_x, global_y)

        self.logger.debug(
            f"Sending click: global=({global_x}, {global_y}), client=({client_x}, {client_y})"
        )

        lParam = win32api.MAKELONG(client_x, client_y)
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)

    def send_click_relative(self, local_x: int, local_y: int) -> None:
        """
        Send a click at client-relative coordinates.

        Args:
            local_x: Client-relative X coordinate
            local_y: Client-relative Y coordinate
        """
        lParam = win32api.MAKELONG(local_x, local_y)

        self.logger.debug(f"Sending relative click: ({local_x}, {local_y})")

        win32api.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lParam)
        win32api.SendMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lParam)

    def get_client_rect(self) -> Tuple[int, int, int, int]:
        """
        Get the client area rectangle.

        Returns:
            (left, top, right, bottom) tuple
        """
        return win32gui.GetClientRect(self.hwnd)
