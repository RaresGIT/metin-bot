"""Template matching abstraction."""
from pathlib import Path
from typing import List, Optional, Tuple, Generator

import pyautogui
import pyscreeze
from PIL import Image

from ..core.logger import Logger


class ImageMatch:
    """Represents a matched image location."""

    def __init__(self, left: int, top: int, width: int, height: int):
        self.left = left
        self.top = top
        self.width = width
        self.height = height

    @property
    def center(self) -> Tuple[int, int]:
        """Get center coordinates of the match."""
        return (self.left + self.width // 2, self.top + self.height // 2)

    def __repr__(self) -> str:
        return f"ImageMatch(left={self.left}, top={self.top}, width={self.width}, height={self.height})"


class ImageMatcher:
    """Handles template matching operations."""

    def __init__(self, logger: Logger, debug: bool = False):
        self.logger = logger
        self.debug = debug

    def find_all(
        self,
        template_path: str,
        region: Optional[Tuple[int, int, int, int]] = None,
        confidence: float = 0.7,
        grayscale: bool = True,
    ) -> List[ImageMatch]:
        """
        Find all instances of a template image on screen.

        Args:
            template_path: Path to template image
            region: (x, y, width, height) to search in, or None for full screen
            confidence: Minimum confidence threshold (0.0 to 1.0)
            grayscale: Whether to use grayscale matching

        Returns:
            List of ImageMatch objects
        """
        try:
            generator = pyautogui.locateAllOnScreen(
                template_path,
                region=region,
                confidence=confidence,
                grayscale=grayscale,
            )

            matches = [
                ImageMatch(match.left, match.top, match.width, match.height)
                for match in generator
            ]

            if self.debug and matches:
                self.logger.debug(
                    f"Found {len(matches)} instances of {Path(template_path).name}"
                )

            return matches

        except (pyautogui.ImageNotFoundException, pyscreeze.ImageNotFoundException) as e:
            if self.debug:
                self.logger.debug(
                    f"{Path(template_path).name} not found (confidence too low)"
                )
            return []

    def find_one(
        self,
        template_path: str,
        region: Optional[Tuple[int, int, int, int]] = None,
        confidence: float = 0.7,
        grayscale: bool = True,
    ) -> Optional[ImageMatch]:
        """
        Find the first instance of a template image on screen.

        Args:
            template_path: Path to template image
            region: (x, y, width, height) to search in, or None for full screen
            confidence: Minimum confidence threshold (0.0 to 1.0)
            grayscale: Whether to use grayscale matching

        Returns:
            ImageMatch object or None if not found
        """
        try:
            match = pyautogui.locateOnScreen(
                template_path,
                region=region,
                confidence=confidence,
                grayscale=grayscale,
            )

            if match:
                if self.debug:
                    self.logger.debug(f"Found {Path(template_path).name}")
                return ImageMatch(match.left, match.top, match.width, match.height)

            return None

        except (pyautogui.ImageNotFoundException, pyscreeze.ImageNotFoundException):
            if self.debug:
                self.logger.debug(
                    f"{Path(template_path).name} not found (confidence too low)"
                )
            return None
