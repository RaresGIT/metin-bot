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

    def execute(self) -> None:
        """Execute one iteration of stone farming."""
        # Check for UI pause (inventory open)
        if self._check_ui_pause():
            return

        # Search for stones using COLOR-BASED detection
        # Determine color from stone name (pumpkin = orange)
        color = 'orange' if 'pumpkin' in str(self.config.stone_names).lower() else 'orange'

        from ..vision.color_target_finder import ColorTargetFinder
        color_finder = ColorTargetFinder(
            self.target_finder.screen_capture,
            self.target_finder.monitor_manager,
            self.logger,
            debug=self.config.debug
        )

        stones = color_finder.find_by_color(
            color_name=color,
            monitor_index=self.config.monitor_index,
            min_area=100,
            max_area=10000,
        )

        # Farm stones using appropriate mode
        if self.config.wait_after_stone_destroyed > 0:
            self._farm_stones_timer_mode(stones)
        else:
            self._farm_stones_ui_mode(stones)

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
            wait_time=self.config.wait_after_stone_destroyed,
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
