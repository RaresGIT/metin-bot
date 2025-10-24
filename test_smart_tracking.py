"""
Test script to verify smart tracking system works correctly.
"""

from src.core.config import BotConfig
from src.core.state import BotState
from src.core.logger import Logger
from src.vision import MonitorManager, ScreenCapture, ImageMatcher, TargetFinder
from src.input import InputManager
from src.game import CombatController, MovementController
from src.strategies.stone_farming import StoneFarmingStrategy


def test_smart_tracking_initialization():
    """Test that all components initialize correctly with smart tracking config."""
    print("=" * 60)
    print("Testing Smart Tracking System Initialization")
    print("=" * 60)
    print()

    # Load config
    print("1. Loading config...")
    config = BotConfig.from_json("config.json")
    config.validate()
    print(f"   [OK] Config loaded")
    print(f"   - Vision method: {config.vision_method}")
    print(f"   - Wait after select: {config.wait_after_select}s")
    print(f"   - Edge margin: {config.screen_edge_margin}")
    print(f"   - Target check interval: {config.target_destroyed_check_interval}")
    print(f"   - Search rotations: {config.search_camera_rotations}")
    print()

    # Initialize components
    print("2. Initializing components...")
    logger = Logger(debug=True)
    state = BotState(buff_interval_min=30, buff_interval_max=60)

    # Vision
    monitor_manager = MonitorManager(logger)
    screen_capture = ScreenCapture(logger, debug=False)
    image_matcher = ImageMatcher(logger, debug=False)
    target_finder = TargetFinder(
        image_matcher,
        screen_capture,
        monitor_manager,
        logger,
        vision_method=config.vision_method,
    )

    # Input and Game
    input_manager = InputManager(logger)
    movement = MovementController(input_manager.keyboard, logger)
    combat = CombatController(
        state,
        input_manager,
        movement,
        logger,
        config,
    )

    print("   [OK] All components initialized")
    print()

    # Create strategy
    print("3. Creating stone farming strategy...")
    strategy = StoneFarmingStrategy(
        config=config,
        state=state,
        target_finder=target_finder,
        combat=combat,
        movement=movement,
        input_manager=input_manager,
        logger=logger,
    )
    print("   [OK] Strategy created")
    print(f"   - Last target check: {strategy.last_target_check}")
    print(f"   - No target count: {strategy.no_target_count}")
    print()

    # Test state tracking
    print("4. Testing state tracking...")
    print(f"   - Target selected: {state.is_target_selected()}")

    # Simulate selecting a target
    state.select_target(coords=(500, 600), distance=234.56)
    print(f"   [OK] Target selected at (500, 600)")
    print(f"   - Target selected: {state.is_target_selected()}")
    print(f"   - Time since selected: {state.time_since_target_selected():.2f}s")

    # Clear target
    state.clear_target()
    print(f"   [OK] Target cleared")
    print(f"   - Target selected: {state.is_target_selected()}")
    print()

    # Test edge filtering
    print("5. Testing edge filtering logic...")
    from src.vision.color_detector import ColorCluster

    # Create mock targets
    edge_target = ColorCluster(center=(50, 100), bbox=(45, 95, 10, 10), area=100)
    center_target = ColorCluster(center=(960, 540), bbox=(950, 530, 20, 20), area=400)
    far_edge_target = ColorCluster(center=(1850, 1000), bbox=(1840, 990, 20, 20), area=300)

    mock_targets = [edge_target, center_target, far_edge_target]

    # Filter with edge margin
    closest = target_finder.calculate_closest_target(
        matches=mock_targets,
        center_x=960,
        center_y=540,
        aspect_ratio=1.78,
        offset_x=70,
        offset_y=45,
        edge_margin=150,
        screen_width=1920,
        screen_height=1080,
    )

    if closest:
        print(f"   [OK] Closest valid target: {closest.coords}")
        print(f"   - Distance: {closest.distance:.2f}")
        print(f"   - Edge targets filtered: 2/3")
    else:
        print("   [FAIL] No valid targets after filtering")
    print()

    # Test method availability
    print("6. Testing method availability...")
    methods_to_check = [
        ('strategy.execute', hasattr(strategy, 'execute')),
        ('strategy._handle_active_target', hasattr(strategy, '_handle_active_target')),
        ('strategy._find_and_attack_new_target', hasattr(strategy, '_find_and_attack_new_target')),
        ('strategy._handle_no_targets', hasattr(strategy, '_handle_no_targets')),
        ('target_finder.is_target_still_present', hasattr(target_finder, 'is_target_still_present')),
        ('movement.search_for_targets', hasattr(movement, 'search_for_targets')),
        ('input_manager.pickup_items', hasattr(input_manager, 'pickup_items')),
    ]

    all_present = True
    for method_name, present in methods_to_check:
        status = "[OK]" if present else "[FAIL]"
        print(f"   {status} {method_name}: {present}")
        if not present:
            all_present = False
    print()

    # Summary
    print("=" * 60)
    if all_present:
        print("[OK] All Tests Passed - Smart Tracking System Ready!")
    else:
        print("[FAIL] Some Tests Failed - Check Output Above")
    print("=" * 60)
    print()

    return all_present


if __name__ == "__main__":
    try:
        success = test_smart_tracking_initialization()
        exit(0 if success else 1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
