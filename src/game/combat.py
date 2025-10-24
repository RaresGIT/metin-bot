"""Combat logic and stuck detection."""
import time
from typing import Optional, List

from ..core.state import BotState
from ..core.logger import Logger
from ..core.config import BotConfig
from ..input.input_manager import InputManager
from ..vision.target_finder import Target
from ..vision.image_matcher import ImageMatch
from .movement import MovementController


class CombatController:
    """Manages combat operations."""

    def __init__(
        self,
        state: BotState,
        input_manager: InputManager,
        movement: MovementController,
        logger: Logger,
        config: BotConfig,
        max_stuck_iterations: int = 3,
        max_seconds_stuck: float = 1.0,
    ):
        self.state = state
        self.input_manager = input_manager
        self.movement = movement
        self.logger = logger
        self.config = config
        self.max_stuck_iterations = max_stuck_iterations
        self.max_seconds_stuck = max_seconds_stuck

    def attack_target(self, target: Target) -> None:
        """
        Attack a target.

        Args:
            target: Target object with coordinates and distance
        """
        self.logger.info(f"Attacking target at {target.coords}")
        self.input_manager.attack_target(target.coords)
        self.state.select_target(target.coords, target.distance)
        self.logger.debug(f"Target selected at {time.time()}")

        # Pause after selecting target
        if self.config.wait_after_select > 0:
            self.logger.debug(f"Pausing for {self.config.wait_after_select}s after target selection")
            time.sleep(self.config.wait_after_select)

    def handle_pickup(self, pickup_enabled: bool, pickup_key: str = "z") -> None:
        """
        Handle item pickup after combat.

        Args:
            pickup_enabled: Whether pickup is enabled
            pickup_key: Key to press for pickup
        """
        if not pickup_enabled:
            return

        self.logger.debug("Handling item pickup")
        self.input_manager.pickup_items(pickup_key)

    def check_combat_finished_timer(self, wait_time: float, pickup_enabled: bool) -> bool:
        """
        Check if combat is finished using timer-based mode.

        Args:
            wait_time: How long to wait after attacking
            pickup_enabled: Whether to pickup items

        Returns:
            True if combat is finished
        """
        if not self.state.is_target_selected():
            return True

        elapsed = self.state.time_since_target_selected()

        if elapsed >= wait_time:
            self.logger.debug(
                f"Timer-based: Combat finished ({elapsed:.2f}s >= {wait_time}s)"
            )
            self.state.clear_target()
            self.handle_pickup(pickup_enabled)
            return True

        self.logger.debug(
            f"Timer-based: Waiting for combat ({elapsed:.2f}s / {wait_time}s)"
        )
        return False

    def check_combat_finished_ui(
        self,
        hp_bar: Optional[ImageMatch],
        top_bar: Optional[ImageMatch],
        pickup_enabled: bool,
        center_x: int,
        center_y: int,
    ) -> bool:
        """
        Check if combat is finished using UI detection.

        Args:
            hp_bar: HP bar match (if found)
            top_bar: Top bar match (if found)
            pickup_enabled: Whether to pickup items
            center_x: Screen center X for unstuck logic
            center_y: Screen center Y for unstuck logic

        Returns:
            True if we should look for new targets
        """
        # Combat finished - top bar disappeared
        if top_bar is None:
            if self.state.is_target_selected():
                self.logger.debug("UI-based: Top bar disappeared, combat finished")
                self.state.clear_target()
                self.handle_pickup(pickup_enabled)
            return True

        # Still in combat - check for stuck
        if top_bar is not None and hp_bar is not None and self.state.is_target_selected():
            elapsed = self.state.time_since_target_selected()

            if elapsed > self.max_seconds_stuck:
                self.logger.warning(f"Stuck detected! Time elapsed: {elapsed:.2f}s")
                self.movement.unstuck(
                    self.state.last_selected.coords, center_x, center_y
                )
                self.state.increment_stuck_iterations()
                self.logger.info(
                    f"Unstuck attempt {self.state.stuck_for_iterations}/{self.max_stuck_iterations}"
                )

                # Max unstuck attempts reached
                if self.state.stuck_for_iterations >= self.max_stuck_iterations:
                    self.logger.warning(
                        f"Max stuck iterations reached ({self.max_stuck_iterations}), giving up"
                    )
                    self.input_manager.cancel_target()
                    self.movement.move_camera_and_search()
                    self.state.reset_stuck_iterations()
                    return True

        return False

    def should_attack(
        self, targets_found: int, top_bar: Optional[ImageMatch], timer_mode: bool
    ) -> bool:
        """
        Check if we should attack a new target.

        Args:
            targets_found: Number of targets visible
            top_bar: Top bar UI element (for UI mode)
            timer_mode: Whether using timer-based mode

        Returns:
            True if we should attack
        """
        # No targets found
        if targets_found == 0:
            return False

        # Already have a target
        if self.state.is_target_selected():
            return False

        # Timer mode - can always attack if no target selected
        if timer_mode:
            return True

        # UI mode - only attack if not in combat (no top bar)
        return top_bar is None
