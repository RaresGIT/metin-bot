"""
Experimental script for detecting orange clusters (metin stones) in screenshots.
Uses color-based detection in HSV color space to identify orange/yellow glowing objects.
"""

import cv2
import numpy as np
from datetime import datetime
import os


def detect_orange_clusters(image_path: str, output_path: str = None) -> None:
    """
    Detect orange/yellow clusters in an image and export annotated result.

    Args:
        image_path: Path to input image
        output_path: Path to save output image (optional, auto-generated if None)
    """
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image from {image_path}")

    print(f"Image loaded: {image.shape[1]}x{image.shape[0]} pixels")

    # Convert to HSV color space (better for color detection)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define range for orange/yellow colors (metin stones glow)
    # Hue: 10-35 (orange to yellow)
    # Saturation: 100-255 (vibrant colors)
    # Value: 150-255 (bright)
    lower_orange = np.array([10, 100, 150])
    upper_orange = np.array([35, 255, 255])

    # Create mask for orange colors
    mask = cv2.inRange(hsv, lower_orange, upper_orange)

    # Apply morphological operations to clean up the mask
    # Remove noise with opening (erosion followed by dilation)
    kernel_small = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel_small, iterations=2)

    # Close gaps with closing (dilation followed by erosion)
    kernel_large = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_large, iterations=2)

    # Find contours (clusters)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print(f"Found {len(contours)} orange clusters")

    # Create output image with annotations
    annotated = image.copy()

    # Filter and annotate clusters with shape analysis
    valid_clusters = []
    rejected_clusters = []

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)

        # Filter out very small clusters (noise)
        if area < 50:
            continue

        # Calculate circularity (how round/circular the shape is)
        perimeter = cv2.arcLength(contour, True)
        if perimeter == 0:
            continue

        # Circularity formula: 4π * area / perimeter²
        # Perfect circle = 1.0, square ≈ 0.785, irregular shapes < 0.5
        circularity = 4 * np.pi * area / (perimeter * perimeter)

        # Calculate aspect ratio (width/height ratio)
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h if h > 0 else 0

        # Fit ELLIPSE instead of circle to better match stone shapes
        if len(contour) >= 5:  # Need at least 5 points to fit ellipse
            ellipse = cv2.fitEllipse(contour)
            (ellipse_cx, ellipse_cy), (ellipse_width, ellipse_height), angle = ellipse
            ellipse_area = np.pi * (ellipse_width / 2) * (ellipse_height / 2)

            # Extent: how well the shape fills its ellipse (better than circle for ovals)
            extent = float(area) / ellipse_area if ellipse_area > 0 else 0

            # Ellipse aspect ratio (width/height of the fitted ellipse)
            ellipse_aspect = max(ellipse_width, ellipse_height) / min(ellipse_width, ellipse_height) if min(ellipse_width, ellipse_height) > 0 else 1.0

            # Normalize angle to 0-180 range
            normalized_angle = angle % 180

            # Check if ellipse is roughly horizontal
            # Horizontal: 90° ± 25° (75-115°) allowing some tolerance
            # Reject vertical or diagonal ellipses
            is_horizontal = (75 <= normalized_angle <= 115)

            # Store ellipse info for visualization
            has_ellipse = True
            ellipse_params = ellipse
            ellipse_angle = normalized_angle
        else:
            # Fallback to circle if not enough points for ellipse
            (circle_x, circle_y), radius = cv2.minEnclosingCircle(contour)
            circle_area = np.pi * (radius ** 2)
            extent = float(area) / circle_area if circle_area > 0 else 0
            ellipse_aspect = 1.0
            is_horizontal = True  # Assume horizontal for circles
            has_ellipse = False
            ellipse_params = None
            ellipse_angle = 0

        # Get center point
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = x + w // 2, y + h // 2

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

        # Thresholds tuned for ELLIPTICAL stone-like shapes
        MIN_CIRCULARITY = 0.25  # Lower for ellipses (was 0.4 for circles)
        MIN_SHAPE_SCORE = 0.45   # Slightly lower for ellipses (was 0.5)
        MIN_EXTENT = 0.45        # Must fill at least 45% of ellipse (was 50% of circle)
        MAX_ELLIPSE_ASPECT = 3.0  # Allow more elongation (ellipses can be 3:1)

        is_elliptical = (
            circularity >= MIN_CIRCULARITY and
            shape_score >= MIN_SHAPE_SCORE and
            extent >= MIN_EXTENT and
            ellipse_aspect <= MAX_ELLIPSE_ASPECT and
            is_horizontal  # MUST be horizontal (not vertical/diagonal)
        )

        cluster_info = {
            "id": len(valid_clusters) + 1 if is_elliptical else -(len(rejected_clusters) + 1),
            "center": (cx, cy),
            "bbox": (x, y, w, h),
            "area": area,
            "circularity": circularity,
            "aspect_ratio": aspect_ratio,
            "ellipse_aspect": ellipse_aspect,
            "extent": extent,
            "shape_score": shape_score,
            "is_elliptical": is_elliptical,
            "is_horizontal": is_horizontal,
            "has_ellipse": has_ellipse,
            "ellipse_params": ellipse_params,
            "ellipse_angle": ellipse_angle,
            "compactness": compactness
        }

        if is_elliptical:
            valid_clusters.append(cluster_info)
        else:
            rejected_clusters.append(cluster_info)

        # Color coding: Green = valid (elliptical), Red = rejected (non-elliptical)
        color = (0, 255, 0) if is_elliptical else (0, 0, 255)
        thickness = 2 if is_elliptical else 1

        # Draw bounding box
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, thickness)

        # Draw fitted ellipse for valid clusters
        if is_elliptical and has_ellipse:
            cv2.ellipse(annotated, ellipse_params, (255, 0, 255), 1)

        # Draw center point
        cv2.circle(annotated, (cx, cy), 3, color, -1)

        # Draw crosshair at center for valid clusters
        if is_elliptical:
            cv2.line(annotated, (cx - 15, cy), (cx + 15, cy), (0, 0, 255), 2)
            cv2.line(annotated, (cx, cy - 15), (cx, cy + 15), (0, 0, 255), 2)

        # Add label with shape info
        if is_elliptical:
            label = f"#{cluster_info['id']} | E:{ellipse_aspect:.1f} A:{ellipse_angle:.0f}° S:{shape_score:.2f}"
        else:
            reject_reason = ""
            if not is_horizontal:
                reject_reason = f"angle:{ellipse_angle:.0f}°"
            elif circularity < MIN_CIRCULARITY:
                reject_reason = f"C:{circularity:.2f}"
            elif shape_score < MIN_SHAPE_SCORE:
                reject_reason = f"S:{shape_score:.2f}"
            label = f"X#{abs(cluster_info['id'])} | {reject_reason}"

        # Position label above bounding box
        label_y = y - 10 if y > 30 else y + h + 20
        cv2.putText(annotated, label, (x, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    print(f"Valid elliptical clusters: {len(valid_clusters)}")
    print(f"Rejected non-elliptical clusters: {len(rejected_clusters)}")

    # Add summary text at the top
    summary = f"Elliptical Stones: {len(valid_clusters)} | Rejected: {len(rejected_clusters)}"
    cv2.putText(annotated, summary, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Generate output path if not provided
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "debug"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{timestamp}_orange_clusters_annotated.png")

    # Save annotated image
    cv2.imwrite(output_path, annotated)
    print(f"Annotated image saved to: {output_path}")

    # Also save the mask for debugging
    mask_path = output_path.replace("_annotated.png", "_mask.png")
    cv2.imwrite(mask_path, mask)
    print(f"Detection mask saved to: {mask_path}")

    # Print cluster information
    print("\n" + "=" * 80)
    print("VALID ELLIPTICAL CLUSTERS (Stones)")
    print("=" * 80)
    for cluster in valid_clusters:
        print(f"Cluster #{cluster['id']}:")
        print(f"  Center: {cluster['center']}")
        print(f"  Bounding Box: {cluster['bbox']}")
        print(f"  Area: {cluster['area']:.0f} pixels")
        if cluster['has_ellipse']:
            print(f"  Ellipse Aspect: {cluster['ellipse_aspect']:.2f} (1.0 = circle, >1 = elongated)")
            print(f"  Ellipse Angle: {cluster['ellipse_angle']:.1f}° (horizontal: 75-115°)")
        print(f"  Circularity: {cluster['circularity']:.3f} (1.0 = perfect circle)")
        print(f"  Aspect Ratio: {cluster['aspect_ratio']:.2f} (1.0 = perfect square)")
        print(f"  Extent: {cluster['extent']:.2f} (fills {cluster['extent']*100:.0f}% of ellipse)")
        print(f"  Shape Score: {cluster['shape_score']:.3f} (overall elliptical quality)")
        print()

    if rejected_clusters:
        print("=" * 80)
        print("REJECTED NON-ELLIPTICAL CLUSTERS (Not stones)")
        print("=" * 80)
        for cluster in rejected_clusters:
            print(f"Cluster X#{abs(cluster['id'])}:")
            print(f"  Center: {cluster['center']} | Area: {cluster['area']:.0f}px")
            print(f"  Why rejected:")
            if not cluster['is_horizontal']:
                print(f"    - Not horizontal (angle: {cluster['ellipse_angle']:.1f}° - must be 75-115°)")
            if cluster['circularity'] < MIN_CIRCULARITY:
                print(f"    - Too irregular (circularity: {cluster['circularity']:.3f} < {MIN_CIRCULARITY})")
            if cluster['shape_score'] < MIN_SHAPE_SCORE:
                print(f"    - Low shape score: {cluster['shape_score']:.3f} < {MIN_SHAPE_SCORE}")
            if cluster['extent'] < MIN_EXTENT:
                print(f"    - Doesn't fill ellipse (extent: {cluster['extent']:.2f} < {MIN_EXTENT})")
            if cluster['ellipse_aspect'] > MAX_ELLIPSE_ASPECT:
                print(f"    - Too elongated (ellipse aspect: {cluster['ellipse_aspect']:.2f} > {MAX_ELLIPSE_ASPECT})")
            print()

    return valid_clusters


def main():
    """Main entry point for the script."""
    # Input image path
    input_image = "Screenshot_5.png"

    print("=" * 60)
    print("Orange Cluster Detection - Experimental Script")
    print("=" * 60)
    print()

    try:
        clusters = detect_orange_clusters(input_image)
        print("\n" + "=" * 60)
        print(f"Success! Found {len(clusters)} orange clusters.")
        print("=" * 60)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
