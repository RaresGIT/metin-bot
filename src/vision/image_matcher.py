"""Template matching abstraction."""
from pathlib import Path
from typing import List, Optional, Tuple, Generator
import tempfile
import os

import pyautogui
import pyscreeze
from PIL import Image, ImageDraw, ImageOps
import cv2
import numpy as np

from ..core.logger import Logger


class ImageMatch:
    """Represents a matched image location."""

    def __init__(self, left: int, top: int, width: int, height: int, confidence: float = 1.0, scale: float = 1.0):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.confidence = confidence  # Match confidence score 0.0-1.0
        self.scale = scale  # Scale factor used for this match

    @property
    def center(self) -> Tuple[int, int]:
        """Get center coordinates of the match."""
        return (self.left + self.width // 2, self.top + self.height // 2)

    def __repr__(self) -> str:
        return f"ImageMatch(left={self.left}, top={self.top}, width={self.width}, height={self.height}, conf={self.confidence:.3f}, scale={self.scale:.2f})"


class ImageMatcher:
    """Handles template matching operations."""

    def __init__(self, logger: Logger, debug: bool = False):
        self.logger = logger
        self.debug = debug
        self._last_screenshot = None
        self._last_region = None
        self._temp_files = []  # Track temporary files for cleanup

    def _preprocess_image(self, img: np.ndarray, is_grayscale: bool = False, roi_mask: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Apply comprehensive preprocessing pipeline to an image.

        Pipeline order:
        1. Mask ROI (if provided)
        2. Convert to grayscale (if needed)
        3. Denoise (light Gaussian blur)
        4. CLAHE (local contrast normalization)
        5. Global normalization (Z-score)
        6. Gamma correction
        7. Subtle sharpening

        Args:
            img: Input image (BGR or grayscale)
            is_grayscale: Whether to convert to grayscale
            roi_mask: Optional mask to apply (0 = exclude, 255 = include)

        Returns:
            Preprocessed image
        """
        if img is None:
            return img

        # 1. Apply ROI mask if provided
        if roi_mask is not None:
            img = cv2.bitwise_and(img, img, mask=roi_mask)

        # 2. Convert to grayscale
        if is_grayscale and len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 3. Denoise - light Gaussian blur (σ=0.8)
        img = cv2.GaussianBlur(img, (3, 3), 0.8)

        # 4. CLAHE - local contrast normalization
        if len(img.shape) == 2:  # Grayscale
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            img = clahe.apply(img)
        else:  # Color - apply to L channel in LAB
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            l = clahe.apply(l)
            lab = cv2.merge([l, a, b])
            img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        # 5. Global normalization - normalize to 0-255 range
        # Use min-max normalization instead of Z-score to preserve brightness order
        img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        # 6. Gamma correction - normalize brightness
        gamma = 1.0  # Could be adjusted based on scene
        img = np.power(img / 255.0, gamma) * 255.0
        img = img.astype(np.uint8)

        # 7. Subtle sharpening - unsharp mask
        blurred = cv2.GaussianBlur(img, (0, 0), 1.5)
        img = cv2.addWeighted(img, 1.8, blurred, -0.8, 0)
        img = np.clip(img, 0, 255).astype(np.uint8)

        return img

    def create_preprocessing_visualization(
        self,
        screenshot: Image.Image,
        template_path: str,
        region: Optional[Tuple[int, int, int, int]],
        roi_exclusions: Optional[List[Tuple[int, int, int, int]]],
        grayscale: bool
    ) -> Optional[Image.Image]:
        """
        Create a visualization showing the preprocessing pipeline results.

        Args:
            screenshot: Original screenshot (PIL Image)
            template_path: Path to template file
            region: Region coordinates
            roi_exclusions: ROI exclusions list
            grayscale: Whether preprocessing uses grayscale

        Returns:
            PIL Image showing preprocessing results
        """
        try:
            # Convert screenshot to cv2 format
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            template = cv2.imread(template_path)

            if screenshot_cv is None or template is None:
                return None

            # Create ROI mask
            roi_mask = None
            if roi_exclusions and region:
                region_x, region_y = region[0], region[1]
                adjusted_exclusions = []
                for ex, ey, ew, eh in roi_exclusions:
                    adj_ex = ex - region_x
                    adj_ey = ey - region_y
                    if adj_ex < screenshot_cv.shape[1] and adj_ey < screenshot_cv.shape[0]:
                        adjusted_exclusions.append((max(0, adj_ex), max(0, adj_ey), ew, eh))

                if adjusted_exclusions:
                    h, w = screenshot_cv.shape[:2]
                    roi_mask = self._create_roi_mask((h, w), adjusted_exclusions)

            # Apply preprocessing
            screenshot_processed = self._preprocess_image(screenshot_cv.copy(), is_grayscale=grayscale, roi_mask=roi_mask)
            template_processed = self._preprocess_image(template.copy(), is_grayscale=grayscale, roi_mask=None)

            # Convert back to color for visualization if grayscale
            if grayscale:
                screenshot_processed = cv2.cvtColor(screenshot_processed, cv2.COLOR_GRAY2BGR)
                template_processed = cv2.cvtColor(template_processed, cv2.COLOR_GRAY2BGR)

            # Create composite image
            # Place preprocessed screenshot as main image
            result = screenshot_processed.copy()

            # Resize template to fit in top-left corner (max 200x200)
            th, tw = template_processed.shape[:2]
            max_size = 200
            if th > max_size or tw > max_size:
                scale = min(max_size / th, max_size / tw)
                new_w = int(tw * scale)
                new_h = int(th * scale)
                template_processed = cv2.resize(template_processed, (new_w, new_h))

            # Place template in top-left corner with border
            th, tw = template_processed.shape[:2]
            border = 5
            x_pos, y_pos = 10, 10  # Position in top-left

            # Draw white border around template
            cv2.rectangle(
                result,
                (x_pos - border, y_pos - border),
                (x_pos + tw + border, y_pos + th + border),
                (255, 255, 255),
                2
            )

            # Overlay template
            result[y_pos:y_pos+th, x_pos:x_pos+tw] = template_processed

            # Add text label
            cv2.putText(
                result,
                "Template (preprocessed)",
                (x_pos, y_pos - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA
            )

            # Add preprocessing info text
            info_text = [
                "Preprocessing Applied:",
                "1. ROI Masking",
                "2. Grayscale" if grayscale else "2. Color (BGR)",
                "3. Denoise (sigma=0.8)",
                "4. CLAHE (clip=2.5)",
                "5. Min-Max Normalize",
                "6. Gamma Correct",
                "7. Sharpen"
            ]

            y_offset = result.shape[0] - 20 - (len(info_text) * 20)
            for i, text in enumerate(info_text):
                cv2.putText(
                    result,
                    text,
                    (10, y_offset + i * 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 255, 0),
                    1,
                    cv2.LINE_AA
                )

            # Convert back to PIL Image
            result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
            return Image.fromarray(result_rgb)

        except Exception as e:
            self.logger.debug(f"Failed to create preprocessing visualization: {e}")
            return None

    def _create_roi_mask(self, shape: Tuple[int, int], exclusions: List[Tuple[int, int, int, int]]) -> np.ndarray:
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
            mask[ey:ey+eh, ex:ex+ew] = 0

        return mask

    def _create_transformed_template(self, template_path: str, flip: bool = False, rotate: int = 0, scale: float = 1.0) -> str:
        """
        Create a transformed version of a template image.

        Args:
            template_path: Path to original template
            flip: Whether to flip horizontally
            rotate: Degrees to rotate (0, 90, 180, 270)
            scale: Scale factor (1.0 = original size, 0.5 = half size, 2.0 = double size)

        Returns:
            Path to temporary transformed image file
        """
        img = Image.open(template_path)

        # Apply scale first
        if scale != 1.0:
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            img = img.resize((new_width, new_height), Image.LANCZOS)

        if flip:
            img = ImageOps.mirror(img)

        if rotate != 0:
            img = img.rotate(rotate, expand=True)

        # Save to temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.png')
        os.close(temp_fd)
        img.save(temp_path)

        self._temp_files.append(temp_path)
        return temp_path

    def _cleanup_temp_files(self):
        """Clean up temporary transformed template files."""
        for temp_path in self._temp_files:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                self.logger.debug(f"Failed to remove temp file {temp_path}: {e}")
        self._temp_files.clear()

    def _filter_by_min_distance(self, matches: List[ImageMatch], min_distance: int) -> List[ImageMatch]:
        """
        Filter matches to enforce minimum distance between peaks.

        Args:
            matches: List of ImageMatch objects
            min_distance: Minimum distance in pixels between match centers

        Returns:
            Filtered list with distance constraint applied
        """
        if len(matches) <= 1:
            return matches

        # Sort by confidence (highest first)
        sorted_matches = sorted(matches, key=lambda m: m.confidence, reverse=True)

        keep = []
        for match in sorted_matches:
            mx, my = match.center

            # Check distance to all kept matches
            too_close = False
            for kept in keep:
                kx, ky = kept.center
                distance = np.sqrt((mx - kx)**2 + (my - ky)**2)

                if distance < min_distance:
                    too_close = True
                    break

            if not too_close:
                keep.append(match)

        return keep

    def find_all(
        self,
        template_path: str,
        region: Optional[Tuple[int, int, int, int]] = None,
        confidence: float = 0.7,
        grayscale: bool = True,
        use_transformations: bool = True,
        scales: Optional[List[float]] = None,
        roi_exclusions: Optional[List[Tuple[int, int, int, int]]] = None,
    ) -> List[ImageMatch]:
        """
        Find all instances of a template image on screen.

        Args:
            template_path: Path to template image
            region: (x, y, width, height) to search in, or None for full screen
            confidence: Minimum confidence threshold (0.0 to 1.0)
            grayscale: Whether to use grayscale matching
            use_transformations: Whether to also search for flipped and rotated versions
            scales: List of scale factors to try (e.g., [0.7, 0.85, 1.0, 1.2, 1.5])
                   If None, defaults to [1.0] (original size only)

        Returns:
            List of ImageMatch objects
        """
        # Capture screenshot in debug mode
        if self.debug:
            self._last_screenshot = pyautogui.screenshot(region=region)
            self._last_region = region

        all_matches = []

        # Default to original scale if not specified
        if scales is None:
            scales = [1.0]

        # Define transformations to try: (flip, rotation)
        transformations = [(False, 0)]  # Original
        if use_transformations:
            transformations.extend([
                (True, 0),    # Flipped
                (False, 90),  # Rotated 90°
                (False, 270), # Rotated 270° (same as -90°)
            ])

        # Try each scale
        for scale in scales:
            # Try each transformation at this scale
            for flip, rotate in transformations:
                try:
                    # Build transformation description
                    transform_parts = []
                    if scale != 1.0:
                        transform_parts.append(f"scale {scale:.2f}x")
                    if flip:
                        transform_parts.append("flipped")
                    if rotate != 0:
                        transform_parts.append(f"rotated {rotate}°")
                    transform_desc = ", ".join(transform_parts) if transform_parts else "original"

                    # Use original or create transformed template
                    if flip or rotate != 0 or scale != 1.0:
                        search_path = self._create_transformed_template(template_path, flip, rotate, scale)
                    else:
                        search_path = template_path

                    # Use cv2 template matching with all-peaks approach
                    screenshot = pyautogui.screenshot(region=region)
                    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                    template = cv2.imread(search_path)

                    if screenshot_cv is None or template is None:
                        continue

                    # Create ROI mask if exclusions provided
                    roi_mask = None
                    if roi_exclusions:
                        # Adjust exclusions for region offset
                        region_x = region[0] if region else 0
                        region_y = region[1] if region else 0

                        adjusted_exclusions = []
                        for ex, ey, ew, eh in roi_exclusions:
                            # Convert to region-relative coordinates
                            adj_ex = ex - region_x
                            adj_ey = ey - region_y
                            # Only include if it overlaps with the region
                            if adj_ex < screenshot_cv.shape[1] and adj_ey < screenshot_cv.shape[0]:
                                adjusted_exclusions.append((max(0, adj_ex), max(0, adj_ey), ew, eh))

                        if adjusted_exclusions:
                            h, w = screenshot_cv.shape[:2]
                            roi_mask = self._create_roi_mask((h, w), adjusted_exclusions)

                    # Apply comprehensive preprocessing pipeline
                    screenshot_cv = self._preprocess_image(screenshot_cv, is_grayscale=grayscale, roi_mask=roi_mask)
                    template = self._preprocess_image(template, is_grayscale=grayscale, roi_mask=None)

                    # Template matching
                    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)

                    # Response map smoothing for stable peak detection
                    result = cv2.GaussianBlur(result, (3, 3), 0.5)

                    # Find local maxima (peaks) instead of thresholding all pixels
                    h, w = template.shape[:2]

                    # Create dilation kernel for peak detection (~10% of template size)
                    kernel_size = max(3, min(h, w) // 10)
                    if kernel_size % 2 == 0:
                        kernel_size += 1
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))

                    # Dilate to find local maxima
                    local_max = cv2.dilate(result, kernel)

                    # Peaks are where result equals local max AND above threshold
                    peaks = (result == local_max) & (result >= confidence)
                    locations = np.where(peaks)

                    # Create ImageMatch objects with confidence scores
                    region_x = region[0] if region else 0
                    region_y = region[1] if region else 0

                    matches = []
                    for pt in zip(*locations[::-1]):  # Switch x and y
                        match_confidence = result[pt[1], pt[0]]
                        matches.append(
                            ImageMatch(
                                pt[0] + region_x,
                                pt[1] + region_y,
                                w,
                                h,
                                float(match_confidence),
                                scale=scale
                            )
                        )

                    # Apply minimum distance constraint between peaks
                    min_distance = int(0.3 * min(w, h))
                    matches = self._filter_by_min_distance(matches, min_distance)

                    # Cap matches per scale to top 50 by score
                    if len(matches) > 50:
                        matches = sorted(matches, key=lambda m: m.confidence, reverse=True)[:50]

                    if matches:
                        if self.debug:
                            self.logger.debug(
                                f"Found {len(matches)} instances of {Path(template_path).name} ({transform_desc})"
                            )
                        all_matches.extend(matches)

                except (pyautogui.ImageNotFoundException, pyscreeze.ImageNotFoundException):
                    pass  # No matches for this transformation, continue

        # Cleanup temporary files
        self._cleanup_temp_files()

        if self.debug:
            if all_matches:
                self.logger.debug(
                    f"Total {len(all_matches)} instances of {Path(template_path).name} found (all scales/transformations)"
                )
            else:
                self.logger.debug(
                    f"{Path(template_path).name} not found (confidence too low)"
                )

        return all_matches

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
        # Capture screenshot in debug mode
        if self.debug:
            self._last_screenshot = pyautogui.screenshot(region=region)
            self._last_region = region

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

    def draw_matches_overlay(
        self,
        matches: List[ImageMatch],
        click_coords: Optional[Tuple[int, int]] = None,
        label: Optional[str] = None,
        roi_exclusions: Optional[List[Tuple[int, int, int, int]]] = None,
    ) -> Optional[Image.Image]:
        """
        Draw bounding boxes around matches and mark click location.

        Args:
            matches: List of ImageMatch objects to visualize
            click_coords: Optional (x, y) coordinates where click would occur
            label: Optional label for the image
            roi_exclusions: Optional list of (x, y, w, h) regions to draw as exclusion zones

        Returns:
            PIL Image with overlays, or None if no screenshot available
        """
        if self._last_screenshot is None:
            return None

        # Create a copy to draw on
        img = self._last_screenshot.copy()
        draw = ImageDraw.Draw(img)

        # Draw ROI exclusion zones (semi-transparent red overlay)
        if roi_exclusions:
            for exclusion in roi_exclusions:
                x_offset = self._last_region[0] if self._last_region else 0
                y_offset = self._last_region[1] if self._last_region else 0

                ex, ey, ew, eh = exclusion
                ex -= x_offset
                ey -= y_offset

                # Draw hatched pattern for exclusion zone
                for i in range(ey, ey + eh, 10):
                    draw.line([(ex, i), (ex + ew, i)], fill="red", width=1)
                for i in range(ex, ex + ew, 10):
                    draw.line([(i, ey), (i, ey + eh)], fill="red", width=1)

                # Draw border
                draw.rectangle(
                    [ex, ey, ex + ew, ey + eh],
                    outline="red",
                    width=2
                )

        # Draw bounding boxes around matches (green)
        for match in matches:
            # Adjust coordinates if we're working with a region
            x_offset = self._last_region[0] if self._last_region else 0
            y_offset = self._last_region[1] if self._last_region else 0

            left = match.left - x_offset
            top = match.top - y_offset
            right = left + match.width
            bottom = top + match.height

            # Draw rectangle (green, 3px width)
            draw.rectangle(
                [left, top, right, bottom],
                outline="green",
                width=3
            )

            # Draw center cross
            cx, cy = match.center
            cx -= x_offset
            cy -= y_offset
            cross_size = 10
            draw.line(
                [(cx - cross_size, cy), (cx + cross_size, cy)],
                fill="green",
                width=2
            )
            draw.line(
                [(cx, cy - cross_size), (cx, cy + cross_size)],
                fill="green",
                width=2
            )

        # Draw click location (red crosshair)
        if click_coords:
            x_offset = self._last_region[0] if self._last_region else 0
            y_offset = self._last_region[1] if self._last_region else 0

            cx = click_coords[0] - x_offset
            cy = click_coords[1] - y_offset

            # Draw larger red crosshair for click location
            cross_size = 20
            draw.line(
                [(cx - cross_size, cy), (cx + cross_size, cy)],
                fill="red",
                width=4
            )
            draw.line(
                [(cx, cy - cross_size), (cx, cy + cross_size)],
                fill="red",
                width=4
            )

            # Draw circle around click point
            circle_radius = 15
            draw.ellipse(
                [cx - circle_radius, cy - circle_radius,
                 cx + circle_radius, cy + circle_radius],
                outline="red",
                width=3
            )

        return img
