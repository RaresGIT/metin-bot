"""Target detection logic for stones and UI elements."""
from math import sqrt
from pathlib import Path
from typing import List, Optional, Tuple
import cv2
import numpy as np

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

    def _calculate_iou(self, match1: ImageMatch, match2: ImageMatch) -> float:
        """
        Calculate Intersection over Union (IoU) between two matches.

        Args:
            match1: First ImageMatch
            match2: Second ImageMatch

        Returns:
            IoU value (0.0 to 1.0)
        """
        # Calculate intersection
        x1 = max(match1.left, match2.left)
        y1 = max(match1.top, match2.top)
        x2 = min(match1.left + match1.width, match2.left + match2.width)
        y2 = min(match1.top + match1.height, match2.top + match2.height)

        if x2 <= x1 or y2 <= y1:
            return 0.0

        intersection = (x2 - x1) * (y2 - y1)

        # Calculate union
        area1 = match1.width * match1.height
        area2 = match2.width * match2.height
        union = area1 + area2 - intersection

        return intersection / union if union > 0 else 0.0

    def _non_maximum_suppression(self, matches: List[ImageMatch], iou_threshold: float = 0.4) -> List[ImageMatch]:
        """
        Apply Non-Maximum Suppression using IoU.
        Keeps matches with highest confidence, suppresses overlapping ones.

        Args:
            matches: List of ImageMatch objects with confidence scores
            iou_threshold: IoU threshold for suppression (default 0.4)

        Returns:
            Filtered list with NMS applied
        """
        if len(matches) <= 1:
            return matches

        # Sort by confidence (descending)
        sorted_matches = sorted(matches, key=lambda m: m.confidence, reverse=True)

        keep = []

        while sorted_matches:
            # Take the match with highest confidence
            best = sorted_matches.pop(0)
            keep.append(best)

            # Remove all matches with high IoU overlap
            sorted_matches = [
                m for m in sorted_matches
                if self._calculate_iou(best, m) < iou_threshold
            ]

        return keep

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

        # Define ROI exclusion zones (edges + UI elements)
        # Format: (x, y, width, height)
        x, y, w, h = search_region
        roi_exclusions = [
            # Bottom edge (taskbar/skills) - 120px from bottom
            (x, y + h - 120, w, 120),
            # Top edge - 40px from top
            (x, y, w, 40),
            # Left edge - 60px from left
            (x, y, 60, h),
            # Right edge - 60px from right
            (x + w - 60, y, 60, h),
            # Top-left minimap area
            (x, y, 250, 250),
        ]

        # Adjust search region to exclude bottom UI
        search_region = (x, y, w, h - 120)

        if self.logger.debug_enabled:
            if monitor_region:
                self.logger.debug(
                    f"Searching for stones on monitor {monitor_index}: region={search_region}"
                )
            else:
                self.logger.debug(f"Searching for stones in region: {search_region}")

            self.logger.debug(f"Searching for stones: {stone_names}")

        # Multi-scale search with smaller incremental scales
        # Covers: smaller (0.8x), slightly smaller (0.9x), normal (1.0x), slightly larger (1.1x), larger (1.2x)
        scales = [0.8, 0.9, 1.0, 1.1, 1.2]

        for stone_name in stone_names:
            template_path = f"{templates_folder}/{stone_name}_stone.png"

            # Search each scale separately and apply per-scale NMS
            scale_matches = {}  # Store matches by scale

            for scale in scales:
                # Primary search with grayscale (more stable)
                matches = self.image_matcher.find_all(
                    template_path=template_path,
                    region=search_region,
                    confidence=0.82,  # High confidence threshold
                    grayscale=True,
                    scales=[scale],  # One scale at a time
                    use_transformations=False,
                    roi_exclusions=roi_exclusions,  # Pass ROI exclusions for masking
                )

                # Apply NMS per scale
                if matches:
                    matches = self._non_maximum_suppression(matches, iou_threshold=0.4)
                    scale_matches[scale] = matches

            # Collect all per-scale matches
            for matches in scale_matches.values():
                stones_found.extend(matches)

            # Adaptive fallback: if no matches found, try with lower confidence
            if len(stones_found) == 0:
                if self.logger.debug_enabled:
                    self.logger.debug(f"No matches for {stone_name} at 0.82, trying fallback")

                # Dynamic thresholding with steps
                for threshold in [0.78, 0.74, 0.72]:
                    if len(stones_found) >= 3:  # Stop if we found enough
                        break

                    if self.logger.debug_enabled:
                        self.logger.debug(f"Trying confidence {threshold}")

                    fallback_scales = [0.9, 1.0, 1.1]
                    for scale in fallback_scales:
                        matches = self.image_matcher.find_all(
                            template_path=template_path,
                            region=search_region,
                            confidence=threshold,
                            grayscale=False,  # Try color
                            scales=[scale],
                            use_transformations=False,
                            roi_exclusions=roi_exclusions,
                        )
                        if matches:
                            matches = self._non_maximum_suppression(matches, iou_threshold=0.4)
                            stones_found.extend(matches)

        # Apply cross-scale NMS to remove duplicates across different scales
        stones_found = self._non_maximum_suppression(stones_found, iou_threshold=0.45)

        # Sort final matches by confidence (highest first)
        stones_found = sorted(stones_found, key=lambda m: m.confidence, reverse=True)

        if self.logger.debug_enabled:
            self.logger.debug(f"Total stones found (after filtering): {len(stones_found)}")

            # Capture full monitor region for debug visualization
            full_region = monitor_region  # Use the full monitor region
            screenshot = self.screen_capture.capture_region(full_region)

            # Manually set the screenshot for overlay drawing
            self.image_matcher._last_screenshot = screenshot
            self.image_matcher._last_region = full_region

            # Generate annotated image showing all found stones and ROI exclusions
            annotated_img = self.image_matcher.draw_matches_overlay(
                matches=stones_found,
                label="Stones Found",
                roi_exclusions=roi_exclusions
            )
            if annotated_img:
                self.screen_capture.save_debug_screenshot(
                    annotated_img, "stones_found_annotated.png"
                )

            # Generate preprocessing visualization
            if stone_names:
                template_path = f"{templates_folder}/{stone_names[0]}_stone.png"
                preprocessing_img = self.image_matcher.create_preprocessing_visualization(
                    screenshot=screenshot,
                    template_path=template_path,
                    region=full_region,
                    roi_exclusions=roi_exclusions,
                    grayscale=True
                )
                if preprocessing_img:
                    self.screen_capture.save_debug_screenshot(
                        preprocessing_img, "preprocessing_visualization.png"
                    )

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

            # Generate annotated image showing all targets and the selected closest one
            annotated_img = self.image_matcher.draw_matches_overlay(
                matches=matches,
                click_coords=closest.coords,
                label="Target Selection"
            )
            if annotated_img:
                self.screen_capture.save_debug_screenshot(
                    annotated_img, "target_selection_annotated.png"
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
                self.logger.debug(
                    f"Searching for {element_name} on monitor {monitor_index}"
                )
            else:
                self.logger.debug(f"Searching for {element_name} on all monitors")

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
