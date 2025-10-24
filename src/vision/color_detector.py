"""
Color-based target detection (Vision v2).
Uses HSV color space to detect orange/yellow glowing clusters.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass

from ..core.logger import Logger


@dataclass
class ColorCluster:
    """Represents a detected color cluster."""

    center: Tuple[int, int]
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    area: float
    confidence: float = 1.0


class ColorBasedDetector:
    """
    Color-based target detector using HSV color space.
    Detects orange/yellow glowing objects (metin stones).
    """

    def __init__(
        self,
        logger: Logger,
        debug: bool = False,
        min_area: int = 50,
        min_circularity: float = 0.25,
        min_shape_score: float = 0.45,
        min_extent: float = 0.45,
        max_ellipse_aspect: float = 3.0,
        lower_hsv: Optional[np.ndarray] = None,
        upper_hsv: Optional[np.ndarray] = None,
    ):
        """
        Initialize color-based detector.

        Args:
            logger: Logger instance
            debug: Enable debug output
            min_area: Minimum cluster area in pixels to filter noise
            min_circularity: Minimum circularity (0-1, 0.25 for ellipses)
            min_shape_score: Minimum overall shape score (0-1, 0.45 for ellipses)
            min_extent: Minimum extent (how well shape fills ellipse, 0.45 default)
            max_ellipse_aspect: Maximum ellipse aspect ratio (3.0 default)
            lower_hsv: Lower HSV bound (default: orange/yellow range)
            upper_hsv: Upper HSV bound (default: orange/yellow range)
        """
        self.logger = logger
        self.debug = debug
        self.min_area = min_area
        self.min_circularity = min_circularity
        self.min_shape_score = min_shape_score
        self.min_extent = min_extent
        self.max_ellipse_aspect = max_ellipse_aspect

        # Default HSV range for orange/yellow glowing stones
        # Hue: 10-35 (orange to yellow)
        # Saturation: 100-255 (vibrant colors)
        # Value: 150-255 (bright)
        self.lower_hsv = lower_hsv if lower_hsv is not None else np.array([10, 100, 150])
        self.upper_hsv = upper_hsv if upper_hsv is not None else np.array([35, 255, 255])

        self.logger.info(
            f"Color detector initialized (v2 - elliptical) - HSV range: {self.lower_hsv} to {self.upper_hsv}, "
            f"min_circularity: {self.min_circularity}, min_shape_score: {self.min_shape_score}, "
            f"min_extent: {self.min_extent}, max_ellipse_aspect: {self.max_ellipse_aspect}"
        )

    def detect_clusters(self, image: np.ndarray) -> List[ColorCluster]:
        """
        Detect color clusters in an image.

        Args:
            image: BGR image from OpenCV (numpy array)

        Returns:
            List of detected ColorCluster objects
        """
        if image is None or image.size == 0:
            self.logger.warning("Empty image provided to color detector")
            return []

        # Convert to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Create mask for target colors
        mask = cv2.inRange(hsv, self.lower_hsv, self.upper_hsv)

        # Apply morphological operations to clean up the mask
        # Remove noise with opening (erosion followed by dilation)
        kernel_small = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_small, iterations=2)

        # Close gaps with closing (dilation followed by erosion)
        kernel_large = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_large, iterations=2)

        # Find contours (clusters)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if self.debug:
            self.logger.debug(f"Found {len(contours)} raw contours")

        # Extract and filter clusters with shape analysis
        clusters = []
        rejected_count = 0

        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter out small clusters (noise)
            if area < self.min_area:
                continue

            # Calculate shape metrics
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue

            # Circularity: 4π * area / perimeter² (1.0 = perfect circle)
            circularity = 4 * np.pi * area / (perimeter * perimeter)

            # Aspect ratio
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h if h > 0 else 0

            # Fit ELLIPSE instead of circle to better match stone shapes
            if len(contour) >= 5:  # Need at least 5 points to fit ellipse
                ellipse = cv2.fitEllipse(contour)
                (ellipse_cx, ellipse_cy), (ellipse_width, ellipse_height), angle = ellipse
                ellipse_area = np.pi * (ellipse_width / 2) * (ellipse_height / 2)

                # Extent: how well the shape fills its ellipse
                extent = float(area) / ellipse_area if ellipse_area > 0 else 0

                # Ellipse aspect ratio (width/height of the fitted ellipse)
                ellipse_aspect = max(ellipse_width, ellipse_height) / min(ellipse_width, ellipse_height) if min(ellipse_width, ellipse_height) > 0 else 1.0

                # Normalize angle to 0-180 range
                normalized_angle = angle % 180

                # Check if ellipse is roughly horizontal
                # Horizontal: 90° ± 25° (75-115°) allowing some tolerance
                # Reject vertical or diagonal ellipses
                is_horizontal = (75 <= normalized_angle <= 115)
            else:
                # Fallback to circle if not enough points for ellipse
                (circle_x, circle_y), radius = cv2.minEnclosingCircle(contour)
                circle_area = np.pi * (radius ** 2)
                extent = float(area) / circle_area if circle_area > 0 else 0
                ellipse_aspect = 1.0
                is_horizontal = True  # Assume horizontal for circles
                normalized_angle = 90

            # Calculate shape score for ELLIPSE/OVAL shapes (0-1, higher = better match)
            # Metin stones are elliptical, not perfectly circular

            # Circularity: Still useful, but lower threshold for ellipses
            # Ellipse circularity typically 0.3-0.7 (lower than circles)
            circularity_score = min(circularity / 0.6, 1.0)  # Normalize, 0.6 = good ellipse

            # Extent: How well it fills the ellipse (should be high for stones)
            extent_score = extent

            # Ellipse aspect ratio: Stones can be elongated (1.0 to 2.5)
            # 1.0 = circle, 1.5 = slight oval, 2.0 = moderate oval, 2.5 = elongated
            if ellipse_aspect <= 2.5:
                ellipse_aspect_score = 1.0 - (abs(ellipse_aspect - 1.5) / 2.0)  # Peak at 1.5 (typical stone)
            else:
                ellipse_aspect_score = 0.0  # Too elongated

            # Compactness: Perimeter relative to area (lower = more compact/stone-like)
            compactness = (perimeter ** 2) / area if area > 0 else float('inf')
            compactness_score = max(0, 1.0 - (compactness / 50.0))  # Normalize to 0-1

            # Overall shape score (weighted for elliptical stones)
            shape_score = (
                circularity_score * 0.3 +      # Less important for ellipses
                extent_score * 0.35 +           # Very important - must fill ellipse
                ellipse_aspect_score * 0.25 +   # Important - captures oval shape
                compactness_score * 0.1         # Minor factor - filters very irregular
            )

            # Filter based on shape (must be elliptical and horizontal)
            is_elliptical = (
                circularity >= self.min_circularity and
                shape_score >= self.min_shape_score and
                extent >= self.min_extent and
                ellipse_aspect <= self.max_ellipse_aspect and
                is_horizontal  # MUST be horizontal (not vertical/diagonal)
            )

            if not is_elliptical:
                rejected_count += 1
                if self.debug:
                    reject_reason = ""
                    if not is_horizontal:
                        reject_reason = f"angle:{normalized_angle:.0f}°"
                    elif circularity < self.min_circularity:
                        reject_reason = f"circularity:{circularity:.2f}"
                    elif shape_score < self.min_shape_score:
                        reject_reason = f"score:{shape_score:.2f}"
                    self.logger.debug(
                        f"Rejected cluster at ({x}, {y}): {reject_reason}"
                    )
                continue

            # Calculate center point
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = x + w // 2, y + h // 2

            # Use shape_score as confidence (higher shape score = more circular = more confident)
            confidence = min(shape_score, 1.0)

            cluster = ColorCluster(
                center=(cx, cy),
                bbox=(x, y, w, h),
                area=area,
                confidence=confidence,
            )
            clusters.append(cluster)

        if self.debug:
            self.logger.debug(
                f"Shape filtering: {len(clusters)} valid elliptical clusters, "
                f"{rejected_count} non-elliptical rejected (min_area={self.min_area}, angle_range=75-115°)"
            )

        return clusters

    def find_closest_cluster(
        self,
        clusters: List[ColorCluster],
        screen_center: Tuple[int, int],
        aspect_ratio: float = 1.78,
    ) -> Optional[ColorCluster]:
        """
        Find the closest cluster to screen center with aspect ratio correction.

        Args:
            clusters: List of detected clusters
            screen_center: Center point of the screen (cx, cy)
            aspect_ratio: Screen aspect ratio for distance correction

        Returns:
            Closest ColorCluster or None if no clusters
        """
        if not clusters:
            return None

        center_x, center_y = screen_center

        # Calculate distances with aspect ratio correction
        def distance(cluster: ColorCluster) -> float:
            cx, cy = cluster.center
            dx = (cx - center_x) / aspect_ratio
            dy = cy - center_y
            return (dx**2 + dy**2) ** 0.5

        closest = min(clusters, key=distance)

        if self.debug:
            dist = distance(closest)
            self.logger.debug(
                f"Closest cluster at {closest.center}, distance: {dist:.2f}, area: {closest.area:.0f}px"
            )

        return closest

    def annotate_image(self, image: np.ndarray, clusters: List[ColorCluster]) -> np.ndarray:
        """
        Annotate image with detected clusters for debugging.

        Args:
            image: BGR image to annotate
            clusters: List of detected clusters

        Returns:
            Annotated image
        """
        annotated = image.copy()

        for i, cluster in enumerate(clusters, 1):
            x, y, w, h = cluster.bbox
            cx, cy = cluster.center

            # Draw bounding box (green)
            cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Draw center point (red)
            cv2.circle(annotated, (cx, cy), 5, (0, 0, 255), -1)

            # Draw crosshair
            cv2.line(annotated, (cx - 15, cy), (cx + 15, cy), (0, 0, 255), 2)
            cv2.line(annotated, (cx, cy - 15), (cx, cy + 15), (0, 0, 255), 2)

            # Add label
            label = f"#{i} ({int(cluster.area)}px)"
            cv2.putText(
                annotated,
                label,
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2,
            )

        # Add summary
        summary = f"Clusters: {len(clusters)} (v2)"
        cv2.putText(annotated, summary, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return annotated
