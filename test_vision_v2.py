"""
Test script to verify v2 (color detection) vision implementation.
"""

from src.core.config import BotConfig
from src.core.logger import Logger
from src.vision import MonitorManager, ScreenCapture, ImageMatcher, TargetFinder


def test_vision_v2():
    """Test v2 color detection on a screenshot."""
    print("=" * 60)
    print("Testing Vision v2 (Color Detection)")
    print("=" * 60)
    print()

    # Load config
    print("Loading config...")
    config = BotConfig.from_json("config.json")
    config.debug = True  # Enable debug mode for testing
    config.validate()
    print(f"Vision method: {config.vision_method}")
    print()

    # Initialize components
    print("Initializing vision components...")
    logger = Logger(debug=True)
    monitor_manager = MonitorManager(logger)
    screen_capture = ScreenCapture(logger, debug=True)
    image_matcher = ImageMatcher(logger, debug=True)

    target_finder = TargetFinder(
        image_matcher,
        screen_capture,
        monitor_manager,
        logger,
        vision_method=config.vision_method,
    )
    print()

    # Test finding stones
    print("Searching for stones with v2 (color detection)...")
    stones = target_finder.find_stones(
        stone_names=config.stone_names,  # Not used in v2, but required for API compatibility
        monitor_index=config.monitor_index,
    )
    print(f"Found {len(stones)} stones")
    print()

    if stones:
        print("Stone details:")
        for i, stone in enumerate(stones, 1):
            print(f"  Stone #{i}:")
            print(f"    Center: {stone.center}")
            print(f"    Area: {stone.area:.0f} pixels")
            print(f"    Bounding Box: {stone.bbox}")
        print()

        # Test finding closest stone
        print("Finding closest stone to screen center...")
        from screeninfo import get_monitors

        monitors = get_monitors()
        primary = monitors[0] if monitors else None
        if primary:
            center_x = primary.width // 2
            center_y = primary.height // 2
        else:
            center_x, center_y = 960, 540

        print(f"Screen center: ({center_x}, {center_y})")

        closest = target_finder.calculate_closest_target(
            matches=stones,
            center_x=center_x,
            center_y=center_y,
            aspect_ratio=1.78,
            offset_x=config.offset_x,
            offset_y=config.offset_y,
        )
        print(f"Closest stone: coords={closest.coords}, distance={closest.distance:.2f}")
        print()

    print("=" * 60)
    print("Test completed! Check debug/ folder for annotated images.")
    print("=" * 60)


def test_vision_v1():
    """Test v1 template matching for comparison."""
    print("=" * 60)
    print("Testing Vision v1 (Template Matching)")
    print("=" * 60)
    print()

    # Load config and force v1
    print("Loading config...")
    config = BotConfig.from_json("config.json")
    config.debug = True
    config.vision_method = "v1"
    config.validate()
    print(f"Vision method: {config.vision_method}")
    print()

    # Initialize components
    print("Initializing vision components...")
    logger = Logger(debug=True)
    monitor_manager = MonitorManager(logger)
    screen_capture = ScreenCapture(logger, debug=True)
    image_matcher = ImageMatcher(logger, debug=True)

    target_finder = TargetFinder(
        image_matcher,
        screen_capture,
        monitor_manager,
        logger,
        vision_method=config.vision_method,
    )
    print()

    # Test finding stones
    print("Searching for stones with v1 (template matching)...")
    stones = target_finder.find_stones(
        stone_names=config.stone_names,
        monitor_index=config.monitor_index,
    )
    print(f"Found {len(stones)} stones")
    print()

    if stones:
        print("Stone details:")
        for i, stone in enumerate(stones, 1):
            print(f"  Stone #{i}:")
            print(f"    Position: ({stone.left}, {stone.top})")
            print(f"    Confidence: {stone.confidence:.2f}")
        print()

    print("=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    import sys

    # Test v2 by default
    if len(sys.argv) > 1 and sys.argv[1] == "v1":
        test_vision_v1()
    else:
        test_vision_v2()
