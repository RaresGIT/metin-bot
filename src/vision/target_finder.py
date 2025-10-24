"""Target detection logic for stones and UI elements."""
from math import sqrt
from pathlib import Path
from typing import List, Optional, Tuple, Union
import numpy as np

from .image_matcher import ImageMatcher, ImageMatch
from .screen_capture import ScreenCapture, MonitorManager
from .color_detector import ColorBasedDetector, ColorCluster
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
        vision_method: str = "v2",
        color_detector: Optional[ColorBasedDetector] = None,
    ):
        self.image_matcher = image_matcher
        self.screen_capture = screen_capture
        self.monitor_manager = monitor_manager
        self.logger = logger
        self.vision_method = vision_method

        # Initialize color detector for v2
        if color_detector is not None:
            self.color_detector = color_detector
        else:
            self.color_detector = ColorBasedDetector(logger=logger, debug=logger.debug_enabled)

        self.logger.info(f"TargetFinder initialized with vision method: {vision_method}")

    def find_stones(
        self,
        stone_names: List[str],
        monitor_index: Optional[int] = None,
        templates_folder: str = "./src/assets/stones",
    ) -> Union[List[ImageMatch], List[ColorCluster]]:
        """
        Search for stone templates on screen.
        Uses either v1 (template matching) or v2 (color detection) based on vision_method.

        Args:
            stone_names: List of stone names (e.g., ['blue', 'red']) - used for v1 only
            monitor_index: Monitor to search on (None for all)
            templates_folder: Folder containing stone template images - used for v1 only

        Returns:
            List of ImageMatch objects (v1) or ColorCluster objects (v2)
        """
        monitor_region = self.monitor_manager.get_monitor_region(monitor_index)
        search_region = monitor_region or (100, 100, 2500, 1200)

        if self.vision_method == "v2":
            # Color-based detection (v2)
            if self.logger.debug_enabled:
                self.logger.debug(f"Using color detection (v2) on region: {search_region}")

            # Capture screenshot
            screenshot = self.screen_capture.capture_region(search_region)

            # Convert PIL Image to numpy array for OpenCV
            import cv2
            screenshot_np = np.array(screenshot)
            screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

            # Detect clusters
            clusters = self.color_detector.detect_clusters(screenshot_bgr)

            # Adjust cluster coordinates to account for region offset
            region_x, region_y = search_region[0], search_region[1]
            for cluster in clusters:
                cx, cy = cluster.center
                cluster.center = (cx + region_x, cy + region_y)

                x, y, w, h = cluster.bbox
                cluster.bbox = (x + region_x, y + region_y, w, h)

            if self.logger.debug_enabled:
                self.logger.debug(f"Color detection found {len(clusters)} clusters")

                # Save annotated debug image
                annotated = self.color_detector.annotate_image(screenshot_bgr, clusters)
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                import cv2
                import os
                debug_dir = "debug"
                os.makedirs(debug_dir, exist_ok=True)
                cv2.imwrite(f"{debug_dir}/{timestamp}_stones_found_annotated.png", annotated)

            return clusters

        else:
            # Template matching (v1)
            stones_found = []

            if self.logger.debug_enabled:
                if monitor_region:
                    self.logger.debug(
                        f"Using template matching (v1) on monitor {monitor_index}: region={search_region}"
                    )
                else:
                    self.logger.debug(f"Using template matching (v1) in region: {search_region}")

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
                self.logger.debug(f"Template matching found {len(stones_found)} stones")

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
        matches: Union[List[ImageMatch], List[ColorCluster]],
        center_x: int,
        center_y: int,
        aspect_ratio: float,
        offset_x: int,
        offset_y: int,
        edge_margin: int = 0,
        center_exclusion_radius: int = 0,
        screen_width: Optional[int] = None,
        screen_height: Optional[int] = None,
    ) -> Optional[Target]:
        """
        Find the closest target from a list of matches or clusters.

        Args:
            matches: List of ImageMatch objects (v1) or ColorCluster objects (v2)
            center_x: Screen center X coordinate
            center_y: Screen center Y coordinate
            aspect_ratio: Screen aspect ratio for distance correction
            offset_x: Click offset X
            offset_y: Click offset Y
            edge_margin: Ignore targets within this distance from screen edges
            center_exclusion_radius: Ignore targets within this radius from screen center (player position)
            screen_width: Screen width for edge filtering
            screen_height: Screen height for edge filtering

        Returns:
            Target object with coordinates and distance, or None if no valid targets
        """
        targets = []

        # Get screen dimensions from monitor manager if not provided
        if edge_margin > 0 and (screen_width is None or screen_height is None):
            from screeninfo import get_monitors
            monitors = get_monitors()
            if monitors:
                screen_width = monitors[0].width
                screen_height = monitors[0].height

        for match in matches:
            if isinstance(match, ColorCluster):
                # Handle v2 color clusters
                cx, cy = match.center

                # Skip targets near screen edges
                if edge_margin > 0 and screen_width and screen_height:
                    if (cx < edge_margin or cx > screen_width - edge_margin or
                        cy < edge_margin or cy > screen_height - edge_margin):
                        if self.logger.debug_enabled:
                            self.logger.debug(f"Skipping edge cluster at ({cx}, {cy})")
                        continue

                # Skip targets too close to screen center (player position)
                if center_exclusion_radius > 0:
                    distance_from_center = sqrt(
                        pow(cx - center_x, 2) + pow(cy - center_y, 2)
                    )
                    if distance_from_center < center_exclusion_radius:
                        if self.logger.debug_enabled:
                            self.logger.debug(
                                f"Skipping center cluster at ({cx}, {cy}), "
                                f"distance from center: {distance_from_center:.1f}px < {center_exclusion_radius}px"
                            )
                        continue

                # Calculate distance from center with aspect ratio correction
                distance = sqrt(
                    pow(cx - center_x, 2)
                    + (pow(aspect_ratio * (cy - center_y), 2))
                )

                # Use center as click coordinates (no offset needed for v2)
                click_coords = (cx, cy)

                targets.append(Target(coords=click_coords, distance=distance))

                if self.logger.debug_enabled:
                    self.logger.debug(
                        f"Target distance: {distance:.2f}, cluster center: {match.center}, area: {match.area:.0f}"
                    )

            else:
                # Handle v1 template matches
                x, y = match.left, match.top

                # Skip targets near screen edges
                if edge_margin > 0 and screen_width and screen_height:
                    if (x < edge_margin or x > screen_width - edge_margin or
                        y < edge_margin or y > screen_height - edge_margin):
                        if self.logger.debug_enabled:
                            self.logger.debug(f"Skipping edge match at ({x}, {y})")
                        continue

                # Skip targets too close to screen center (player position)
                if center_exclusion_radius > 0:
                    distance_from_center = sqrt(
                        pow(x - center_x, 2) + pow(y - center_y, 2)
                    )
                    if distance_from_center < center_exclusion_radius:
                        if self.logger.debug_enabled:
                            self.logger.debug(
                                f"Skipping center match at ({x}, {y}), "
                                f"distance from center: {distance_from_center:.1f}px < {center_exclusion_radius}px"
                            )
                        continue

                # Calculate distance from center with aspect ratio correction
                distance = sqrt(
                    pow(x - center_x, 2)
                    + (pow(aspect_ratio * (y - center_y), 2))
                )

                # Calculate click coordinates with offset
                click_coords = (x + offset_x, y + offset_y)

                targets.append(Target(coords=click_coords, distance=distance))

                if self.logger.debug_enabled:
                    self.logger.debug(f"Target distance: {distance:.2f}, match: {match}")

        # Return None if no valid targets
        if not targets:
            if self.logger.debug_enabled:
                self.logger.debug("No valid targets after filtering")
            return None

        # Return closest target
        closest = min(targets, key=lambda t: t.distance)

        if self.logger.debug_enabled:
            self.logger.debug(
                f"Closest target: coords={closest.coords}, distance={closest.distance:.2f}"
            )

        return closest

    def is_target_still_present(
        self,
        target_coords: Tuple[int, int],
        stone_names: List[str],
        monitor_index: Optional[int] = None,
        tolerance: int = 50,
    ) -> bool:
        """
        Check if a target is still present at or near the specified coordinates.

        Args:
            target_coords: Original target coordinates (x, y)
            stone_names: Stone names to search for (v1 only)
            monitor_index: Monitor to search on
            tolerance: Distance tolerance for considering target as "same"

        Returns:
            True if target still exists, False if destroyed
        """
        # Find all current targets
        current_targets = self.find_stones(stone_names, monitor_index)

        if not current_targets:
            return False

        target_x, target_y = target_coords

        # Check if any current target is close to our original target
        for match in current_targets:
            if isinstance(match, ColorCluster):
                cx, cy = match.center
            else:
                cx, cy = match.left, match.top

            distance = sqrt(pow(cx - target_x, 2) + pow(cy - target_y, 2))

            if distance <= tolerance:
                if self.logger.debug_enabled:
                    self.logger.debug(f"Target still present at ({cx}, {cy}), distance: {distance:.2f}")
                return True

        if self.logger.debug_enabled:
            self.logger.debug(f"Target at ({target_x}, {target_y}) no longer present")
        return False

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
