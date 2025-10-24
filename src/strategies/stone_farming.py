"""Stone farming strategy implementation."""
import time
from typing import Optional

import pyautogui

from .base import BotStrategy
from ..core.config import BotConfig
from ..core.state import BotState
from ..core.logger import Logger
from ..vision.target_finder import TargetFinder
from ..game.combat import CombatController
from ..game.movement import MovementController
from ..input.input_manager import InputManager


class StoneFarmingStrategy(BotStrategy):
    """Strategy for farming metin stones."""

    def __init__(
        self,
        config: BotConfig,
        state: BotState,
        target_finder: TargetFinder,
        combat: CombatController,
        movement: MovementController,
        input_manager: InputManager,
        logger: Logger,
    ):
        self.config = config
        self.state = state
        self.target_finder = target_finder
        self.combat = combat
        self.movement = movement
        self.input_manager = input_manager
        self.logger = logger
        self.last_target_check = 0.0  # Last time we checked if target still exists
        self.no_target_count = 0  # Count consecutive iterations with no targets

        # Pathfinding unstuck tracking
        self.last_cluster_positions = []  # Track cluster positions to detect stuck
        self.last_position_change_time = time.time()  # When positions last changed

    def execute(self) -> None:
        """Execute one iteration of stone farming with smart target tracking."""
        # Check for UI pause (inventory open)
        if self._check_ui_pause():
            return

        # Check if we have an active target
        if self.state.is_target_selected():
            self._handle_active_target()
        else:
            self._find_and_attack_new_target()

    def _handle_active_target(self) -> None:
        """Handle ongoing combat with current target."""
        current_time = time.time()

        # Reset position tracking while in combat (not pathfinding)
        self.last_cluster_positions = []
        self.last_position_change_time = current_time

        # Periodically check if target still exists
        if current_time - self.last_target_check >= self.config.target_destroyed_check_interval:
            self.last_target_check = current_time

            target_coords = self.state.last_selected.coords
            still_present = self.target_finder.is_target_still_present(
                target_coords=target_coords,
                stone_names=self.config.stone_names,
                monitor_index=self.config.monitor_index,
                tolerance=50,
            )

            if not still_present:
                self.logger.info("Target destroyed! Searching for new target...")
                self.state.clear_target()

                # Pickup drops if enabled
                if self.config.pickup_drop:
                    time.sleep(0.5)
                    self.input_manager.pickup_items()
                    time.sleep(0.5)

                # Reset no-target counter
                self.no_target_count = 0
            else:
                if self.config.debug:
                    elapsed = self.state.time_since_target_selected()
                    self.logger.debug(f"Target still present, combat ongoing ({elapsed:.1f}s)")

    def _find_and_attack_new_target(self) -> None:
        """Find and attack a new target."""
        # Search for stones
        stones = self.target_finder.find_stones(
            stone_names=self.config.stone_names,
            monitor_index=self.config.monitor_index,
        )

        stones_found = len(stones) if stones else 0

        if stones_found > 0:
            if self.config.debug:
                self.logger.debug(f"Found {stones_found} stone(s)")

            # Check if we're stuck (clusters not changing position)
            if self._check_pathfinding_stuck(stones):
                return  # Unstuck was performed, return early

            # Filter out edge targets and find closest
            target = self.target_finder.calculate_closest_target(
                matches=stones,
                center_x=self.config.center_x,
                center_y=self.config.center_y,
                aspect_ratio=self.config.aspect_ratio,
                offset_x=self.config.offset_x,
                offset_y=self.config.offset_y,
                edge_margin=self.config.screen_edge_margin,
            )

            if target:
                self.logger.info(f"Attacking new target at {target.coords}")
                self.combat.attack_target(target)
                self.no_target_count = 0
            else:
                if self.config.debug:
                    self.logger.debug("All targets filtered out (too close to edges)")
                self._handle_no_targets()
        else:
            self._handle_no_targets()

    def _check_pathfinding_stuck(self, stones) -> bool:
        """
        Check if player is stuck while pathfinding to stones.
        Returns True if unstuck was performed, False otherwise.

        Args:
            stones: List of detected stone clusters

        Returns:
            True if unstuck was performed
        """
        from ..vision.color_detector import ColorCluster
        from ..vision.image_matcher import ImageMatch

        # Extract positions from stones (works for both v1 and v2)
        current_positions = []
        for stone in stones:
            if isinstance(stone, ColorCluster):
                current_positions.append(stone.center)
            elif isinstance(stone, ImageMatch):
                current_positions.append((stone.left, stone.top))

        # Check if positions have changed significantly
        positions_changed = self._have_positions_changed(
            current_positions, self.last_cluster_positions, threshold=50
        )

        current_time = time.time()

        if positions_changed:
            # Positions changed, reset tracking
            self.last_cluster_positions = current_positions
            self.last_position_change_time = current_time
            return False

        # Positions haven't changed, check timeout
        time_stuck = current_time - self.last_position_change_time

        if time_stuck >= self.config.unstuck_timeout:
            # We're stuck! Perform unstuck
            self.logger.warning(
                f"Stuck detected! Cluster positions unchanged for {time_stuck:.1f}s "
                f"(threshold: {self.config.unstuck_timeout}s)"
            )
            self.movement.unstuck_pathfinding()

            # Reset tracking after unstuck
            self.last_cluster_positions = []
            self.last_position_change_time = current_time
            return True

        # Not stuck yet, but positions haven't changed
        if self.config.debug:
            self.logger.debug(
                f"Positions unchanged for {time_stuck:.1f}s/{self.config.unstuck_timeout}s"
            )
        return False

    def _have_positions_changed(self, current_positions, last_positions, threshold=50) -> bool:
        """
        Check if cluster positions have changed significantly.

        Args:
            current_positions: List of current (x, y) positions
            last_positions: List of previous (x, y) positions
            threshold: Distance threshold in pixels

        Returns:
            True if positions have changed significantly
        """
        # If different number of clusters, positions changed
        if len(current_positions) != len(last_positions):
            return True

        # If no previous positions, consider it changed
        if not last_positions:
            return True

        # Sort both lists to match corresponding positions
        current_sorted = sorted(current_positions)
        last_sorted = sorted(last_positions)

        # Check if any position moved more than threshold
        for (cx, cy), (lx, ly) in zip(current_sorted, last_sorted):
            distance = ((cx - lx) ** 2 + (cy - ly) ** 2) ** 0.5
            if distance > threshold:
                return True

        return False

    def _handle_no_targets(self) -> None:
        """Handle situation when no targets are found."""
        self.no_target_count += 1

        # Reset position tracking when no targets found
        self.last_cluster_positions = []
        self.last_position_change_time = time.time()

        if self.no_target_count >= 3:
            # After 3 consecutive no-target iterations, do comprehensive search
            self.logger.info("No targets found, performing search...")

            # Create a callback that checks for stones after each rotation
            def check_for_stones() -> bool:
                """Check if any stones are visible. Returns True if found."""
                stones = self.target_finder.find_stones(
                    stone_names=self.config.stone_names,
                    monitor_index=self.config.monitor_index,
                )

                if stones:
                    # Filter out edge targets
                    target = self.target_finder.calculate_closest_target(
                        matches=stones,
                        center_x=self.config.center_x,
                        center_y=self.config.center_y,
                        aspect_ratio=self.config.aspect_ratio,
                        offset_x=self.config.offset_x,
                        offset_y=self.config.offset_y,
                        edge_margin=self.config.screen_edge_margin,
                    )

                    if target:
                        if self.config.debug:
                            self.logger.debug(f"Found stone during search at {target.coords}")
                        # Attack the target immediately
                        self.combat.attack_target(target)
                        self.no_target_count = 0
                        return True

                return False

            # Perform search with callback - will stop early if stones found
            found = self.movement.search_for_targets(
                num_rotations=self.config.search_camera_rotations,
                move_forward_time=self.config.search_move_forward_time,
                check_callback=check_for_stones,
            )

            # If search completed without finding anything, reset counter
            if not found:
                self.no_target_count = 0
        else:
            # Quick camera rotation
            if self.config.debug:
                self.logger.debug("No targets, rotating camera")
            self.movement.rotate_camera(duration=0.5)
            time.sleep(0.3)

    def _check_ui_pause(self) -> bool:
        """
        Check if UI is open and should pause bot.

        Returns:
            True if paused
        """
        try:
            ui_element = self.target_finder.find_ui_element(
                element_name="on_screen_check",
                monitor_index=self.config.monitor_index,
            )

            if ui_element is not None:
                if self.config.debug:
                    self.logger.debug("UI pause detected (inventory/UI open)")
                self.logger.info("Inventory on screen, pausing. Retrying in 1s")
                time.sleep(1)
                return True

        except pyautogui.ImageNotFoundException:
            if self.config.debug:
                self.logger.debug("UI pause check: not found, continuing")

        return False

    def _farm_stones_timer_mode(self, stones: list) -> None:
        """
        Farm stones using timer-based mode.

        Args:
            stones: List of stone matches
        """
        stones_found = len(stones)

        if self.config.debug:
            self.logger.debug(f"Timer mode: {stones_found} stones found")

        # Check if current combat is finished
        if self.combat.check_combat_finished_timer(
            wait_time=self.config.wait_after_select,
            pickup_enabled=self.config.pickup_drop,
        ):
            # Ready for new target
            if stones_found > 0:
                if self.config.debug:
                    self.logger.debug(f"Ready to attack! {stones_found} stone(s) visible")

                target = self.target_finder.calculate_closest_target(
                    matches=stones,
                    center_x=self.config.center_x,
                    center_y=self.config.center_y,
                    aspect_ratio=self.config.aspect_ratio,
                    offset_x=self.config.offset_x,
                    offset_y=self.config.offset_y,
                )
                self.combat.attack_target(target)
            else:
                if self.config.debug:
                    self.logger.debug("No stones found, moving camera")
                self.movement.move_camera_and_search()

    def _farm_stones_ui_mode(self, stones: list) -> None:
        """
        Farm stones using UI detection mode.

        Args:
            stones: List of stone matches
        """
        stones_found = len(stones)

        if self.config.debug:
            self.logger.debug(f"UI mode: {stones_found} stones found")

        # Check combat UI
        hp_bar, top_bar = self.target_finder.find_combat_ui(
            monitor_index=self.config.monitor_index
        )

        # Check if combat is finished or handle stuck
        if self.combat.check_combat_finished_ui(
            hp_bar=hp_bar,
            top_bar=top_bar,
            pickup_enabled=self.config.pickup_drop,
            center_x=self.config.center_x,
            center_y=self.config.center_y,
        ):
            # Ready for new target
            if self.combat.should_attack(stones_found, top_bar, timer_mode=False):
                if self.config.debug:
                    self.logger.debug(f"Ready to attack! {stones_found} stone(s) visible")

                target = self.target_finder.calculate_closest_target(
                    matches=stones,
                    center_x=self.config.center_x,
                    center_y=self.config.center_y,
                    aspect_ratio=self.config.aspect_ratio,
                    offset_x=self.config.offset_x,
                    offset_y=self.config.offset_y,
                )
                self.combat.attack_target(target)
            elif stones_found == 0 and top_bar is None:
                if self.config.debug:
                    self.logger.debug("No stones found, moving camera")
                self.movement.move_camera_and_search()
            else:
                if self.config.debug:
                    self.logger.debug(
                        f"Waiting: top_bar={top_bar is not None}, "
                        f"stones={stones_found}, selected={self.state.is_target_selected()}"
                    )

    def should_continue(self) -> bool:
        """Check if the strategy should continue running."""
        # Check exit key
        if self.input_manager.check_exit_key():
            self.logger.info("Exit key pressed")
            self.state.stop()
            return False

        # Check deadline
        elapsed_hours = self.state.elapsed_hours()
        if elapsed_hours >= self.config.deadline:
            self.logger.info(
                f"Deadline reached! Elapsed: {elapsed_hours:.2f}h / {self.config.deadline}h"
            )
            self.state.stop()
            return False

        return self.state.is_running

    def cleanup(self) -> None:
        """Cleanup when strategy is stopped."""
        self.logger.info("Stone farming strategy stopped")
