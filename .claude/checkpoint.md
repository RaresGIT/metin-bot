# Metin Bot - Project Checkpoint

**Date:** 2025-10-11
**Project:** Metin2 Stone Farming Bot (Refactored)
**Location:** `D:\GitHub\metin-bot\`

## Project Overview

This is a Python automation bot for Metin2 game that automatically searches for and destroys metin stones. The bot uses computer vision (PyAutoGUI + OpenCV) to detect stones on screen and automates combat, camera movement, and buff management.

**Version 2.0** - Completely refactored with clean architecture, proper abstraction layers, and dependency injection.

## Architecture Overview

The refactored codebase follows a **layered architecture** with clear separation of concerns:

```
src/
├── core/           # Core abstractions (config, state, logging)
├── vision/         # Computer vision and target detection
├── input/          # Keyboard and mouse input abstraction
├── game/           # Game-specific logic (combat, movement, buffs)
├── strategies/     # Bot strategies (farming, mining, dungeons)
├── bot.py          # Main orchestrator
└── main.py         # Entry point

Legacy files (kept for backward compatibility):
├── metin.py        # Original implementation
├── utils.py        # Original utilities
├── mining.py       # Original mining script
├── dungeons.py     # Original dungeon script
└── config.json     # Configuration file
```

## New Architecture Benefits

1. **Dependency Injection** - No global state, all dependencies passed explicitly
2. **Single Responsibility** - Each class has one clear purpose
3. **Testability** - All components can be mocked and tested independently
4. **Extensibility** - Easy to add new strategies or modify behavior
5. **Type Safety** - Full type hints throughout
6. **Clean Interfaces** - Clear contracts between layers

## Layer Descriptions

### Core Layer (`src/core/`)

**Purpose:** Fundamental bot components used by all other layers

- **`config.py`** - Configuration management with validation
  - `BotConfig` dataclass with type-safe configuration
  - `from_json()` factory method for loading config
  - `validate()` method to ensure config correctness

- **`logger.py`** - Centralized logging
  - `Logger` class with debug/info/warning/error levels
  - Debug mode support
  - Timestamped output

- **`state.py`** - Bot runtime state management
  - `BotState` class tracks combat state, buff timing
  - `SelectedTarget` dataclass for target information
  - No global variables - all state encapsulated

### Vision Layer (`src/vision/`)

**Purpose:** Screen capture, image matching, target detection

- **`screen_capture.py`** - Screen capture and monitor management
  - `MonitorManager` - Multi-monitor detection and region calculation
  - `ScreenCapture` - Screenshot capture and debug image saving

- **`image_matcher.py`** - Template matching abstraction
  - `ImageMatcher` - Wrapper around PyAutoGUI template matching
  - `ImageMatch` - Data class for match results
  - Exception handling for missing templates

- **`target_finder.py`** - High-level target detection
  - `TargetFinder` - Finds stones, ores, UI elements
  - `calculate_closest_target()` - Distance calculation with aspect ratio
  - `find_combat_ui()` - HP bar and top bar detection

### Input Layer (`src/input/`)

**Purpose:** Keyboard and mouse input abstraction

- **`keyboard.py`** - Keyboard input operations
  - `KeyboardController` - Press, hold, combo support
  - Random timing for natural behavior
  - Key sequence support

- **`mouse.py`** - Mouse input operations
  - `MouseController` - Move, click, position tracking
  - Support for different mouse buttons

- **`input_manager.py`** - High-level input coordination
  - `InputManager` - Coordinates keyboard + mouse
  - Game-specific actions (attack, pickup, buffs)
  - Abstracts away input library details

### Game Layer (`src/game/`)

**Purpose:** Game-specific logic and mechanics

- **`window.py`** - Game window management
  - `GameWindow` - Window handle detection
  - Coordinate conversion (global ↔ client)
  - Direct window messaging (Win32 API)

- **`movement.py`** - Character and camera movement
  - `MovementController` - Camera rotation, character movement
  - `unstuck()` - Logic to escape being stuck
  - Random movement timings

- **`combat.py`** - Combat logic and stuck detection
  - `CombatController` - Attack, combat state management
  - Timer-based and UI-based combat detection
  - Stuck detection and recovery

- **`buff_manager.py`** - Buff refresh timing
  - `BuffManager` - Automatic buff refresh
  - Randomized intervals for natural behavior
  - Configurable buff keys

### Strategies Layer (`src/strategies/`)

**Purpose:** Different bot operating modes

- **`base.py`** - Abstract strategy interface
  - `BotStrategy` ABC defining strategy contract
  - `execute()` - Run one iteration
  - `should_continue()` - Check if should keep running
  - `cleanup()` - Cleanup on stop

- **`stone_farming.py`** - Metin stone farming strategy
  - `StoneFarmingStrategy` - Main farming logic
  - Supports timer-based and UI-based modes
  - UI pause detection (inventory)
  - Closest stone selection and attack

- **`ore_mining.py`** - Ore mining strategy
  - `OreMiningStrategy` - Mining ore nodes
  - Simplified combat (wait for mining animation)
  - Auto-pickup after mining

- **`dungeon_runner.py`** - Dungeon automation strategy
  - `DungeonRunnerStrategy` - Phase detection
  - Handles different dungeon objectives
  - Stone clicking, combat phases, auto-combat

### Bot Orchestrator (`src/bot.py`)

**Purpose:** Main bot coordinator

- **`MetinBot`** - Main orchestrator class
  - Initializes all components with dependency injection
  - Coordinates strategy execution with buff management
  - Factory methods for different bot types:
    - `create_stone_farming_bot()`
    - `create_ore_mining_bot()`
    - `create_dungeon_bot()`
  - Main run loop with error handling

## Dependencies Management

### Using Poetry (Recommended)

The project now uses Poetry for dependency management with a local `.venv` folder.

```bash
# Install Poetry (if not already installed)
python -m pip install poetry

# Configure Poetry to use local .venv
python -m poetry config virtualenvs.in-project true

# Install all dependencies (including dev)
python -m poetry install

# Install only production dependencies
python -m poetry install --only main

# Activate virtual environment
python -m poetry shell

# Run bot with Poetry
python -m poetry run metin-bot
```

### Using pip (Legacy)

```bash
pip install keyboard pyautogui pydirectinput pywin32 Pillow opencv-python screeninfo
```

**Package List:**
- `keyboard` - Keyboard input detection (ESC to exit)
- `pyautogui` - Screen capture and image recognition
- `pydirectinput` - Direct input for game controls
- `pywin32` - Windows API for window management
- `Pillow` - Image processing (PIL)
- `opencv-python` - Computer vision for template matching
- `screeninfo` - Multi-monitor support

**Dev Dependencies (Poetry only):**
- `pytest` - Testing framework
- `pytest-cov` - Code coverage
- `black` - Code formatter
- `isort` - Import sorter
- `mypy` - Type checker
- `flake8` - Linter

## Configuration (config.json)

```json
{
  "CENTER_X": 960,
  "CENTER_Y": 540,
  "OFFSET_X": 90,
  "OFFSET_Y": 50,
  "ASPECT_RATIO": 1.78,
  "STONE_NAMES": ["dragon"],
  "PICKUP_DROP": false,
  "LURE_KEY": "3",
  "DEADLINE": 6,
  "DEBUG": false,
  "WAIT_AFTER_STONE_DESTROYED": 7,
  "MONITOR_INDEX": 1,
  "BUFF_KEYS": "ctrl+v",
  "KEEP_BUFF_UPTIME": true,
  "BUFF_INTERVAL_MIN": 30,
  "BUFF_INTERVAL_MAX": 60
}
```

## Usage

### Running with Poetry (Recommended)

```bash
# Activate virtual environment
python -m poetry shell

# Run stone farming (default)
python -m poetry run metin-bot
# or simply: metin-bot (when shell is active)

# Run ore mining
python -m poetry run metin-bot-mining

# Run dungeon runner
python -m poetry run metin-bot-dungeon

# Or run directly with Python
python src/main.py
```

### Running without Poetry

```bash
# Run stone farming bot (default)
python src/main.py

# Or import and create custom bot
from src.bot import MetinBot

# Stone farming
bot = MetinBot.create_stone_farming_bot("config.json")
bot.run()

# Ore mining
bot = MetinBot.create_ore_mining_bot("config.json")
bot.run()

# Dungeon running
bot = MetinBot.create_dungeon_bot("config.json")
bot.run()
```

### Legacy Scripts (Still Available)

```bash
# Original implementation
python metin.py

# Original mining
python mining.py

# Original dungeons
python dungeons.py
```

## Key Improvements Over Original

### Before (Original Code)
- ❌ 20+ global variables in metin.py
- ❌ Mixed concerns in utils.py (vision + input + logging)
- ❌ Duplicated code across metin.py, mining.py, dungeons.py
- ❌ Hardcoded dependencies (window handle, game name)
- ❌ No abstraction layers - direct library calls everywhere
- ❌ Difficult to test or modify
- ❌ No type hints

### After (Refactored Code)
- ✅ Zero global variables - all state encapsulated
- ✅ Clean separation: core → vision → input → game → strategies
- ✅ Shared code via composition and inheritance
- ✅ Dependency injection throughout
- ✅ Multiple abstraction layers with clear interfaces
- ✅ Easily testable and modular
- ✅ Full type hints and documentation

## Development Workflow

### Adding a New Strategy

1. Create new strategy class in `src/strategies/`
2. Inherit from `BotStrategy` ABC
3. Implement `execute()`, `should_continue()`, `cleanup()`
4. Add factory method to `MetinBot` class
5. Use existing components via dependency injection

Example:
```python
from src.strategies.base import BotStrategy

class MyCustomStrategy(BotStrategy):
    def __init__(self, config, state, target_finder, combat, ...):
        self.config = config
        self.state = state
        # ... store dependencies

    def execute(self):
        # Your logic here
        pass

    def should_continue(self):
        return self.state.is_running

    def cleanup(self):
        self.logger.info("Custom strategy stopped")

# In bot.py
@classmethod
def create_custom_bot(cls, config_path: str) -> "MetinBot":
    config = BotConfig.from_json(config_path)
    config.validate()

    bot = cls.__new__(cls)
    bot.config = config
    bot.logger = Logger(debug=config.debug)
    bot._initialize_components()

    strategy = MyCustomStrategy(
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
```

### Modifying Behavior

**To change stone detection:**
- Modify `src/vision/target_finder.py`

**To change combat logic:**
- Modify `src/game/combat.py`

**To change movement:**
- Modify `src/game/movement.py`

**To change input handling:**
- Modify `src/input/` layer

Changes are isolated to single files with minimal side effects.

## Testing Strategy

Each layer can be tested independently:

```python
# Test vision layer with mock images
from src.vision import ImageMatcher, TargetFinder
matcher = ImageMatcher(logger, debug=True)
matches = matcher.find_all("test_stone.png", confidence=0.7)

# Test combat with mock state
from src.game import CombatController
combat = CombatController(mock_state, mock_input, mock_movement, logger)
combat.attack_target(target)

# Test strategy with mock dependencies
from src.strategies import StoneFarmingStrategy
strategy = StoneFarmingStrategy(mock_config, mock_state, ...)
strategy.execute()
```

## Features Implemented

### 1. Core Bot Functionality
- **Stone Detection** - Template matching with configurable confidence
- **Closest Stone Selection** - Distance calculation with aspect ratio correction
- **Auto Attack** - Click-to-attack with configurable offsets
- **Camera Movement** - Rotation and forward movement
- **Pickup/Drop** - Item looting after combat

### 2. Combat Modes

#### Timer-Based Mode (Recommended)
- Set `WAIT_AFTER_STONE_DESTROYED > 0` in config
- Waits configured time after attacking
- **No UI detection needed** - faster and more reliable
- Bypasses HP/top bar checking

#### UI-Based Mode (Legacy)
- Set `WAIT_AFTER_STONE_DESTROYED = 0` in config
- Uses image recognition for HP/top bar
- Waits for top bar to disappear
- Includes stuck detection and recovery

### 3. Multi-Monitor Support
- `MONITOR_INDEX` config option
- `0` = primary, `1` = second, etc.
- `null` = search all monitors
- Dynamic monitor detection

### 4. Debug Mode
- Detailed console logging
- Screenshot capture to `debug/` folder
- Execution flow visualization
- Monitor and configuration info

### 5. Buff Auto-Refresh
- Automatic buff key pressing
- Randomized intervals (30-60s default)
- Supports key combos (`ctrl+v`)
- Configurable timing

### 6. Error Handling
- Graceful handling of missing templates
- Monitor detection failures
- Exit key detection (ESC)
- Deadline checking

## Recent Changes & Fixes

### Session 2 (2025-10-11) - Complete Refactor & Poetry Setup

1. **Architecture Redesign**
   - Implemented layered architecture (core/vision/input/game/strategies)
   - Eliminated all global state
   - Added dependency injection throughout
   - Created abstract strategy pattern for bot modes

2. **Code Organization**
   - Split monolithic files into focused modules
   - Created clear interfaces between layers
   - Separated concerns (vision/input/logic/state)
   - Added comprehensive type hints

3. **New Components**
   - `BotConfig` dataclass with validation
   - `BotState` for runtime state management
   - `Logger` with debug levels
   - Component classes for all major subsystems
   - Factory methods for bot creation

4. **Improved Testability**
   - All components can be mocked
   - Clear contracts via ABC interfaces
   - Isolated functionality per module
   - No hardcoded dependencies

5. **Backward Compatibility**
   - Original scripts (metin.py, utils.py, etc.) preserved
   - Can still run legacy code
   - Config file format unchanged
   - Same dependencies

6. **Poetry Integration**
   - Added `pyproject.toml` with all dependencies
   - Configured for local `.venv` directory
   - Added dev dependencies (pytest, black, mypy, etc.)
   - Created Poetry CLI commands (metin-bot, metin-bot-mining, etc.)
   - Updated `.gitignore` for Poetry artifacts
   - Created comprehensive `README.md`

## Migration Guide

### For Users
- **No changes needed** - Original scripts still work
- To use refactored version: `python src/main.py`
- Config file format is identical

### For Developers
- Study `src/bot.py` to understand architecture
- Look at strategy implementations for patterns
- Use factory methods to create bots
- Follow dependency injection pattern
- Add type hints to new code

## Development Environment

- **OS:** Windows (win32)
- **Python:** 3.12+
- **Working Directory:** `D:\GitHub\metin-bot`
- **Game Window:** "Honor2.net!" (configurable in code)

## Future Enhancement Ideas

- Web dashboard for bot control
- Statistics and analytics tracking
- Machine learning for stone detection
- Path recording and playback
- Discord webhook notifications
- Auto-restart on disconnect
- HP/MP potion management
- Multiple character support
- Configuration GUI

## How to Resume Development

1. **Read this checkpoint** to understand the new architecture
2. **Review `src/bot.py`** to see how components connect
3. **Study strategy pattern** in `src/strategies/`
4. **Check layer interfaces** to understand contracts
5. **Enable DEBUG mode** to see execution flow
6. **Run tests** to verify functionality

## Quick Start Commands

### Windows (Recommended)

```batch
# Navigate to project
cd D:\GitHub\metin-bot

# Install dependencies (first time only)
python -m poetry install

# Activate environment using helper script
activate.bat

# Or activate manually
.\.venv\Scripts\activate

# Run refactored bot (stone farming)
python src/main.py

# Or use the convenience script
run.bat

# Run original bot (legacy, still works)
python metin.py

# Emergency stop
# Press ESC key while bot is running
```

### Using Poetry Commands

```bash
# Install dependencies
python -m poetry install

# Run with Poetry (no activation needed)
python -m poetry run python src/main.py

# Activate Poetry shell
python -m poetry shell

# Then run
python src/main.py
```

**Note:** If `poetry` command isn't recognized, always prefix with `python -m`

## Directory Structure (Complete)

```
D:\GitHub\metin-bot\
├── src/                          # New refactored code
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration dataclass
│   │   ├── logger.py             # Logging
│   │   └── state.py              # Runtime state
│   ├── vision/
│   │   ├── __init__.py
│   │   ├── screen_capture.py    # Screenshots, monitors
│   │   ├── image_matcher.py     # Template matching
│   │   └── target_finder.py     # Stone/UI detection
│   ├── input/
│   │   ├── __init__.py
│   │   ├── keyboard.py          # Keyboard control
│   │   ├── mouse.py             # Mouse control
│   │   └── input_manager.py    # High-level input
│   ├── game/
│   │   ├── __init__.py
│   │   ├── window.py            # Window management
│   │   ├── combat.py            # Combat logic
│   │   ├── movement.py          # Movement control
│   │   └── buff_manager.py      # Buff timing
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py              # Strategy ABC
│   │   ├── stone_farming.py    # Farming strategy
│   │   ├── ore_mining.py       # Mining strategy
│   │   └── dungeon_runner.py   # Dungeon strategy
│   ├── __init__.py
│   ├── bot.py                   # Main orchestrator
│   └── main.py                  # Entry point
│
├── .claude/
│   └── checkpoint.md            # This file
│
├── metin.py                     # Legacy: main bot
├── utils.py                     # Legacy: utilities
├── mining.py                    # Legacy: mining
├── dungeons.py                  # Legacy: dungeons
├── index.py                     # Legacy: GUI (WIP)
├── config.json                  # Configuration
│
├── stones/                      # Stone templates
│   └── *_stone.png
├── mining/                      # Ore templates
│   └── *_stone.png
├── dungeons/                    # Dungeon templates
│   └── *.png
├── utils/                       # UI templates
│   ├── hp_bar.png
│   ├── top_bar.png
│   └── on_screen_check.png
└── debug/                       # Debug screenshots
```

---

**Last Updated:** 2025-10-11
**Status:** Fully Refactored and Functional
**Next Session:** Ready for feature additions, testing, or further refinements
