"""Color-based target detection for finding objects by distinctive colors."""
from typing import List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

from .image_matcher import ImageMatch
from .screen_capture import ScreenCapture, MonitorManager
from ..core.logger import Logger


class ColorTargetFinder:
    """Finds targets based on color characteristics instead of template matching."""

    def __init__(
        self,
        screen_capture: ScreenCapture,
        monitor_manager: MonitorManager,
        logger: Logger,
        debug: bool = False,
    ):
        self.screen_capture = screen_capture
        self.monitor_manager = monitor_manager
        self.logger = logger
        self.debug = debug

    def _create_roi_mask(
        self,
        shape: Tuple[int, int],
        exclusions: List[Tuple[int, int, int, int]]
    ) -> np.ndarray:
        """
        Create a binary mask for ROI exclusions.

        Args:
            shape: (height, width) of the image
            exclusions: List of (x, y, w, h) regions to exclude

        Returns:
            Binary mask (255 = include, 0 = exclude)
        """
        mask = np.ones(shape, dtype=np.uint8) * 255

        for ex, ey, ew, eh in exclusions:
            # Ensure coordinates are within bounds
            ey = max(0, min(ey, shape[0]))
            ex = max(0, min(ex, shape[1]))
            eh = max(0, min(eh, shape[0] - ey))
            ew = max(0, min(ew, shape[1] - ex))

            if eh > 0 and ew > 0:
                mask[ey:ey+eh, ex:ex+ew] = 0

        return mask

    def find_by_color(
        self,
        color_name: str,
        monitor_index: Optional[int] = None,
        min_area: int = 100,
        max_area: int = 10000,
    ) -> List[ImageMatch]:
        """
        Find targets by detecting specific color ranges.

        Args:
            color_name: Color to search for (e.g., 'orange', 'yellow')
            monitor_index: Monitor to search on (None for all)
            min_area: Minimum blob area in pixels
            max_area: Maximum blob area in pixels

        Returns:
            List of ImageMatch objects for detected color regions
        """
        # Get monitor region
        monitor_region = self.monitor_manager.get_monitor_region(monitor_index)
        search_region = monitor_region or (100, 100, 2500, 1200)

        # Define ROI exclusion zones (same as template-based finder)
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

        if self.debug:
            self.logger.debug(f"Searching for color '{color_name}' in region: {search_region}")

        # Capture screenshot
        screenshot = self.screen_capture.capture_region(search_region)
        img_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

        # Create ROI mask
        region_x, region_y = x, y
        adjusted_exclusions = []
        for ex, ey, ew, eh in roi_exclusions:
            adj_ex = ex - region_x
            adj_ey = ey - region_y
            if adj_ex < img_cv.shape[1] and adj_ey < img_cv.shape[0]:
                adjusted_exclusions.append((max(0, adj_ex), max(0, adj_ey), ew, eh))

        roi_mask = self._create_roi_mask((img_cv.shape[0], img_cv.shape[1]), adjusted_exclusions)

        # Convert to HSV for color detection
        hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)

        # Define color ranges in HSV
        color_ranges = self._get_color_ranges(color_name)

        # Create combined mask for all color ranges
        color_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in color_ranges:
            mask = cv2.inRange(hsv, lower, upper)
            color_mask = cv2.bitwise_or(color_mask, mask)

        # Apply ROI mask
        color_mask = cv2.bitwise_and(color_mask, roi_mask)

        # Morphological operations to clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel)

        # Find contours (blobs)
        contours, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter and convert to ImageMatch objects
        matches = []
        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter by area
            if area < min_area or area > max_area:
                continue

            # Get bounding box
            x_local, y_local, w_local, h_local = cv2.boundingRect(contour)

            # Calculate confidence based on color purity and area
            roi = color_mask[y_local:y_local+h_local, x_local:x_local+w_local]
            color_ratio = np.count_nonzero(roi) / (w_local * h_local) if (w_local * h_local) > 0 else 0

            # Confidence score: combination of color purity and compactness
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
            confidence = (color_ratio * 0.7) + (circularity * 0.3)

            # Convert to global coordinates
            global_x = x_local + region_x
            global_y = y_local + region_y

            matches.append(
                ImageMatch(
                    left=global_x,
                    top=global_y,
                    width=w_local,
                    height=h_local,
                    confidence=float(confidence),
                    scale=1.0
                )
            )

        # Sort by confidence
        matches = sorted(matches, key=lambda m: m.confidence, reverse=True)

        if self.debug:
            self.logger.debug(f"Found {len(matches)} color blobs for '{color_name}'")

            # Save debug visualization
            self._save_debug_visualization(
                img_cv, color_mask, matches, roi_exclusions,
                region_x, region_y, color_name
            )

        return matches

    def _get_color_ranges(self, color_name: str) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Get HSV color ranges for a given color name.

        Args:
            color_name: Name of the color

        Returns:
            List of (lower_bound, upper_bound) HSV tuples
        """
        # HSV ranges for different colors
        # H: 0-179, S: 0-255, V: 0-255 in OpenCV
        color_ranges = {
            'orange': [
                # Orange tones (pumpkin-like)
                (np.array([5, 100, 100]), np.array([20, 255, 255])),
                # Deeper orange/red-orange
                (np.array([0, 100, 100]), np.array([10, 255, 255])),
            ],
            'yellow': [
                # Yellow tones
                (np.array([20, 100, 100]), np.array([35, 255, 255])),
            ],
            'red': [
                # Red wraps around in HSV
                (np.array([0, 100, 100]), np.array([10, 255, 255])),
                (np.array([170, 100, 100]), np.array([180, 255, 255])),
            ],
            'blue': [
                (np.array([100, 100, 100]), np.array([130, 255, 255])),
            ],
            'green': [
                (np.array([40, 100, 100]), np.array([80, 255, 255])),
            ],
        }

        return color_ranges.get(color_name.lower(), color_ranges['orange'])

    def _save_debug_visualization(
        self,
        img: np.ndarray,
        color_mask: np.ndarray,
        matches: List[ImageMatch],
        roi_exclusions: List[Tuple[int, int, int, int]],
        region_x: int,
        region_y: int,
        color_name: str,
    ):
        """Save debug visualization showing color detection."""
        # Create visualization image
        vis = img.copy()

        # Draw ROI exclusions (red hatched pattern)
        for ex, ey, ew, eh in roi_exclusions:
            adj_ex = ex - region_x
            adj_ey = ey - region_y

            # Draw hatched pattern
            for i in range(adj_ey, min(adj_ey + eh, vis.shape[0]), 10):
                cv2.line(vis, (adj_ex, i), (adj_ex + ew, i), (0, 0, 255), 1)
            for i in range(adj_ex, min(adj_ex + ew, vis.shape[1]), 10):
                cv2.line(vis, (i, adj_ey), (i, adj_ey + eh), (0, 0, 255), 1)

            # Draw border
            cv2.rectangle(vis, (adj_ex, adj_ey), (adj_ex + ew, adj_ey + eh), (0, 0, 255), 2)

        # Draw detected regions (green boxes)
        for match in matches:
            x_local = match.left - region_x
            y_local = match.top - region_y

            # Draw bounding box
            cv2.rectangle(
                vis,
                (x_local, y_local),
                (x_local + match.width, y_local + match.height),
                (0, 255, 0),
                2
            )

            # Draw confidence score
            cv2.putText(
                vis,
                f"{match.confidence:.2f}",
                (x_local, y_local - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
                cv2.LINE_AA
            )

        # Add color mask overlay (semi-transparent)
        color_overlay = cv2.cvtColor(color_mask, cv2.COLOR_GRAY2BGR)
        color_overlay = cv2.applyColorMap(color_overlay, cv2.COLORMAP_HOT)
        vis = cv2.addWeighted(vis, 0.7, color_overlay, 0.3, 0)

        # Add info text
        cv2.putText(
            vis,
            f"Color Detection: {color_name.upper()}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

        cv2.putText(
            vis,
            f"Found {len(matches)} targets",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        # Convert to PIL and save
        vis_rgb = cv2.cvtColor(vis, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(vis_rgb)
        self.screen_capture.save_debug_screenshot(pil_img, f"color_detection_{color_name}.png")
