"""Main bot orchestrator."""
import time

from .core.config import BotConfig
from .core.state import BotState
from .core.logger import Logger
from .vision.screen_capture import MonitorManager, ScreenCapture
from .vision.image_matcher import ImageMatcher
from .vision.target_finder import TargetFinder
from .input.input_manager import InputManager
from .input.hotkey_listener import HotkeyListener
from .game.window import GameWindow
from .game.combat import CombatController
from .game.movement import MovementController
from .game.buff_manager import BuffManager
from .strategies.base import BotStrategy


class MetinBot:
    """Main bot orchestrator that coordinates all components."""

    def __init__(self, config: BotConfig, strategy: BotStrategy):
        self.config = config
        self.strategy = strategy
        self.logger = Logger(debug=config.debug)

        # Initialize all components
        self._initialize_components()

        # Log startup info
        self._log_startup_info()

    def _initialize_components(self) -> None:
        """Initialize all bot components."""
        # Core
        self.state = BotState(
            buff_interval_min=self.config.buff_interval_min,
            buff_interval_max=self.config.buff_interval_max,
        )

        # Vision
        self.monitor_manager = MonitorManager(self.logger)
        self.screen_capture = ScreenCapture(self.logger, debug=self.config.debug)
        self.image_matcher = ImageMatcher(self.logger, debug=self.config.debug)
        self.target_finder = TargetFinder(
            self.image_matcher,
            self.screen_capture,
            self.monitor_manager,
            self.logger,
        )

        # Color-based target finder (new alternative approach)
        from .vision.color_target_finder import ColorTargetFinder
        self.color_target_finder = ColorTargetFinder(
            self.screen_capture,
            self.monitor_manager,
            self.logger,
            debug=self.config.debug,
        )

        # Input
        self.input_manager = InputManager(self.logger, debug=self.config.debug)
        self.hotkey_listener = HotkeyListener(self.logger)

        # Game
        self.game_window = GameWindow("Honor2.net!", self.logger)
        self.movement = MovementController(
            self.input_manager.keyboard, self.logger, debug=self.config.debug
        )
        self.combat = CombatController(
            self.state,
            self.input_manager,
            self.movement,
            self.logger,
            max_stuck_iterations=self.config.max_permitted_stuck_iterations,
            max_seconds_stuck=self.config.max_seconds_stuck,
        )
        self.buff_manager = BuffManager(
            self.state,
            self.input_manager,
            self.logger,
            enabled=self.config.keep_buff_uptime,
            interval_min=self.config.buff_interval_min,
            interval_max=self.config.buff_interval_max,
            buff_keys=self.config.buff_keys,
        )

    def _log_startup_info(self) -> None:
        """Log startup information."""
        if not self.config.debug:
            return

        self.logger.debug("=" * 50)
        self.logger.debug("DEBUG MODE ENABLED")
        self.logger.info(">>> Mouse clicks and keyboard inputs are DISABLED in debug mode <<<")
        self.logger.info(">>> Annotated images will be saved to debug/ folder <<<")
        self.logger.debug(
            f"Configuration: CENTER=({self.config.center_x}, {self.config.center_y}), "
            f"OFFSET=({self.config.offset_x}, {self.config.offset_y})"
        )
        self.logger.debug(
            f"ASPECT_RATIO={self.config.aspect_ratio}, DEADLINE={self.config.deadline}h"
        )
        self.logger.debug(f"STONE_NAMES={self.config.stone_names}")
        self.logger.debug(
            f"PICKUP_DROP={self.config.pickup_drop}, LURE_KEY={self.config.lure_key}"
        )

        # Monitor info
        self.monitor_manager.list_monitors()
        if self.config.monitor_index is not None:
            self.logger.debug(
                f"MONITOR_INDEX={self.config.monitor_index} (targeting specific monitor)"
            )
            monitor_region = self.monitor_manager.get_monitor_region(
                self.config.monitor_index
            )
            if monitor_region:
                self.logger.debug(f"  Monitor region: {monitor_region}")
        else:
            self.logger.debug("MONITOR_INDEX=None (searching all monitors)")

        # Mode info
        if self.config.wait_after_stone_destroyed > 0:
            self.logger.debug(
                f"WAIT_AFTER_STONE_DESTROYED={self.config.wait_after_stone_destroyed}s (Timer-based mode)"
            )
            self.logger.debug(
                "Top bar checking is DISABLED - using timer-based stone destruction detection"
            )
        else:
            self.logger.debug(
                f"WAIT_AFTER_STONE_DESTROYED={self.config.wait_after_stone_destroyed}s (Top bar mode)"
            )
            self.logger.debug("Using top bar checking for stone destruction detection")

        # Buff info
        if self.config.keep_buff_uptime:
            self.logger.debug("KEEP_BUFF_UPTIME=True")
            self.logger.debug(f"  Buff keys: {self.config.buff_keys}")
            self.logger.debug(
                f"  Buff interval: {self.config.buff_interval_min}-{self.config.buff_interval_max}s"
            )
            self.logger.debug(
                f"  Next buff in: {self.state.next_buff_interval:.1f}s"
            )
        else:
            self.logger.debug("KEEP_BUFF_UPTIME=False (buff refresh disabled)")

        self.logger.debug("=" * 50)

    def _setup_hotkeys(self) -> None:
        """Setup keyboard hotkeys for bot control."""
        # Pause hotkey
        self.hotkey_listener.register_hotkey(
            self.config.hotkey_pause,
            lambda: self._on_pause(),
            "Pause bot"
        )

        # Resume hotkey
        self.hotkey_listener.register_hotkey(
            self.config.hotkey_resume,
            lambda: self._on_resume(),
            "Resume bot"
        )

        # Toggle pause hotkey
        self.hotkey_listener.register_hotkey(
            self.config.hotkey_toggle_pause,
            lambda: self._on_toggle_pause(),
            "Toggle pause/resume"
        )

        # Stop hotkey
        self.hotkey_listener.register_hotkey(
            self.config.hotkey_stop,
            lambda: self._on_stop(),
            "Stop bot"
        )

        self.logger.info("=" * 50)
        self.logger.info("KEYBOARD SHORTCUTS:")
        self.logger.info(f"  {self.config.hotkey_pause.upper()}: Pause bot")
        self.logger.info(f"  {self.config.hotkey_resume.upper()}: Resume bot")
        self.logger.info(f"  {self.config.hotkey_toggle_pause.upper()}: Toggle pause/resume")
        self.logger.info(f"  {self.config.hotkey_stop.upper()}: Stop bot")
        self.logger.info("=" * 50)

    def _on_pause(self) -> None:
        """Handle pause hotkey."""
        if not self.state.is_paused:
            self.state.pause()
            self.logger.info("Bot PAUSED")

    def _on_resume(self) -> None:
        """Handle resume hotkey."""
        if self.state.is_paused:
            self.state.resume()
            self.logger.info("Bot RESUMED")

    def _on_toggle_pause(self) -> None:
        """Handle toggle pause hotkey."""
        self.state.toggle_pause()
        if self.state.is_paused:
            self.logger.info("Bot PAUSED")
        else:
            self.logger.info("Bot RESUMED")

    def _on_stop(self) -> None:
        """Handle stop hotkey."""
        self.logger.info(f"Stop hotkey ({self.config.hotkey_stop.upper()}) pressed - stopping bot...")
        self.state.stop()

    def run(self) -> None:
        """Run the bot main loop."""
        self.logger.info("Starting bot...")

        # Setup hotkeys
        self._setup_hotkeys()

        self.logger.info("Waiting 1 sec for alt tab!")
        time.sleep(1)

        try:
            while self.strategy.should_continue():
                # Check if paused
                if self.state.is_paused:
                    time.sleep(0.5)
                    continue

                # Check and refresh buffs
                self.buff_manager.check_and_refresh()

                # Execute strategy
                time.sleep(0.5)
                self.strategy.execute()

        except KeyboardInterrupt:
            self.logger.info("Bot stopped by user")
        except Exception as e:
            self.logger.error(f"Bot error: {e}")
            raise
        finally:
            self.hotkey_listener.unregister_all()
            self.strategy.cleanup()
            self.logger.info("Bot stopped")

    @classmethod
    def create_stone_farming_bot(cls, config_path: str = "config.json") -> "MetinBot":
        """
        Factory method to create a stone farming bot.

        Args:
            config_path: Path to configuration file

        Returns:
            Configured MetinBot instance
        """
        from .strategies.stone_farming import StoneFarmingStrategy

        config = BotConfig.from_json(config_path)
        config.validate()

        # Create bot instance without strategy first
        bot = cls.__new__(cls)
        bot.config = config
        bot.logger = Logger(debug=config.debug)
        bot._initialize_components()

        # Calculate screen center and aspect ratio from monitor
        center_x, center_y = bot.monitor_manager.get_screen_center(config.monitor_index)
        aspect_ratio = bot.monitor_manager.get_aspect_ratio(config.monitor_index)

        # Add calculated values to config
        bot.config.center_x = center_x
        bot.config.center_y = center_y
        bot.config.aspect_ratio = aspect_ratio

        # Create strategy with bot components
        strategy = StoneFarmingStrategy(
            config=bot.config,
            state=bot.state,
            target_finder=bot.target_finder,
            combat=bot.combat,
            movement=bot.movement,
            input_manager=bot.input_manager,
            logger=bot.logger,
        )

        bot.strategy = strategy
        bot._log_startup_info()

        return bot

    @classmethod
    def create_ore_mining_bot(cls, config_path: str = "config.json") -> "MetinBot":
        """Factory method to create an ore mining bot."""
        from .strategies.ore_mining import OreMiningStrategy

        config = BotConfig.from_json(config_path)
        config.validate()

        bot = cls.__new__(cls)
        bot.config = config
        bot.logger = Logger(debug=config.debug)
        bot._initialize_components()

        # Calculate screen center and aspect ratio from monitor
        center_x, center_y = bot.monitor_manager.get_screen_center(config.monitor_index)
        aspect_ratio = bot.monitor_manager.get_aspect_ratio(config.monitor_index)

        # Add calculated values to config
        bot.config.center_x = center_x
        bot.config.center_y = center_y
        bot.config.aspect_ratio = aspect_ratio

        strategy = OreMiningStrategy(
            config=bot.config,
            state=bot.state,
            target_finder=bot.target_finder,
            movement=bot.movement,
            input_manager=bot.input_manager,
            logger=bot.logger,
        )

        bot.strategy = strategy
        bot._log_startup_info()

        return bot

    @classmethod
    def create_dungeon_bot(cls, config_path: str = "config.json") -> "MetinBot":
        """Factory method to create a dungeon running bot."""
        from .strategies.dungeon_runner import DungeonRunnerStrategy

        config = BotConfig.from_json(config_path)
        config.validate()

        bot = cls.__new__(cls)
        bot.config = config
        bot.logger = Logger(debug=config.debug)
        bot._initialize_components()

        # Calculate screen center and aspect ratio from monitor
        center_x, center_y = bot.monitor_manager.get_screen_center(config.monitor_index)
        aspect_ratio = bot.monitor_manager.get_aspect_ratio(config.monitor_index)

        # Add calculated values to config
        bot.config.center_x = center_x
        bot.config.center_y = center_y
        bot.config.aspect_ratio = aspect_ratio

        strategy = DungeonRunnerStrategy(
            config=bot.config,
            state=bot.state,
            target_finder=bot.target_finder,
            combat=bot.combat,
            movement=bot.movement,
            input_manager=bot.input_manager,
            logger=bot.logger,
        )

        bot.strategy = strategy
        bot._log_startup_info()

        return bot
