"""Ore mining strategy implementation."""
import time

from .base import BotStrategy
from ..core.config import BotConfig
from ..core.state import BotState
from ..core.logger import Logger
from ..vision.target_finder import TargetFinder
from ..game.movement import MovementController
from ..input.input_manager import InputManager


class OreMiningStrategy(BotStrategy):
    """Strategy for mining ores."""

    def __init__(
        self,
        config: BotConfig,
        state: BotState,
        target_finder: TargetFinder,
        movement: MovementController,
        input_manager: InputManager,
        logger: Logger,
    ):
        self.config = config
        self.state = state
        self.target_finder = target_finder
        self.movement = movement
        self.input_manager = input_manager
        self.logger = logger

    def execute(self) -> None:
        """Execute one iteration of ore mining."""
        # Search for ores
        ores = self.target_finder.find_ores(
            ore_names=self.config.stone_names,
            monitor_index=self.config.monitor_index,
        )

        ores_found = len(ores)

        if ores_found == 0:
            self.movement.move_camera_and_search()
            return

        # Small backstep before mining
        self.input_manager.keyboard.hold("s", 0.01)
        time.sleep(0.1)

        # Attack closest ore
        target = self.target_finder.calculate_closest_target(
            matches=ores,
            center_x=self.config.center_x,
            center_y=self.config.center_y,
            aspect_ratio=self.config.aspect_ratio,
            offset_x=self.config.offset_x,
            offset_y=self.config.offset_y,
            center_exclusion_radius=self.config.center_exclusion_radius,
        )

        self.logger.info(f"Mining ore at {target.coords}")
        self.input_manager.attack_target(target.coords)

        # Wait for mining to complete
        time.sleep(13)

        # Pickup items
        self.input_manager.pickup_items()

    def should_continue(self) -> bool:
        """Check if the strategy should continue running."""
        if self.input_manager.check_exit_key():
            self.logger.info("Exit key pressed")
            self.state.stop()
            return False

        elapsed_hours = self.state.elapsed_hours()
        if elapsed_hours >= self.config.deadline:
            self.logger.info(f"Deadline reached!")
            self.state.stop()
            return False

        return self.state.is_running

    def cleanup(self) -> None:
        """Cleanup when strategy is stopped."""
        self.logger.info("Ore mining strategy stopped")
