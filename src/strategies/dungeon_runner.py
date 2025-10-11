"""Dungeon running strategy implementation."""
import time

from .base import BotStrategy
from ..core.config import BotConfig
from ..core.state import BotState
from ..core.logger import Logger
from ..vision.target_finder import TargetFinder
from ..game.combat import CombatController
from ..game.movement import MovementController
from ..input.input_manager import InputManager


class DungeonRunnerStrategy(BotStrategy):
    """Strategy for running dungeons."""

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
        """Execute one iteration of dungeon running."""
        # Check for different dungeon phases
        dungeon_end = self.target_finder.find_ui_element(
            "dungeon_end", confidence=0.7, assets_folder="dungeons"
        )
        if dungeon_end:
            self.logger.info("Finished dungeon")
            return

        click_stone_phase = self.target_finder.find_ui_element(
            "click_stone", confidence=0.7, assets_folder="dungeons"
        )
        if click_stone_phase:
            self._handle_click_stone_phase()
            return

        kill_stones_phase = self.target_finder.find_ui_element(
            "kill_3_stones", confidence=0.7, assets_folder="dungeons"
        )
        stones_for_stone_phase = self.target_finder.find_ui_element(
            "stones_for_stone", confidence=0.7, assets_folder="dungeons"
        )

        if kill_stones_phase or stones_for_stone_phase:
            self._handle_destroy_stones_phase()
        else:
            self._handle_auto_phase()

    def _handle_click_stone_phase(self) -> None:
        """Handle the phase where we need to click on a stone."""
        self.logger.info("In click_stone phase")

        stone = self.target_finder.find_ui_element(
            "stone", confidence=0.7, assets_folder="dungeons"
        )
        if stone is None:
            self.logger.warning("Cannot see stone, waiting for user input...")
        else:
            self.input_manager.mouse.move_to(stone.left, stone.top)
            time.sleep(0.1)
            self.input_manager.mouse.click(button="right")

    def _handle_destroy_stones_phase(self) -> None:
        """Handle phases where we need to destroy stones."""
        self.input_manager.keyboard.keyboard.keyUp("space")
        self.logger.info("In destroy stones phase")

        stones = self.target_finder.find_stones(
            stone_names=["generic"],
            monitor_index=self.config.monitor_index,
            templates_folder="./src/assets/dungeons",
        )

        if stones:
            target = self.target_finder.calculate_closest_target(
                matches=stones,
                center_x=self.config.center_x,
                center_y=self.config.center_y,
                aspect_ratio=self.config.aspect_ratio,
                offset_x=-10,  # Dungeon-specific offset
                offset_y=85,
            )
            self.combat.attack_target(target)

    def _handle_auto_phase(self) -> None:
        """Handle auto-combat phases."""
        self.logger.info("Auto phase - holding space and using skills")
        self.input_manager.pickup_items("z")
        self.input_manager.keyboard.press("3")
        self.input_manager.keyboard.keyboard.keyDown("space")
        time.sleep(0.5)

    def should_continue(self) -> bool:
        """Check if the strategy should continue running."""
        if self.input_manager.check_exit_key():
            self.logger.info("Exit key pressed")
            self.state.stop()
            return False

        return self.state.is_running

    def cleanup(self) -> None:
        """Cleanup when strategy is stopped."""
        self.logger.info("Dungeon runner strategy stopped")
