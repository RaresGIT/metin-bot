"""Target detection logic for stones and UI elements."""
from math import sqrt
from pathlib import Path
from typing import List, Optional, Tuple

from .image_matcher import ImageMatcher, ImageMatch
from .screen_capture import ScreenCapture, MonitorManager
from ..core.logger import Logger


class Target:
    """Represents a detected target with position and distance."""

    def __init__(self, coords: Tuple[int, int], distance: float):
        self.coords = coords
        self.distance = distance

    def __repr__(self) -> str:
        return f"Target(coords={self.coords}, distance={self.distance:.2f})"


class TargetFinder:
    """Finds and ranks targets on screen."""

    def __init__(
        self,
        image_matcher: ImageMatcher,
        screen_capture: ScreenCapture,
        monitor_manager: MonitorManager,
        logger: Logger,
    ):
        self.image_matcher = image_matcher
        self.screen_capture = screen_capture
        self.monitor_manager = monitor_manager
        self.logger = logger

    def find_stones(
        self,
        stone_names: List[str],
        monitor_index: Optional[int] = None,
        templates_folder: str = "./src/assets/stones",
    ) -> List[ImageMatch]:
        """
        Search for stone templates on screen.

        Args:
            stone_names: List of stone names (e.g., ['blue', 'red'])
            monitor_index: Monitor to search on (None for all)
            templates_folder: Folder containing stone template images

        Returns:
            List of ImageMatch objects for all found stones
        """
        stones_found = []
        monitor_region = self.monitor_manager.get_monitor_region(monitor_index)

        # Use hardcoded region as fallback
        search_region = monitor_region or (100, 100, 2500, 1200)

        if self.logger.debug_enabled:
            if monitor_region:
                self.logger.debug(
                    f"Searching for stones on monitor {monitor_index}: region={search_region}"
                )
            else:
                self.logger.debug(f"Searching for stones in region: {search_region}")

            screenshot = self.screen_capture.capture_region(search_region)
            self.screen_capture.save_debug_screenshot(
                screenshot, "search_stones_region.png"
            )
            self.logger.debug(f"Searching for stones: {stone_names}")

        for stone_name in stone_names:
            template_path = f"{templates_folder}/{stone_name}_stone.png"
            matches = self.image_matcher.find_all(
                template_path=template_path,
                region=search_region,
                confidence=0.7,
                grayscale=True,
            )
            stones_found.extend(matches)

        if self.logger.debug_enabled:
            self.logger.debug(f"Total stones found: {len(stones_found)}")

        return stones_found

    def find_ores(
        self,
        ore_names: List[str],
        monitor_index: Optional[int] = None,
    ) -> List[ImageMatch]:
        """Search for ore templates on screen."""
        return self.find_stones(
            stone_names=ore_names,
            monitor_index=monitor_index,
            templates_folder="./src/assets/mining",
        )

    def calculate_closest_target(
        self,
        matches: List[ImageMatch],
        center_x: int,
        center_y: int,
        aspect_ratio: float,
        offset_x: int,
        offset_y: int,
    ) -> Target:
        """
        Find the closest target from a list of matches.

        Args:
            matches: List of ImageMatch objects
            center_x: Screen center X coordinate
            center_y: Screen center Y coordinate
            aspect_ratio: Screen aspect ratio for distance correction
            offset_x: Click offset X
            offset_y: Click offset Y

        Returns:
            Target object with coordinates and distance
        """
        targets = []

        for match in matches:
            # Calculate distance from center with aspect ratio correction
            distance = sqrt(
                pow(match.left - center_x, 2)
                + (pow(aspect_ratio * (match.top - center_y), 2))
            )

            # Calculate click coordinates with offset
            click_coords = (match.left + offset_x, match.top + offset_y)

            targets.append(Target(coords=click_coords, distance=distance))

            if self.logger.debug_enabled:
                self.logger.debug(f"Target distance: {distance:.2f}, match: {match}")

        # Return closest target
        closest = min(targets, key=lambda t: t.distance)

        if self.logger.debug_enabled:
            self.logger.debug(
                f"Closest target: coords={closest.coords}, distance={closest.distance:.2f}"
            )

        return closest

    def find_ui_element(
        self,
        element_name: str,
        monitor_index: Optional[int] = None,
        confidence: float = 0.9,
        assets_folder: str = "utils",
    ) -> Optional[ImageMatch]:
        """
        Find a UI element on screen.

        Args:
            element_name: Name of the UI element (without extension)
            monitor_index: Monitor to search on
            confidence: Confidence threshold
            assets_folder: Subfolder within src/assets to search in

        Returns:
            ImageMatch or None if not found
        """
        monitor_region = self.monitor_manager.get_monitor_region(monitor_index)
        template_path = f"./src/assets/{assets_folder}/{element_name}.png"

        if self.logger.debug_enabled:
            if monitor_region:
                screenshot = self.screen_capture.capture_region(monitor_region)
                self.logger.debug(
                    f"Searching for {element_name} on monitor {monitor_index}"
                )
            else:
                screenshot = self.screen_capture.capture_region()
                self.logger.debug(f"Searching for {element_name} on all monitors")

            self.screen_capture.save_debug_screenshot(
                screenshot, f"find_{element_name}_fullscreen.png"
            )

        match = self.image_matcher.find_one(
            template_path=template_path,
            region=monitor_region,
            confidence=confidence,
            grayscale=True,
        )

        if self.logger.debug_enabled:
            self.logger.debug(f"{element_name} found: {match is not None}")

        return match

    def find_combat_ui(
        self, monitor_index: Optional[int] = None
    ) -> Tuple[Optional[ImageMatch], Optional[ImageMatch]]:
        """
        Find HP bar and top bar UI elements.

        Returns:
            Tuple of (hp_bar, top_bar) matches, either can be None
        """
        hp_bar = self.find_ui_element("hp_bar", monitor_index, confidence=0.9)
        top_bar = self.find_ui_element("top_bar", monitor_index, confidence=0.7)

        if self.logger.debug_enabled:
            self.logger.debug(
                f"hp_bar found: {hp_bar is not None}, top_bar found: {top_bar is not None}"
            )

        return hp_bar, top_bar
